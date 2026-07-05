import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import Button from '../components/Button';
import ErrorState from '../components/ErrorState';
import Loader from '../components/Loader';
import { useAuth } from '../context/AuthContext';
import { getProductRequest } from '../services/catalogService';
import { addToCartRequest, createReviewRequest, getReviewsByProductRequest } from '../services/commerceService';
import { formatCurrency, formatDate } from '../utils/format';

// ── Size mapping (same as ProductCard) ───────────────────────────────────────
const CATEGORY_SIZES = {
  shirts:     ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
  't-shirts': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
  jackets:    ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
  activewear: ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
  kurta:      ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
  punjabi:    ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
  pants:      ['28', '30', '32', '34', '36', '38'],
  jeans:      ['28', '30', '32', '34', '36', '38'],
  trousers:   ['28', '30', '32', '34', '36', '38'],
  shoes:      ['38', '39', '40', '41', '42', '43', '44', '45'],
  accessories: [],
};

function getSizesForCategory(categoryName) {
  if (!categoryName) return null;
  const key = categoryName.toLowerCase();
  for (const [catKey, sizes] of Object.entries(CATEGORY_SIZES)) {
    if (key.includes(catKey) || catKey.includes(key)) return sizes;
  }
  return null;
}

// ── Star Rating ───────────────────────────────────────────────────────────────
function StarRating({ value, onChange, readOnly = false }) {
  return (
    <div className="star-rating">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          className={`star${star <= value ? ' active' : ''}`}
          onClick={readOnly ? undefined : () => onChange(star)}
          disabled={readOnly}
          aria-label={`Rate ${star} star`}
        >
          ★
        </button>
      ))}
      <span className="star-rating__label">{value}/5</span>
    </div>
  );
}

export default function ProductDetailsPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [loading,      setLoading]      = useState(true);
  const [error,        setError]        = useState('');
  const [product,      setProduct]      = useState(null);
  const [reviews,      setReviews]      = useState([]);
  const [quantity,     setQuantity]     = useState(1);
  const [selectedSize, setSelectedSize] = useState('');
  const [cartMessage,  setCartMessage]  = useState('');
  const [reviewForm,   setReviewForm]   = useState({ rating: 5, comment: '' });
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewError,  setReviewError]  = useState('');

  useEffect(() => {
    let active = true;
    async function loadPage() {
      try {
        setLoading(true);
        setError('');
        const [productData, reviewData] = await Promise.all([
          getProductRequest(productId),
          getReviewsByProductRequest(productId),
        ]);
        if (!active) return;
        setProduct(productData);
        setReviews(reviewData);
        // Pre-select first size
        const catSizes = getSizesForCategory(productData?.category_name);
        if (catSizes && catSizes.length > 0) setSelectedSize(catSizes[0]);
      } catch (err) {
        if (!active) return;
        setError(err?.response?.data?.detail || 'Failed to load product details.');
      } finally {
        if (active) setLoading(false);
      }
    }
    loadPage();
    return () => { active = false; };
  }, [productId]);

  const inStock = product?.stock_quantity > 0;

  // Available sizes for this product
  const categorySizes = getSizesForCategory(product?.category_name);
  const availableSizes = product?.available_sizes
    ? product.available_sizes.split(',').map((s) => s.trim()).filter(Boolean)
    : [];
  const displaySizes = categorySizes
    ? availableSizes.length > 0
      ? categorySizes.filter((s) => availableSizes.includes(s))
      : categorySizes
    : availableSizes;

  async function handleAddToCart() {
    if (!user) { navigate('/login'); return; }
    if (!selectedSize && displaySizes.length > 0) {
      setCartMessage('Please select a size first.');
      return;
    }
    try {
      setCartMessage('');
      await addToCartRequest({ customer_id: user.id, product_id: product.id, quantity });
      setCartMessage('✓ Added to cart!');
    } catch (err) {
      setCartMessage(err?.response?.data?.detail || 'Unable to add this item to cart.');
    }
  }

  async function handleReviewSubmit(e) {
    e.preventDefault();
    if (!user) { navigate('/login'); return; }
    setReviewError('');
    try {
      setReviewSubmitting(true);
      await createReviewRequest({
        customer_id: user.id,
        product_id: product.id,
        rating: Number(reviewForm.rating),
        comment: reviewForm.comment || null,
      });
      const nextReviews = await getReviewsByProductRequest(productId);
      setReviews(nextReviews);
      setReviewForm({ rating: 5, comment: '' });
    } catch (err) {
      setReviewError(err?.response?.data?.detail || 'Unable to submit review.');
    } finally {
      setReviewSubmitting(false);
    }
  }

  if (loading) return <Loader label="Loading product…" />;
  if (error)   return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  if (!product) return <ErrorState message="Product not found." />;

  const avgRating = reviews.length
    ? (reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length).toFixed(1)
    : null;

  return (
    <div className="page-stack">
      {/* ── Breadcrumb ── */}
      <nav className="breadcrumb">
        <Link to="/products">Products</Link>
        <span>/</span>
        {product.category_name && (
          <>
            <Link to={`/products?category_id=${product.category_id}`}>{product.category_name}</Link>
            <span>/</span>
          </>
        )}
        <span>{product.name}</span>
      </nav>

      {/* ── Main product layout ── */}
      <div className="product-detail">
        {/* Left: image placeholder */}
        <div className="product-detail__image">
          {product.image_url ? (
            <img src={product.image_url} alt={product.name} />
          ) : (
            <div className="product-detail__image-placeholder">
              <span>🛍️</span>
              <p>Product Image</p>
            </div>
          )}
          {product.is_featured && (
            <div className="product-detail__badge">✦ Featured</div>
          )}
        </div>

        {/* Right: details */}
        <div className="product-detail__info">
          {product.category_name && (
            <p className="eyebrow">{product.category_name} · {product.brand_name}</p>
          )}
          <h1 className="product-detail__name">{product.name}</h1>

          <div className="product-detail__price-row">
            <span className="product-detail__price">{formatCurrency(product.price)}</span>
            <span className={`stock-badge${inStock ? '' : ' stock-badge--out'}`}>
              {inStock ? `✓ In Stock (${product.stock_quantity})` : '✗ Out of Stock'}
            </span>
          </div>

          {avgRating && (
            <div className="product-detail__rating">
              {'★'.repeat(Math.round(Number(avgRating)))}{'☆'.repeat(5 - Math.round(Number(avgRating)))}
              <span> {avgRating} ({reviews.length} review{reviews.length !== 1 ? 's' : ''})</span>
            </div>
          )}

          {product.description && (
            <p className="product-detail__desc">{product.description}</p>
          )}

          {/* Size selector */}
          {displaySizes.length > 0 && (
            <div className="product-detail__sizes">
              <label className="field__label">
                Select Size
                {selectedSize && <strong> — {selectedSize}</strong>}
              </label>
              <div className="size-chips">
                {displaySizes.map((s) => (
                  <button
                    key={s}
                    id={`detail-size-${s}`}
                    type="button"
                    className={`size-chip${selectedSize === s ? ' active' : ''}`}
                    onClick={() => setSelectedSize(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Quantity + Add to cart */}
          <div className="product-detail__actions">
            <div className="qty-row">
              <label className="field__label">Qty</label>
              <div className="qty-control">
                <button type="button" className="qty-btn" onClick={() => setQuantity(Math.max(1, quantity - 1))}>-</button>
                <span className="qty-val">{quantity}</span>
                <button type="button" className="qty-btn" onClick={() => setQuantity(quantity + 1)}>+</button>
              </div>
            </div>
            <Button
              id="add-to-cart-btn"
              onClick={handleAddToCart}
              disabled={!inStock}
              style={{ flex: 1 }}
            >
              {inStock ? 'Add to Cart' : 'Out of Stock'}
            </Button>
          </div>

          {cartMessage && (
            <p className={`inline-message${cartMessage.startsWith('✓') ? ' inline-message--success' : ''}`}>
              {cartMessage}
            </p>
          )}

          {/* Meta */}
          <div className="product-detail__meta">
            {product.sku && <span>SKU: {product.sku}</span>}
            {product.created_at && <span>Added: {formatDate(product.created_at)}</span>}
          </div>
        </div>
      </div>

      {/* ── Reviews ── */}
      <section className="reviews-section card">
        <h2 className="reviews-section__title">
          Customer Reviews
          {avgRating && <span className="reviews-section__avg"> · ★ {avgRating}</span>}
        </h2>

        <div className="reviews-list">
          {reviews.length === 0 ? (
            <p className="muted">No reviews yet. Be the first to review this product!</p>
          ) : (
            reviews.map((review) => (
              <article key={review.id} className="review-card card card--soft">
                <div className="review-card__head">
                  <StarRating value={review.rating} readOnly />
                  <span className="review-card__date">{formatDate(review.created_at)}</span>
                </div>
                <p className="review-card__comment">{review.comment || 'No comment provided.'}</p>
              </article>
            ))
          )}
        </div>

        {/* Submit a review */}
        {user ? (
          <form className="review-form" onSubmit={handleReviewSubmit}>
            <h3>Write a Review</h3>
            {reviewError && <p className="inline-message">{reviewError}</p>}
            <div className="field">
              <label className="field__label">Your Rating</label>
              <StarRating value={reviewForm.rating} onChange={(v) => setReviewForm({ ...reviewForm, rating: v })} />
            </div>
            <div className="field">
              <label className="field__label">Comment (optional)</label>
              <textarea
                className="field__control"
                rows={4}
                placeholder="Share your experience with this product…"
                value={reviewForm.comment}
                onChange={(e) => setReviewForm({ ...reviewForm, comment: e.target.value })}
              />
            </div>
            <Button type="submit" loading={reviewSubmitting}>Submit Review</Button>
          </form>
        ) : (
          <p className="muted">
            <Link to="/login">Sign in</Link> to leave a review.
          </p>
        )}
      </section>
    </div>
  );
}
