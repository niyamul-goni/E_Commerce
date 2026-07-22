import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import Loader from '../components/Loader';
import ProductCard from '../components/ProductCard';
import { useAuth } from '../context/AuthContext';
import {
  getBrandsRequest,
  getCategoriesRequest,
  getFeaturedProductsRequest,
  getTrendingProductsRequest,
  getNewArrivalsRequest,
} from '../services/catalogService';
import { addToCartRequest } from '../services/commerceService';

export default function HomePage() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState('');
  const [categories, setCategories] = useState([]);
  const [brands,     setBrands]     = useState([]);
  const [featured,   setFeatured]   = useState([]);
  const [trending,   setTrending]   = useState([]);
  const [newArrivals, setNewArrivals] = useState([]);
  const [addingId,   setAddingId]   = useState(null);
  const [cartMsg,    setCartMsg]    = useState('');

  useEffect(() => {
    let active = true;

    async function loadHomeData() {
      try {
        setLoading(true);
        setError('');
        const [catData, brandData, featuredData, trendingData, newData] = await Promise.all([
          getCategoriesRequest(),
          getBrandsRequest(),
          getFeaturedProductsRequest(8),
          getTrendingProductsRequest(8),
          getNewArrivalsRequest(8),
        ]);

        if (!active) return;
        setCategories(catData);
        setBrands(brandData);
        setFeatured(featuredData);
        setTrending(trendingData);
        setNewArrivals(newData);
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
      await addToCartRequest({ product_id: product.id, quantity: 1 });
      setCartMsg(`"${product.name}" added to cart!`);
    } catch (err) {
      setCartMsg(err?.response?.data?.detail || 'Could not add to cart.');
    } finally {
      setAddingId(null);
    }
  }

  if (loading) return <Loader label="Preparing storefront" />;
  if (error)   return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="page-stack">
      {/* ── Hero ── */}
      <section className="hero card">
        <div className="hero__content">
          <p className="eyebrow">New season · New perspective</p>
          <h1>Find your next fit with GoDrip</h1>
          <p className="hero__subtitle">
            Discover clothing, footwear and accessories from a growing catalogue of styles and brands.
          </p>
          <div className="hero__actions">
            <Button id="hero-browse-btn" onClick={() => navigate('/products')}>Shop All Products</Button>
            <Link
              id="hero-auth-btn"
              className="button button--secondary"
              to={isAuthenticated ? '/orders' : '/login'}
            >
              {isAuthenticated ? 'My Orders' : 'Sign In'}
            </Link>
          </div>
        </div>
      </section>

      {cartMsg && <p className="inline-message" style={{ marginBottom: '0.5rem' }}>{cartMsg}</p>}

      {/* ── Featured Products ── */}
      {featured.length > 0 && (
        <section className="home-section">
          <div className="home-section__header">
            <div>
              <h2 className="home-section__title">Featured Products</h2>
              <p className="home-section__subtitle">Hand-picked selections from our curated catalog</p>
            </div>
            <Link className="button button--secondary" to="/products">View All →</Link>
          </div>
          <div className="products-grid">
            {featured.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={handleAddToCart}
                loading={addingId === product.id}
              />
            ))}
          </div>
        </section>
      )}

      {/* ── Categories Showcase ── */}
      {categories.length > 0 && (
        <section className="home-section">
          <div className="home-section__header">
            <div>
              <h2 className="home-section__title">Shop by Category</h2>
              <p className="home-section__subtitle">Browse our organized fashion catalog</p>
            </div>
          </div>
          <div className="category-showcase">
            {categories.map((category) => (
              <Link
                key={category.id}
                id={`home-cat-${category.id}`}
                className="category-showcase__card"
                to={`/products?category_id=${category.id}`}
              >
                <div className="category-showcase__icon">
                  {category.name.includes('Men') ? '👔' :
                   category.name.includes('Women') ? '👗' :
                   category.name.includes('Kid') ? '🧸' :
                   category.name.includes('Foot') ? '👟' :
                   category.name.includes('Access') ? '⌚' : '🛍️'}
                </div>
                <h3 className="category-showcase__name">{category.name}</h3>
                <p className="category-showcase__desc">{category.description || 'Explore collection'}</p>
                <span className="category-showcase__link">Browse →</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ── Trending Products ── */}
      {trending.length > 0 && (
        <section className="home-section">
          <div className="home-section__header">
            <div>
              <h2 className="home-section__title">🔥 Trending Now</h2>
              <p className="home-section__subtitle">What everyone&apos;s buying this week</p>
            </div>
            <Link className="button button--secondary" to="/products">View All →</Link>
          </div>
          <div className="products-grid">
            {trending.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={handleAddToCart}
                loading={addingId === product.id}
              />
            ))}
          </div>
        </section>
      )}

      {/* ── Brand Showcase ── */}
      {brands.length > 0 && (
        <section className="home-section">
          <div className="home-section__header">
            <div>
              <h2 className="home-section__title">Premium Brands</h2>
              <p className="home-section__subtitle">Shop your favourite Bangladeshi fashion labels</p>
            </div>
          </div>
          <div className="brand-showcase">
            {brands.map((b) => (
              <Link
                key={b.id}
                id={`home-brand-${b.id}`}
                className="brand-showcase__card"
                to={`/products?brand_id=${b.id}`}
              >
                <span className="brand-showcase__name">{b.name}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ── New Arrivals ── */}
      {newArrivals.length > 0 && (
        <section className="home-section">
          <div className="home-section__header">
            <div>
              <h2 className="home-section__title">✨ New Arrivals</h2>
              <p className="home-section__subtitle">Fresh styles just dropped into the store</p>
            </div>
            <Link className="button button--secondary" to="/products">View All →</Link>
          </div>
          <div className="products-grid">
            {newArrivals.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onAddToCart={handleAddToCart}
                loading={addingId === product.id}
              />
            ))}
          </div>
        </section>
      )}

      {/* ── CTA Banner ── */}
      <section className="cta-banner card">
        <div className="cta-banner__content">
          <h2>Ready to upgrade your wardrobe?</h2>
          <p>Explore new products and brands as the GoDrip catalogue continues to grow.</p>
          <div className="cta-banner__actions">
            <Button onClick={() => navigate('/products')}>Explore All Products</Button>
            {!isAuthenticated && (
              <Link className="button button--secondary" to="/register">Create Account</Link>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
