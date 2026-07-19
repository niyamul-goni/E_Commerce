import { Link } from 'react-router-dom';
import Button from './Button';
import { formatCurrency } from '../utils/format';

export default function ProductCard({
  product,
  onAddToCart,
  onWishlist,
  wishlisted = false,
  loading = false,
}) {
  const inStock = product.stock_quantity > 0;

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

      <div className="product-card__body">
        {product.category_name && (
          <p className="product-card__category">{product.category_name.toUpperCase()}</p>
        )}
        <h3 className="product-card__title">{product.name}</h3>
        {product.brand_name && (
          <p className="product-card__brand">{product.brand_name}</p>
        )}
        <p className="product-card__desc">
          {product.description
            ? product.description.length > 80
              ? product.description.slice(0, 80) + '…'
              : product.description
            : ''}
        </p>
        <div className="product-card__meta">
          <span className="product-card__price">{formatCurrency(product.price)}</span>
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
