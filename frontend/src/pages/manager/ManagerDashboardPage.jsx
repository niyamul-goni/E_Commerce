import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import { useAuth } from '../../context/AuthContext';
import {
  getBestSellingProductsRequest,
  getAllReviewsRequest,
  getManagerKPIsRequest,
} from '../../services/managerService';
import { getAllOrdersRequest } from '../../services/commerceService';
import { formatCurrency, formatDate } from '../../utils/format';

function DashboardIcon({ name }) {
  const paths = {
    revenue: <><path d="M12 2v20M17 5.5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></>,
    orders: <><path d="M6 2h12l2 4v16H4V6l2-4Z" /><path d="M4 6h16M9 10a3 3 0 0 0 6 0" /></>,
    customers: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" /></>,
    average: <><path d="M3 3v18h18" /><path d="m7 16 4-5 4 3 5-7" /></>,
  };

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {paths[name]}
    </svg>
  );
}

function KpiCard({ icon, label, value, sub }) {
  return (
    <article className="kpi-card card">
      <div className="kpi-card__head">
        <p className="kpi-card__label">{label}</p>
        <span className="kpi-card__icon"><DashboardIcon name={icon} /></span>
      </div>
      <p className="kpi-card__value">{value}</p>
      <p className="kpi-card__sub">{sub}</p>
    </article>
  );
}

function OperationsCard({ label, value, to }) {
  const needsAttention = Number(value) > 0;
  return (
    <Link to={to} className="operations-card">
      <span className={`operations-card__indicator${needsAttention ? ' operations-card__indicator--attention' : ''}`} />
      <span className="operations-card__label">{label}</span>
      <strong className="operations-card__value">{value}</strong>
      <span className="operations-card__arrow">›</span>
    </Link>
  );
}

const QUICK_ACTIONS = [
  { to: '/manager/products', label: 'Add or edit products', detail: 'Catalogue and product images' },
  { to: '/manager/inventory', label: 'Update inventory', detail: 'Available and reserved stock' },
  { to: '/manager/orders', label: 'Manage orders', detail: 'Status, fulfilment and shipping' },
  { to: '/manager/analytics', label: 'Open analytics', detail: 'Revenue and performance reports' },
];

export default function ManagerDashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [kpis, setKpis] = useState(null);
  const [orders, setOrders] = useState([]);
  const [sellers, setSellers] = useState([]);
  const [unanswered, setUnanswered] = useState(0);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        setLoading(true);
        setError('');
        const [kpiData, orderData, sellerData, reviewData] = await Promise.all([
          getManagerKPIsRequest(),
          getAllOrdersRequest(),
          getBestSellingProductsRequest(5).catch(() => []),
          getAllReviewsRequest().catch(() => []),
        ]);
        if (!active) return;
        setKpis(kpiData);
        setOrders(orderData.slice(0, 8));
        setSellers(sellerData);
        setUnanswered(reviewData.filter((review) => !review.has_reply).length);
      } catch (loadError) {
        if (!active) return;
        setError(loadError?.response?.data?.detail || 'Failed to load dashboard data.');
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, []);

  if (loading) return <Loader label="Loading dashboard" />;
  if (error) return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  const firstName = user?.first_name && user.first_name !== 'User' ? user.first_name : 'Manager';
  const pendingOrders = Number(kpis?.pending_orders || 0);
  const pendingReturns = Number(kpis?.pending_returns || 0);
  const dateLabel = new Intl.DateTimeFormat('en-US', {
    weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
  }).format(new Date());

  return (
    <div className="mgr-page manager-dashboard">
      <header className="dashboard-header">
        <div>
          <p className="dashboard-header__eyebrow">Store overview</p>
          <h1 className="mgr-page__title">Welcome back, {firstName}</h1>
          <p className="mgr-page__sub">Monitor performance and handle today&apos;s store operations.</p>
        </div>
        <time className="dashboard-header__date">{dateLabel}</time>
      </header>

      <section className="kpi-grid" aria-label="Store performance">
        <KpiCard
          icon="revenue"
          label="Revenue · 30 days"
          value={formatCurrency(kpis?.revenue_last_30d || 0)}
          sub={`${Number(kpis?.orders_last_30d || 0).toLocaleString()} orders in this period`}
        />
        <KpiCard
          icon="orders"
          label="Total orders"
          value={Number(kpis?.total_orders || 0).toLocaleString()}
          sub={`${pendingOrders.toLocaleString()} currently pending`}
        />
        <KpiCard
          icon="customers"
          label="Customers"
          value={Number(kpis?.total_customers || 0).toLocaleString()}
          sub="Registered customer accounts"
        />
        <KpiCard
          icon="average"
          label="Average order value"
          value={formatCurrency(kpis?.avg_order_value || 0)}
          sub="Across non-cancelled orders"
        />
      </section>

      <section className="dashboard-main-grid">
        <div className="mgr-section card dashboard-orders">
          <div className="mgr-section__head">
            <div>
              <h2 className="mgr-section__title">Recent orders</h2>
              <p className="mgr-section__subtitle">Latest activity across the store</p>
            </div>
            <Link to="/manager/orders" className="mgr-section__link">View all orders</Link>
          </div>
          {orders.length === 0 ? (
            <p className="dashboard-empty">No orders yet.</p>
          ) : (
            <div className="mgr-table-wrap">
              <table className="mgr-table dashboard-table">
                <thead>
                  <tr><th>Order</th><th>Customer</th><th>Total</th><th>Status</th><th>Date</th></tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.id}>
                      <td><span className="mono">{order.order_number}</span></td>
                      <td className="dashboard-table__customer">{order.customer_email || 'Customer'}</td>
                      <td>{formatCurrency(order.total_amount)}</td>
                      <td><span className={`status-dot status-dot--${order.status}`}>{order.status}</span></td>
                      <td className="muted">{formatDate(order.order_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <aside className="mgr-section card dashboard-operations">
          <div className="mgr-section__head">
            <div>
              <h2 className="mgr-section__title">Operations</h2>
              <p className="mgr-section__subtitle">Items that may need attention</p>
            </div>
          </div>
          <div className="operations-list">
            <OperationsCard label="Pending orders" value={pendingOrders} to="/manager/orders" />
            <OperationsCard label="Pending returns" value={pendingReturns} to="/manager/orders" />
            <OperationsCard label="Unanswered reviews" value={unanswered} to="/manager/reviews" />
          </div>
          {pendingOrders + pendingReturns + unanswered === 0 ? (
            <p className="operations-complete">All operational queues are clear.</p>
          ) : null}
        </aside>
      </section>

      <section className="dashboard-lower-grid">
        <div className="mgr-section card">
          <div className="mgr-section__head">
            <div>
              <h2 className="mgr-section__title">Best sellers · 90 days</h2>
              <p className="mgr-section__subtitle">Products ranked by recent sales</p>
            </div>
            <Link to="/manager/analytics" className="mgr-section__link">Full report</Link>
          </div>
          {sellers.length === 0 ? (
            <p className="dashboard-empty">No sales data yet.</p>
          ) : (
            <div className="best-sellers-list">
              {sellers.map((seller, index) => (
                <div key={seller.product_id} className="best-seller-row">
                  <span className="best-seller-row__rank">{String(index + 1).padStart(2, '0')}</span>
                  <div className="best-seller-row__info">
                    <p className="best-seller-row__name">{seller.product_name}</p>
                    <p className="muted">{[seller.brand_name, seller.category_name].filter(Boolean).join(' · ') || 'Uncategorized'}</p>
                  </div>
                  <div className="best-seller-row__stats">
                    <p>{Number(seller.total_units_sold || 0).toLocaleString()} sold</p>
                    <p className="brand-text">{formatCurrency(seller.total_revenue)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mgr-section card dashboard-quick-actions">
          <div className="mgr-section__head">
            <div>
              <h2 className="mgr-section__title">Quick actions</h2>
              <p className="mgr-section__subtitle">Common management tasks</p>
            </div>
          </div>
          <div className="quick-actions-list">
            {QUICK_ACTIONS.map((action) => (
              <Link key={action.to} to={action.to} className="quick-action">
                <span><strong>{action.label}</strong><small>{action.detail}</small></span>
                <span className="quick-action__arrow">→</span>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
