import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import Loader from '../components/Loader';
import PageHeader from '../components/PageHeader';
import { useAuth } from '../context/AuthContext';
import {
  addToCartRequest,
  getWishlistRequest,
  removeFromWishlistRequest,
} from '../services/commerceService';
import { formatCurrency } from '../utils/format';
import { resolveProductImage } from '../utils/productImages';

function WishlistCard({ item, onRemove, onAddToCart, addingId }) {
  const isAdding = addingId === item.id;
  const imageUrl = resolveProductImage(item);
  const [imageFailed, setImageFailed] = useState(false);

  return (
    <article className="wishlist-card card">
      {imageUrl && !imageFailed ? (
        <div className="wishlist-card__img">
          <img
            src={imageUrl}
            alt={item.product_name}
            onError={() => setImageFailed(true)}
          />
        </div>
      ) : (
        <div className="wishlist-card__img wishlist-card__img--placeholder">
          🛍️
        </div>
      )}

      <div className="wishlist-card__body">
        <div>
          <p className="eyebrow" style={{ marginBottom: '0.25rem' }}>
            {item.color_name && item.size_name
              ? `${item.color_name} · ${item.size_name}`
              : item.color_name || item.size_name || 'One Size'}
          </p>
          <h3 className="wishlist-card__name">
            <Link to={`/products/${item.product_id}`}>{item.product_name}</Link>
          </h3>
          <p className="wishlist-card__price">{formatCurrency(item.effective_price)}</p>
        </div>

        <div className="wishlist-card__actions">
          <button
            className="button"
            disabled={isAdding}
            onClick={() => onAddToCart(item)}
            id={`wishlist-cart-${item.id}`}
          >
            {isAdding ? '…' : 'Add to Cart'}
          </button>
          <button
            className="button button--secondary"
            onClick={() => onRemove(item.id)}
            id={`wishlist-remove-${item.id}`}
          >
            ✕ Remove
          </button>
        </div>
      </div>
    </article>
  );
}

export default function WishlistPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [items, setItems] = useState([]);
  const [addingId, setAddingId] = useState(null);
  const [cartMsg, setCartMsg] = useState('');

  async function loadWishlist() {
    try {
      setLoading(true);
      setError('');
      const data = await getWishlistRequest();
      setItems(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load wishlist.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadWishlist(); }, []);

  async function handleRemove(itemId) {
    try {
      await removeFromWishlistRequest(itemId);
      setItems((prev) => prev.filter((i) => i.id !== itemId));
      setCartMsg('');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not remove item.');
    }
  }

  async function handleAddToCart(item) {
    if (!user) { navigate('/login'); return; }
    setAddingId(item.id);
    setCartMsg('');
    try {
      await addToCartRequest({
        variant_id: item.variant_id,
        quantity: 1,
      });
      setCartMsg(`✓ "${item.product_name}" added to cart!`);
    } catch (err) {
      setCartMsg(err?.response?.data?.detail || 'Could not add to cart.');
    } finally {
      setAddingId(null);
    }
  }

  if (loading) return <Loader label="Loading wishlist" />;
  if (error)   return <ErrorState message={error} onRetry={loadWishlist} />;
  if (!items.length) {
    return (
      <EmptyState
        title="Your wishlist is empty"
        message="Browse products and tap the heart ♡ to save items here."
      />
    );
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="My Wishlist"
        subtitle={`${items.length} saved ${items.length === 1 ? 'item' : 'items'}`}
        action={
          <a className="button button--secondary" href="/products">
            Continue Shopping
          </a>
        }
      />

      {cartMsg && (
        <p className={`inline-message${cartMsg.startsWith('✓') ? ' inline-message--success' : ''}`}>
          {cartMsg}
        </p>
      )}

      <div className="wishlist-grid">
        {items.map((item) => (
          <WishlistCard
            key={item.id}
            item={item}
            onRemove={handleRemove}
            onAddToCart={handleAddToCart}
            addingId={addingId}
          />
        ))}
      </div>
    </div>
  );
}
