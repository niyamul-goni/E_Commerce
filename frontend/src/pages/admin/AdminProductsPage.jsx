import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import FormField from '../../components/FormField';
import Loader from '../../components/Loader';
import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import {
  createProductRequest,
  deleteProductRequest,
  getCategoriesRequest,
  getProductsRequest,
  getSuppliersRequest,
  updateProductRequest,
  uploadProductImageRequest,
} from '../../services/catalogService';
import { createEmptyErrors, validatePrice, validateQuantity, validateRequired } from '../../utils/validators';
import { formatCurrency } from '../../utils/format';
import { resolveProductImage } from '../../utils/productImages';

const emptyForm = {
  name: '',
  sku: '',
  description: '',
  price: '',
  stock_quantity: '',
  category_id: '',
  supplier_id: '',
  is_active: 'true',
  available_sizes: '',
};

export default function AdminProductsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [formErrors, setFormErrors] = useState(createEmptyErrors());
  const [submitting, setSubmitting] = useState(false);
  const [editingProductId, setEditingProductId] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  async function loadData() {
    try {
      setLoading(true);
      setError('');
      const [productData, categoryData, supplierData] = await Promise.all([
        getProductsRequest(),
        getCategoriesRequest(),
        getSuppliersRequest(),
      ]);
      setProducts(productData);
      setCategories(categoryData);
      setSuppliers(supplierData);
    } catch (loadError) {
      setError(loadError?.response?.data?.detail || 'Failed to load product management data.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function validateForm() {
    const nextErrors = {
      name: validateRequired(form.name, 'Product name'),
      sku: validateRequired(form.sku, 'SKU'),
      price: validatePrice(form.price),
      stock_quantity: validateQuantity(form.stock_quantity),
      category_id: validateRequired(form.category_id, 'Category'),
      supplier_id: validateRequired(form.supplier_id, 'Supplier'),
    };
    setFormErrors(nextErrors);
    return !Object.values(nextErrors).some(Boolean);
  }

  function resetForm() {
    setForm(emptyForm);
    setEditingProductId(null);
    setFormErrors(createEmptyErrors());
    setSelectedFile(null);
    setImagePreview(null);
  }

  function handleFileChange(event) {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!validateForm()) return;

    try {
      setSubmitting(true);
      const payload = {
        name: form.name,
        sku: form.sku,
        description: form.description || null,
        price: Number(form.price),
        stock_quantity: Number(form.stock_quantity),
        category_id: Number(form.category_id),
        supplier_id: Number(form.supplier_id),
        is_active: form.is_active === 'true',
        available_sizes: form.available_sizes || null,
      };

      let savedProductId = editingProductId;

      if (editingProductId) {
        await updateProductRequest(editingProductId, payload);
      } else {
        const created = await createProductRequest(payload);
        savedProductId = created.id;
      }

      // Upload image if a file was selected
      if (selectedFile && savedProductId) {
        await uploadProductImageRequest(savedProductId, selectedFile);
      }

      resetForm();
      await loadData();
    } catch (submitError) {
      setError(submitError?.response?.data?.detail || 'Unable to save product.');
    } finally {
      setSubmitting(false);
    }
  }

  function handleEdit(product) {
    setEditingProductId(product.id);
    setForm({
      name: product.name,
      sku: product.sku,
      description: product.description || '',
      price: product.price,
      stock_quantity: product.stock_quantity,
      category_id: product.category_id,
      supplier_id: product.supplier_id,
      is_active: String(product.is_active),
      available_sizes: product.available_sizes || '',
    });
  }

  async function handleDelete(productId) {
    try {
      await deleteProductRequest(productId);
      await loadData();
    } catch (deleteError) {
      setError(deleteError?.response?.data?.detail || 'Unable to delete product.');
    }
  }

  if (loading) return <Loader label="Loading products" />;
  if (error && !products.length) return <ErrorState message={error} onRetry={loadData} />;

  return (
    <div className="page-stack">
      <PageHeader
        title="Manage products"
        subtitle="Create, update, and remove products from the catalog."
      />
      {error ? <ErrorState title="Product management issue" message={error} onRetry={loadData} /> : null}

      <section className="card admin-form">
        <h3>{editingProductId ? 'Edit product' : 'Create product'}</h3>
        <form className="form-grid" onSubmit={handleSubmit}>
          <FormField label="Name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} error={formErrors.name} />
          <FormField label="SKU" value={form.sku} onChange={(event) => setForm({ ...form, sku: event.target.value })} error={formErrors.sku} />
          <FormField label="Price" type="number" step="0.01" value={form.price} onChange={(event) => setForm({ ...form, price: event.target.value })} error={formErrors.price} />
          <FormField label="Stock quantity" type="number" value={form.stock_quantity} onChange={(event) => setForm({ ...form, stock_quantity: event.target.value })} error={formErrors.stock_quantity} />
          <FormField as="select" label="Category" value={form.category_id} onChange={(event) => setForm({ ...form, category_id: event.target.value })} error={formErrors.category_id}>
            <option value="">Select category</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>{category.name}</option>
            ))}
          </FormField>
          <FormField as="select" label="Supplier" value={form.supplier_id} onChange={(event) => setForm({ ...form, supplier_id: event.target.value })} error={formErrors.supplier_id}>
            <option value="">Select supplier</option>
            {suppliers.map((supplier) => (
              <option key={supplier.id} value={supplier.id}>{supplier.name}</option>
            ))}
          </FormField>
          <FormField as="select" label="Status" value={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.value })}>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </FormField>
          <FormField
            className="form-grid__full"
            label="Available Sizes (comma-separated, e.g. XS,S,M,L,XL)"
            value={form.available_sizes}
            onChange={(event) => setForm({ ...form, available_sizes: event.target.value })}
            placeholder="XS,S,M,L,XL,XXL"
          />
          <FormField
            className="form-grid__full"
            as="textarea"
            rows="4"
            label="Description"
            value={form.description}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
          />
          <div className="form-grid__full" style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>Product Image</label>
            <input
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              onChange={handleFileChange}
              style={{ display: 'block' }}
            />
            {imagePreview && (
              <img
                src={imagePreview}
                alt="Preview"
                style={{ marginTop: '0.75rem', maxWidth: '200px', maxHeight: '200px', borderRadius: '8px', objectFit: 'cover', border: '1px solid #e5e7eb' }}
              />
            )}
          </div>
          <div className="form-grid__full">
            <Button type="submit" loading={submitting}>{editingProductId ? 'Update product' : 'Create product'}</Button>
            {editingProductId ? (
              <Button type="button" variant="secondary" onClick={resetForm}>
                Cancel edit
              </Button>
            ) : null}
          </div>
        </form>
      </section>

      <section className="card admin-table">
        <h3>Existing products</h3>
        {products.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Image</th>
                  <th>Name</th>
                  <th>Price</th>
                  <th>Stock</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id}>
                    <td>
                      {resolveProductImage(product) ? (
                        <img
                          src={resolveProductImage(product)}
                          alt={product.name}
                          onError={(event) => { event.currentTarget.style.display = 'none'; }}
                          style={{ width: '50px', height: '50px', objectFit: 'cover', borderRadius: '6px' }}
                        />
                      ) : (
                        <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>No image</span>
                      )}
                    </td>
                    <td>
                      <strong>{product.name}</strong>
                      <p className="muted">{product.sku}</p>
                    </td>
                    <td>{formatCurrency(product.price)}</td>
                    <td>{product.stock_quantity}</td>
                    <td><StatusBadge value={product.is_active ? 'active' : 'inactive'} /></td>
                    <td>
                      <Button variant="secondary" onClick={() => handleEdit(product)}>Edit</Button>
                      <Button variant="danger" onClick={() => handleDelete(product.id)}>Delete</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="No products available" message="Add the first catalog item using the form above." />
        )}
      </section>
    </div>
  );
}
