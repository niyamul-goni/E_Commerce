import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import FormField from '../../components/FormField';
import Loader from '../../components/Loader';
import {
  getManagedCategoriesRequest,
  createCategoryRequest,
  updateCategoryRequest,
  deleteCategoryRequest,
  getManagedSubcategoriesRequest,
  createSubcategoryRequest,
  updateSubcategoryRequest,
  deleteSubcategoryRequest,
} from '../../services/catalogService';

const EMPTY_CATEGORY = { name:'', description:'', is_active:'true' };
const EMPTY_SUBCATEGORY = {
  name:'', category_id:'', description:'', is_active:'true', sort_order:'0',
};

export default function ManagerCategoriesPage() {
  const [loading, setLoading]   = useState(true);
  const [error,   setError]     = useState('');
  const [cats,    setCats]      = useState([]);
  const [subs,    setSubs]      = useState([]);
  const [catForm, setCatForm]   = useState(EMPTY_CATEGORY);
  const [editCat, setEditCat]   = useState(null);
  const [saving,  setSaving]    = useState(false);
  const [subForm, setSubForm]   = useState(EMPTY_SUBCATEGORY);
  const [editSub, setEditSub]   = useState(null);
  const [savingSub, setSavingSub] = useState(false);
  const [notice, setNotice]     = useState('');

  async function load() {
    try {
      setError('');
      const [c, s] = await Promise.all([
        getManagedCategoriesRequest(),
        getManagedSubcategoriesRequest(),
      ]);
      setCats(c); setSubs(s);
    } catch (e) { setError(e?.response?.data?.detail || 'Failed to load categories.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function handleSaveCat(e) {
    e.preventDefault();
    if (!catForm.name.trim()) {
      setError('Category name is required.');
      return;
    }
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const payload = {
        name: catForm.name.trim(),
        description: catForm.description.trim() || null,
        is_active: catForm.is_active === 'true',
      };
      editCat ? await updateCategoryRequest(editCat, payload) : await createCategoryRequest(payload);
      setNotice(editCat ? 'Category updated successfully.' : 'Category created successfully.');
      setCatForm(EMPTY_CATEGORY); setEditCat(null); await load();
    } catch (e) { setError(e?.response?.data?.detail || 'Save failed.'); }
    finally { setSaving(false); }
  }

  async function handleDeleteCat(id) {
    if (!window.confirm('Deactivate this category? Existing products will be preserved.')) return;
    setError('');
    setNotice('');
    try {
      await deleteCategoryRequest(id);
      setNotice('Category deactivated successfully.');
      await load();
    }
    catch (e) { setError(e?.response?.data?.detail || 'Delete failed.'); }
  }

  async function handleSaveSub(e) {
    e.preventDefault();
    if (!subForm.name.trim() || !subForm.category_id) {
      setError('Subcategory name and parent category are required.');
      return;
    }
    setSavingSub(true);
    setError('');
    setNotice('');
    try {
      const payload = {
        name: subForm.name.trim(),
        category_id: Number(subForm.category_id),
        description: subForm.description.trim() || null,
        is_active: subForm.is_active === 'true',
        sort_order: Number(subForm.sort_order) || 0,
      };
      editSub
        ? await updateSubcategoryRequest(editSub, payload)
        : await createSubcategoryRequest(payload);
      setNotice(editSub ? 'Subcategory updated successfully.' : 'Subcategory created successfully.');
      setSubForm(EMPTY_SUBCATEGORY);
      setEditSub(null);
      await load();
    } catch (e) {
      setError(e?.response?.data?.detail || 'Subcategory save failed.');
    } finally {
      setSavingSub(false);
    }
  }

  async function handleDeleteSub(id) {
    if (!window.confirm('Deactivate this subcategory? Existing products will be preserved.')) return;
    setError('');
    setNotice('');
    try {
      await deleteSubcategoryRequest(id);
      setNotice('Subcategory deactivated successfully.');
      await load();
    } catch (e) {
      setError(e?.response?.data?.detail || 'Subcategory deactivation failed.');
    }
  }

  if (loading) return <Loader label="Loading categories" />;

  return (
    <div className="mgr-page">
      <div className="mgr-page__header">
        <h1 className="mgr-page__title">Categories & Subcategories</h1>
      </div>
      {error && <ErrorState message={error} />}
      {notice && <p className="inline-message inline-message--success" role="status">{notice}</p>}

      <div className="mgr-two-col">
        {/* Category CRUD */}
        <div>
          <div className="card mgr-form-card">
            <h2 className="mgr-form-card__title">{editCat ? 'Edit Category' : 'New Category'}</h2>
            <form onSubmit={handleSaveCat} style={{ display:'grid', gap:'0.75rem' }}>
              <FormField label="Name" value={catForm.name} onChange={(e) => setCatForm({...catForm,name:e.target.value})} placeholder="e.g. Tops" />
              <FormField label="Description" as="textarea" rows="2" value={catForm.description} onChange={(e) => setCatForm({...catForm,description:e.target.value})} />
              <FormField as="select" label="Status" value={catForm.is_active} onChange={(e) => setCatForm({...catForm,is_active:e.target.value})}>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </FormField>
              <div style={{display:'flex',gap:'0.5rem'}}>
                <Button type="submit" loading={saving}>{editCat?'Update':'Create'}</Button>
                {editCat&&<button type="button" className="button button--secondary" onClick={()=>{setEditCat(null);setCatForm(EMPTY_CATEGORY)}}>Cancel</button>}
              </div>
            </form>
          </div>

          <div className="card mgr-table-card" style={{ marginTop:'1rem' }}>
            <h2 className="mgr-form-card__title">Categories ({cats.length})</h2>
            <div className="mgr-table-wrap">
              <table className="mgr-table">
                <thead><tr><th>Name</th><th>Status</th><th>Subcategories</th><th>Actions</th></tr></thead>
                <tbody>
                  {cats.map((c) => (
                    <tr key={c.id}>
                      <td><strong>{c.name}</strong></td>
                      <td>{c.is_active ? 'Active' : 'Inactive'}</td>
                      <td className="muted">{subs.filter((s)=>s.category_id===c.id).length}</td>
                      <td>
                        <div style={{display:'flex',gap:'0.4rem'}}>
                          <button className="mgr-btn" onClick={()=>{setEditCat(c.id);setCatForm({name:c.name,description:c.description||'',is_active:String(c.is_active)})}}>✏️</button>
                          <button className="mgr-btn mgr-btn--danger" onClick={()=>handleDeleteCat(c.id)}>🗑️</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Subcategory CRUD */}
        <div>
          <div className="card mgr-form-card">
            <h2 className="mgr-form-card__title">{editSub ? 'Edit Subcategory' : 'New Subcategory'}</h2>
            <form onSubmit={handleSaveSub} style={{ display:'grid', gap:'0.75rem' }}>
              <FormField label="Name" value={subForm.name} onChange={(e) => setSubForm({...subForm,name:e.target.value})} placeholder="e.g. Graphic Tees" />
              <FormField as="select" label="Parent Category" value={subForm.category_id} onChange={(e) => setSubForm({...subForm,category_id:e.target.value})}>
                <option value="">— Select —</option>
                {cats.filter((category) => category.is_active).map((category) => (
                  <option key={category.id} value={category.id}>{category.name}</option>
                ))}
              </FormField>
              <FormField label="Description" as="textarea" rows="2" value={subForm.description} onChange={(e) => setSubForm({...subForm,description:e.target.value})} />
              <FormField label="Display Order" type="number" min="0" step="1" value={subForm.sort_order} onChange={(e) => setSubForm({...subForm,sort_order:e.target.value})} />
              <FormField as="select" label="Status" value={subForm.is_active} onChange={(e) => setSubForm({...subForm,is_active:e.target.value})}>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </FormField>
              <div style={{display:'flex',gap:'0.5rem'}}>
                <Button type="submit" loading={savingSub}>{editSub ? 'Update' : 'Create'}</Button>
                {editSub && (
                  <button type="button" className="button button--secondary" onClick={() => { setEditSub(null); setSubForm(EMPTY_SUBCATEGORY); }}>
                    Cancel
                  </button>
                )}
              </div>
            </form>
          </div>

          <div className="card mgr-table-card" style={{ marginTop:'1rem' }}>
            <h2 className="mgr-form-card__title">Subcategories ({subs.length})</h2>
            <div className="mgr-table-wrap">
              <table className="mgr-table">
                <thead><tr><th>Name</th><th>Parent</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                  {subs.map((s) => {
                    const parent = cats.find((c) => c.id === s.category_id);
                    return (
                      <tr key={s.id}>
                        <td><strong>{s.name}</strong></td>
                        <td className="muted">{parent?.name || '—'}</td>
                        <td>{s.is_active ? 'Active' : 'Inactive'}</td>
                        <td>
                          <div style={{display:'flex',gap:'0.4rem'}}>
                            <button
                              type="button"
                              className="mgr-btn"
                              aria-label={`Edit ${s.name}`}
                              onClick={() => {
                                setEditSub(s.id);
                                setSubForm({
                                  name:s.name,
                                  category_id:String(s.category_id),
                                  description:s.description || '',
                                  is_active:String(s.is_active),
                                  sort_order:String(s.sort_order || 0),
                                });
                              }}
                            >
                              ✏️
                            </button>
                            <button
                              type="button"
                              className="mgr-btn mgr-btn--danger"
                              aria-label={`Deactivate ${s.name}`}
                              onClick={() => handleDeleteSub(s.id)}
                            >
                              🗑️
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
