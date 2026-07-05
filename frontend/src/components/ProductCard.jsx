import { Link } from 'react-router-dom';
import Button from './Button';
import { formatCurrency } from '../utils/format';

// ── Category → size groups mapping ───────────────────────────────────────────
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
  accessories: ['One Size'],
};

function getSizesForCategory(categoryName) {
  if (!categoryName) return null;
  const key = categoryName.toLowerCase().replace(/\s+/g, '-');
  // Try exact match first, then partial match
  if (CATEGORY_SIZES[key]) return CATEGORY_SIZES[key];
  for (const [catKey, sizes] of Object.entries(CATEGORY_SIZES)) {
    if (key.includes(catKey) || catKey.includes(key)) return sizes;
  }
  return null;
}

export default function ProductCard({ product, onAddToCart, loading = false }) {
  const inStock = product.stock_quantity > 0;

  // Use category-specific sizes if available, otherwise parse available_sizes
  const categorySizes = getSizesForCategory(product.category_name);
  const availableSizes = product.available_sizes
    ? product.available_sizes.split(',').map((s) => s.trim()).filter(Boolean)
    : [];
  // Show category standard sizes, but only those that exist in available_sizes (or all if no available_sizes set)
  const displaySizes = categorySizes
    ? availableSizes.length > 0
      ? categorySizes.filter((s) => availableSizes.includes(s))
      : categorySizes
    : availableSizes;

  return (
    <article className="product-card card">
      {product.is_featured && (
        <div className="product-card__badge">✦ Featured</div>
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
        {displaySizes.length > 0 && displaySizes[0] !== 'One Size' && (
          <div className="product-card__sizes">
            {displaySizes.map((s) => (
              <span key={s} className="size-tag">{s}</span>
            ))}
          </div>
        )}
        <div className="product-card__meta">
          <span className="product-card__price">{formatCurrency(product.price)}</span>
          <span className={`product-card__stock${inStock ? '' : ' product-card__stock--out'}`}>
            {inStock ? `In stock` : 'Out of stock'}
          </span>
        </div>
      </div>
      <div className="product-card__actions">
        <Link className="button button--secondary" to={`/products/${product.id}`}>
          View details
        </Link>
        {onAddToCart ? (
          <Button
            onClick={() => onAddToCart(product)}
            disabled={loading || !inStock}
          >
            {loading ? '…' : 'Add to cart'}
          </Button>
        ) : null}
      </div>
    </article>
  );
}
