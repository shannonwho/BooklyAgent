"""Book catalog and recommendations endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from data.database import get_db
from data.models import Book, Genre, Customer, OrderItem, Order
from api.auth import get_optional_user

router = APIRouter()


class BookResponse(BaseModel):
    id: int
    isbn: str
    title: str
    author: str
    genre: str
    price: float
    description: str
    cover_image: Optional[str]
    stock_quantity: int
    rating: float
    num_reviews: int
    page_count: int

    class Config:
        from_attributes = True


class BookListResponse(BaseModel):
    books: list[BookResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class GenreCount(BaseModel):
    genre: str
    count: int


@router.get("", response_model=BookListResponse)
async def get_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    genre: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: Optional[bool] = None,
    sort_by: str = Query("rating", regex="^(rating|price|title|newest)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_user),
):
    """Get paginated list of books with filtering and sorting."""
    query = select(Book)

    # Apply filters
    if genre:
        try:
            genre_enum = Genre(genre)
            query = query.where(Book.genre == genre_enum)
        except ValueError:
            pass  # Invalid genre, ignore filter

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Book.title.ilike(search_term),
                Book.author.ilike(search_term),
                Book.description.ilike(search_term),
            )
        )

    if min_price is not None:
        query = query.where(Book.price >= min_price)

    if max_price is not None:
        query = query.where(Book.price <= max_price)

    if in_stock:
        query = query.where(Book.stock_quantity > 0)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()

    # Apply sorting
    if sort_by == "rating":
        order_col = Book.rating
    elif sort_by == "price":
        order_col = Book.price
    elif sort_by == "title":
        order_col = Book.title
    elif sort_by == "newest":
        order_col = Book.publication_date
    else:
        order_col = Book.rating

    if sort_order == "desc":
        query = query.order_by(order_col.desc())
    else:
        query = query.order_by(order_col.asc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    books = result.scalars().all()

    return BookListResponse(
        books=[BookResponse(
            id=b.id,
            isbn=b.isbn,
            title=b.title,
            author=b.author,
            genre=b.genre.value,
            price=b.price,
            description=b.description,
            cover_image=b.cover_image,
            stock_quantity=b.stock_quantity,
            rating=b.rating,
            num_reviews=b.num_reviews,
            page_count=b.page_count,
        ) for b in books],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/genres", response_model=list[GenreCount])
async def get_genres(db: AsyncSession = Depends(get_db)):
    """Get list of genres with book counts."""
    query = select(Book.genre, func.count(Book.id)).group_by(Book.genre)
    result = await db.execute(query)
    genres = result.all()

    return [
        GenreCount(genre=g.value, count=count)
        for g, count in genres
    ]


@router.get("/featured", response_model=list[BookResponse])
async def get_featured_books(
    limit: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Get featured/trending books (highest rated with most reviews)."""
    query = (
        select(Book)
        .where(Book.stock_quantity > 0)
        .order_by(Book.rating.desc(), Book.num_reviews.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    books = result.scalars().all()

    return [BookResponse(
        id=b.id,
        isbn=b.isbn,
        title=b.title,
        author=b.author,
        genre=b.genre.value,
        price=b.price,
        description=b.description,
        cover_image=b.cover_image,
        stock_quantity=b.stock_quantity,
        rating=b.rating,
        num_reviews=b.num_reviews,
        page_count=b.page_count,
    ) for b in books]


@router.get("/recommendations", response_model=list[BookResponse])
async def get_recommendations(
    limit: int = Query(8, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[Customer] = Depends(get_optional_user),
):
    """Get personalized book recommendations based on user preferences and history."""
    if not current_user:
        # Return popular books for non-authenticated users
        return await get_featured_books(limit=limit, db=db)

    # Get user's favorite genres
    favorite_genres = current_user.favorite_genres or []

    # Get books user has already purchased
    purchased_query = (
        select(OrderItem.book_id)
        .join(Order)
        .where(Order.customer_id == current_user.id)
    )
    result = await db.execute(purchased_query)
    purchased_book_ids = [r[0] for r in result.all()]

    # Build recommendation query
    query = select(Book).where(Book.stock_quantity > 0)

    # Exclude already purchased books
    if purchased_book_ids:
        query = query.where(Book.id.notin_(purchased_book_ids))

    # If user has preferences, filter by them
    if favorite_genres:
        genre_enums = []
        for g in favorite_genres:
            try:
                genre_enums.append(Genre(g))
            except ValueError:
                pass

        if genre_enums:
            query = query.where(Book.genre.in_(genre_enums))

    # Order by rating
    query = query.order_by(Book.rating.desc(), Book.num_reviews.desc()).limit(limit)

    result = await db.execute(query)
    books = result.scalars().all()

    # If not enough books from preferences, add popular books
    if len(books) < limit:
        remaining = limit - len(books)
        existing_ids = [b.id for b in books] + purchased_book_ids

        fallback_query = (
            select(Book)
            .where(Book.stock_quantity > 0)
            .where(Book.id.notin_(existing_ids) if existing_ids else True)
            .order_by(Book.rating.desc(), Book.num_reviews.desc())
            .limit(remaining)
        )
        result = await db.execute(fallback_query)
        books.extend(result.scalars().all())

    return [BookResponse(
        id=b.id,
        isbn=b.isbn,
        title=b.title,
        author=b.author,
        genre=b.genre.value,
        price=b.price,
        description=b.description,
        cover_image=b.cover_image,
        stock_quantity=b.stock_quantity,
        rating=b.rating,
        num_reviews=b.num_reviews,
        page_count=b.page_count,
    ) for b in books]


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single book by ID."""
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    return BookResponse(
        id=book.id,
        isbn=book.isbn,
        title=book.title,
        author=book.author,
        genre=book.genre.value,
        price=book.price,
        description=book.description,
        cover_image=book.cover_image,
        stock_quantity=book.stock_quantity,
        rating=book.rating,
        num_reviews=book.num_reviews,
        page_count=book.page_count,
    )


@router.get("/{book_id}/similar", response_model=list[BookResponse])
async def get_similar_books(
    book_id: int,
    limit: int = Query(4, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """Get similar books based on genre and author."""
    # Get the original book
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Find similar books (same genre, exclude the original)
    query = (
        select(Book)
        .where(Book.id != book_id)
        .where(Book.stock_quantity > 0)
        .where(
            or_(
                Book.genre == book.genre,
                Book.author == book.author,
            )
        )
        .order_by(Book.rating.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    similar_books = result.scalars().all()

    return [BookResponse(
        id=b.id,
        isbn=b.isbn,
        title=b.title,
        author=b.author,
        genre=b.genre.value,
        price=b.price,
        description=b.description,
        cover_image=b.cover_image,
        stock_quantity=b.stock_quantity,
        rating=b.rating,
        num_reviews=b.num_reviews,
        page_count=b.page_count,
    ) for b in similar_books]
