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
  getAddressesRequest,
  getMyCartItemsRequest,
  recordPaymentRequest,
  validateCouponRequest,
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
  const [addresses, setAddresses] = useState([]);
  const [form, setForm] = useState({
    address_id: '',
    shipping_address: '',
    billing_address: '',
    payment_method: 'card',
  });
  const [formErrors, setFormErrors] = useState(createEmptyErrors());

  // Coupon
  const [couponCode, setCouponCode]       = useState('');
  const [couponApplied, setCouponApplied] = useState(null); // { discount, message }
  const [couponMsg, setCouponMsg]         = useState('');
  const [couponLoading, setCouponLoading] = useState(false);

  async function loadCheckout() {
    try {
      setLoading(true);
      setError('');
      const [cartData, productData, addrData] = await Promise.all([
        getMyCartItemsRequest(),
        getProductsRequest(),
        getAddressesRequest().catch(() => []),
      ]);
      setCartItems(cartData);
      setProducts(productData);
      setAddresses(addrData);
      // Pre-select default address
      const def = addrData.find((a) => a.is_default) || addrData[0];
      if (def) {
        const full = [def.line1, def.line2, def.city, def.state, def.postal_code, def.country]
          .filter(Boolean).join(', ');
        setForm((f) => ({ ...f, address_id: String(def.id), shipping_address: full }));
      }
    } catch (loadError) {
      setError(loadError?.response?.data?.detail || 'Failed to load checkout data.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadCheckout(); }, []);

  const productLookup = useMemo(() => buildProductLookup(products), [products]);
  const enrichedItems = useMemo(() => enrichCartItems(cartItems, productLookup), [cartItems, productLookup]);
  const subtotal      = useMemo(() => calculateCartSubtotal(cartItems, productLookup), [cartItems, productLookup]);
  const discount      = couponApplied?.discount || 0;
  const total         = Math.max(0, subtotal - discount);

  function validateForm() {
    const nextErrors = {
      shipping_address: validateRequired(form.shipping_address, 'Shipping address'),
      payment_method:   validateRequired(form.payment_method, 'Payment method'),
    };
    setFormErrors(nextErrors);
    return !Object.values(nextErrors).some(Boolean);
  }

  async function clearCartItems(items) {
    await Promise.all(items.map((item) => deleteCartItemRequest(item.id)));
  }

  async function handleApplyCoupon() {
    if (!couponCode.trim()) return;
    setCouponLoading(true);
    setCouponMsg('');
    setCouponApplied(null);
    try {
      const result = await validateCouponRequest(couponCode.trim(), subtotal);
      if (result.valid) {
        setCouponApplied({ discount: result.discount, coupon_id: result.coupon_id });
        setCouponMsg(`✓ ${result.message}`);
      } else {
        setCouponMsg(result.message || 'Invalid coupon.');
      }
    } catch {
      setCouponMsg('Could not validate coupon.');
    } finally {
      setCouponLoading(false);
    }
  }

  function handleAddressSelect(e) {
    const id = e.target.value;
    setForm((f) => {
      if (!id) return { ...f, address_id: '', shipping_address: '' };
      const addr = addresses.find((a) => String(a.id) === id);
      if (!addr) return { ...f, address_id: id };
      const full = [addr.line1, addr.line2, addr.city, addr.state, addr.postal_code, addr.country]
        .filter(Boolean).join(', ');
      return { ...f, address_id: id, shipping_address: full };
    });
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
        amount: total,
        payment_method: form.payment_method,
        payment_status: 'paid',
        transaction_reference: `WEB-${Date.now()}`,
        coupon_id: couponApplied?.coupon_id || null,
      });

      // Cart may already be cleared by the backend, so don't block on this
      try { await clearCartItems(enrichedItems); } catch { /* already cleared */ }
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
      <PageHeader title="Checkout" subtitle="Review your order, apply a coupon, and complete payment." />
      {error ? <ErrorState title="Checkout issue" message={error} onRetry={loadCheckout} /> : null}

      <section className="checkout-grid">
        <form className="card checkout-form" onSubmit={handleSubmit}>
          {/* ── Saved Addresses ── */}
          {addresses.length > 0 ? (
            <FormField
              label="Shipping Address"
              as="select"
              value={form.address_id}
              onChange={handleAddressSelect}
              error={formErrors.shipping_address}
            >
              <option value="">— Enter manually —</option>
              {addresses.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.label}: {a.line1}, {a.city}
                  {a.is_default ? ' (Default)' : ''}
                </option>
              ))}
            </FormField>
          ) : null}

          {/* Manual shipping address (shown when no saved addr selected) */}
          {(!form.address_id || addresses.length === 0) && (
            <FormField
              label={addresses.length > 0 ? 'Custom Shipping Address' : 'Shipping Address'}
              as="textarea"
              rows="4"
              value={form.shipping_address}
              onChange={(event) => setForm({ ...form, shipping_address: event.target.value })}
              error={formErrors.shipping_address}
              placeholder="Street, city, state, postal code"
            />
          )}

          {form.address_id && (
            <div className="address-preview card card--soft">
              <p className="muted" style={{ fontSize: '0.85rem', marginBottom: 0 }}>
                📍 {form.shipping_address}
              </p>
            </div>
          )}

          <FormField
            label="Billing Address (optional)"
            as="textarea"
            rows="3"
            value={form.billing_address}
            onChange={(event) => setForm({ ...form, billing_address: event.target.value })}
            placeholder="Leave blank if same as shipping"
          />

          <FormField
            label="Payment Method"
            as="select"
            value={form.payment_method}
            onChange={(event) => setForm({ ...form, payment_method: event.target.value })}
            error={formErrors.payment_method}
          >
            <option value="card">Card</option>
            <option value="bkash">bKash</option>
            <option value="nagad">Nagad</option>
            <option value="rocket">Rocket</option>
            <option value="cash">Cash on Delivery</option>
          </FormField>

          {/* ── Coupon Code ── */}
          <div className="coupon-row">
            <div className="field" style={{ flex: 1 }}>
              <label className="field__label">Coupon Code</label>
              <input
                id="coupon-input"
                className="field__control"
                type="text"
                placeholder="e.g. SAVE20"
                value={couponCode}
                onChange={(e) => {
                  setCouponCode(e.target.value.toUpperCase());
                  setCouponApplied(null);
                  setCouponMsg('');
                }}
              />
            </div>
            <button
              id="apply-coupon-btn"
              type="button"
              className="button button--secondary"
              onClick={handleApplyCoupon}
              disabled={couponLoading || !couponCode.trim()}
              style={{ alignSelf: 'flex-end' }}
            >
              {couponLoading ? '…' : 'Apply'}
            </button>
          </div>
          {couponMsg && (
            <p className={`inline-message${couponMsg.startsWith('✓') ? ' inline-message--success' : ''}`}>
              {couponMsg}
            </p>
          )}

          <Button type="submit" loading={submitting}>Place Order</Button>
        </form>

        {/* ── Order Summary ── */}
        <aside className="cart-summary card">
          <h3>Order Summary</h3>
          {enrichedItems.map((item) => (
            <div key={item.id} className="summary-row">
              <span>{item.product?.name || `Product #${item.product_id}`}</span>
              <span>×{item.quantity}</span>
            </div>
          ))}
          <div className="summary-row" style={{ marginTop: '1rem', borderTop: '1px solid var(--line)', paddingTop: '1rem' }}>
            <span>Subtotal</span>
            <span>{formatCurrency(subtotal)}</span>
          </div>
          {discount > 0 && (
            <div className="summary-row" style={{ color: 'var(--success)' }}>
              <span>Discount</span>
              <span>− {formatCurrency(discount)}</span>
            </div>
          )}
          <div className="summary-total">
            <strong>Total</strong>
            <strong>{formatCurrency(total)}</strong>
          </div>
        </aside>
      </section>
    </div>
  );
}
