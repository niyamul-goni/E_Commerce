import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import FormField from '../../components/FormField';
import Loader from '../../components/Loader';
import StatusBadge from '../../components/StatusBadge';
import {
  createProductRequest,
  deleteProductRequest,
  getBrandsRequest,
  getManagedCategoriesRequest,
  getManagedProductsRequest,
  getSubcategoriesRequest,
  getSuppliersRequest,
  updateProductRequest,
  uploadProductImageRequest,
} from '../../services/catalogService';
import { formatCurrency } from '../../utils/format';
import { resolveProductImage } from '../../utils/productImages';

const EMPTY = { name:'', sku:'', description:'', price:'', stock_quantity:'', category_id:'', subcategory_id:'', brand_id:'', supplier_id:'', is_active:'true', available_sizes:'' };
const ALLOWED_IMAGE_TYPES = new Set(['image/jpeg', 'image/png', 'image/gif', 'image/webp']);
const ALLOWED_IMAGE_EXTENSIONS = new Set(['jpg', 'jpeg', 'png', 'gif', 'webp']);
const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

function productToForm(product) {
  return {
    name: product.name,
    sku: product.sku,
    description: product.description || '',
    price: String(product.price),
    stock_quantity: String(product.stock_quantity),
    category_id: product.category_id ? String(product.category_id) : '',
    subcategory_id: product.subcategory_id ? String(product.subcategory_id) : '',
    brand_id: product.brand_id ? String(product.brand_id) : '',
    supplier_id: product.supplier_id ? String(product.supplier_id) : '',
    is_active: String(product.is_active),
    available_sizes: Array.isArray(product.available_sizes)
      ? product.available_sizes.join(',')
      : (product.available_sizes || ''),
  };
}

function formToPayload(form) {
  return {
    name: form.name.trim(),
    sku: form.sku.trim(),
    description: form.description.trim() || null,
    available_sizes: form.available_sizes.trim() || null,
    price: Number(form.price),
    stock_quantity: Number(form.stock_quantity),
    category_id: Number(form.category_id),
    subcategory_id: Number(form.subcategory_id),
    brand_id: Number(form.brand_id),
    supplier_id: Number(form.supplier_id),
    is_active: form.is_active === 'true',
  };
}

function ProductImageCell({ product, previewUrl }) {
  const imageUrl = previewUrl || resolveProductImage(product);
  const [failed, setFailed] = useState(false);

  useEffect(() => { setFailed(false); }, [imageUrl]);

  return (
    <div className="mgr-product-image">
      {imageUrl && !failed ? (
        <img src={imageUrl} alt={product.name} onError={() => setFailed(true)} />
      ) : (
        <div className="mgr-product-image__empty" aria-label={`${product.name} has no image`}>
          <span>▧</span>
          <small>No image</small>
        </div>
      )}
    </div>
  );
}

export default function ManagerProductsPage() {
  const [loading, setLoading]       = useState(true);
  const [error,   setError]         = useState('');
  const [products, setProducts]     = useState([]);
  const [categories, setCategories] = useState([]);
  const [subcategories, setSubcategories] = useState([]);
  const [brands, setBrands]         = useState([]);
  const [suppliers, setSuppliers]   = useState([]);
  const [form, setForm]             = useState(EMPTY);
  const [originalForm, setOriginalForm] = useState(null);
  const [editId, setEditId]         = useState(null);
  const [saving, setSaving]         = useState(false);
  const [search, setSearch]         = useState('');
  const [showForm, setShowForm]     = useState(false);
  const [uploadingId, setUploadingId] = useState(null);
  const [uploadPreview, setUploadPreview] = useState(null);
  const [notice, setNotice]         = useState('');

  async function load(showLoader = true) {
    try {
      if (showLoader) setLoading(true);
      setError('');
      const [p, c, sc, b, s] = await Promise.all([
        getManagedProductsRequest(), getManagedCategoriesRequest(), getSubcategoriesRequest(),
        getBrandsRequest(), getSuppliersRequest(),
      ]);
      setProducts(p); setCategories(c); setSubcategories(sc); setBrands(b); setSuppliers(s);
    } catch (e) { setError(e?.response?.data?.detail || 'Failed to load.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);
  useEffect(() => () => {
    if (uploadPreview?.url) URL.revokeObjectURL(uploadPreview.url);
  }, [uploadPreview]);

  function startEdit(p) {
    const nextForm = productToForm(p);
    setEditId(p.id);
    setForm(nextForm);
    setOriginalForm(nextForm);
    setShowForm(true);
  }
  function cancelEdit() {
    setEditId(null);
    setForm(EMPTY);
    setOriginalForm(null);
    setShowForm(false);
  }

  async function handleSave(e) {
    e.preventDefault();
    setError('');
    setNotice('');
    if (!form.name.trim() || !form.sku.trim() || !form.price || !form.category_id || !form.subcategory_id || !form.brand_id || !form.supplier_id) {
      setError('Name, SKU, price, category, subcategory, brand, and supplier are required.');
      return;
    }
    if (!Number.isFinite(Number(form.price)) || Number(form.price) <= 0) {
      setError('Price must be greater than zero.');
      return;
    }
    if (!Number.isInteger(Number(form.stock_quantity)) || Number(form.stock_quantity) < 0) {
      setError('Stock must be a whole number of zero or more.');
      return;
    }
    setSaving(true);
    try {
      const payload = formToPayload(form);
      if (editId) {
        const originalPayload = formToPayload(originalForm);
        const changedPayload = Object.fromEntries(
          Object.entries(payload).filter(([key, value]) => value !== originalPayload[key]),
        );
        if (Object.keys(changedPayload).length === 0) {
          setNotice('No product changes to save.');
          setSaving(false);
          return;
        }
        await updateProductRequest(editId, changedPayload);
      } else {
        await createProductRequest(payload);
      }
      setNotice(editId ? 'Product updated successfully.' : 'Product created successfully.');
      cancelEdit(); await load(false);
    } catch (e) { setError(e?.response?.data?.detail || 'Save failed.'); }
    finally { setSaving(false); }
  }

  async function handleDelete(id) {
    if (!window.confirm('Deactivate this product? Order history will be preserved.')) return;
    setError(''); setNotice('');
    try {
      await deleteProductRequest(id);
      setNotice('Product deactivated successfully.');
      await load(false);
    }
    catch (e) { setError(e?.response?.data?.detail || 'Delete failed.'); }
  }

  async function handleImageSelected(product, event) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;

    setError('');
    setNotice('');
    const extension = file.name.split('.').pop()?.toLowerCase();
    if ((!ALLOWED_IMAGE_TYPES.has(file.type) && file.type) || !ALLOWED_IMAGE_EXTENSIONS.has(extension)) {
      setError('Choose a JPG, PNG, GIF, or WebP image.');
      return;
    }
    if (file.size <= 0 || file.size > MAX_IMAGE_BYTES) {
      setError('The image must be larger than 0 bytes and no more than 5 MB.');
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    setUploadPreview({ productId: product.id, url: previewUrl });
    setUploadingId(product.id);
    try {
      const uploaded = await uploadProductImageRequest(product.id, file);
      setProducts((current) => current.map((item) => (
        item.id === product.id ? { ...item, image_url: uploaded.image_url } : item
      )));
      setNotice(`Image uploaded for “${product.name}”.`);
    } catch (uploadError) {
      setError(
        uploadError?.response?.data?.detail
        || uploadError?.message
        || 'Image upload failed. Please try again.',
      );
    } finally {
      setUploadingId(null);
      setUploadPreview(null);
    }
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
      {notice && <p className="inline-message inline-message--success" role="status">{notice}</p>}

      {showForm && (
        <div className="card mgr-form-card">
          <h2 className="mgr-form-card__title">{editId ? 'Edit Product' : 'Create Product'}</h2>
          <form className="form-grid" onSubmit={handleSave}>
            <FormField label="Name" value={form.name} onChange={(e) => setForm({...form,name:e.target.value})} />
            <FormField label={editId ? 'Primary variant SKU' : 'SKU'} value={form.sku} onChange={(e) => setForm({...form,sku:e.target.value})} />
            <FormField label="Price" type="number" step="0.01" value={form.price} onChange={(e) => setForm({...form,price:e.target.value})} />
            <FormField label="Stock" type="number" value={form.stock_quantity} onChange={(e) => setForm({...form,stock_quantity:e.target.value})} />
            <FormField as="select" label="Category" value={form.category_id} onChange={(e) => setForm({...form,category_id:e.target.value,subcategory_id:''})}>
              <option value="">— Select —</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </FormField>
            <FormField as="select" label="Subcategory" value={form.subcategory_id} onChange={(e) => setForm({...form,subcategory_id:e.target.value})}>
              <option value="">— Select —</option>
              {subcategories.filter((sc) => String(sc.category_id) === String(form.category_id)).map((sc) => (
                <option key={sc.id} value={sc.id}>{sc.name}</option>
              ))}
            </FormField>
            <FormField as="select" label="Brand" value={form.brand_id} onChange={(e) => setForm({...form,brand_id:e.target.value})}>
              <option value="">— Select —</option>
              {brands.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
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
            <thead><tr><th>Image</th><th>Product</th><th>Price</th><th>Stock</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id}>
                  <td>
                    <ProductImageCell
                      product={p}
                      previewUrl={uploadPreview?.productId === p.id ? uploadPreview.url : null}
                    />
                  </td>
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
                      <label
                        className={`mgr-btn mgr-upload-btn${uploadingId === p.id ? ' mgr-upload-btn--busy' : ''}`}
                        htmlFor={`product-image-${p.id}`}
                        aria-disabled={uploadingId !== null}
                      >
                        {uploadingId === p.id ? 'Uploading…' : p.image_url && resolveProductImage(p) ? '🖼️ Replace' : '🖼️ Upload'}
                      </label>
                      <input
                        id={`product-image-${p.id}`}
                        className="visually-hidden"
                        type="file"
                        accept="image/jpeg,image/png,image/gif,image/webp"
                        disabled={uploadingId !== null}
                        onChange={(event) => handleImageSelected(p, event)}
                      />
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
