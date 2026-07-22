import { useEffect, useState } from 'react';
import EmptyState from '../components/EmptyState';
import ErrorState from '../components/ErrorState';
import Loader from '../components/Loader';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import {
  getMyOrdersRequest,
  getShipmentByOrderRequest,
} from '../services/commerceService';
import { formatCurrency, formatDate } from '../utils/format';

function ShipmentInfo({ orderId }) {
  const [shipment, setShipment] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getShipmentByOrderRequest(orderId)
      .then((data) => { if (active) setShipment(data); })
      .catch(() => { /* no shipment yet */ })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [orderId]);

  if (loading || !shipment) return null;
  const shipmentStatus = shipment.shipment_status || shipment.status;

  return (
    <div className="shipment-info">
      <span className="shipment-info__label">📦 Shipment</span>
      <span className={`shipment-status shipment-status--${shipmentStatus}`}>
        {shipmentStatus}
      </span>
      {shipment.tracking_number && (
        <span className="shipment-info__track">
          Tracking: <strong>{shipment.tracking_number}</strong>
        </span>
      )}
      {shipment.carrier && (
        <span className="shipment-info__carrier">via {shipment.carrier}</span>
      )}
      {shipment.estimated_delivery && (
        <span className="shipment-info__eta">
          ETA: {formatDate(shipment.estimated_delivery)}
        </span>
      )}
    </div>
  );
}

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
    return () => { active = false; };
  }, []);

  if (loading) return <Loader label="Loading orders" />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;
  if (!orders.length) {
    return <EmptyState title="No orders yet" message="Your order history will appear here after checkout." />;
  }

  return (
    <div className="page-stack">
      <PageHeader title="Order History" subtitle="Track what you ordered and how each order is progressing." />
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
            <p style={{ color: 'var(--text-2)', fontSize: '0.875rem' }}>
              📍 {order.shipping_address}
            </p>

            {/* Order Items */}
            {(order.items || []).length > 0 && (
              <div className="order-items">
                {order.items.map((item) => (
                  <div key={item.id} className="summary-row">
                    <span>Product #{item.product_id}</span>
                    <span>×{item.quantity}</span>
                    {item.unit_price && (
                      <span style={{ color: 'var(--brand)' }}>{formatCurrency(item.unit_price)}</span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Shipment Info (lazy-loaded per order) */}
            <ShipmentInfo orderId={order.id} />
          </article>
        ))}
      </div>
    </div>
  );
}
