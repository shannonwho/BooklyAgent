import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { CreditCard, Truck, ArrowLeft, Lock } from 'lucide-react';
import { useCartStore } from '../store/cartStore';
import { useAuthStore } from '../store/authStore';
import { ordersApi } from '../services/api';

export default function CheckoutPage() {
  const { cart, fetchCart, clearCart } = useCartStore();
  const { isAuthenticated, user } = useAuthStore();
  const navigate = useNavigate();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [shipping, setShipping] = useState({
    name: '',
    street: '',
    city: '',
    state: '',
    zip: '',
  });

  const [payment, setPayment] = useState({
    cardNumber: '',
    expiry: '',
    cvv: '',
    cardName: '',
  });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    fetchCart();
  }, [isAuthenticated, fetchCart, navigate]);

  useEffect(() => {
    if (user) {
      setShipping((prev) => ({
        ...prev,
        name: user.name,
      }));
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      const order = await ordersApi.checkout({
        shipping_address: shipping,
      });
      clearCart();
      navigate(`/order-confirm/${order.id}`);
    } catch (err) {
      setError('Failed to process order. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!cart || cart.items.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Your cart is empty</h1>
        <Link to="/books" className="btn btn-primary">Browse Books</Link>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link to="/cart" className="inline-flex items-center text-gray-600 hover:text-primary-600 mb-8">
        <ArrowLeft className="h-5 w-5 mr-2" /> Back to Cart
      </Link>

      <h1 className="text-3xl font-bold text-gray-900 mb-8">Checkout</h1>

      {error && (
        <div className="p-4 bg-red-50 text-red-600 rounded-lg mb-6">{error}</div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            {/* Shipping Address */}
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4">
                <Truck className="h-5 w-5 text-primary-600" />
                <h2 className="text-lg font-semibold">Shipping Address</h2>
              </div>

              <div className="grid gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <input
                    type="text"
                    value={shipping.name}
                    onChange={(e) => setShipping({ ...shipping, name: e.target.value })}
                    className="input"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Street Address</label>
                  <input
                    type="text"
                    value={shipping.street}
                    onChange={(e) => setShipping({ ...shipping, street: e.target.value })}
                    className="input"
                    placeholder="123 Main St"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="col-span-2 md:col-span-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                    <input
                      type="text"
                      value={shipping.city}
                      onChange={(e) => setShipping({ ...shipping, city: e.target.value })}
                      className="input"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                    <input
                      type="text"
                      value={shipping.state}
                      onChange={(e) => setShipping({ ...shipping, state: e.target.value })}
                      className="input"
                      maxLength={2}
                      placeholder="CA"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">ZIP Code</label>
                    <input
                      type="text"
                      value={shipping.zip}
                      onChange={(e) => setShipping({ ...shipping, zip: e.target.value })}
                      className="input"
                      maxLength={5}
                      required
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Payment (Mocked) */}
            <div className="card p-6">
              <div className="flex items-center gap-3 mb-4">
                <CreditCard className="h-5 w-5 text-primary-600" />
                <h2 className="text-lg font-semibold">Payment Details</h2>
                <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">Demo Mode</span>
              </div>

              <div className="p-3 bg-blue-50 text-blue-700 rounded-lg text-sm mb-4">
                This is a demo checkout. No real payment will be processed.
              </div>

              <div className="grid gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Card Number</label>
                  <input
                    type="text"
                    value={payment.cardNumber}
                    onChange={(e) => setPayment({ ...payment, cardNumber: e.target.value })}
                    className="input"
                    placeholder="4242 4242 4242 4242"
                    maxLength={19}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name on Card</label>
                  <input
                    type="text"
                    value={payment.cardName}
                    onChange={(e) => setPayment({ ...payment, cardName: e.target.value })}
                    className="input"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date</label>
                    <input
                      type="text"
                      value={payment.expiry}
                      onChange={(e) => setPayment({ ...payment, expiry: e.target.value })}
                      className="input"
                      placeholder="MM/YY"
                      maxLength={5}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">CVV</label>
                    <input
                      type="text"
                      value={payment.cvv}
                      onChange={(e) => setPayment({ ...payment, cvv: e.target.value })}
                      className="input"
                      placeholder="123"
                      maxLength={4}
                      required
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Order Summary */}
          <div className="card p-6 h-fit sticky top-4">
            <h2 className="text-lg font-semibold mb-4">Order Summary</h2>

            <div className="space-y-3 mb-4">
              {cart.items.map((item) => (
                <div key={item.id} className="flex justify-between text-sm">
                  <span className="text-gray-600">
                    {item.book_title} x {item.quantity}
                  </span>
                  <span>${(item.book_price * item.quantity).toFixed(2)}</span>
                </div>
              ))}
            </div>

            <hr className="my-4" />

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span>${cart.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Shipping</span>
                <span>{cart.shipping === 0 ? 'FREE' : `$${cart.shipping.toFixed(2)}`}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tax (estimated)</span>
                <span>${(cart.subtotal * 0.08).toFixed(2)}</span>
              </div>
            </div>

            <hr className="my-4" />

            <div className="flex justify-between text-lg font-semibold mb-6">
              <span>Total</span>
              <span>${(cart.total + cart.subtotal * 0.08).toFixed(2)}</span>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full btn btn-primary py-3 flex items-center justify-center gap-2"
            >
              <Lock className="h-4 w-4" />
              {isSubmitting ? 'Processing...' : 'Place Order'}
            </button>

            <p className="text-xs text-gray-400 text-center mt-4">
              By placing your order, you agree to our Terms of Service and Privacy Policy
            </p>
          </div>
        </div>
      </form>
    </div>
  );
}
