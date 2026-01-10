import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Users } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../services/api';
import type { DemoAccount } from '../types';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [demoAccounts, setDemoAccounts] = useState<DemoAccount[]>([]);
  const [showDemoAccounts, setShowDemoAccounts] = useState(false);

  const { login, isLoading, error, clearError, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    // Fetch demo accounts
    authApi.getDemoAccounts().then(setDemoAccounts).catch(console.error);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    try {
      await login({ email, password });
      navigate('/');
    } catch {
      // Error handled in store
    }
  };

  const handleDemoLogin = async (account: DemoAccount) => {
    setEmail(account.email);
    setPassword('demo123');
    clearError();

    try {
      await login({ email: account.email, password: 'demo123' });
      navigate('/');
    } catch {
      // Error handled in store
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Welcome back</h1>
          <p className="text-gray-500 mt-2">Sign in to your Bookly account</p>
        </div>

        <div className="card p-8">
          {/* Demo Account Selector */}
          <div className="mb-6">
            <button
              type="button"
              onClick={() => setShowDemoAccounts(!showDemoAccounts)}
              className="w-full btn btn-secondary flex items-center justify-center space-x-2"
            >
              <Users className="h-5 w-5" />
              <span>Quick Login with Demo Account</span>
            </button>

            {showDemoAccounts && (
              <div className="mt-4 max-h-64 overflow-y-auto space-y-2">
                {demoAccounts.map((account) => (
                  <button
                    key={account.email}
                    onClick={() => handleDemoLogin(account)}
                    disabled={isLoading}
                    className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors disabled:opacity-50"
                  >
                    <div className="font-medium text-gray-900">{account.name}</div>
                    <div className="text-sm text-gray-500">{account.email}</div>
                    <div className="text-xs text-gray-400 mt-1">
                      {account.description}
                    </div>
                    {account.preferences.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {account.preferences.map((pref) => (
                          <span
                            key={pref}
                            className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                          >
                            {pref}
                          </span>
                        ))}
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-white text-gray-500">or sign in manually</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="you@example.com"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pr-10"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn btn-primary py-3"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="text-center text-gray-500 mt-6">
            Don't have an account?{' '}
            <Link to="/register" className="text-primary-600 hover:text-primary-700 font-medium">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
