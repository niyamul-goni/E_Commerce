import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Button from '../components/Button';
import ErrorState from '../components/ErrorState';
import FormField from '../components/FormField';
import Loader from '../components/Loader';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';
import { getCategoriesRequest, getProductRequest, getSuppliersRequest } from '../services/catalogService';
import { addToCartRequest, createReviewRequest, getReviewsByProductRequest } from '../services/commerceService';
import { formatCurrency, formatDate } from '../utils/format';
import { createEmptyErrors, validateRating, validateRequired } from '../utils/validators';

export default function ProductDetailsPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [product, setProduct] = useState(null);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [quantity, setQuantity] = useState(1);
  const [cartMessage, setCartMessage] = useState('');
  const [reviewForm, setReviewForm] = useState({ rating: 5, comment: '' });
  const [reviewErrors, setReviewErrors] = useState(createEmptyErrors());
  const [reviewSubmitting, setReviewSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadProductPage() {
      try {
        setLoading(true);
        setError('');
        const [productData, categoryData, supplierData, reviewData] = await Promise.all([
          getProductRequest(productId),
          getCategoriesRequest(),
          getSuppliersRequest(),
          getReviewsByProductRequest(productId),
        ]);

        if (!active) return;
        setProduct(productData);
        setCategories(categoryData);
        setSuppliers(supplierData);
        setReviews(reviewData);
      } catch (loadError) {
        if (!active) return;
        setError(loadError?.response?.data?.detail || 'Failed to load product details.');
      } finally {
        if (active) setLoading(false);
      }
    }

    loadProductPage();
    return () => {
      active = false;
    };
  }, [productId]);

  const categoryName = useMemo(
    () => categories.find((category) => category.id === product?.category_id)?.name,
    [categories, product],
  );
  const supplierName = useMemo(
    () => suppliers.find((supplier) => supplier.id === product?.supplier_id)?.name,
    [suppliers, product],
  );

  async function handleAddToCart() {
    if (!user) {
      navigate('/login');
      return;
    }

    try {
      setCartMessage('');
      await addToCartRequest({
        customer_id: user.id,
        product_id: product.id,
        quantity,
      });
      setCartMessage('Added to cart successfully.');
    } catch (addError) {
      setCartMessage(addError?.response?.data?.detail || 'Unable to add this item to cart.');
    }
  }

  function validateReview() {
    const nextErrors = {
      rating: validateRating(reviewForm.rating),
      comment: reviewForm.comment ? '' : '',
      customer_id: user ? '' : 'Sign in to leave a review',
    };
    setReviewErrors(nextErrors);
    return !Object.values(nextErrors).some(Boolean);
  }

  async function handleReviewSubmit(event) {
    event.preventDefault();
    if (!user || !validateReview()) return;

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
    } catch (reviewError) {
      setError(reviewError?.response?.data?.detail || 'Unable to submit review.');
    } finally {
      setReviewSubmitting(false);
    }
  }

  if (loading) return <Loader label="Loading product details" />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  if (!product) return <ErrorState message="Product not found." />;

  return (
    <div className="page-stack">
      <PageHeader
        title={product.name}
        subtitle={product.description || 'Detailed product information from the API.'}
        action={<StatusBadge value={product.is_active ? 'active' : 'inactive'} />}
      />

      <section className="product-detail card">
        <div className="product-detail__main">
          <p className="eyebrow">SKU {product.sku}</p>
          <h2>{formatCurrency(product.price)}</h2>
          <p>Category: {categoryName || 'Unassigned'}</p>
          <p>Supplier: {supplierName || 'Unassigned'}</p>
          <p>Stock available: {product.stock_quantity}</p>
          <div className="product-detail__actions">
            <FormField
              label="Quantity"
              type="number"
              min="1"
              value={quantity}
              onChange={(event) => setQuantity(Number(event.target.value))}
            />
            <Button onClick={handleAddToCart}>Add to cart</Button>
          </div>
          {cartMessage ? <p className="inline-message">{cartMessage}</p> : null}
        </div>

        <div className="product-detail__side card card--soft">
          <h3>Product meta</h3>
          <p>Created: {formatDate(product.created_at)}</p>
          <p>Updated: {formatDate(product.updated_at)}</p>
          <p>Category ID: {product.category_id}</p>
          <p>Supplier ID: {product.supplier_id}</p>
        </div>
      </section>

      <section className="reviews-panel card">
        <PageHeader title="Reviews" subtitle="Customer feedback collected through the reviews endpoint." />
        <div className="reviews-list">
          {reviews.length ? (
            reviews.map((review) => (
              <article key={review.id} className="review-card card card--soft">
                <div className="review-card__head">
                  <strong>Rating {review.rating}/5</strong>
                  <span>{formatDate(review.created_at)}</span>
                </div>
                <p>{review.comment || 'No comment provided.'}</p>
              </article>
            ))
          ) : (
            <p className="muted">No reviews yet.</p>
          )}
        </div>

        <form className="review-form" onSubmit={handleReviewSubmit}>
          <FormField
            label="Rating"
            as="select"
            value={reviewForm.rating}
            onChange={(event) => setReviewForm({ ...reviewForm, rating: event.target.value })}
            error={reviewErrors.rating}
          >
            {[1, 2, 3, 4, 5].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </FormField>
          <FormField
            label="Comment"
            as="textarea"
            rows="4"
            value={reviewForm.comment}
            onChange={(event) => setReviewForm({ ...reviewForm, comment: event.target.value })}
            error={reviewErrors.comment}
            placeholder="Share what you think about this product"
          />
          <Button type="submit" loading={reviewSubmitting}>
            Submit review
          </Button>
        </form>
      </section>
    </div>
  );
}
