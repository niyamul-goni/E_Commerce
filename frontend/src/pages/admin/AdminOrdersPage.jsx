import { useEffect, useState } from 'react';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { getAllOrdersRequest, updateOrderStatusRequest } from '../../services/commerceService';
import { formatCurrency, formatDate } from '../../utils/format';

const statusOptions = ['pending', 'paid', 'shipped', 'delivered', 'cancelled'];

export default function AdminOrdersPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [orders, setOrders] = useState([]);
  const [statusDrafts, setStatusDrafts] = useState({});

  async function loadOrders() {
    try {
      setLoading(true);
      setError('');
      const data = await getAllOrdersRequest();
      setOrders(data);
      setStatusDrafts(Object.fromEntries(data.map((order) => [order.id, order.status])));
    } catch (loadError) {
      setError(loadError?.response?.data?.detail || 'Failed to load orders.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOrders();
  }, []);

  async function handleUpdateStatus(orderId) {
    try {
      await updateOrderStatusRequest(orderId, statusDrafts[orderId]);
      await loadOrders();
    } catch (updateError) {
      setError(updateError?.response?.data?.detail || 'Unable to update order status.');
    }
  }

  if (loading) return <Loader label="Loading orders" />;
  if (error && !orders.length) return <ErrorState message={error} onRetry={loadOrders} />;

  return (
    <div className="page-stack">
      <PageHeader title="Manage orders" subtitle="Review the order pipeline and change fulfillment status." />
      {error ? <ErrorState title="Order management issue" message={error} onRetry={loadOrders} /> : null}

      <div className="orders-list">
        {orders.map((order) => (
          <article key={order.id} className="card order-card">
            <div className="order-card__header">
              <div>
                <p className="eyebrow">{order.order_number}</p>
                <h3>{formatCurrency(order.total_amount)}</h3>
              </div>
              <StatusBadge value={order.status} />
            </div>

            <p>Customer ID: {order.customer_id}</p>
            <p>Placed on {formatDate(order.order_date)}</p>
            <div className="order-items">
              {(order.items || []).map((item) => (
                <div key={item.id} className="summary-row">
                  <span>Product #{item.product_id}</span>
                  <span>x{item.quantity}</span>
                </div>
              ))}
            </div>

            <div className="admin-toolbar">
              <label className="field">
                <span className="field__label">Status</span>
                <select
                  className="field__control"
                  value={statusDrafts[order.id] || order.status}
                  onChange={(event) => setStatusDrafts({ ...statusDrafts, [order.id]: event.target.value })}
                >
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </label>
              <Button onClick={() => handleUpdateStatus(order.id)}>Update status</Button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
