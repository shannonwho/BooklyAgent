import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { CheckCircle, Package, ArrowRight, MessageCircle } from 'lucide-react';
import { ordersApi } from '../services/api';
import { useChatStore } from '../store/chatStore';
import type { Order } from '../types';

export default function OrderConfirmPage() {
  const { id } = useParams<{ id: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const { setIsOpen: setChatOpen } = useChatStore();

  useEffect(() => {
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
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="animate-pulse">
          <div className="h-16 w-16 bg-gray-200 rounded-full mx-auto mb-6" />
          <div className="h-8 bg-gray-200 rounded w-2/3 mx-auto mb-4" />
          <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto" />
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Order not found</h1>
        <Link to="/orders" className="text-primary-600 hover:underline">View all orders</Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
          <CheckCircle className="h-10 w-10 text-green-500" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Order Confirmed!</h1>
        <p className="text-gray-600">
          Thank you for your purchase. Your order has been received and is being processed.
        </p>
      </div>

      <div className="card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Order Details</h2>
          <span className="badge badge-info">{order.status}</span>
        </div>

        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Order Number</span>
            <span className="font-medium">{order.order_number}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Order Date</span>
            <span>{new Date(order.order_date).toLocaleDateString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Items</span>
            <span>{order.items.length} book{order.items.length !== 1 ? 's' : ''}</span>
          </div>
        </div>

        <hr className="my-4" />

        <div className="space-y-3">
          {order.items.map((item) => (
            <div key={item.id} className="flex gap-3">
              <div className="w-12 h-16 bg-gray-100 rounded overflow-hidden flex-shrink-0">
                <img
                  src={item.book_cover || `https://picsum.photos/seed/${item.book_id}/48/64`}
                  alt={item.book_title}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-900">{item.book_title}</p>
                <p className="text-sm text-gray-500">Qty: {item.quantity}</p>
              </div>
              <p className="font-medium">${item.subtotal.toFixed(2)}</p>
            </div>
          ))}
        </div>

        <hr className="my-4" />

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Subtotal</span>
            <span>${order.subtotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Shipping</span>
            <span>{order.shipping_cost === 0 ? 'FREE' : `$${order.shipping_cost.toFixed(2)}`}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Tax</span>
            <span>${order.tax.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-lg font-semibold pt-2">
            <span>Total</span>
            <span>${order.total_amount.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {order.shipping_address && (
        <div className="card p-6 mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Package className="h-5 w-5 text-gray-400" />
            <h3 className="font-semibold">Shipping To</h3>
          </div>
          <p className="text-gray-600">
            {order.shipping_address.name}<br />
            {order.shipping_address.street}<br />
            {order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.zip}
          </p>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-4">
        <Link to="/orders" className="flex-1 btn btn-primary py-3 flex items-center justify-center gap-2">
          View All Orders
          <ArrowRight className="h-4 w-4" />
        </Link>
        <Link to="/books" className="flex-1 btn btn-outline py-3">
          Continue Shopping
        </Link>
      </div>

      <div className="mt-8 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-start gap-3">
          <MessageCircle className="h-5 w-5 text-primary-600 mt-0.5" />
          <div>
            <p className="font-medium text-gray-900">Need help with your order?</p>
            <p className="text-sm text-gray-500 mb-2">
              Our support team is here to assist you with any questions.
            </p>
            <button
              onClick={() => setChatOpen(true)}
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              Chat with Support
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
