import { useEffect, useState } from 'react';
import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import FormField from '../components/FormField';
import Loader from '../components/Loader';
import PageHeader from '../components/PageHeader';
import { useAuth } from '../context/AuthContext';
import { getProductsRequest } from '../services/catalogService';
import { createReviewRequest, getReviewsByProductRequest } from '../services/commerceService';
import { formatDate } from '../utils/format';
import { createEmptyErrors, validateRating, validateRequired } from '../utils/validators';

export default function ReviewsPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [reviews, setReviews] = useState([]);
  const [form, setForm] = useState({ rating: 5, comment: '' });
  const [formErrors, setFormErrors] = useState(createEmptyErrors());
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadProducts() {
      try {
        setLoading(true);
        setError('');
        const data = await getProductsRequest();
        if (!active) return;
        setProducts(data);
        const firstProductId = data[0]?.id ? String(data[0].id) : '';
        setSelectedProductId(firstProductId);
      } catch (loadError) {
        if (!active) return;
        setError(loadError?.response?.data?.detail || 'Failed to load reviews page.');
      } finally {
        if (active) setLoading(false);
      }
    }

    loadProducts();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedProductId) return;
    let active = true;

    async function loadReviews() {
      try {
        const data = await getReviewsByProductRequest(selectedProductId);
        if (active) setReviews(data);
      } catch (loadError) {
        if (active) setError(loadError?.response?.data?.detail || 'Failed to load product reviews.');
      }
    }

    loadReviews();
    return () => {
      active = false;
    };
  }, [selectedProductId]);

  function validateForm() {
    const nextErrors = {
      rating: validateRating(form.rating),
      comment: validateRequired(form.comment, 'Comment'),
      customer_id: user ? '' : 'You must be signed in to review',
    };
    setFormErrors(nextErrors);
    return !Object.values(nextErrors).some(Boolean);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!user || !validateForm()) return;

    try {
      setSubmitting(true);
      await createReviewRequest({
        customer_id: user.id,
        product_id: Number(selectedProductId),
        rating: Number(form.rating),
        comment: form.comment,
      });
      const data = await getReviewsByProductRequest(selectedProductId);
      setReviews(data);
      setForm({ rating: 5, comment: '' });
    } catch (submitError) {
      setError(submitError?.response?.data?.detail || 'Unable to submit review.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <Loader label="Loading reviews" />;
  if (error && !products.length) return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  if (!products.length) return <EmptyState title="No products found" message="Create products before adding reviews." />;

  const selectedProduct = products.find((product) => String(product.id) === selectedProductId);

  return (
    <div className="page-stack">
      <PageHeader title="Reviews" subtitle="Pick a product, read reviews, and publish your own feedback." />
      {error ? <ErrorState title="Review loading issue" message={error} /> : null}

      <section className="reviews-layout">
        <div className="card reviews-selector">
          <FormField
            as="select"
            label="Product"
            value={selectedProductId}
            onChange={(event) => setSelectedProductId(event.target.value)}
          >
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name}
              </option>
            ))}
          </FormField>
          <p className="muted">Selected: {selectedProduct?.name}</p>
        </div>

        <section className="card">
          <h3>Review feed</h3>
          <div className="reviews-list">
            {reviews.length ? (
              reviews.map((review) => (
                <article key={review.id} className="review-card card card--soft">
                  <div className="review-card__head">
                    <strong>Rating {review.rating}/5</strong>
                    <span>{formatDate(review.created_at)}</span>
                  </div>
                  <p>{review.comment}</p>
                </article>
              ))
            ) : (
              <p className="muted">No reviews yet for this product.</p>
            )}
          </div>
        </section>

        <form className="card review-form" onSubmit={handleSubmit}>
          <h3>Write a review</h3>
          <FormField
            label="Rating"
            as="select"
            value={form.rating}
            onChange={(event) => setForm({ ...form, rating: event.target.value })}
            error={formErrors.rating}
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
            rows="5"
            value={form.comment}
            onChange={(event) => setForm({ ...form, comment: event.target.value })}
            error={formErrors.customer_id}
          />
          <Button type="submit" loading={submitting}>
            Publish review
          </Button>
        </form>
      </section>
    </div>
  );
}
