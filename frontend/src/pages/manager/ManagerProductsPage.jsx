import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import FormField from '../../components/FormField';
import Loader from '../../components/Loader';
import StatusBadge from '../../components/StatusBadge';
import {
  createProductRequest,
  deleteProductRequest,
  getCategoriesRequest,
  getProductsRequest,
  getSuppliersRequest,
  updateProductRequest,
} from '../../services/catalogService';
import { formatCurrency } from '../../utils/format';

const EMPTY = { name:'', sku:'', description:'', price:'', stock_quantity:'', category_id:'', supplier_id:'', is_active:'true', available_sizes:'' };

export default function ManagerProductsPage() {
  const [loading, setLoading]       = useState(true);
  const [error,   setError]         = useState('');
  const [products, setProducts]     = useState([]);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers]   = useState([]);
  const [form, setForm]             = useState(EMPTY);
  const [editId, setEditId]         = useState(null);
  const [saving, setSaving]         = useState(false);
  const [search, setSearch]         = useState('');
  const [showForm, setShowForm]     = useState(false);

  async function load() {
    try {
      setLoading(true);
      const [p, c, s] = await Promise.all([getProductsRequest(), getCategoriesRequest(), getSuppliersRequest()]);
      setProducts(p); setCategories(c); setSuppliers(s);
    } catch (e) { setError(e?.response?.data?.detail || 'Failed to load.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  function startEdit(p) {
    setEditId(p.id);
    setForm({ name:p.name, sku:p.sku, description:p.description||'', price:p.price,
      stock_quantity:p.stock_quantity, category_id:p.category_id, supplier_id:p.supplier_id,
      is_active:String(p.is_active), available_sizes:p.available_sizes||'' });
    setShowForm(true);
  }
  function cancelEdit() { setEditId(null); setForm(EMPTY); setShowForm(false); }

  async function handleSave(e) {
    e.preventDefault();
    if (!form.name || !form.price) return;
    setSaving(true);
    try {
      const payload = { ...form, price:Number(form.price), stock_quantity:Number(form.stock_quantity),
        category_id:Number(form.category_id), supplier_id:Number(form.supplier_id), is_active:form.is_active==='true' };
      editId ? await updateProductRequest(editId, payload) : await createProductRequest(payload);
      cancelEdit(); await load();
    } catch (e) { setError(e?.response?.data?.detail || 'Save failed.'); }
    finally { setSaving(false); }
  }

  async function handleDelete(id) {
    if (!window.confirm('Delete this product?')) return;
    try { await deleteProductRequest(id); await load(); }
    catch (e) { setError(e?.response?.data?.detail || 'Delete failed.'); }
  }

  const filtered = products.filter((p) =>
    !search || p.name.toLowerCase().includes(search.toLowerCase()) || (p.sku||'').toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <Loader label="Loading products" />;

  return (
    <div className="mgr-page">
      <div className="mgr-page__header">
        <div>
          <h1 className="mgr-page__title">Products</h1>
          <p className="mgr-page__sub">{products.length} products in catalogue</p>
        </div>
        <button className="button" onClick={() => { cancelEdit(); setShowForm(!showForm); }}>
          {showForm ? '✕ Close Form' : '+ New Product'}
        </button>
      </div>
      {error && <ErrorState message={error} />}

      {showForm && (
        <div className="card mgr-form-card">
          <h2 className="mgr-form-card__title">{editId ? 'Edit Product' : 'Create Product'}</h2>
          <form className="form-grid" onSubmit={handleSave}>
            <FormField label="Name" value={form.name} onChange={(e) => setForm({...form,name:e.target.value})} />
            <FormField label="SKU" value={form.sku} onChange={(e) => setForm({...form,sku:e.target.value})} />
            <FormField label="Price" type="number" step="0.01" value={form.price} onChange={(e) => setForm({...form,price:e.target.value})} />
            <FormField label="Stock" type="number" value={form.stock_quantity} onChange={(e) => setForm({...form,stock_quantity:e.target.value})} />
            <FormField as="select" label="Category" value={form.category_id} onChange={(e) => setForm({...form,category_id:e.target.value})}>
              <option value="">— Select —</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </FormField>
            <FormField as="select" label="Supplier" value={form.supplier_id} onChange={(e) => setForm({...form,supplier_id:e.target.value})}>
              <option value="">— Select —</option>
              {suppliers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </FormField>
            <FormField as="select" label="Status" value={form.is_active} onChange={(e) => setForm({...form,is_active:e.target.value})}>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </FormField>
            <FormField label="Sizes (comma-sep)" value={form.available_sizes} onChange={(e) => setForm({...form,available_sizes:e.target.value})} placeholder="XS,S,M,L,XL" />
            <FormField className="form-grid__full" as="textarea" rows="3" label="Description" value={form.description} onChange={(e) => setForm({...form,description:e.target.value})} />
            <div className="form-grid__full" style={{display:'flex',gap:'0.75rem'}}>
              <Button type="submit" loading={saving}>{editId ? 'Update' : 'Create'}</Button>
              <button type="button" className="button button--secondary" onClick={cancelEdit}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="mgr-toolbar">
        <input className="mgr-search" placeholder="Search products…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <span className="muted">{filtered.length} result{filtered.length !== 1 ? 's' : ''}</span>
      </div>

      <div className="card mgr-table-card">
        <div className="mgr-table-wrap">
          <table className="mgr-table">
            <thead><tr><th>Product</th><th>Price</th><th>Stock</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id}>
                  <td>
                    <strong>{p.name}</strong>
                    <p className="muted" style={{fontSize:'0.78rem'}}>{p.sku}</p>
                  </td>
                  <td>{formatCurrency(p.price)}</td>
                  <td>
                    <span className={`stock-pill${p.stock_quantity < 5 ? ' stock-pill--out' : p.stock_quantity < 20 ? ' stock-pill--low' : ''}`}>
                      {p.stock_quantity}
                    </span>
                  </td>
                  <td><StatusBadge value={p.is_active ? 'active' : 'inactive'} /></td>
                  <td>
                    <div style={{display:'flex',gap:'0.5rem'}}>
                      <button className="mgr-btn" onClick={() => startEdit(p)}>✏️ Edit</button>
                      <button className="mgr-btn mgr-btn--danger" onClick={() => handleDelete(p.id)}>🗑️</button>
                    </div>
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
