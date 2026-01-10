import { Link } from 'react-router-dom';
import { BookOpen, MessageCircle } from 'lucide-react';
import { useChatStore } from '../../store/chatStore';

export default function Footer() {
  const { openChat } = useChatStore();

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <Link to="/" className="flex items-center space-x-2 mb-4">
              <BookOpen className="h-8 w-8 text-primary-400" />
              <span className="text-xl font-bold text-white">Bookly</span>
            </Link>
            <p className="text-gray-400 mb-4">
              Discover your next great read. Browse thousands of books across
              all genres with personalized recommendations.
            </p>
            <button
              onClick={openChat}
              className="flex items-center space-x-2 text-primary-400 hover:text-primary-300 transition-colors"
            >
              <MessageCircle className="h-5 w-5" />
              <span>Need help? Chat with us</span>
            </button>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/books" className="hover:text-white transition-colors">
                  Browse Books
                </Link>
              </li>
              <li>
                <Link to="/books?genre=Fiction" className="hover:text-white transition-colors">
                  Fiction
                </Link>
              </li>
              <li>
                <Link to="/books?genre=Sci-Fi" className="hover:text-white transition-colors">
                  Sci-Fi
                </Link>
              </li>
              <li>
                <Link to="/books?genre=Mystery" className="hover:text-white transition-colors">
                  Mystery
                </Link>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="text-white font-semibold mb-4">Support</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/support" className="hover:text-white transition-colors">
                  Contact Us
                </Link>
              </li>
              <li>
                <button
                  onClick={openChat}
                  className="hover:text-white transition-colors"
                >
                  Live Chat
                </button>
              </li>
              <li>
                <span className="text-gray-500">1-800-BOOKLY</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-500 text-sm">
          <p>&copy; {new Date().getFullYear()} Bookly. All rights reserved.</p>
          <p className="mt-2">
            Demo project - Built with React, FastAPI, and Claude AI
          </p>
        </div>
      </div>
    </footer>
  );
}
