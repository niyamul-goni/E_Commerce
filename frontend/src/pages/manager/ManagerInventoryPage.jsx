import { useEffect, useState } from 'react';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import {
  getInventoryLevelsRequest,
  updateInventoryStockRequest,
} from '../../services/managerService';
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
  const [drafts,    setDrafts]    = useState({});
  const [savingId,  setSavingId]  = useState(null);
  const [notice,    setNotice]    = useState('');
  const [saveError, setSaveError] = useState('');

  useEffect(() => {
    getInventoryLevelsRequest()
      .then((rows) => {
        setInventory(rows);
        setDrafts(Object.fromEntries(rows.map((row) => [row.product_id, String(row.available_stock)])));
      })
      .catch((e) => setError(e?.response?.data?.detail || 'Failed to load inventory.'))
      .finally(() => setLoading(false));
  }, []);

  async function saveStock(product) {
    const nextStock = Number(drafts[product.product_id]);
    if (!Number.isInteger(nextStock) || nextStock < 0) {
      setNotice('');
      setSaveError('Available stock must be a whole number of zero or more.');
      return;
    }

    try {
      setSavingId(product.product_id);
      setSaveError('');
      setNotice('');
      const updated = await updateInventoryStockRequest(product.product_id, nextStock);
      setInventory((current) => current.map((row) => (
        row.product_id === product.product_id
          ? { ...row, ...updated }
          : row
      )));
      setDrafts((current) => ({ ...current, [product.product_id]: String(updated.available_stock) }));
      setNotice(`${product.product_name} inventory updated.`);
    } catch (updateError) {
      setSaveError(updateError?.response?.data?.detail || 'Failed to update inventory.');
    } finally {
      setSavingId(null);
    }
  }

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

      {notice ? <p className="mgr-inline-notice mgr-inline-notice--success">{notice}</p> : null}
      {saveError ? <p className="mgr-inline-notice mgr-inline-notice--error">{saveError}</p> : null}

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
                <th>Set available stock</th>
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
                  <td>
                    <div className="inventory-editor">
                      <input
                        type="number"
                        min="0"
                        step="1"
                        aria-label={`Available stock for ${p.product_name}`}
                        value={drafts[p.product_id] ?? ''}
                        onChange={(event) => setDrafts({
                          ...drafts,
                          [p.product_id]: event.target.value,
                        })}
                      />
                      <button
                        type="button"
                        className="mgr-btn"
                        disabled={savingId === p.product_id || String(p.available_stock) === drafts[p.product_id]}
                        onClick={() => saveStock(p)}
                      >
                        {savingId === p.product_id ? 'Saving…' : 'Save'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 ? (
                <tr><td colSpan="9" className="mgr-empty-table">No inventory matches this view.</td></tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
