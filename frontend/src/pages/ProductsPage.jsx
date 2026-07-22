import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import ProductCard from '../components/ProductCard';
import { useAuth } from '../context/AuthContext';
import {
  getBrandsRequest,
  getCategoriesRequest,
  getProductsRequest,
} from '../services/catalogService';
import { addToCartRequest } from '../services/commerceService';

// ── Size groups per category type ────────────────────────────────────────────
const CLOTHING_CATS   = ['shirts', 't-shirts', 'jackets', 'activewear', 'kurta', 'punjabi'];
const BOTTOM_CATS     = ['pants', 'jeans', 'trousers'];
const SHOE_CATS       = ['shoes'];
const ACCESSORY_CATS  = ['accessories'];

const CLOTH_SIZES   = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
const BOTTOM_SIZES  = ['28', '30', '32', '34', '36', '38'];
const SHOE_SIZES    = ['38', '39', '40', '41', '42', '43', '44', '45'];
const ALL_SIZES     = [...CLOTH_SIZES, ...BOTTOM_SIZES, ...SHOE_SIZES];

function getSizesForCategoryName(name) {
  if (!name) return ALL_SIZES;
  const key = name.toLowerCase();
  if (CLOTHING_CATS.some((c) => key.includes(c))) return CLOTH_SIZES;
  if (BOTTOM_CATS.some((c) => key.includes(c))) return BOTTOM_SIZES;
  if (SHOE_CATS.some((c) => key.includes(c))) return SHOE_SIZES;
  if (ACCESSORY_CATS.some((c) => key.includes(c))) return [];
  return ALL_SIZES;
}

export default function ProductsPage() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  // Filter state — initialise from URL
  const [query,        setQuery]        = useState(searchParams.get('q')           || '');
  const [categoryId,   setCategoryId]   = useState(searchParams.get('category_id') || '');
  const [brandId,      setBrandId]      = useState(searchParams.get('brand_id')    || '');
  const [selectedSize, setSelectedSize] = useState(searchParams.get('size')        || '');
  const [minPrice,     setMinPrice]     = useState(searchParams.get('min_price')   || '');
  const [maxPrice,     setMaxPrice]     = useState(searchParams.get('max_price')   || '');

  // Reference data
  const [categories, setCategories] = useState([]);
  const [brands,     setBrands]     = useState([]);

  // Results
  const [products,    setProducts]    = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [searching,   setSearching]   = useState(false);
  const [error,       setError]       = useState('');
  const [addingId,    setAddingId]    = useState(null);
  const [cartMsg,     setCartMsg]     = useState('');

  // Load reference data once
  useEffect(() => {
    async function loadReferenceData() {
      try {
        const [catData, brandData] = await Promise.all([
          getCategoriesRequest(),
          getBrandsRequest(),
        ]);
        setCategories(catData);
        setBrands(brandData);
      } catch { /* non-fatal */ }
    }
    loadReferenceData();
  }, []);

  // Auto-search on mount — always load products
  useEffect(() => {
    performSearch({
      query:       searchParams.get('q')           || '',
      category_id: searchParams.get('category_id') || '',
      brand_id:    searchParams.get('brand_id')    || '',
      size:        searchParams.get('size')        || '',
      min_price:   searchParams.get('min_price')   || '',
      max_price:   searchParams.get('max_price')   || '',
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Dynamic size chips based on selected category
  const activeCategoryName = useMemo(() => {
    if (!categoryId) return null;
    return categories.find((c) => String(c.id) === String(categoryId))?.name || null;
  }, [categoryId, categories]);

  const sizeOptions = useMemo(
    () => getSizesForCategoryName(activeCategoryName),
    [activeCategoryName]
  );

  async function performSearch(overrides = {}) {
    const params = {
      query:       overrides.query       ?? query,
      category_id: overrides.category_id ?? categoryId,
      brand_id:    overrides.brand_id    ?? brandId,
      size:        overrides.size        ?? selectedSize,
      min_price:   overrides.min_price   ?? minPrice,
      max_price:   overrides.max_price   ?? maxPrice,
    };

    // Sync URL
    const nextParams = {};
    if (params.query)       nextParams.q           = params.query;
    if (params.category_id) nextParams.category_id = params.category_id;
    if (params.brand_id)    nextParams.brand_id    = params.brand_id;
    if (params.size)        nextParams.size        = params.size;
    if (params.min_price)   nextParams.min_price   = params.min_price;
    if (params.max_price)   nextParams.max_price   = params.max_price;
    setSearchParams(nextParams);

    setHasSearched(true);
    setSearching(true);
    setError('');
    setCartMsg('');
    try {
      const data = await getProductsRequest(params);
      setProducts(data);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Search failed. Please try again.');
    } finally {
      setSearching(false);
    }
  }

  function handleReset() {
    setQuery('');
    setCategoryId('');
    setBrandId('');
    setSelectedSize('');
    setMinPrice('');
    setMaxPrice('');
    setSearchParams({});
    setHasSearched(false);
    setProducts([]);
    setCartMsg('');
    setError('');
  }

  function handleCategoryChange(id) {
    const next = String(categoryId) === String(id) ? '' : String(id);
    setCategoryId(next);
    setSelectedSize(''); // reset size when category changes
    performSearch({ category_id: next, size: '' });
  }

  function handleBrandChange(id) {
    const next = String(brandId) === String(id) ? '' : String(id);
    setBrandId(next);
    performSearch({ brand_id: next });
  }

  function handleSizeClick(size) {
    const next = selectedSize === size ? '' : size;
    setSelectedSize(next);
    performSearch({ size: next });
  }

  async function handleAddToCart(product) {
    if (!user) {
      setCartMsg('Please sign in to add items to your cart.');
      return;
    }
    if (product.stock_quantity === 0) {
      setCartMsg('This item is out of stock.');
      return;
    }
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

  return (
    <div className="page-stack">
      {/* ── Hero Search Bar ── */}
      <div className="search-hero card">
        <h1 className="search-hero__title">Explore GoDrip</h1>
        <p className="search-hero__sub">Search the complete catalogue across every available product and brand.</p>
        <div className="search-bar">
          <input
            id="product-search-input"
            className="search-bar__input"
            type="text"
            placeholder="Search products, brands…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') performSearch(); }}
          />
          <button
            id="product-search-btn"
            className="button"
            style={{ borderRadius: 999, padding: '0.75rem 2rem', whiteSpace: 'nowrap' }}
            onClick={() => performSearch()}
          >
            Search
          </button>
        </div>
      </div>

      {/* ── Filter Bar ── */}
      <div className="filter-bar card">
        <div className="filter-bar__grid">
          {/* Category */}
          <div className="field">
            <label className="field__label">Category</label>
            <select
              id="filter-category"
              className="field__control"
              value={categoryId}
              onChange={(e) => {
                const next = e.target.value;
                setCategoryId(next);
                setSelectedSize('');
                performSearch({ category_id: next, size: '' });
              }}
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          {/* Brand */}
          <div className="field">
            <label className="field__label">Brand</label>
            <select
              id="filter-brand"
              className="field__control"
              value={brandId}
              onChange={(e) => {
                setBrandId(e.target.value);
                performSearch({ brand_id: e.target.value });
              }}
            >
              <option value="">All Brands</option>
              {brands.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>

          {/* Min Price */}
          <div className="field">
            <label className="field__label">Min Price (BDT)</label>
            <input
              id="filter-min-price"
              className="field__control"
              type="number"
              placeholder="0"
              value={minPrice}
              onChange={(e) => setMinPrice(e.target.value)}
            />
          </div>

          {/* Max Price */}
          <div className="field">
            <label className="field__label">Max Price (BDT)</label>
            <input
              id="filter-max-price"
              className="field__control"
              type="number"
              placeholder="Any"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
            />
          </div>
        </div>

        {/* Dynamic size chips — change based on selected category */}
        {sizeOptions.length > 0 && (
          <div className="field">
            <label className="field__label">
              Size
              {activeCategoryName && (
                <span className="field__label-hint">
                  {' '}— {activeCategoryName}
                </span>
              )}
            </label>
            <div className="size-chips">
              {sizeOptions.map((s) => (
                <button
                  key={s}
                  id={`size-chip-${s}`}
                  className={`size-chip${selectedSize === s ? ' active' : ''}`}
                  onClick={() => handleSizeClick(s)}
                  type="button"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="filter-bar__actions">
          <button id="apply-filters-btn" className="button" onClick={() => performSearch()}>
            Apply Filters
          </button>
          <button id="reset-filters-btn" className="button button--secondary" onClick={handleReset}>
            Reset
          </button>
          {cartMsg && (
            <span className="inline-message" style={{ marginLeft: 'auto' }}>{cartMsg}</span>
          )}
        </div>
      </div>

      {/* ── Brand Pills ── */}
      {brands.length > 0 && !hasSearched && (
        <div>
          <div className="eyebrow" style={{ marginBottom: '1rem' }}>Shop by Brand</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
            {brands.map((b) => (
              <button
                key={b.id}
                id={`brand-pill-${b.id}`}
                type="button"
                onClick={() => handleBrandChange(b.id)}
                className={`brand-pill${String(brandId) === String(b.id) ? ' active' : ''}`}
              >
                {b.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Category Pills ── */}
      {categories.length > 0 && !hasSearched && (
        <div>
          <div className="eyebrow" style={{ marginBottom: '1rem' }}>Shop by Category</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
            {categories.map((c) => (
              <button
                key={c.id}
                id={`cat-pill-${c.id}`}
                type="button"
                onClick={() => handleCategoryChange(c.id)}
                className={`cat-pill${String(categoryId) === String(c.id) ? ' active' : ''}`}
              >
                {c.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Prompt State ── */}
      {!hasSearched && (
        <div className="catalog-empty-state">
          <div style={{ fontSize: '3rem', opacity: 0.25 }}>🛍️</div>
          <h2>Discover Bangladeshi Fashion</h2>
          <p>Search for products or pick a brand / category above to get started.</p>
        </div>
      )}

      {/* ── Searching ── */}
      {hasSearched && searching && (
        <div className="state state--loading">
          <div className="spinner" />
          <p style={{ color: 'var(--text-2)', marginTop: '1rem' }}>Finding products…</p>
        </div>
      )}

      {/* ── Error ── */}
      {hasSearched && !searching && error && (
        <ErrorState message={error} onRetry={() => performSearch()} />
      )}

      {/* ── Results ── */}
      {hasSearched && !searching && !error && (
        <>
          <div className="results-header">
            <span className="results-count">
              {products.length} {products.length === 1 ? 'product' : 'products'} found
              {activeCategoryName && ` in ${activeCategoryName}`}
            </span>
          </div>

          {products.length === 0 ? (
            <EmptyState
              title="No Results"
              message="Try adjusting your filters or search term."
            />
          ) : (
            <div className="products-grid">
              {products.map((p) => (
                <ProductCard
                  key={p.id}
                  product={p}
                  onAddToCart={handleAddToCart}
                  loading={addingId === p.id}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
