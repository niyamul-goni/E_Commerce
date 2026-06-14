import { useEffect, useState } from 'react';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import Loader from '../components/Loader';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import { getMyOrdersRequest } from '../services/commerceService';
import { formatCurrency, formatDate } from '../utils/format';

export default function OrdersPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    let active = true;

    async function loadOrders() {
      try {
        setLoading(true);
        setError('');
        const data = await getMyOrdersRequest();
        if (!active) return;
        setOrders(data);
      } catch (loadError) {
        if (!active) return;
        setError(loadError?.response?.data?.detail || 'Failed to load your orders.');
      } finally {
        if (active) setLoading(false);
      }
    }

    loadOrders();
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <Loader label="Loading orders" />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  if (!orders.length) {
    return <EmptyState title="No orders yet" message="Your order history will appear here after checkout." />;
  }

  return (
    <div className="page-stack">
      <PageHeader title="Order history" subtitle="Track what you ordered and how each order is progressing." />
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
            <p>Placed on {formatDate(order.order_date)}</p>
            <p>Shipping address: {order.shipping_address}</p>
            <div className="order-items">
              {(order.items || []).map((item) => (
                <div key={item.id} className="summary-row">
                  <span>Product #{item.product_id}</span>
                  <span>x{item.quantity}</span>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
