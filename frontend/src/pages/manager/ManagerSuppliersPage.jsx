import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import FormField from '../../components/FormField';
import Loader from '../../components/Loader';
import {
  getSuppliersRequest,
  createSupplierRequest,
  updateSupplierRequest,
  deleteSupplierRequest,
} from '../../services/catalogService';

const EMPTY = { name:'', contact_person:'', email:'', phone:'', address:'', country:'Bangladesh' };

export default function ManagerSuppliersPage() {
  const [loading, setLoading]   = useState(true);
  const [error,   setError]     = useState('');
  const [suppliers, setSuppliers] = useState([]);
  const [form, setForm]         = useState(EMPTY);
  const [editId, setEditId]     = useState(null);
  const [saving, setSaving]     = useState(false);

  async function load() {
    try { setSuppliers(await getSuppliersRequest()); }
    catch (e) { setError(e?.response?.data?.detail || 'Failed to load suppliers.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  function startEdit(s) {
    setEditId(s.id);
    setForm({ name:s.name, contact_person:s.contact_person||'', email:s.email||'', phone:s.phone||'', address:s.address||'', country:s.country||'Bangladesh' });
  }
  function cancel() { setEditId(null); setForm(EMPTY); }

  async function handleSave(e) {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      editId ? await updateSupplierRequest(editId, form) : await createSupplierRequest(form);
      cancel(); await load();
    } catch (e) { setError(e?.response?.data?.detail || 'Save failed.'); }
    finally { setSaving(false); }
  }

  async function handleDelete(id) {
    if (!window.confirm('Delete this supplier?')) return;
    try { await deleteSupplierRequest(id); await load(); }
    catch (e) { setError(e?.response?.data?.detail || 'Delete failed.'); }
  }

  if (loading) return <Loader label="Loading suppliers" />;

  return (
    <div className="mgr-page">
      <div className="mgr-page__header">
        <h1 className="mgr-page__title">Suppliers</h1>
        <p className="mgr-page__sub">{suppliers.length} suppliers</p>
      </div>
      {error && <ErrorState message={error} />}

      <div className="mgr-two-col">
        <div className="card mgr-form-card">
          <h2 className="mgr-form-card__title">{editId ? 'Edit Supplier' : 'New Supplier'}</h2>
          <form onSubmit={handleSave} style={{ display:'grid', gap:'0.75rem' }}>
            <FormField label="Company Name" value={form.name} onChange={(e)=>setForm({...form,name:e.target.value})} />
            <FormField label="Contact Person" value={form.contact_person} onChange={(e)=>setForm({...form,contact_person:e.target.value})} />
            <FormField label="Email" type="email" value={form.email} onChange={(e)=>setForm({...form,email:e.target.value})} />
            <FormField label="Phone" value={form.phone} onChange={(e)=>setForm({...form,phone:e.target.value})} />
            <FormField label="Country" value={form.country} onChange={(e)=>setForm({...form,country:e.target.value})} />
            <FormField label="Address" as="textarea" rows="2" value={form.address} onChange={(e)=>setForm({...form,address:e.target.value})} />
            <div style={{display:'flex',gap:'0.5rem'}}>
              <Button type="submit" loading={saving}>{editId?'Update':'Create'}</Button>
              {editId&&<button type="button" className="button button--secondary" onClick={cancel}>Cancel</button>}
            </div>
          </form>
        </div>

        <div className="card mgr-table-card">
          <div className="mgr-table-wrap">
            <table className="mgr-table">
              <thead><tr><th>Company</th><th>Contact</th><th>Email</th><th>Country</th><th>Actions</th></tr></thead>
              <tbody>
                {suppliers.map((s)=>(
                  <tr key={s.id}>
                    <td><strong>{s.name}</strong></td>
                    <td className="muted">{s.contact_person||'—'}</td>
                    <td className="muted">{s.email||'—'}</td>
                    <td className="muted">{s.country||'—'}</td>
                    <td>
                      <div style={{display:'flex',gap:'0.4rem'}}>
                        <button className="mgr-btn" onClick={()=>startEdit(s)}>✏️</button>
                        <button className="mgr-btn mgr-btn--danger" onClick={()=>handleDelete(s.id)}>🗑️</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
