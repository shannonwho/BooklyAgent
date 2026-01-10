import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Save, Check } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { profileApi } from '../services/api';
import { GENRES } from '../types';

export default function ProfilePage() {
  const { user, isAuthenticated, updateUser } = useAuthStore();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    if (user) {
      setName(user.name);
      setEmail(user.email);
      setSelectedGenres(user.favorite_genres || []);
    }
  }, [isAuthenticated, user, navigate]);

  const toggleGenre = (genre: string) => {
    setSelectedGenres((prev) =>
      prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]
    );
    setSaved(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSaved(false);

    try {
      const updated = await profileApi.updateProfile({
        name,
        favorite_genres: selectedGenres,
      });
      updateUser(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center gap-4 mb-8">
        <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
          <User className="h-8 w-8 text-primary-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
          <p className="text-gray-500">Manage your account settings and preferences</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="p-3 bg-red-50 text-red-600 rounded-lg text-sm">{error}</div>
        )}

        {saved && (
          <div className="p-3 bg-green-50 text-green-600 rounded-lg text-sm flex items-center gap-2">
            <Check className="h-4 w-4" />
            Profile updated successfully!
          </div>
        )}

        <div className="card p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Account Information</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setSaved(false);
              }}
              className="input"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              disabled
              className="input bg-gray-50 text-gray-500 cursor-not-allowed"
            />
            <p className="text-xs text-gray-400 mt-1">Email cannot be changed</p>
          </div>
        </div>

        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Reading Preferences</h2>
          <p className="text-sm text-gray-500 mb-4">
            Select your favorite genres to get personalized book recommendations
          </p>

          <div className="flex flex-wrap gap-2">
            {GENRES.map((genre) => (
              <button
                key={genre}
                type="button"
                onClick={() => toggleGenre(genre)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  selectedGenres.includes(genre)
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {genre}
              </button>
            ))}
          </div>

          {selectedGenres.length > 0 && (
            <p className="text-sm text-gray-500 mt-4">
              Selected: {selectedGenres.join(', ')}
            </p>
          )}
        </div>

        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Account Stats</h2>
          <div className="grid grid-cols-2 gap-4 text-center">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-primary-600">{user.order_count || 0}</p>
              <p className="text-sm text-gray-500">Orders Placed</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-primary-600">{selectedGenres.length}</p>
              <p className="text-sm text-gray-500">Favorite Genres</p>
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="w-full btn btn-primary py-3 flex items-center justify-center gap-2"
        >
          {saving ? (
            'Saving...'
          ) : (
            <>
              <Save className="h-5 w-5" />
              Save Changes
            </>
          )}
        </button>
      </form>
    </div>
  );
}
