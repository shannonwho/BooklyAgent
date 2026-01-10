import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Star, ShoppingCart, ArrowLeft } from 'lucide-react';
import { booksApi } from '../services/api';
import { useCartStore } from '../store/cartStore';
import { useAuthStore } from '../store/authStore';
import type { Book } from '../types';

export default function BookDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [book, setBook] = useState<Book | null>(null);
  const [similarBooks, setSimilarBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [addingToCart, setAddingToCart] = useState(false);
  const { addToCart } = useCartStore();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    async function fetchBook() {
      if (!id) return;
      setLoading(true);
      try {
        const [bookData, similar] = await Promise.all([
          booksApi.getBook(parseInt(id)),
          booksApi.getSimilarBooks(parseInt(id), 4),
        ]);
        setBook(bookData);
        setSimilarBooks(similar);
      } catch (error) {
        console.error('Failed to fetch book:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchBook();
  }, [id]);

  const handleAddToCart = async () => {
    if (!book || !isAuthenticated) return;
    setAddingToCart(true);
    try {
      await addToCart(book.id);
    } finally {
      setAddingToCart(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="animate-pulse">
          <div className="h-8 w-48 bg-gray-200 rounded mb-8" />
          <div className="grid md:grid-cols-2 gap-8">
            <div className="aspect-[2/3] bg-gray-200 rounded-xl" />
            <div className="space-y-4">
              <div className="h-8 bg-gray-200 rounded w-3/4" />
              <div className="h-6 bg-gray-200 rounded w-1/2" />
              <div className="h-24 bg-gray-200 rounded" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Book not found</h1>
        <Link to="/books" className="text-primary-600 hover:underline">
          Back to catalog
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link to="/books" className="inline-flex items-center text-gray-600 hover:text-primary-600 mb-8">
        <ArrowLeft className="h-5 w-5 mr-2" /> Back to catalog
      </Link>

      <div className="grid md:grid-cols-2 gap-12">
        <div className="aspect-[2/3] bg-gray-100 rounded-xl overflow-hidden">
          <img
            src={book.cover_image || `https://picsum.photos/seed/${book.isbn}/400/600`}
            alt={book.title}
            className="w-full h-full object-cover"
          />
        </div>

        <div>
          <span className="badge badge-info mb-4">{book.genre}</span>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{book.title}</h1>
          <p className="text-xl text-gray-600 mb-4">by {book.author}</p>

          <div className="flex items-center gap-4 mb-6">
            <div className="flex items-center">
              <Star className="h-5 w-5 text-yellow-400 fill-current mr-1" />
              <span className="font-medium">{book.rating.toFixed(1)}</span>
              <span className="text-gray-500 ml-1">({book.num_reviews} reviews)</span>
            </div>
            <span className="text-gray-300">|</span>
            <span className="text-gray-500">{book.page_count} pages</span>
          </div>

          <p className="text-gray-600 mb-8">{book.description}</p>

          <div className="flex items-center gap-4 mb-8">
            <span className="text-3xl font-bold text-primary-600">${book.price.toFixed(2)}</span>
            {book.stock_quantity > 0 ? (
              <span className="badge badge-success">In Stock</span>
            ) : (
              <span className="badge badge-error">Out of Stock</span>
            )}
          </div>

          {isAuthenticated ? (
            <button
              onClick={handleAddToCart}
              disabled={book.stock_quantity === 0 || addingToCart}
              className="btn btn-primary px-8 py-3"
            >
              <ShoppingCart className="h-5 w-5 mr-2" />
              {addingToCart ? 'Adding...' : 'Add to Cart'}
            </button>
          ) : (
            <Link to="/login" className="btn btn-primary px-8 py-3">
              Login to Purchase
            </Link>
          )}
        </div>
      </div>

      {similarBooks.length > 0 && (
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Similar Books</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {similarBooks.map((b) => (
              <Link key={b.id} to={`/books/${b.id}`} className="card p-4 hover:shadow-md transition-shadow">
                <div className="aspect-[2/3] bg-gray-100 rounded-lg mb-3 overflow-hidden">
                  <img src={b.cover_image || `https://picsum.photos/seed/${b.isbn}/200/300`} alt={b.title} className="w-full h-full object-cover" />
                </div>
                <h3 className="font-medium text-gray-900 line-clamp-1">{b.title}</h3>
                <p className="text-sm text-gray-500">{b.author}</p>
                <span className="text-primary-600 font-semibold">${b.price.toFixed(2)}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
