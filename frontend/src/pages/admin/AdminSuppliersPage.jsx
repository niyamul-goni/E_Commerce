import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import FormField from '../../components/FormField';
import Loader from '../../components/Loader';
import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import {
  createSupplierRequest,
  deleteSupplierRequest,
  getSuppliersRequest,
  updateSupplierRequest,
} from '../../services/catalogService';
import { createEmptyErrors, validateEmail, validateRequired } from '../../utils/validators';

const emptyForm = {
  name: '',
  contact_email: '',
  contact_phone: '',
  address: '',
  is_active: 'true',
};

export default function AdminSuppliersPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [suppliers, setSuppliers] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [formErrors, setFormErrors] = useState(createEmptyErrors());
  const [editingSupplierId, setEditingSupplierId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function loadData() {
    try {
      setLoading(true);
      setError('');
      const data = await getSuppliersRequest();
      setSuppliers(data);
    } catch (loadError) {
      setError(loadError?.response?.data?.detail || 'Failed to load suppliers.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function validateForm() {
    const nextErrors = {
      name: validateRequired(form.name, 'Supplier name'),
      contact_email: form.contact_email ? validateEmail(form.contact_email) : '',
      address: validateRequired(form.address, 'Address'),
    };
    setFormErrors(nextErrors);
    return !Object.values(nextErrors).some(Boolean);
  }

  function resetForm() {
    setForm(emptyForm);
    setEditingSupplierId(null);
    setFormErrors(createEmptyErrors());
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!validateForm()) return;

    try {
      setSubmitting(true);
      const payload = {
        name: form.name,
        contact_email: form.contact_email || null,
        contact_phone: form.contact_phone || null,
        address: form.address || null,
        is_active: form.is_active === 'true',
      };

      if (editingSupplierId) {
        await updateSupplierRequest(editingSupplierId, payload);
      } else {
        await createSupplierRequest(payload);
      }

      resetForm();
      await loadData();
    } catch (submitError) {
      setError(submitError?.response?.data?.detail || 'Unable to save supplier.');
    } finally {
      setSubmitting(false);
    }
  }

  function handleEdit(supplier) {
    setEditingSupplierId(supplier.id);
    setForm({
      name: supplier.name,
      contact_email: supplier.contact_email || '',
      contact_phone: supplier.contact_phone || '',
      address: supplier.address || '',
      is_active: String(supplier.is_active),
    });
  }

  async function handleDelete(supplierId) {
    try {
      await deleteSupplierRequest(supplierId);
      await loadData();
    } catch (deleteError) {
      setError(deleteError?.response?.data?.detail || 'Unable to delete supplier.');
    }
  }

  if (loading) return <Loader label="Loading suppliers" />;
  if (error && !suppliers.length) return <ErrorState message={error} onRetry={loadData} />;

  return (
    <div className="page-stack">
      <PageHeader title="Manage suppliers" subtitle="Maintain the vendor master data used by the catalog." />
      {error ? <ErrorState title="Supplier management issue" message={error} onRetry={loadData} /> : null}

      <section className="card admin-form">
        <h3>{editingSupplierId ? 'Edit supplier' : 'Create supplier'}</h3>
        <form className="form-grid" onSubmit={handleSubmit}>
          <FormField label="Name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} error={formErrors.name} />
          <FormField label="Contact email" type="email" value={form.contact_email} onChange={(event) => setForm({ ...form, contact_email: event.target.value })} error={formErrors.contact_email} />
          <FormField label="Contact phone" value={form.contact_phone} onChange={(event) => setForm({ ...form, contact_phone: event.target.value })} />
          <FormField as="select" label="Status" value={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.value })}>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </FormField>
          <FormField
            className="form-grid__full"
            as="textarea"
            rows="4"
            label="Address"
            value={form.address}
            onChange={(event) => setForm({ ...form, address: event.target.value })}
            error={formErrors.address}
          />
          <div className="form-grid__full">
            <Button type="submit" loading={submitting}>{editingSupplierId ? 'Update supplier' : 'Create supplier'}</Button>
            {editingSupplierId ? <Button type="button" variant="secondary" onClick={resetForm}>Cancel edit</Button> : null}
          </div>
        </form>
      </section>

      <section className="card admin-table">
        <h3>Existing suppliers</h3>
        {suppliers.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Contact</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map((supplier) => (
                  <tr key={supplier.id}>
                    <td>
                      <strong>{supplier.name}</strong>
                      <p className="muted">{supplier.address}</p>
                    </td>
                    <td>
                      <p>{supplier.contact_email || 'No email'}</p>
                      <p className="muted">{supplier.contact_phone || 'No phone'}</p>
                    </td>
                    <td><StatusBadge value={supplier.is_active ? 'active' : 'inactive'} /></td>
                    <td>
                      <Button variant="secondary" onClick={() => handleEdit(supplier)}>Edit</Button>
                      <Button variant="danger" onClick={() => handleDelete(supplier.id)}>Delete</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="No suppliers available" message="Add the first supplier using the form above." />
        )}
      </section>
    </div>
  );
}
