import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import Loader from '../components/Loader';
import PageHeader from '../components/PageHeader';
import QuantityStepper from '../components/QuantityStepper';
import { useAuth } from '../context/AuthContext';
import {
  deleteCartItemRequest,
  getMyCartItemsRequest,
  updateCartItemRequest,
} from '../services/commerceService';
import { getProductsRequest } from '../services/catalogService';
import { buildProductLookup, calculateCartSubtotal, enrichCartItems } from '../utils/cart';
import { formatCurrency } from '../utils/format';

export default function CartPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [cartItems, setCartItems] = useState([]);
  const [products, setProducts] = useState([]);

  async function loadCart() {
    try {
      setLoading(true);
      setError('');
      const [cartData, productData] = await Promise.all([getMyCartItemsRequest(), getProductsRequest()]);
      setCartItems(cartData);
      setProducts(productData);
    } catch (loadError) {
      setError(loadError?.response?.data?.detail || 'Failed to load your cart.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCart();
  }, []);

  const productLookup = useMemo(() => buildProductLookup(products), [products]);
  const enrichedItems = useMemo(() => enrichCartItems(cartItems, productLookup), [cartItems, productLookup]);
  const subtotal = useMemo(() => calculateCartSubtotal(cartItems, productLookup), [cartItems, productLookup]);

  async function handleQuantityChange(cartItemId, quantity) {
    try {
      await updateCartItemRequest(cartItemId, { quantity });
      await loadCart();
    } catch (updateError) {
      setError(updateError?.response?.data?.detail || 'Unable to update cart item.');
    }
  }

  async function handleRemove(cartItemId) {
    try {
      await deleteCartItemRequest(cartItemId);
      await loadCart();
    } catch (removeError) {
      setError(removeError?.response?.data?.detail || 'Unable to remove cart item.');
    }
  }

  if (loading) return <Loader label="Loading cart" />;
  if (error) return <ErrorState message={error} onRetry={loadCart} />;
  if (!enrichedItems.length) {
    return (
      <EmptyState
        title="Your cart is empty"
        message="Browse the catalog and add items before heading to checkout."
      />
    );
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Shopping cart"
        subtitle="Review quantities, remove items, and continue to checkout when ready."
        action={<Button onClick={() => navigate('/checkout')}>Checkout</Button>}
      />

      <section className="cart-grid">
        <div className="cart-list">
          {enrichedItems.map((item) => (
            <article key={item.id} className="cart-item card">
              <div>
                <h3>{item.product?.name || `Product #${item.product_id}`}</h3>
                <p>{formatCurrency(item.unit_price ?? item.product?.price)}</p>
                {(item.color_name || item.size_name) && (
                  <p className="muted">{[item.color_name, item.size_name].filter(Boolean).join(' · ')}</p>
                )}
                <Link to={`/products/${item.product_id}`}>View product</Link>
              </div>
              <div className="cart-item__actions">
                <QuantityStepper
                  value={item.quantity}
                  onChange={(nextQuantity) => handleQuantityChange(item.id, nextQuantity)}
                />
                <Button variant="secondary" onClick={() => handleRemove(item.id)}>
                  Remove
                </Button>
              </div>
            </article>
          ))}
        </div>

        <aside className="cart-summary card">
          <h3>Order summary</h3>
          <p>Items: {enrichedItems.length}</p>
          <p>Subtotal: {formatCurrency(subtotal)}</p>
          <Button onClick={() => navigate('/checkout')}>Proceed to checkout</Button>
        </aside>
      </section>
    </div>
  );
}
