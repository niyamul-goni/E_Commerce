import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import StatusBadge from '../../components/StatusBadge';
import { getAllOrdersRequest, updateOrderStatusRequest, createShipmentRequest } from '../../services/commerceService';
import { formatCurrency, formatDate } from '../../utils/format';

const STATUS_OPTIONS = ['pending','paid','processing','shipped','delivered','cancelled'];

export default function ManagerOrdersPage() {
  const [loading, setLoading]   = useState(true);
  const [error,   setError]     = useState('');
  const [orders,  setOrders]    = useState([]);
  const [drafts,  setDrafts]    = useState({});
  const [expanded, setExpanded] = useState(null);
  const [filter,  setFilter]    = useState('all');
  const [search,  setSearch]    = useState('');
  const [shipForm, setShipForm] = useState({ tracking_number:'', carrier:'', status:'shipped' });
  const [shipping, setShipping] = useState(null); // order being shipped

  async function load() {
    try { setLoading(true); const d = await getAllOrdersRequest(); setOrders(d); setDrafts(Object.fromEntries(d.map((o)=>[o.id,o.status]))); }
    catch (e) { setError(e?.response?.data?.detail || 'Failed to load orders.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function handleStatusUpdate(orderId) {
    try { await updateOrderStatusRequest(orderId, drafts[orderId]); await load(); }
    catch (e) { setError(e?.response?.data?.detail || 'Status update failed.'); }
  }

  async function handleShip(orderId) {
    try {
      await createShipmentRequest({ order_id: orderId, ...shipForm });
      await updateOrderStatusRequest(orderId, 'shipped');
      setShipping(null); setShipForm({ tracking_number:'', carrier:'', status:'shipped' });
      await load();
    } catch (e) { setError(e?.response?.data?.detail || 'Failed to create shipment.'); }
  }

  const filtered = orders.filter((o) => {
    if (filter !== 'all' && o.status !== filter) return false;
    if (search && !((o.order_number||'').includes(search) || String(o.customer_id).includes(search))) return false;
    return true;
  });

  if (loading) return <Loader label="Loading orders" />;

  return (
    <div className="mgr-page">
      <div className="mgr-page__header">
        <div>
          <h1 className="mgr-page__title">Orders</h1>
          <p className="mgr-page__sub">{orders.length} total · {orders.filter(o=>o.status==='pending').length} pending</p>
        </div>
      </div>
      {error && <ErrorState message={error} />}

      <div className="mgr-toolbar">
        <input className="mgr-search" placeholder="Search order # or customer ID…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <div className="mgr-filters">
          {['all',...STATUS_OPTIONS].map((s) => (
            <button key={s} className={`mgr-filter-btn${filter===s?' active':''}`} onClick={() => setFilter(s)}>
              {s.charAt(0).toUpperCase()+s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="card mgr-table-card">
        <div className="mgr-table-wrap">
          <table className="mgr-table">
            <thead>
              <tr><th>Order</th><th>Customer</th><th>Total</th><th>Date</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {filtered.map((o) => (
                <>
                  <tr key={o.id} className={expanded===o.id?'mgr-table__expanded':''}>
                    <td><span className="mono">{o.order_number}</span></td>
                    <td className="muted">#{o.customer_id}</td>
                    <td>{formatCurrency(o.total_amount)}</td>
                    <td className="muted">{formatDate(o.order_date)}</td>
                    <td>
                      <select className="mgr-status-select"
                        value={drafts[o.id]||o.status}
                        onChange={(e)=>setDrafts({...drafts,[o.id]:e.target.value})}>
                        {STATUS_OPTIONS.map((s)=><option key={s} value={s}>{s}</option>)}
                      </select>
                    </td>
                    <td>
                      <div style={{display:'flex',gap:'0.4rem',flexWrap:'wrap'}}>
                        <button className="mgr-btn" onClick={()=>handleStatusUpdate(o.id)}>Save</button>
                        <button className="mgr-btn" onClick={()=>setExpanded(expanded===o.id?null:o.id)}>
                          {expanded===o.id?'▲':'▼'} Items
                        </button>
                        <button className="mgr-btn" onClick={()=>setShipping(shipping===o.id?null:o.id)}>
                          📦 Ship
                        </button>
                      </div>
                    </td>
                  </tr>
                  {expanded===o.id && (
                    <tr key={`${o.id}-items`}><td colSpan={6}>
                      <div className="order-expand-panel">
                        <p><strong>Shipping:</strong> {o.shipping_address}</p>
                        {(o.items||[]).map((item)=>(
                          <div key={item.id} className="summary-row">
                            <span>Product #{item.product_id}</span><span>×{item.quantity}</span>
                          </div>
                        ))}
                      </div>
                    </td></tr>
                  )}
                  {shipping===o.id && (
                    <tr key={`${o.id}-ship`}><td colSpan={6}>
                      <div className="order-expand-panel order-ship-panel">
                        <h4>Create Shipment</h4>
                        <div className="form-row-3">
                          <div className="field"><label className="field__label">Carrier</label>
                            <input className="field__control" value={shipForm.carrier} onChange={(e)=>setShipForm({...shipForm,carrier:e.target.value})} placeholder="DHL, FedEx…" /></div>
                          <div className="field"><label className="field__label">Tracking #</label>
                            <input className="field__control" value={shipForm.tracking_number} onChange={(e)=>setShipForm({...shipForm,tracking_number:e.target.value})} placeholder="1Z999…" /></div>
                          <div className="field"><label className="field__label">Ship Status</label>
                            <select className="field__control" value={shipForm.status} onChange={(e)=>setShipForm({...shipForm,status:e.target.value})}>
                              <option value="processing">Processing</option><option value="shipped">Shipped</option>
                            </select></div>
                        </div>
                        <Button onClick={()=>handleShip(o.id)}>Confirm Shipment</Button>
                      </div>
                    </td></tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
