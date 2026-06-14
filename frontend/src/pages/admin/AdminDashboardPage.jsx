import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import PageHeader from '../../components/PageHeader';
import StatCard from '../../components/StatCard';
import StatusBadge from '../../components/StatusBadge';
import { getAllOrdersRequest, getDashboardSummaryRequest } from '../../services/commerceService';
import { formatCurrency, formatDate } from '../../utils/format';

export default function AdminDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState(null);
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      try {
        setLoading(true);
        setError('');
        const [summaryData, orderData] = await Promise.all([getDashboardSummaryRequest(), getAllOrdersRequest()]);
        if (!active) return;
        setSummary(summaryData);
        setOrders(orderData.slice(0, 5));
      } catch (loadError) {
        if (!active) return;
        setError(loadError?.response?.data?.detail || 'Failed to load admin dashboard.');
      } finally {
        if (active) setLoading(false);
      }
    }

    loadDashboard();
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <Loader label="Loading admin dashboard" />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  return (
    <div className="page-stack">
      <PageHeader
        title="Admin dashboard"
        subtitle="Track business totals and jump straight to management pages."
        action={<Link className="button" to="/products">Open storefront</Link>}
      />

      <section className="admin-dashboard__stats stats-grid">
        <StatCard label="Products" value={summary.total_products} />
        <StatCard label="Customers" value={summary.total_customers} />
        <StatCard label="Orders" value={summary.total_orders} />
        <StatCard label="Sales" value={formatCurrency(summary.total_sales)} />
        <StatCard label="Average order" value={formatCurrency(summary.average_order_value)} />
        <StatCard label="Low stock" value={summary.low_stock_products} />
      </section>

      <section className="section-grid">
        <div className="card admin-summary">
          <h3>Quick actions</h3>
          <div className="chip-grid">
            <Link className="category-chip" to="/admin/products">Products</Link>
            <Link className="category-chip" to="/admin/categories">Categories</Link>
            <Link className="category-chip" to="/admin/suppliers">Suppliers</Link>
            <Link className="category-chip" to="/admin/orders">Orders</Link>
          </div>
          <Button variant="secondary" onClick={() => window.location.reload()}>
            Refresh metrics
          </Button>
        </div>

        <div className="card admin-summary">
          <h3>Recent orders</h3>
          {orders.map((order) => (
            <div key={order.id} className="summary-row">
              <div>
                <strong>{order.order_number}</strong>
                <p>{formatDate(order.order_date)}</p>
              </div>
              <StatusBadge value={order.status} />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
