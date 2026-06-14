import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import FormField from '../components/FormField';
import Loader from '../components/Loader';
import PageHeader from '../components/PageHeader';
import { useAuth } from '../context/AuthContext';
import { getProductsRequest } from '../services/catalogService';
import {
  createOrderRequest,
  deleteCartItemRequest,
  getMyCartItemsRequest,
  recordPaymentRequest,
} from '../services/commerceService';
import { buildProductLookup, calculateCartSubtotal, enrichCartItems } from '../utils/cart';
import { formatCurrency } from '../utils/format';
import { createEmptyErrors, validateRequired } from '../utils/validators';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [cartItems, setCartItems] = useState([]);
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState({
    shipping_address: '',
    billing_address: '',
    payment_method: 'card',
  });
  const [formErrors, setFormErrors] = useState(createEmptyErrors());

  async function loadCheckout() {
    try {
      setLoading(true);
      setError('');
      const [cartData, productData] = await Promise.all([getMyCartItemsRequest(), getProductsRequest()]);
      setCartItems(cartData);
      setProducts(productData);
    } catch (loadError) {
      setError(loadError?.response?.data?.detail || 'Failed to load checkout data.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCheckout();
  }, []);

  const productLookup = useMemo(() => buildProductLookup(products), [products]);
  const enrichedItems = useMemo(() => enrichCartItems(cartItems, productLookup), [cartItems, productLookup]);
  const subtotal = useMemo(() => calculateCartSubtotal(cartItems, productLookup), [cartItems, productLookup]);

  function validateForm() {
    const nextErrors = {
      shipping_address: validateRequired(form.shipping_address, 'Shipping address'),
      payment_method: validateRequired(form.payment_method, 'Payment method'),
    };
    setFormErrors(nextErrors);
    return !Object.values(nextErrors).some(Boolean);
  }

  async function clearCartItems(items) {
    await Promise.all(items.map((item) => deleteCartItemRequest(item.id)));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!validateForm()) return;

    try {
      setSubmitting(true);
      setError('');

      const order = await createOrderRequest({
        customer_id: user.id,
        shipping_address: form.shipping_address,
        billing_address: form.billing_address || null,
        items: enrichedItems.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
        })),
      });

      await recordPaymentRequest({
        order_id: order.id,
        amount: subtotal,
        payment_method: form.payment_method,
        payment_status: 'completed',
        transaction_reference: `WEB-${Date.now()}`,
      });

      await clearCartItems(enrichedItems);
      navigate('/orders', { replace: true });
    } catch (checkoutError) {
      setError(checkoutError?.response?.data?.detail || 'Checkout failed.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <Loader label="Preparing checkout" />;
  if (error && !enrichedItems.length) return <ErrorState message={error} onRetry={loadCheckout} />;
  if (!enrichedItems.length) {
    return (
      <EmptyState
        title="No items to checkout"
        message="Add products to your cart before placing an order."
      />
    );
  }

  return (
    <div className="page-stack">
      <PageHeader title="Checkout" subtitle="Create the order, record payment, and clear the cart in one flow." />
      {error ? <ErrorState title="Checkout issue" message={error} onRetry={loadCheckout} /> : null}

      <section className="checkout-grid">
        <form className="card checkout-form" onSubmit={handleSubmit}>
          <FormField
            label="Shipping address"
            as="textarea"
            rows="4"
            value={form.shipping_address}
            onChange={(event) => setForm({ ...form, shipping_address: event.target.value })}
            error={formErrors.shipping_address}
            placeholder="Street, city, state, postal code"
          />
          <FormField
            label="Billing address"
            as="textarea"
            rows="4"
            value={form.billing_address}
            onChange={(event) => setForm({ ...form, billing_address: event.target.value })}
            placeholder="Optional if same as shipping"
          />
          <FormField
            label="Payment method"
            as="select"
            value={form.payment_method}
            onChange={(event) => setForm({ ...form, payment_method: event.target.value })}
            error={formErrors.payment_method}
          >
            <option value="card">Card</option>
            <option value="upi">UPI</option>
            <option value="cash">Cash on delivery</option>
          </FormField>
          <Button type="submit" loading={submitting}>
            Place order
          </Button>
        </form>

        <aside className="cart-summary card">
          <h3>Items</h3>
          {enrichedItems.map((item) => (
            <div key={item.id} className="summary-row">
              <span>{item.product?.name || `Product #${item.product_id}`}</span>
              <span>x{item.quantity}</span>
            </div>
          ))}
          <div className="summary-total">
            <strong>Total</strong>
            <strong>{formatCurrency(subtotal)}</strong>
          </div>
        </aside>
      </section>
    </div>
  );
}
