import { useState } from 'react';
import { Link } from 'react-router-dom';
import Button from './Button';
import { formatCurrency } from '../utils/format';
import { resolveProductImage } from '../utils/productImages';

export default function ProductCard({
  product,
  onAddToCart,
  onWishlist,
  wishlisted = false,
  loading = false,
}) {
  const inStock = product.stock_quantity > 0;
  const [imgError, setImgError] = useState(false);
  const [imgLoaded, setImgLoaded] = useState(false);

  const imageUrl = imgError ? null : resolveProductImage(product);
  const hasDiscount = product.discount_price && product.discount_price < product.price;
  const discountPercent = hasDiscount
    ? Math.round(((product.price - product.discount_price) / product.price) * 100)
    : 0;

  return (
    <article className="product-card card">
      {/* Wishlist heart */}
      {onWishlist && (
        <button
          type="button"
          className={`product-card__heart${wishlisted ? ' active' : ''}`}
          onClick={() => onWishlist(product)}
          id={`wishlist-btn-${product.id}`}
          title={wishlisted ? 'Remove from wishlist' : 'Save to wishlist'}
        >
          {wishlisted ? '♥' : '♡'}
        </button>
      )}

      {/* Badges */}
      <div className="product-card__badges">
        {hasDiscount && (
          <span className="product-card__badge product-card__badge--sale">-{discountPercent}%</span>
        )}
        {product.is_new_arrival && (
          <span className="product-card__badge product-card__badge--new">NEW</span>
        )}
        {product.is_trending && !product.is_new_arrival && (
          <span className="product-card__badge product-card__badge--trending">TRENDING</span>
        )}
        {!inStock && (
          <span className="product-card__badge product-card__badge--oos">SOLD OUT</span>
        )}
      </div>

      {/* Image */}
      <Link to={`/products/${product.id}`} className="product-card__image-link">
        <div className="product-card__image-wrap">
          {imageUrl ? (
            <>
              {!imgLoaded && <div className="product-card__image-skeleton" />}
              <img
                src={imageUrl}
                alt={product.name}
                className={`product-card__image${imgLoaded ? ' loaded' : ''}`}
                loading="lazy"
                onLoad={() => setImgLoaded(true)}
                onError={() => setImgError(true)}
              />
            </>
          ) : (
            <div className="product-card__image-placeholder" role="img" aria-label={`${product.name} has no image`}>
              <span>▧</span>
              <small>No image uploaded</small>
            </div>
          )}
        </div>
      </Link>

      <div className="product-card__body">
        {product.category_name && (
          <p className="product-card__category">{product.category_name.toUpperCase()}</p>
        )}
        <Link to={`/products/${product.id}`} className="product-card__title-link">
          <h3 className="product-card__title">{product.name}</h3>
        </Link>
        {product.brand_name && (
          <p className="product-card__brand">{product.brand_name}</p>
        )}

        {/* Rating */}
        {product.avg_rating && (
          <div className="product-card__rating">
            <span className="product-card__stars">
              {'★'.repeat(Math.round(product.avg_rating))}
              {'☆'.repeat(5 - Math.round(product.avg_rating))}
            </span>
            <span className="product-card__rating-text">
              {product.avg_rating} ({product.review_count})
            </span>
          </div>
        )}

        <p className="product-card__desc">
          {product.short_description || (product.description
            ? product.description.length > 60
              ? product.description.slice(0, 60) + '…'
              : product.description
            : '')}
        </p>

        <div className="product-card__meta">
          <div className="product-card__price-group">
            {hasDiscount ? (
              <>
                <span className="product-card__price product-card__price--sale">
                  {formatCurrency(product.discount_price)}
                </span>
                <span className="product-card__price product-card__price--original">
                  {formatCurrency(product.price)}
                </span>
              </>
            ) : (
              <span className="product-card__price">{formatCurrency(product.price)}</span>
            )}
          </div>
          <span className={`product-card__stock${inStock ? '' : ' product-card__stock--out'}`}>
            {inStock ? 'In stock' : 'Out of stock'}
          </span>
        </div>
      </div>

      <div className="product-card__actions">
        <Link className="button button--secondary" to={`/products/${product.id}`}>
          View Details
        </Link>
        {onAddToCart ? (
          <Button onClick={() => onAddToCart(product)} disabled={loading || !inStock}>
            {loading ? '…' : 'Add to Cart'}
          </Button>
        ) : null}
      </div>
    </article>
  );
}
