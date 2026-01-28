import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Search, Star, ChevronLeft, ChevronRight } from 'lucide-react';
import { booksApi } from '../services/api';
import type { Book, BookListResponse } from '../types';
import { GENRES } from '../types';

export default function CatalogPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [books, setBooks] = useState<Book[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);

  const page = parseInt(searchParams.get('page') || '1');
  const genre = searchParams.get('genre') || '';
  const search = searchParams.get('search') || '';
  const sortBy = searchParams.get('sort_by') || '';
  const sortOrder = searchParams.get('sort_order') || 'desc';

  useEffect(() => {
    async function fetchBooks() {
      setLoading(true);
      try {
        const response = await booksApi.getBooks({
          page,
          page_size: 20,
          genre: genre || undefined,
          search: search || undefined,
          sort_by: sortBy || undefined,
          sort_order: sortOrder || undefined,
        });
        setBooks(response.books);
        setTotal(response.total);
        setTotalPages(response.total_pages);
      } catch (error) {
        console.error('Failed to fetch books:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchBooks();
  }, [page, genre, search, sortBy, sortOrder]);

  const updateParams = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams);
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    if (key !== 'page') params.set('page', '1');
    setSearchParams(params);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Browse Books</h1>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search books..."
            value={search}
            onChange={(e) => updateParams('search', e.target.value)}
            className="input pl-10"
          />
        </div>
        <select
          value={genre}
          onChange={(e) => updateParams('genre', e.target.value)}
          className="input w-full md:w-[217px]"
        >
          <option value="">All Genres</option>
          {GENRES.map((g) => (
            <option key={g} value={g}>{g}</option>
          ))}
        </select>
        <select
          value={sortBy ? `${sortBy}_${sortOrder}` : ''}
          onChange={(e) => {
            const value = e.target.value;
            if (value) {
              const [by, order] = value.split('_');
              const params = new URLSearchParams(searchParams);
              params.set('sort_by', by);
              params.set('sort_order', order);
              params.set('page', '1');
              setSearchParams(params);
            } else {
              const params = new URLSearchParams(searchParams);
              params.delete('sort_by');
              params.delete('sort_order');
              params.set('page', '1');
              setSearchParams(params);
            }
          }}
          className="input w-full md:w-[217px]"
        >
          <option value="">Sort by Rating</option>
          <option value="rating_desc">Rating: High to Low</option>
          <option value="rating_asc">Rating: Low to High</option>
        </select>
      </div>

      <p className="text-gray-500 mb-4">{total} books found</p>

      {/* Books Grid */}
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
          {[...Array(20)].map((_, i) => (
            <div key={i} className="card p-4 animate-pulse">
              <div className="aspect-[2/3] bg-gray-200 rounded-lg mb-3" />
              <div className="h-4 bg-gray-200 rounded mb-2" />
              <div className="h-3 bg-gray-200 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
          {books.map((book) => (
            <Link key={book.id} to={`/books/${book.id}`} className="card p-4 hover:shadow-md transition-shadow group">
              <div className="aspect-[2/3] bg-gray-100 rounded-lg mb-3 overflow-hidden">
                <img
                  src={book.cover_image || `https://picsum.photos/seed/${book.isbn}/200/300`}
                  alt={book.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                />
              </div>
              <h3 className="font-medium text-gray-900 line-clamp-1">{book.title}</h3>
              <p className="text-sm text-gray-500 line-clamp-1">{book.author}</p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-primary-600 font-semibold">${book.price.toFixed(2)}</span>
                <div className="flex items-center text-sm text-gray-500">
                  <Star className="h-4 w-4 text-yellow-400 fill-current mr-1" />
                  {book.rating.toFixed(1)}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-4 mt-8">
          <button
            onClick={() => updateParams('page', String(page - 1))}
            disabled={page <= 1}
            className="btn btn-outline"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
          <span className="text-gray-600">Page {page} of {totalPages}</span>
          <button
            onClick={() => updateParams('page', String(page + 1))}
            disabled={page >= totalPages}
            className="btn btn-outline"
          >
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      )}
    </div>
  );
}
