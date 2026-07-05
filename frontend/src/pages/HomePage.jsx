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
import {
  getBrandsRequest,
  getCategoriesRequest,
  getProductsRequest,
} from '../services/catalogService';
import { addToCartRequest } from '../services/commerceService';

export default function HomePage() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState('');
  const [categories, setCategories] = useState([]);
  const [brands,     setBrands]     = useState([]);
  const [products,   setProducts]   = useState([]);
  const [addingId,   setAddingId]   = useState(null);
  const [cartMsg,    setCartMsg]    = useState('');

  useEffect(() => {
    let active = true;

    async function loadHomeData() {
      try {
        setLoading(true);
        setError('');
        const [catData, brandData, productData] = await Promise.all([
          getCategoriesRequest(),
          getBrandsRequest(),
          getProductsRequest({ limit: 8 }),
        ]);

        if (!active) return;
        setCategories(catData);
        setBrands(brandData);
        setProducts(productData.slice(0, 8));
      } catch (loadError) {
        if (!active) return;
        setError(loadError?.response?.data?.detail || 'Failed to load home page data.');
      } finally {
        if (active) setLoading(false);
      }
    }

    loadHomeData();
    return () => { active = false; };
  }, []);

  async function handleAddToCart(product) {
    if (!user) { navigate('/login'); return; }
    if (product.stock_quantity === 0) { setCartMsg('Out of stock.'); return; }
    setAddingId(product.id);
    setCartMsg('');
    try {
      await addToCartRequest({ customer_id: user.id, product_id: product.id, quantity: 1 });
      setCartMsg(`"${product.name}" added to cart!`);
    } catch (err) {
      setCartMsg(err?.response?.data?.detail || 'Could not add to cart.');
    } finally {
      setAddingId(null);
    }
  }

  const featuredCategories = categories.slice(0, 6);

  if (loading) return <Loader label="Preparing storefront" />;
  if (error)   return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="page-stack">
      {/* ── Hero ── */}
      <section className="hero card">
        <div className="hero__content">
          <p className="eyebrow">🇧🇩 Made in Bangladesh · Dhaka Fashion Hub</p>
          <h1>Discover Bangladeshi Fashion Brands</h1>
          <p>
            Shop Infinity, Richman, Yellow, Easy, Sailor, Ecstasy, Westecs & Texmart —
            authentic Bangladeshi fashion at real BDT prices.
          </p>
          <div className="hero__actions">
            <Button id="hero-browse-btn" onClick={() => navigate('/products')}>Shop Now</Button>
            <Link
              id="hero-auth-btn"
              className="button button--secondary"
              to={isAuthenticated ? '/orders' : '/login'}
            >
              {isAuthenticated ? 'My Orders' : 'Sign In'}
            </Link>
          </div>
        </div>
        <div className="hero__panel">
          <StatCard label="Products"   value={products.length}   hint="Live from Supabase" />
          <StatCard label="Categories" value={categories.length} hint="Organized catalog" />
          <StatCard label="Brands"     value={brands.length}     hint="Premium labels" />
        </div>
      </section>

      {/* ── Featured Products ── */}
      <section className="section-grid">
        <div>
          <PageHeader
            title="Featured products"
            subtitle="Curated picks from the live Supabase catalog."
          />
          {cartMsg && <p className="inline-message" style={{ marginBottom: '1rem' }}>{cartMsg}</p>}
          {products.length ? (
            <div className="cards-grid">
              {products.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  onAddToCart={handleAddToCart}
                  loading={addingId === product.id}
                />
              ))}
            </div>
          ) : (
            <EmptyState title="No products yet" message="Add sample products from the admin panel." />
          )}
        </div>

        <aside className="sidebar-stack">
          <PageHeader title="Categories" subtitle="Browse the full catalog by category." />
          <div className="chip-grid">
            {featuredCategories.map((category) => (
              <Link
                key={category.id}
                id={`home-cat-${category.id}`}
                className="category-chip"
                to={`/products?category_id=${category.id}`}
              >
                {category.name}
              </Link>
            ))}
          </div>

          {brands.length > 0 && (
            <>
              <PageHeader title="Brands" subtitle="Shop your favourite fashion labels." />
              <div className="chip-grid">
                {brands.map((b) => (
                  <Link
                    key={b.id}
                    id={`home-brand-${b.id}`}
                    className="category-chip"
                    to={`/products?brand_id=${b.id}`}
                  >
                    {b.name}
                  </Link>
                ))}
              </div>
            </>
          )}

          <div className="card callout">
            <h3>45-table normalized schema</h3>
            <p>
              Supports brands, variants, inventory, coupons, addresses, reviews, wishlists
              and the full commerce lifecycle from cart to delivered shipment.
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
