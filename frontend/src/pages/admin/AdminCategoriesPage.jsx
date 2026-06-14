import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import EmptyState from '../../components/EmptyState';
import ErrorState from '../../components/ErrorState';
import FormField from '../../components/FormField';
import Loader from '../../components/Loader';
import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import {
  createCategoryRequest,
  deleteCategoryRequest,
  getCategoriesRequest,
  updateCategoryRequest,
} from '../../services/catalogService';
import { createEmptyErrors, validateRequired } from '../../utils/validators';

const emptyForm = {
  name: '',
  description: '',
  is_active: 'true',
};

export default function AdminCategoriesPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [formErrors, setFormErrors] = useState(createEmptyErrors());
  const [editingCategoryId, setEditingCategoryId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function loadData() {
    try {
      setLoading(true);
      setError('');
      const data = await getCategoriesRequest();
      setCategories(data);
    } catch (loadError) {
      setError(loadError?.response?.data?.detail || 'Failed to load categories.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  function validateForm() {
    const nextErrors = {
      name: validateRequired(form.name, 'Category name'),
    };
    setFormErrors(nextErrors);
    return !Object.values(nextErrors).some(Boolean);
  }

  function resetForm() {
    setForm(emptyForm);
    setEditingCategoryId(null);
    setFormErrors(createEmptyErrors());
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!validateForm()) return;

    try {
      setSubmitting(true);
      const payload = {
        name: form.name,
        description: form.description || null,
        is_active: form.is_active === 'true',
      };

      if (editingCategoryId) {
        await updateCategoryRequest(editingCategoryId, payload);
      } else {
        await createCategoryRequest(payload);
      }

      resetForm();
      await loadData();
    } catch (submitError) {
      setError(submitError?.response?.data?.detail || 'Unable to save category.');
    } finally {
      setSubmitting(false);
    }
  }

  function handleEdit(category) {
    setEditingCategoryId(category.id);
    setForm({
      name: category.name,
      description: category.description || '',
      is_active: String(category.is_active),
    });
  }

  async function handleDelete(categoryId) {
    try {
      await deleteCategoryRequest(categoryId);
      await loadData();
    } catch (deleteError) {
      setError(deleteError?.response?.data?.detail || 'Unable to delete category.');
    }
  }

  if (loading) return <Loader label="Loading categories" />;
  if (error && !categories.length) return <ErrorState message={error} onRetry={loadData} />;

  return (
    <div className="page-stack">
      <PageHeader title="Manage categories" subtitle="Keep the product taxonomy normalized and curated." />
      {error ? <ErrorState title="Category management issue" message={error} onRetry={loadData} /> : null}

      <section className="card admin-form">
        <h3>{editingCategoryId ? 'Edit category' : 'Create category'}</h3>
        <form className="form-grid" onSubmit={handleSubmit}>
          <FormField label="Name" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} error={formErrors.name} />
          <FormField as="select" label="Status" value={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.value })}>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </FormField>
          <FormField
            className="form-grid__full"
            as="textarea"
            rows="4"
            label="Description"
            value={form.description}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
          />
          <div className="form-grid__full">
            <Button type="submit" loading={submitting}>{editingCategoryId ? 'Update category' : 'Create category'}</Button>
            {editingCategoryId ? <Button type="button" variant="secondary" onClick={resetForm}>Cancel edit</Button> : null}
          </div>
        </form>
      </section>

      <section className="card admin-table">
        <h3>Existing categories</h3>
        {categories.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {categories.map((category) => (
                  <tr key={category.id}>
                    <td>
                      <strong>{category.name}</strong>
                      <p className="muted">{category.description}</p>
                    </td>
                    <td><StatusBadge value={category.is_active ? 'active' : 'inactive'} /></td>
                    <td>
                      <Button variant="secondary" onClick={() => handleEdit(category)}>Edit</Button>
                      <Button variant="danger" onClick={() => handleDelete(category.id)}>Delete</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="No categories available" message="Add the first category using the form above." />
        )}
      </section>
    </div>
  );
}
