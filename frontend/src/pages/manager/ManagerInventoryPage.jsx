import { useEffect, useState } from 'react';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import { getInventoryLevelsRequest } from '../../services/managerService';
import { formatCurrency } from '../../utils/format';

const FILTERS = [
  { key: 'all',          label: 'All Products' },
  { key: 'out_of_stock', label: '🔴 Out of Stock' },
  { key: 'low_stock',    label: '🟡 Low Stock' },
  { key: 'ok',           label: '🟢 Healthy' },
];

export default function ManagerInventoryPage() {
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState('');
  const [inventory, setInventory] = useState([]);
  const [filter,    setFilter]    = useState('all');
  const [search,    setSearch]    = useState('');

  useEffect(() => {
    getInventoryLevelsRequest()
      .then(setInventory)
      .catch((e) => setError(e?.response?.data?.detail || 'Failed to load inventory.'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = inventory.filter((p) => {
    if (filter !== 'all' && p.stock_status !== filter) return false;
    if (search && !p.product_name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const outCount  = inventory.filter((p) => p.stock_status === 'out_of_stock').length;
  const lowCount  = inventory.filter((p) => p.stock_status === 'low_stock').length;

  if (loading) return <Loader label="Loading inventory" />;
  if (error)   return <ErrorState message={error} />;

  return (
    <div className="mgr-page">
      <div className="mgr-page__header">
        <div>
          <h1 className="mgr-page__title">Inventory</h1>
          <p className="mgr-page__sub">
            {inventory.length} products ·
            <span className="text-danger"> {outCount} out of stock</span> ·
            <span className="text-warn"> {lowCount} low stock</span>
          </p>
        </div>
      </div>

      <div className="mgr-toolbar">
        <input className="mgr-search" placeholder="Search products…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <div className="mgr-filters">
          {FILTERS.map((f) => (
            <button key={f.key} className={`mgr-filter-btn${filter===f.key?' active':''}`} onClick={() => setFilter(f.key)}>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="card mgr-table-card">
        <div className="mgr-table-wrap">
          <table className="mgr-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Brand</th>
                <th>Category</th>
                <th>Price</th>
                <th>Variants</th>
                <th>Available</th>
                <th>Reserved</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.product_id} className={`inv-row inv-row--${p.stock_status}`}>
                  <td><strong>{p.product_name}</strong></td>
                  <td className="muted">{p.brand_name || '—'}</td>
                  <td className="muted">{p.category_name || '—'}</td>
                  <td>{formatCurrency(p.base_price)}</td>
                  <td className="muted">{p.variant_count}</td>
                  <td>
                    <span className={`stock-pill stock-pill--${p.stock_status}`}>
                      {p.available_stock}
                    </span>
                  </td>
                  <td className="muted">{p.reserved_stock}</td>
                  <td>
                    {p.stock_status === 'out_of_stock' && <span className="inv-badge inv-badge--out">Out of Stock</span>}
                    {p.stock_status === 'low_stock'    && <span className="inv-badge inv-badge--low">Low Stock</span>}
                    {p.stock_status === 'ok'           && <span className="inv-badge inv-badge--ok">✓ OK</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
