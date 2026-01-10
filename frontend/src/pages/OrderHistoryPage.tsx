import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Package, ChevronRight, ShoppingBag } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { ordersApi } from '../services/api';
import type { Order } from '../types';

const statusColors: Record<string, string> = {
  pending: 'badge-warning',
  processing: 'badge-info',
  shipped: 'badge-info',
  delivered: 'badge-success',
  cancelled: 'badge-error',
  returned: 'badge-secondary',
};

export default function OrderHistoryPage() {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    async function fetchOrders() {
      try {
        const data = await ordersApi.getOrders();
        setOrders(data.orders);
      } catch (error) {
        console.error('Failed to fetch orders:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchOrders();
  }, [isAuthenticated, navigate]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Order History</h1>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="flex justify-between mb-4">
                <div className="h-5 bg-gray-200 rounded w-32" />
                <div className="h-5 bg-gray-200 rounded w-20" />
              </div>
              <div className="h-4 bg-gray-200 rounded w-48 mb-2" />
              <div className="h-4 bg-gray-200 rounded w-32" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <ShoppingBag className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-gray-900 mb-4">No orders yet</h1>
        <p className="text-gray-500 mb-6">Start shopping to see your orders here.</p>
        <Link to="/books" className="btn btn-primary">Browse Books</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Order History</h1>

      <div className="space-y-4">
        {orders.map((order) => (
          <Link
            key={order.id}
            to={`/orders/${order.id}`}
            className="card p-6 block hover:shadow-md transition-shadow"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-gray-100 rounded-lg">
                  <Package className="h-6 w-6 text-gray-600" />
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-semibold text-gray-900">{order.order_number}</span>
                    <span className={`badge ${statusColors[order.status] || 'badge-secondary'}`}>
                      {order.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">
                    {new Date(order.order_date).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {order.items.length} item{order.items.length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="font-semibold text-gray-900">${order.total_amount.toFixed(2)}</p>
                </div>
                <ChevronRight className="h-5 w-5 text-gray-400" />
              </div>
            </div>

            {/* Order items preview */}
            <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
              {order.items.slice(0, 4).map((item) => (
                <div
                  key={item.id}
                  className="w-12 h-16 bg-gray-100 rounded overflow-hidden flex-shrink-0"
                >
                  <img
                    src={item.book_cover || `https://picsum.photos/seed/${item.book_id}/48/64`}
                    alt={item.book_title}
                    className="w-full h-full object-cover"
                  />
                </div>
              ))}
              {order.items.length > 4 && (
                <div className="w-12 h-16 bg-gray-100 rounded flex items-center justify-center flex-shrink-0">
                  <span className="text-xs text-gray-500">+{order.items.length - 4}</span>
                </div>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
