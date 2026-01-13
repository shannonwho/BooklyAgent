import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Package, Truck, CheckCircle, Clock, XCircle, RotateCcw, MessageCircle } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { ordersApi } from '../services/api';
import { useChatStore } from '../store/chatStore';
import type { Order } from '../types';

const statusIcons: Record<string, React.ReactNode> = {
  pending: <Clock className="h-5 w-5" />,
  processing: <Package className="h-5 w-5" />,
  shipped: <Truck className="h-5 w-5" />,
  delivered: <CheckCircle className="h-5 w-5" />,
  cancelled: <XCircle className="h-5 w-5" />,
  returned: <RotateCcw className="h-5 w-5" />,
};

const statusColors: Record<string, string> = {
  pending: 'text-yellow-600 bg-yellow-50',
  processing: 'text-blue-600 bg-blue-50',
  shipped: 'text-blue-600 bg-blue-50',
  delivered: 'text-green-600 bg-green-50',
  cancelled: 'text-red-600 bg-red-50',
  returned: 'text-gray-600 bg-gray-50',
};

const statusDescriptions: Record<string, string> = {
  pending: 'Your order is being reviewed',
  processing: 'Your order is being prepared',
  shipped: 'Your order is on the way',
  delivered: 'Your order has been delivered',
  cancelled: 'This order was cancelled',
  returned: 'This order was returned',
};

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const { openChat, sendMessage } = useChatStore();
  const { user } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    async function fetchOrder() {
      if (!id) return;
      try {
        const data = await ordersApi.getOrder(parseInt(id));
        setOrder(data);
      } catch (error) {
        console.error('Failed to fetch order:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchOrder();
  }, [id, isAuthenticated, navigate]);

  const handleGetHelp = () => {
    openChat();
    if (order) {
      // Small delay to ensure chat is open and connected before sending
      setTimeout(() => {
        sendMessage(`I need help with order ${order.order_number}`, user?.email);
      }, 500);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-32 mb-8" />
          <div className="card p-6">
            <div className="h-8 bg-gray-200 rounded w-48 mb-4" />
            <div className="h-4 bg-gray-200 rounded w-32 mb-2" />
            <div className="h-4 bg-gray-200 rounded w-64" />
          </div>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Order not found</h1>
        <Link to="/orders" className="text-primary-600 hover:underline">View all orders</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link to="/orders" className="inline-flex items-center text-gray-600 hover:text-primary-600 mb-8">
        <ArrowLeft className="h-5 w-5 mr-2" /> Back to Orders
      </Link>

      {/* Order Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{order.order_number}</h1>
          <p className="text-gray-500">
            Placed on {new Date(order.order_date).toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>
        <button
          onClick={handleGetHelp}
          className="btn btn-outline flex items-center gap-2"
        >
          <MessageCircle className="h-4 w-4" />
          Need Help?
        </button>
      </div>

      {/* Status Banner */}
      <div className={`rounded-lg p-4 mb-8 ${statusColors[order.status] || 'bg-gray-50'}`}>
        <div className="flex items-center gap-3">
          {statusIcons[order.status]}
          <div>
            <p className="font-semibold capitalize">{order.status}</p>
            <p className="text-sm opacity-80">{statusDescriptions[order.status]}</p>
          </div>
        </div>
        {order.tracking_number && (
          <div className="mt-3 pt-3 border-t border-current border-opacity-20">
            <p className="text-sm">
              Tracking Number: <span className="font-mono font-medium">{order.tracking_number}</span>
            </p>
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          {/* Order Items */}
          <div className="card p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Order Items</h2>
            <div className="space-y-4">
              {order.items.map((item) => (
                <div key={item.id} className="flex gap-4">
                  <Link to={`/books/${item.book_id}`} className="flex-shrink-0">
                    <div className="w-16 h-24 bg-gray-100 rounded overflow-hidden">
                      <img
                        src={item.book_cover || `https://picsum.photos/seed/${item.book_id}/64/96`}
                        alt={item.book_title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  </Link>
                  <div className="flex-1">
                    <Link to={`/books/${item.book_id}`} className="font-medium text-gray-900 hover:text-primary-600">
                      {item.book_title}
                    </Link>
                    <p className="text-sm text-gray-500">{item.book_author}</p>
                    <p className="text-sm text-gray-500">Qty: {item.quantity}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">${item.subtotal.toFixed(2)}</p>
                    <p className="text-sm text-gray-500">${item.price_per_unit.toFixed(2)} each</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Shipping Address */}
          {order.shipping_address && (
            <div className="card p-6">
              <h2 className="text-lg font-semibold mb-4">Shipping Address</h2>
              <div className="text-gray-600">
                <p className="font-medium text-gray-900">{order.shipping_address.name}</p>
                <p>{order.shipping_address.street}</p>
                <p>
                  {order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.zip}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Order Summary */}
        <div className="card p-6 h-fit">
          <h2 className="text-lg font-semibold mb-4">Order Summary</h2>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Subtotal</span>
              <span>${order.subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Shipping</span>
              <span>{order.shipping_cost === 0 ? 'FREE' : `$${order.shipping_cost.toFixed(2)}`}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Tax</span>
              <span>${order.tax.toFixed(2)}</span>
            </div>
            <hr className="my-2" />
            <div className="flex justify-between text-lg font-semibold">
              <span>Total</span>
              <span>${order.total_amount.toFixed(2)}</span>
            </div>
          </div>

          {(order.status === 'delivered' || order.status === 'shipped') && (
            <div className="mt-6 pt-4 border-t">
              <p className="text-sm text-gray-500 mb-2">Need to return an item?</p>
              <button
                onClick={handleGetHelp}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                Start a return request
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
