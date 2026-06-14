import { Link } from 'react-router-dom';
import Button from './Button';
import { formatCurrency } from '../utils/format';

export default function ProductCard({ product, onAddToCart }) {
  return (
    <article className="product-card card">
      <div className="product-card__body">
        <p className="product-card__sku">SKU {product.sku}</p>
        <h3>{product.name}</h3>
        <p className="product-card__desc">{product.description || 'No description available.'}</p>
        <div className="product-card__meta">
          <span>{formatCurrency(product.price)}</span>
          <span>Stock {product.stock_quantity}</span>
        </div>
      </div>
      <div className="product-card__actions">
        <Link className="button button--secondary" to={`/products/${product.id}`}>
          View details
        </Link>
        {onAddToCart ? (
          <Button onClick={() => onAddToCart(product)}>
            Add to cart
          </Button>
        ) : null}
      </div>
    </article>
  );
}
