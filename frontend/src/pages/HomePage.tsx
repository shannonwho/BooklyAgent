import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Star } from 'lucide-react';
import { booksApi } from '../services/api';
import { useAuthStore } from '../store/authStore';
import type { Book } from '../types';

function BookCard({ book }: { book: Book }) {
  return (
    <Link
      to={`/books/${book.id}`}
      className="card p-4 hover:shadow-md transition-shadow group"
    >
      <div className="aspect-[2/3] bg-gray-100 rounded-lg mb-3 overflow-hidden">
        <img
          src={book.cover_image || `https://picsum.photos/seed/${book.isbn}/200/300`}
          alt={book.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform"
        />
      </div>
      <h3 className="font-medium text-gray-900 line-clamp-1 group-hover:text-primary-600 transition-colors">
        {book.title}
      </h3>
      <p className="text-sm text-gray-500 line-clamp-1">{book.author}</p>
      <div className="flex items-center justify-between mt-2">
        <span className="text-primary-600 font-semibold">${book.price.toFixed(2)}</span>
        <div className="flex items-center text-sm text-gray-500">
          <Star className="h-4 w-4 text-yellow-400 fill-current mr-1" />
          {book.rating.toFixed(1)}
        </div>
      </div>
    </Link>
  );
}

export default function HomePage() {
  const [featuredBooks, setFeaturedBooks] = useState<Book[]>([]);
  const [recommendations, setRecommendations] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    async function fetchBooks() {
      try {
        const [featured, recs] = await Promise.all([
          booksApi.getFeaturedBooks(8),
          booksApi.getRecommendations(8),
        ]);
        setFeaturedBooks(featured);
        setRecommendations(recs);
      } catch (error) {
        console.error('Failed to fetch books:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchBooks();
  }, [isAuthenticated]);

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-50 to-primary-100 py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl lg:text-6xl font-bold text-gray-900 mb-6">
              Discover Your Next
              <span className="text-primary-600"> Great Read</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Browse thousands of books across all genres. Get personalized
              recommendations based on your reading preferences.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link to="/books" className="btn btn-primary px-8 py-3 text-lg">
                Browse Books
              </Link>
              {!isAuthenticated && (
                <Link to="/register" className="btn btn-outline px-8 py-3 text-lg">
                  Create Account
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* For You Section (when logged in) */}
      {isAuthenticated && recommendations.length > 0 && (
        <section className="py-12 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">For You</h2>
                <p className="text-gray-500">
                  Based on your preferences
                  {user?.favorite_genres && user.favorite_genres.length > 0 && (
                    <span> ({user.favorite_genres.join(', ')})</span>
                  )}
                </p>
              </div>
              <Link
                to="/books"
                className="text-primary-600 hover:text-primary-700 flex items-center"
              >
                View All <ArrowRight className="h-4 w-4 ml-1" />
              </Link>
            </div>
            {loading ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="card p-4 animate-pulse">
                    <div className="aspect-[2/3] bg-gray-200 rounded-lg mb-3" />
                    <div className="h-4 bg-gray-200 rounded mb-2" />
                    <div className="h-3 bg-gray-200 rounded w-2/3" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {recommendations.map((book) => (
                  <BookCard key={book.id} book={book} />
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Featured Books */}
      <section className="py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Featured Books</h2>
              <p className="text-gray-500">Top-rated books our readers love</p>
            </div>
            <Link
              to="/books"
              className="text-primary-600 hover:text-primary-700 flex items-center"
            >
              View All <ArrowRight className="h-4 w-4 ml-1" />
            </Link>
          </div>
          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="card p-4 animate-pulse">
                  <div className="aspect-[2/3] bg-gray-200 rounded-lg mb-3" />
                  <div className="h-4 bg-gray-200 rounded mb-2" />
                  <div className="h-3 bg-gray-200 rounded w-2/3" />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {featuredBooks.map((book) => (
                <BookCard key={book.id} book={book} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-primary-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Need Help Finding the Perfect Book?
          </h2>
          <p className="text-primary-100 mb-8 max-w-2xl mx-auto">
            Our AI-powered support assistant can help you with orders,
            recommendations, and any questions about our store.
          </p>
          <Link to="/support" className="btn bg-white text-primary-600 hover:bg-gray-100 px-8 py-3">
            Chat with Support
          </Link>
        </div>
      </section>
    </div>
  );
}
