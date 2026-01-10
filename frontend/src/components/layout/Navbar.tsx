import { Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, User, BookOpen, LogOut, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { useAuthStore } from '../../store/authStore';
import { useCartStore } from '../../store/cartStore';

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { user, isAuthenticated, logout } = useAuthStore();
  const { cart } = useCartStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const cartItemCount = cart?.total_items || 0;

  return (
    <nav className="bg-white shadow-sm sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <BookOpen className="h-8 w-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">Bookly</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              to="/books"
              className="text-gray-600 hover:text-primary-600 transition-colors"
            >
              Browse Books
            </Link>
            <Link
              to="/support"
              className="text-gray-600 hover:text-primary-600 transition-colors"
            >
              Support
            </Link>
          </div>

          {/* Right side */}
          <div className="hidden md:flex items-center space-x-4">
            {/* Cart */}
            <Link
              to="/cart"
              className="relative p-2 text-gray-600 hover:text-primary-600 transition-colors"
            >
              <ShoppingCart className="h-6 w-6" />
              {cartItemCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-primary-600 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
                  {cartItemCount}
                </span>
              )}
            </Link>

            {/* Auth */}
            {isAuthenticated ? (
              <div className="relative group">
                <button className="flex items-center space-x-2 p-2 text-gray-600 hover:text-primary-600 transition-colors">
                  <User className="h-6 w-6" />
                  <span className="text-sm">{user?.name?.split(' ')[0]}</span>
                </button>
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                  <Link
                    to="/profile"
                    className="block px-4 py-2 text-gray-700 hover:bg-gray-100"
                  >
                    Profile
                  </Link>
                  <Link
                    to="/orders"
                    className="block px-4 py-2 text-gray-700 hover:bg-gray-100"
                  >
                    My Orders
                  </Link>
                  <hr className="my-2" />
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Logout</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Link
                  to="/login"
                  className="btn btn-outline text-sm"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="btn btn-primary text-sm"
                >
                  Sign Up
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 text-gray-600"
            >
              {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMenuOpen && (
        <div className="md:hidden bg-white border-t">
          <div className="px-4 py-4 space-y-4">
            <Link
              to="/books"
              className="block text-gray-600"
              onClick={() => setIsMenuOpen(false)}
            >
              Browse Books
            </Link>
            <Link
              to="/cart"
              className="block text-gray-600"
              onClick={() => setIsMenuOpen(false)}
            >
              Cart ({cartItemCount})
            </Link>
            <Link
              to="/support"
              className="block text-gray-600"
              onClick={() => setIsMenuOpen(false)}
            >
              Support
            </Link>
            {isAuthenticated ? (
              <>
                <Link
                  to="/profile"
                  className="block text-gray-600"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Profile
                </Link>
                <Link
                  to="/orders"
                  className="block text-gray-600"
                  onClick={() => setIsMenuOpen(false)}
                >
                  My Orders
                </Link>
                <button
                  onClick={() => {
                    handleLogout();
                    setIsMenuOpen(false);
                  }}
                  className="block text-gray-600"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="block text-gray-600"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="block text-primary-600 font-medium"
                  onClick={() => setIsMenuOpen(false)}
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
