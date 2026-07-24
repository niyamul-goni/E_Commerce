import { Fragment, useEffect, useState } from 'react';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import StatusBadge from '../../components/StatusBadge';
import { getAllOrdersRequest, updateOrderStatusRequest, createShipmentRequest } from '../../services/commerceService';
import { formatCurrency, formatDate } from '../../utils/format';

const STATUS_OPTIONS = ['pending','confirmed','packed','shipped','delivered','cancelled','returned','refunded'];
const FALLBACK_TRANSITIONS = {
  pending: ['pending', 'confirmed', 'cancelled'],
  confirmed: ['confirmed', 'packed', 'cancelled'],
  packed: ['packed', 'shipped', 'cancelled'],
  shipped: ['shipped', 'delivered', 'returned'],
  delivered: ['delivered', 'returned'],
  returned: ['returned', 'refunded'],
  cancelled: ['cancelled'],
  refunded: ['refunded'],
};

function statusOptionsFor(order) {
  return Array.isArray(order.allowed_statuses) && order.allowed_statuses.length
    ? order.allowed_statuses
    : FALLBACK_TRANSITIONS[order.status] || [order.status];
}

function shipmentOptionsFor(orderStatus) {
  if (orderStatus === 'confirmed') return ['packed', 'in_transit'];
  if (orderStatus === 'packed') return ['packed', 'in_transit', 'delivered'];
  if (orderStatus === 'shipped') return ['in_transit', 'delivered', 'returned'];
  if (orderStatus === 'delivered') return ['delivered', 'returned'];
  return [];
}

export default function ManagerOrdersPage() {
  const [loading, setLoading]   = useState(true);
  const [error,   setError]     = useState('');
  const [orders,  setOrders]    = useState([]);
  const [drafts,  setDrafts]    = useState({});
  const [expanded, setExpanded] = useState(null);
  const [filter,  setFilter]    = useState('all');
  const [search,  setSearch]    = useState('');
  const [shipForm, setShipForm] = useState({ tracking_number:'', carrier:'', status:'in_transit' });
  const [shipping, setShipping] = useState(null); // order being shipped
  const [savingId, setSavingId] = useState(null);
  const [notice, setNotice] = useState('');

  async function load() {
    try {
      setLoading(true);
      setError('');
      const d = await getAllOrdersRequest();
      setOrders(d);
      setDrafts(Object.fromEntries(d.map((o)=>[o.id,o.status])));
    }
    catch (e) { setError(e?.response?.data?.detail || 'Failed to load orders.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function handleStatusUpdate(orderId) {
    const order = orders.find((item) => item.id === orderId);
    const requestedStatus = drafts[orderId] || order?.status;
    if (!order || requestedStatus === order.status) return;

    try {
      setSavingId(orderId);
      setError('');
      setNotice('');
      const updated = await updateOrderStatusRequest(orderId, requestedStatus);
      setOrders((current) => current.map((item) => (
        item.id === orderId
          ? {
              ...item,
              status: updated.status,
              allowed_statuses: updated.allowed_statuses,
            }
          : item
      )));
      setDrafts((current) => ({ ...current, [orderId]: updated.status }));
      setNotice(`Order ${order.order_number} is now ${updated.status}.`);
    }
    catch (e) { setError(e?.response?.data?.detail || 'Status update failed.'); }
    finally { setSavingId(null); }
  }

  async function handleShip(orderId) {
    try {
      const order = orders.find((item) => item.id === orderId);
      setError('');
      setNotice('');
      const shipment = await createShipmentRequest({ order_id: orderId, ...shipForm });
      setShipping(null); setShipForm({ tracking_number:'', carrier:'', status:'in_transit' });
      await load();
      setNotice(
        `Shipment saved for ${order?.order_number || `order #${orderId}`}`
        + (shipment.order_status ? ` · order is now ${shipment.order_status}.` : '.'),
      );
    } catch (e) { setError(e?.response?.data?.detail || 'Failed to create shipment.'); }
  }

  function toggleShipping(order) {
    if (shipping === order.id) {
      setShipping(null);
      return;
    }
    const options = shipmentOptionsFor(order.status);
    setShipForm({
      tracking_number: '',
      carrier: '',
      status: options.includes('in_transit') ? 'in_transit' : options[0],
    });
    setShipping(order.id);
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
      {notice && <p className="inline-message inline-message--success" role="status">{notice}</p>}

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
                <Fragment key={o.id}>
                  <tr key={o.id} className={expanded===o.id?'mgr-table__expanded':''}>
                    <td><span className="mono">{o.order_number}</span></td>
                    <td className="muted">#{o.customer_id}</td>
                    <td>{formatCurrency(o.total_amount)}</td>
                    <td className="muted">{formatDate(o.order_date)}</td>
                    <td>
                      <div className="mgr-order-status-control">
                        <StatusBadge status={o.status} />
                        <select className="mgr-status-select"
                        value={drafts[o.id]||o.status}
                        disabled={savingId === o.id}
                        onChange={(e)=>setDrafts({...drafts,[o.id]:e.target.value})}>
                          {statusOptionsFor(o).map((s)=>(
                            <option key={s} value={s}>
                              {s.charAt(0).toUpperCase()+s.slice(1)}
                            </option>
                          ))}
                        </select>
                      </div>
                    </td>
                    <td>
                      <div style={{display:'flex',gap:'0.4rem',flexWrap:'wrap'}}>
                        <button
                          className="mgr-btn"
                          disabled={savingId === o.id || (drafts[o.id] || o.status) === o.status}
                          onClick={()=>handleStatusUpdate(o.id)}
                        >
                          {savingId === o.id ? 'Saving…' : 'Save'}
                        </button>
                        <button className="mgr-btn" onClick={()=>setExpanded(expanded===o.id?null:o.id)}>
                          {expanded===o.id?'▲':'▼'} Items
                        </button>
                        {shipmentOptionsFor(o.status).length > 0 && (
                          <button className="mgr-btn" onClick={()=>toggleShipping(o)}>
                            📦 Shipment
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                  {expanded===o.id && (
                    <tr key={`${o.id}-items`}><td colSpan={6}>
                      <div className="order-expand-panel">
                        <p><strong>Shipping:</strong> {o.shipping_address}</p>
                        {(o.items||[]).map((item)=>(
                          <div key={item.id} className="summary-row">
                            <span>{item.product_name || `Product #${item.product_id}`}{item.size_name ? ` · ${item.size_name}` : ''}{item.color_name ? ` · ${item.color_name}` : ''}</span><span>×{item.quantity}</span>
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
                              {shipmentOptionsFor(o.status).map((shipmentStatus) => (
                                <option key={shipmentStatus} value={shipmentStatus}>
                                  {shipmentStatus === 'in_transit'
                                    ? 'In Transit'
                                    : shipmentStatus.charAt(0).toUpperCase()+shipmentStatus.slice(1)}
                                </option>
                              ))}
                            </select></div>
                        </div>
                        <Button onClick={()=>handleShip(o.id)}>Confirm Shipment</Button>
                      </div>
                    </td></tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
