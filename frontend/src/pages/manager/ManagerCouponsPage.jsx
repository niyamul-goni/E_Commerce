import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import { api } from '../../services/api';
import { formatDate } from '../../utils/format';

const EMPTY_COUPON = { code:'', coupon_type:'percentage', value:'', min_order_amount:'', max_discount_amount:'', max_uses:'', valid_until:'', description:'' };

export default function ManagerCouponsPage() {
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const [coupons, setCoupons] = useState([]);
  const [form,    setForm]    = useState(EMPTY_COUPON);
  const [saving,  setSaving]  = useState(false);
  const [showForm, setShowForm] = useState(false);

  async function load() {
    try {
      const { data } = await api.get('/coupons/list').catch(() => ({ data: [] }));
      setCoupons(data || []);
    } catch { setCoupons([]); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function handleCreate(e) {
    e.preventDefault();
    if (!form.code || !form.value) return;
    setSaving(true);
    try {
      await api.post('/coupons', {
        ...form,
        code:  form.code.toUpperCase(),
        value: Number(form.value),
        min_order_amount:    form.min_order_amount    ? Number(form.min_order_amount)    : null,
        max_discount_amount: form.max_discount_amount ? Number(form.max_discount_amount) : null,
        max_uses:            form.max_uses            ? Number(form.max_uses)            : null,
        valid_until:         form.valid_until         || null,
        is_active:           true,
      });
      setForm(EMPTY_COUPON); setShowForm(false); await load();
    } catch (e) { setError(e?.response?.data?.detail || 'Failed to create coupon.'); }
    finally { setSaving(false); }
  }

  async function toggleActive(coupon) {
    try {
      await api.put(`/coupons/${coupon.id}`, { is_active: !coupon.is_active });
      await load();
    } catch (e) { setError(e?.response?.data?.detail || 'Update failed.'); }
  }

  if (loading) return <Loader label="Loading coupons" />;

  return (
    <div className="mgr-page">
      <div className="mgr-page__header">
        <div>
          <h1 className="mgr-page__title">Coupons</h1>
          <p className="mgr-page__sub">{coupons.length} codes · {coupons.filter(c=>c.is_active).length} active</p>
        </div>
        <button className="button" onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Close' : '+ New Coupon'}
        </button>
      </div>
      {error && <ErrorState message={error} />}

      {showForm && (
        <div className="card mgr-form-card">
          <h2 className="mgr-form-card__title">Create Coupon</h2>
          <form className="form-grid" onSubmit={handleCreate}>
            <div className="field">
              <label className="field__label">Code</label>
              <input className="field__control" value={form.code} onChange={(e) => setForm({...form,code:e.target.value.toUpperCase()})} placeholder="SAVE20" style={{textTransform:'uppercase',fontFamily:'monospace,monospace'}} />
            </div>
            <div className="field">
              <label className="field__label">Type</label>
              <select className="field__control" value={form.coupon_type} onChange={(e) => setForm({...form,coupon_type:e.target.value})}>
                <option value="percentage">Percentage (%)</option>
                <option value="fixed">Fixed Amount</option>
              </select>
            </div>
            <div className="field">
              <label className="field__label">Value ({form.coupon_type==='percentage'?'%':'BDT'})</label>
              <input className="field__control" type="number" step="0.01" value={form.value} onChange={(e) => setForm({...form,value:e.target.value})} placeholder="20" />
            </div>
            <div className="field">
              <label className="field__label">Min Order (BDT)</label>
              <input className="field__control" type="number" value={form.min_order_amount} onChange={(e) => setForm({...form,min_order_amount:e.target.value})} placeholder="Optional" />
            </div>
            <div className="field">
              <label className="field__label">Max Discount (BDT)</label>
              <input className="field__control" type="number" value={form.max_discount_amount} onChange={(e) => setForm({...form,max_discount_amount:e.target.value})} placeholder="Optional" />
            </div>
            <div className="field">
              <label className="field__label">Max Uses</label>
              <input className="field__control" type="number" value={form.max_uses} onChange={(e) => setForm({...form,max_uses:e.target.value})} placeholder="Unlimited" />
            </div>
            <div className="field">
              <label className="field__label">Valid Until</label>
              <input className="field__control" type="datetime-local" value={form.valid_until} onChange={(e) => setForm({...form,valid_until:e.target.value})} />
            </div>
            <div className="field">
              <label className="field__label">Description</label>
              <input className="field__control" value={form.description} onChange={(e) => setForm({...form,description:e.target.value})} placeholder="Shown to customer on apply" />
            </div>
            <div className="form-grid__full" style={{display:'flex',gap:'0.75rem'}}>
              <Button type="submit" loading={saving}>Create Coupon</Button>
              <button type="button" className="button button--secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card mgr-table-card">
        {coupons.length === 0 ? (
          <p className="muted" style={{padding:'1.5rem'}}>No coupons yet. Create one above.</p>
        ) : (
          <div className="mgr-table-wrap">
            <table className="mgr-table">
              <thead><tr><th>Code</th><th>Type</th><th>Value</th><th>Min Order</th><th>Uses</th><th>Expires</th><th>Status</th><th>Toggle</th></tr></thead>
              <tbody>
                {coupons.map((c) => (
                  <tr key={c.id}>
                    <td><code className="mono">{c.code}</code></td>
                    <td className="muted">{c.coupon_type}</td>
                    <td>{c.coupon_type==='percentage'?`${c.value}%`:`৳${c.value}`}</td>
                    <td className="muted">{c.min_order_amount?`৳${c.min_order_amount}`:'—'}</td>
                    <td className="muted">{c.used_count}/{c.max_uses||'∞'}</td>
                    <td className="muted">{c.valid_until?formatDate(c.valid_until):'—'}</td>
                    <td>
                      <span className={`role-tag${c.is_active?' role-tag--active':''}`}>
                        {c.is_active?'Active':'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button className="mgr-btn" onClick={() => toggleActive(c)}>
                        {c.is_active?'Deactivate':'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
