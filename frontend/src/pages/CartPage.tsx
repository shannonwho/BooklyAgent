import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Trash2, Plus, Minus, ShoppingBag } from 'lucide-react';
import { useCartStore } from '../store/cartStore';
import { useAuthStore } from '../store/authStore';

export default function CartPage() {
  const { cart, fetchCart, updateQuantity, removeItem, isLoading } = useCartStore();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      fetchCart();
    }
  }, [isAuthenticated, fetchCart]);

  if (!isAuthenticated) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <ShoppingBag className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Please login to view your cart</h1>
        <Link to="/login" className="btn btn-primary">Login</Link>
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <ShoppingBag className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Your cart is empty</h1>
        <Link to="/books" className="btn btn-primary">Browse Books</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Shopping Cart</h1>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          {cart.items.map((item) => (
            <div key={item.id} className="card p-4 flex gap-4">
              <div className="w-20 h-28 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                <img src={item.book_cover || `https://picsum.photos/seed/${item.book_id}/80/112`} alt={item.book_title} className="w-full h-full object-cover" />
              </div>
              <div className="flex-1">
                <Link to={`/books/${item.book_id}`} className="font-medium text-gray-900 hover:text-primary-600">
                  {item.book_title}
                </Link>
                <p className="text-sm text-gray-500">{item.book_author}</p>
                <p className="text-primary-600 font-semibold">${item.book_price.toFixed(2)}</p>
              </div>
              <div className="flex flex-col items-end justify-between">
                <button onClick={() => removeItem(item.id)} className="text-gray-400 hover:text-red-500">
                  <Trash2 className="h-5 w-5" />
                </button>
                <div className="flex items-center gap-2">
                  <button onClick={() => updateQuantity(item.id, item.quantity - 1)} disabled={isLoading || item.quantity <= 1} className="p-1 rounded border hover:bg-gray-50 disabled:opacity-50">
                    <Minus className="h-4 w-4" />
                  </button>
                  <span className="w-8 text-center">{item.quantity}</span>
                  <button onClick={() => updateQuantity(item.id, item.quantity + 1)} disabled={isLoading} className="p-1 rounded border hover:bg-gray-50 disabled:opacity-50">
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="card p-6 h-fit">
          <h2 className="text-lg font-semibold mb-4">Order Summary</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Subtotal ({cart.total_items} items)</span>
              <span>${cart.subtotal.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Shipping</span>
              <span>{cart.shipping === 0 ? 'FREE' : `$${cart.shipping.toFixed(2)}`}</span>
            </div>
            {cart.shipping > 0 && <p className="text-xs text-gray-500">Free shipping on orders over $35</p>}
            <hr className="my-4" />
            <div className="flex justify-between text-lg font-semibold">
              <span>Total</span>
              <span>${cart.total.toFixed(2)}</span>
            </div>
          </div>
          <Link to="/checkout" className="btn btn-primary w-full mt-6">Proceed to Checkout</Link>
        </div>
      </div>
    </div>
  );
}
