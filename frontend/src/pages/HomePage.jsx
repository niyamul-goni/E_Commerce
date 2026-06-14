import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import Loader from '../components/Loader';
import PageHeader from '../components/PageHeader';
import ProductCard from '../components/ProductCard';
import StatCard from '../components/StatCard';
import { useAuth } from '../context/AuthContext';
import { getCategoriesRequest, getProductsRequest } from '../services/catalogService';

export default function HomePage() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);

  useEffect(() => {
    let active = true;

    async function loadHomeData() {
      try {
        setLoading(true);
        setError('');
        const [categoryData, productData] = await Promise.all([
          getCategoriesRequest(),
          getProductsRequest(),
        ]);

        if (!active) return;
        setCategories(categoryData);
        setProducts(productData.slice(0, 4));
      } catch (loadError) {
        if (!active) return;
        setError(loadError?.response?.data?.detail || 'Failed to load home page data.');
      } finally {
        if (active) setLoading(false);
      }
    }

    loadHomeData();
    return () => {
      active = false;
    };
  }, []);

  const featuredCategories = categories.slice(0, 3);

  if (loading) return <Loader label="Preparing storefront" />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="page-stack">
      <section className="hero card">
        <div className="hero__content">
          <p className="eyebrow">FastAPI + React + PostgreSQL</p>
          <h1>Run the full commerce flow from catalog to checkout.</h1>
          <p>
            Browse products, manage a cart, place orders, record payments, track shipments,
            and handle the admin workflow from a single clean interface.
          </p>
          <div className="hero__actions">
            <Button onClick={() => navigate('/products')}>Browse products</Button>
            <Link className="button button--secondary" to={isAuthenticated ? '/orders' : '/login'}>
              {isAuthenticated ? 'View orders' : 'Sign in'}
            </Link>
          </div>
        </div>
        <div className="hero__panel">
          <StatCard label="Products" value={products.length} hint="Featured from the live catalog" />
          <StatCard label="Categories" value={categories.length} hint="Structured master data" />
          <StatCard label="Flow" value="Cart → Order → Payment" hint="End-to-end commerce lifecycle" />
        </div>
      </section>

      <section className="section-grid">
        <div>
          <PageHeader
            title="Featured products"
            subtitle="A snapshot of the live catalog powered by the backend API."
          />
          {products.length ? (
            <div className="cards-grid">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : (
            <EmptyState title="No products yet" message="Add sample products from the admin panel." />
          )}
        </div>

        <aside className="sidebar-stack">
          <PageHeader title="Categories" subtitle="Everything stays normalized in the database." />
          <div className="chip-grid">
            {featuredCategories.map((category) => (
              <Link key={category.id} className="category-chip" to={`/products?category_id=${category.id}`}>
                {category.name}
              </Link>
            ))}
          </div>

          <div className="card callout">
            <h3>Built for DBMS demos</h3>
            <p>
              The schema supports joins, subqueries, grouping, ordering, constraints, and
              update/delete operations for course reporting.
            </p>
            <Link className="button button--secondary" to="/reviews">
              Explore reviews
            </Link>
          </div>
        </aside>
      </section>
    </div>
  );
}
