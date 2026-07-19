import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import FormField from '../../components/FormField';
import Loader from '../../components/Loader';
import {
  getCategoriesRequest,
  createCategoryRequest,
  updateCategoryRequest,
  deleteCategoryRequest,
  getSubcategoriesRequest,
} from '../../services/catalogService';

export default function ManagerCategoriesPage() {
  const [loading, setLoading]   = useState(true);
  const [error,   setError]     = useState('');
  const [cats,    setCats]      = useState([]);
  const [subs,    setSubs]      = useState([]);
  const [catForm, setCatForm]   = useState({ name:'', description:'' });
  const [editCat, setEditCat]   = useState(null);
  const [saving,  setSaving]    = useState(false);

  async function load() {
    try {
      const [c, s] = await Promise.all([getCategoriesRequest(), getSubcategoriesRequest()]);
      setCats(c); setSubs(s);
    } catch (e) { setError(e?.response?.data?.detail || 'Failed to load categories.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function handleSaveCat(e) {
    e.preventDefault();
    if (!catForm.name.trim()) return;
    setSaving(true);
    try {
      editCat ? await updateCategoryRequest(editCat, catForm) : await createCategoryRequest(catForm);
      setCatForm({ name:'', description:'' }); setEditCat(null); await load();
    } catch (e) { setError(e?.response?.data?.detail || 'Save failed.'); }
    finally { setSaving(false); }
  }

  async function handleDeleteCat(id) {
    if (!window.confirm('Delete this category?')) return;
    try { await deleteCategoryRequest(id); await load(); }
    catch (e) { setError(e?.response?.data?.detail || 'Delete failed.'); }
  }

  if (loading) return <Loader label="Loading categories" />;

  return (
    <div className="mgr-page">
      <div className="mgr-page__header">
        <h1 className="mgr-page__title">Categories & Subcategories</h1>
      </div>
      {error && <ErrorState message={error} />}

      <div className="mgr-two-col">
        {/* Category CRUD */}
        <div>
          <div className="card mgr-form-card">
            <h2 className="mgr-form-card__title">{editCat ? 'Edit Category' : 'New Category'}</h2>
            <form onSubmit={handleSaveCat} style={{ display:'grid', gap:'0.75rem' }}>
              <FormField label="Name" value={catForm.name} onChange={(e) => setCatForm({...catForm,name:e.target.value})} placeholder="e.g. Tops" />
              <FormField label="Description" as="textarea" rows="2" value={catForm.description} onChange={(e) => setCatForm({...catForm,description:e.target.value})} />
              <div style={{display:'flex',gap:'0.5rem'}}>
                <Button type="submit" loading={saving}>{editCat?'Update':'Create'}</Button>
                {editCat&&<button type="button" className="button button--secondary" onClick={()=>{setEditCat(null);setCatForm({name:'',description:''})}}>Cancel</button>}
              </div>
            </form>
          </div>

          <div className="card mgr-table-card" style={{ marginTop:'1rem' }}>
            <h2 className="mgr-form-card__title">Categories ({cats.length})</h2>
            <div className="mgr-table-wrap">
              <table className="mgr-table">
                <thead><tr><th>Name</th><th>Subcategories</th><th>Actions</th></tr></thead>
                <tbody>
                  {cats.map((c) => (
                    <tr key={c.id}>
                      <td><strong>{c.name}</strong></td>
                      <td className="muted">{subs.filter((s)=>s.category_id===c.id).length}</td>
                      <td>
                        <div style={{display:'flex',gap:'0.4rem'}}>
                          <button className="mgr-btn" onClick={()=>{setEditCat(c.id);setCatForm({name:c.name,description:c.description||''})}}>✏️</button>
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

        {/* Subcategories list */}
        <div className="card mgr-table-card">
          <h2 className="mgr-form-card__title">Subcategories ({subs.length})</h2>
          <div className="mgr-table-wrap">
            <table className="mgr-table">
              <thead><tr><th>Name</th><th>Parent Category</th></tr></thead>
              <tbody>
                {subs.map((s) => {
                  const parent = cats.find((c) => c.id === s.category_id);
                  return (
                    <tr key={s.id}>
                      <td>{s.name}</td>
                      <td className="muted">{parent?.name || '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
