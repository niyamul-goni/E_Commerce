import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import Button from '../components/Button';
import ErrorState from '../components/ErrorState';
import Loader from '../components/Loader';
import ProductCard from '../components/ProductCard';
import { useAuth } from '../context/AuthContext';
import {
  getProductRequest,
  getProductVariantsRequest,
  getRelatedProductsRequest,
} from '../services/catalogService';
import {
  addToCartRequest,
  addToWishlistRequest,
  createReviewRequest,
  getReviewsByProductRequest,
} from '../services/commerceService';
import { formatCurrency, formatDate } from '../utils/format';

const PLACEHOLDER_IMG = 'https://picsum.photos/seed/placeholder/600/800';

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

// ── Color Swatch ──────────────────────────────────────────────────────────────
function ColorSwatch({ variant, selected, onClick }) {
  return (
    <button
      type="button"
      title={variant.color_name}
      className={`color-swatch${selected ? ' color-swatch--selected' : ''}`}
      style={{ background: variant.hex_code || '#888' }}
      onClick={onClick}
      id={`swatch-${variant.id}`}
    />
  );
}

export default function ProductDetailsPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [loading,          setLoading]          = useState(true);
  const [error,            setError]            = useState('');
  const [product,          setProduct]          = useState(null);
  const [variants,         setVariants]         = useState([]);
  const [reviews,          setReviews]          = useState([]);
  const [relatedProducts,  setRelatedProducts]  = useState([]);
  const [selectedVariant,  setSelectedVariant]  = useState(null);
  const [quantity,         setQuantity]         = useState(1);
  const [cartMessage,      setCartMessage]      = useState('');
  const [wishlistMsg,      setWishlistMsg]      = useState('');
  const [reviewForm,       setReviewForm]       = useState({ rating: 5, comment: '' });
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewError,      setReviewError]      = useState('');
  const [activeImageIdx,   setActiveImageIdx]   = useState(0);

  useEffect(() => {
    let active = true;
    async function loadPage() {
      try {
        setLoading(true);
        setError('');
        const [productData, variantData, reviewData, relatedData] = await Promise.all([
          getProductRequest(productId),
          getProductVariantsRequest(productId).catch(() => []),
          getReviewsByProductRequest(productId).catch(() => []),
          getRelatedProductsRequest(productId).catch(() => []),
        ]);
        if (!active) return;
        setProduct(productData);
        setVariants(variantData);
        setReviews(reviewData);
        setRelatedProducts(relatedData);
        setActiveImageIdx(0);
        // Pre-select first in-stock variant
        const firstAvailable = variantData.find((v) => v.available_stock > 0) || variantData[0];
        if (firstAvailable) setSelectedVariant(firstAvailable);
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

  const inStock = selectedVariant
    ? selectedVariant.available_stock > 0
    : (product?.stock_quantity ?? 0) > 0;

  const displayPrice = selectedVariant?.price_override
    ? selectedVariant.price_override
    : product?.price;

  // Build gallery images from product data
  const galleryImages = product?.images?.length
    ? product.images.map((img) => img.image_url)
    : product?.image_url
      ? [product.image_url]
      : [PLACEHOLDER_IMG];

  // Derive unique sizes and colors for grouped variant selector
  const uniqueSizes  = [...new Map(variants.map((v) => [v.size_name, v])).values()].filter((v) => v.size_name);
  const uniqueColors = [...new Map(variants.map((v) => [v.color_id, v])).values()].filter((v) => v.color_id);

  async function handleAddToCart() {
    if (!user) { navigate('/login'); return; }
    try {
      setCartMessage('');
      await addToCartRequest({
        customer_id: user.id,
        product_id: product.id,
        quantity,
      });
      setCartMessage('Added to cart!');
    } catch (err) {
      setCartMessage(err?.response?.data?.detail || 'Unable to add this item to cart.');
    }
  }

  async function handleAddToWishlist() {
    if (!user) { navigate('/login'); return; }
    if (!selectedVariant) { setWishlistMsg('Select a variant first.'); return; }
    try {
      setWishlistMsg('');
      await addToWishlistRequest(selectedVariant.id);
      setWishlistMsg('Saved to wishlist!');
    } catch (err) {
      setWishlistMsg(err?.response?.data?.detail || 'Could not add to wishlist.');
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

  const avgRating = product.avg_rating || (reviews.length
    ? (reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length).toFixed(1)
    : null);

  const hasDiscount = product.discount_price && product.discount_price < product.price;

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
        {/* Left: image gallery */}
        <div className="product-detail__gallery">
          <div className="product-detail__image-main">
            {galleryImages[activeImageIdx] ? (
              <img
                src={galleryImages[activeImageIdx]}
                alt={product.name}
                className="product-detail__image"
                onError={(e) => { e.target.src = PLACEHOLDER_IMG; }}
              />
            ) : (
              <div className="product-detail__image-placeholder">
                <span>🛍️</span>
                <p>Product Image</p>
              </div>
            )}
            {hasDiscount && (
              <span className="product-detail__sale-badge">
                -{Math.round(((product.price - product.discount_price) / product.price) * 100)}% OFF
              </span>
            )}
          </div>
          {galleryImages.length > 1 && (
            <div className="product-detail__thumbnails">
              {galleryImages.map((img, idx) => (
                <button
                  key={idx}
                  type="button"
                  className={`product-detail__thumb${idx === activeImageIdx ? ' active' : ''}`}
                  onClick={() => setActiveImageIdx(idx)}
                >
                  <img src={img} alt={`${product.name} thumbnail ${idx + 1}`} />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: details */}
        <div className="product-detail__info">
          {product.category_name && (
            <p className="eyebrow">{product.category_name} · {product.brand_name}</p>
          )}
          <h1 className="product-detail__name">{product.name}</h1>

          <div className="product-detail__price-row">
            <div className="product-detail__price-group">
              {hasDiscount ? (
                <>
                  <span className="product-detail__price product-detail__price--sale">
                    {formatCurrency(product.discount_price)}
                  </span>
                  <span className="product-detail__price product-detail__price--original">
                    {formatCurrency(product.price)}
                  </span>
                  <span className="product-detail__save-badge">
                    Save {formatCurrency(product.price - product.discount_price)}
                  </span>
                </>
              ) : (
                <span className="product-detail__price">{formatCurrency(displayPrice)}</span>
              )}
            </div>
            <span className={`stock-badge${inStock ? '' : ' stock-badge--out'}`}>
              {inStock
                ? selectedVariant
                  ? `In Stock (${selectedVariant.available_stock})`
                  : `In Stock (${product.stock_quantity})`
                : 'Out of Stock'}
            </span>
          </div>

          {avgRating && (
            <div className="product-detail__rating">
              {'★'.repeat(Math.round(Number(avgRating)))}{'☆'.repeat(5 - Math.round(Number(avgRating)))}
              <span> {avgRating} ({product.review_count || reviews.length} review{(product.review_count || reviews.length) !== 1 ? 's' : ''})</span>
            </div>
          )}

          {product.description && (
            <p className="product-detail__desc">{product.description}</p>
          )}

          {/* Tags */}
          {product.tags && (
            <div className="product-detail__tags">
              {product.tags.split(',').map((tag) => (
                <span key={tag.trim()} className="product-detail__tag">{tag.trim()}</span>
              ))}
            </div>
          )}

          {/* ── Variant Selectors ── */}
          {variants.length > 0 && (
            <div className="variant-selectors">
              {/* Color swatches */}
              {uniqueColors.length > 0 && (
                <div className="product-detail__sizes" style={{ marginBottom: '1rem' }}>
                  <label className="field__label">
                    Color
                    {selectedVariant?.color_name && (
                      <strong> — {selectedVariant.color_name}</strong>
                    )}
                  </label>
                  <div className="color-swatches">
                    {uniqueColors.map((v) => (
                      <ColorSwatch
                        key={v.color_id}
                        variant={v}
                        selected={selectedVariant?.color_id === v.color_id}
                        onClick={() => {
                          const match = variants.find(
                            (x) =>
                              x.color_id === v.color_id &&
                              (selectedVariant ? x.size_id === selectedVariant.size_id : true)
                          ) || variants.find((x) => x.color_id === v.color_id);
                          if (match) setSelectedVariant(match);
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Size chips */}
              {uniqueSizes.length > 0 && (
                <div className="product-detail__sizes">
                  <label className="field__label">
                    Size
                    {selectedVariant?.size_name && (
                      <strong> — {selectedVariant.size_name}</strong>
                    )}
                  </label>
                  <div className="size-chips">
                    {uniqueSizes.map((v) => {
                      const isAvail = variants.some(
                        (x) =>
                          x.size_id === v.size_id &&
                          (selectedVariant ? x.color_id === selectedVariant.color_id : true) &&
                          x.available_stock > 0
                      );
                      return (
                        <button
                          key={v.size_id}
                          id={`detail-size-${v.size_name}`}
                          type="button"
                          className={`size-chip${selectedVariant?.size_id === v.size_id ? ' active' : ''}${!isAvail ? ' disabled' : ''}`}
                          disabled={!isAvail}
                          onClick={() => {
                            const match = variants.find(
                              (x) =>
                                x.size_id === v.size_id &&
                                (selectedVariant ? x.color_id === selectedVariant.color_id : true)
                            ) || variants.find((x) => x.size_id === v.size_id);
                            if (match) setSelectedVariant(match);
                          }}
                        >
                          {v.size_name}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Quantity + Add to cart + Wishlist */}
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
            <button
              id="add-to-wishlist-btn"
              type="button"
              className="wishlist-btn"
              onClick={handleAddToWishlist}
              title="Save to Wishlist"
            >
              ♡
            </button>
          </div>

          {cartMessage && (
            <p className={`inline-message${cartMessage.includes('Added') ? ' inline-message--success' : ''}`}>
              {cartMessage}
            </p>
          )}
          {wishlistMsg && (
            <p className={`inline-message${wishlistMsg.includes('Saved') ? ' inline-message--success' : ''}`}>
              {wishlistMsg}
            </p>
          )}

          {/* Meta */}
          <div className="product-detail__meta">
            {selectedVariant?.sku && <span>SKU: {selectedVariant.sku}</span>}
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
                {review.customer_email && (
                  <p className="review-card__author">{review.customer_email}</p>
                )}
                <p className="review-card__comment">{review.comment || 'No comment provided.'}</p>
                {review.reply_text && (
                  <div className="review-reply">
                    <span className="review-reply__badge">Admin Reply</span>
                    <p>{review.reply_text}</p>
                  </div>
                )}
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

      {/* ── Related Products ── */}
      {relatedProducts.length > 0 && (
        <section className="home-section">
          <div className="home-section__header">
            <div>
              <h2 className="home-section__title">You May Also Like</h2>
              <p className="home-section__subtitle">Similar products from the same category</p>
            </div>
          </div>
          <div className="products-grid">
            {relatedProducts.slice(0, 4).map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
