import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Button from '../components/Button';
import ErrorState from '../components/ErrorState';
import FormField from '../components/FormField';
import Loader from '../components/Loader';
import PageHeader from '../components/PageHeader';
import ProductCard from '../components/ProductCard';
import { useAuth } from '../context/AuthContext';
import { addToCartRequest } from '../services/commerceService';
import { getCategoriesRequest, getProductsRequest } from '../services/catalogService';
import { createEmptyErrors, validatePrice } from '../utils/validators';

export default function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterError, setFilterError] = useState('');
  const [filters, setFilters] = useState({
    query: searchParams.get('query') || '',
    category_id: searchParams.get('category_id') || '',
    min_price: searchParams.get('min_price') || '',
    max_price: searchParams.get('max_price') || '',
  });
  const [cartMessage, setCartMessage] = useState('');

  useEffect(() => {
    let active = true;

    async function loadProducts() {
      try {
        setLoading(true);
        setError('');
        const [categoryData, productData] = await Promise.all([
          getCategoriesRequest(),
          getProductsRequest({
            query: searchParams.get('query') || '',
            category_id: searchParams.get('category_id') || '',
            min_price: searchParams.get('min_price') || '',
            max_price: searchParams.get('max_price') || '',
          }),
        ]);

        if (!active) return;
        setCategories(categoryData);
        setProducts(productData);
      } catch (loadError) {
        if (!active) return;
        setError(loadError?.response?.data?.detail || 'Failed to load products.');
      } finally {
        if (active) setLoading(false);
      }
    }

    loadProducts();
    return () => {
      active = false;
    };
  }, [searchParams]);

  function handleSearch(event) {
    event.preventDefault();
    setFilterError('');
    const nextErrors = {};
    if (filters.min_price && validatePrice(filters.min_price)) nextErrors.min_price = validatePrice(filters.min_price);
    if (filters.max_price && validatePrice(filters.max_price)) nextErrors.max_price = validatePrice(filters.max_price);
    if (Object.keys(nextErrors).length) {
      setFilterError(Object.values(nextErrors)[0]);
      return;
    }

    const nextParams = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) nextParams.set(key, value);
    });
    setSearchParams(nextParams);
  }

  async function handleAddToCart(product) {
    if (!user) {
      navigate('/login');
      return;
    }

    try {
      setCartMessage('');
      await addToCartRequest({
        customer_id: user.id,
        product_id: product.id,
        quantity: 1,
      });
      setCartMessage(`${product.name} added to cart.`);
    } catch (addError) {
      setCartMessage(addError?.response?.data?.detail || 'Unable to add to cart.');
    }
  }

  const categoryMap = useMemo(() => new Map(categories.map((category) => [category.id, category.name])), [categories]);

  if (loading) return <Loader label="Loading catalog" />;
  if (error) return <ErrorState message={error} onRetry={() => setSearchParams({})} />;

  return (
    <div className="page-stack">
      <PageHeader
        title="Product catalog"
        subtitle="Search by name, category, or price range, then open a product or add it to cart."
      />

      <section className="card filter-panel">
        <form className="filters" onSubmit={handleSearch}>
          <FormField
            label="Search"
            value={filters.query}
            onChange={(event) => setFilters({ ...filters, query: event.target.value })}
            placeholder="Search products"
          />
          <FormField
            as="select"
            label="Category"
            value={filters.category_id}
            onChange={(event) => setFilters({ ...filters, category_id: event.target.value })}
          >
            <option value="">All categories</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </FormField>
          <FormField
            label="Min price"
            type="number"
            value={filters.min_price}
            onChange={(event) => setFilters({ ...filters, min_price: event.target.value })}
            placeholder="0"
          />
          <FormField
            label="Max price"
            type="number"
            value={filters.max_price}
            onChange={(event) => setFilters({ ...filters, max_price: event.target.value })}
            placeholder="10000"
          />
          <div className="filters__actions">
            <Button type="submit">Apply filters</Button>
            <Button variant="secondary" onClick={() => {
              setFilters({ query: '', category_id: '', min_price: '', max_price: '' });
              setSearchParams({});
            }}>
              Reset
            </Button>
          </div>
        </form>
      </section>

      {filterError ? <p className="inline-message">{filterError}</p> : null}
      {cartMessage ? <p className="inline-message">{cartMessage}</p> : null}

      <div className="cards-grid">
        {products.map((product) => (
          <div key={product.id} className="product-with-meta">
            <ProductCard product={{ ...product, category_name: categoryMap.get(product.category_id) }} onAddToCart={handleAddToCart} />
            <p className="mini-meta">Category: {categoryMap.get(product.category_id) || 'Unassigned'}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
