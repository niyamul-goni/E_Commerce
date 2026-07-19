import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import {
  getBestSellingProductsRequest,
  getAllReviewsRequest,
  getManagerKPIsRequest,
} from '../../services/managerService';
import { getAllOrdersRequest } from '../../services/commerceService';
import { formatCurrency, formatDate } from '../../utils/format';

function KpiCard({ icon, label, value, sub, accent }) {
  return (
    <div className="kpi-card card" style={{ '--kpi-accent': accent }}>
      <div className="kpi-card__icon">{icon}</div>
      <div className="kpi-card__body">
        <p className="kpi-card__label">{label}</p>
        <p className="kpi-card__value">{value}</p>
        {sub && <p className="kpi-card__sub">{sub}</p>}
      </div>
    </div>
  );
}

function AlertRow({ icon, text, to }) {
  return (
    <Link to={to} className="alert-row">
      <span className="alert-row__icon">{icon}</span>
      <span className="alert-row__text">{text}</span>
      <span className="alert-row__arrow">→</span>
    </Link>
  );
}

export default function ManagerDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const [kpis,    setKpis]    = useState(null);
  const [orders,  setOrders]  = useState([]);
  const [sellers, setSellers] = useState([]);
  const [unanswered, setUnanswered] = useState(0);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        setLoading(true);
        const [kpiData, orderData, sellerData, reviewData] = await Promise.all([
          getManagerKPIsRequest().catch(() => null),
          getAllOrdersRequest().catch(() => []),
          getBestSellingProductsRequest(5).catch(() => []),
          getAllReviewsRequest().catch(() => []),
        ]);
        if (!active) return;
        setKpis(kpiData);
        setOrders(orderData.slice(0, 8));
        setSellers(sellerData);
        setUnanswered(reviewData.filter((r) => !r.has_reply).length);
      } catch (err) {
        if (!active) return;
        setError(err?.response?.data?.detail || 'Failed to load dashboard data.');
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, []);

  if (loading) return <Loader label="Loading dashboard" />;
  if (error)   return <ErrorState message={error} onRetry={() => window.location.reload()} />;

  const pendingOrders = orders.filter((o) => o.status === 'pending').length;

  return (
    <div className="mgr-page">
      <div className="mgr-page__header">
        <h1 className="mgr-page__title">Dashboard</h1>
        <p className="mgr-page__sub">Good day — here's what's happening with your store.</p>
      </div>

      {/* ── KPI Cards ── */}
      <div className="kpi-grid">
        <KpiCard
          icon="💰" label="Revenue (30d)" accent="#c9a96e"
          value={kpis ? formatCurrency(kpis.revenue_last_30d) : '—'}
          sub={kpis ? `${kpis.orders_last_30d} orders` : ''}
        />
        <KpiCard
          icon="📦" label="Total Orders" accent="#6e8dc9"
          value={kpis ? kpis.total_orders.toLocaleString() : '—'}
          sub={`${pendingOrders} pending`}
        />
        <KpiCard
          icon="👥" label="Customers" accent="#6ec9a9"
          value={kpis ? kpis.total_customers.toLocaleString() : '—'}
        />
        <KpiCard
          icon="💳" label="Avg Order Value" accent="#c96e9a"
          value={kpis ? formatCurrency(kpis.avg_order_value) : '—'}
        />
        <KpiCard
          icon="↩️" label="Pending Returns" accent="#c9906e"
          value={kpis ? kpis.pending_returns : '—'}
          sub="needs review"
        />
        <KpiCard
          icon="⭐" label="Unanswered Reviews" accent="#9a6ec9"
          value={unanswered}
          sub="awaiting reply"
        />
      </div>

      {/* ── Alerts ── */}
      {(pendingOrders > 0 || unanswered > 0 || (kpis?.pending_returns ?? 0) > 0) && (
        <div className="mgr-section card">
          <h2 className="mgr-section__title">🔔 Action Required</h2>
          <div className="alert-list">
            {pendingOrders > 0 && (
              <AlertRow icon="⏳" text={`${pendingOrders} orders are awaiting fulfilment`} to="/manager/orders" />
            )}
            {unanswered > 0 && (
              <AlertRow icon="💬" text={`${unanswered} customer reviews need a reply`} to="/manager/reviews" />
            )}
            {(kpis?.pending_returns ?? 0) > 0 && (
              <AlertRow icon="↩️" text={`${kpis.pending_returns} return requests pending`} to="/manager/orders" />
            )}
          </div>
        </div>
      )}

      <div className="mgr-two-col">
        {/* ── Recent Orders ── */}
        <div className="mgr-section card">
          <div className="mgr-section__head">
            <h2 className="mgr-section__title">Recent Orders</h2>
            <Link to="/manager/orders" className="mgr-section__link">View all →</Link>
          </div>
          {orders.length === 0 ? (
            <p className="muted">No orders yet.</p>
          ) : (
            <div className="mgr-table-wrap">
              <table className="mgr-table">
                <thead>
                  <tr>
                    <th>Order</th>
                    <th>Total</th>
                    <th>Status</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((o) => (
                    <tr key={o.id}>
                      <td><span className="mono">{o.order_number}</span></td>
                      <td>{formatCurrency(o.total_amount)}</td>
                      <td>
                        <span className={`status-dot status-dot--${o.status}`}>{o.status}</span>
                      </td>
                      <td className="muted">{formatDate(o.order_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* ── Best Sellers ── */}
        <div className="mgr-section card">
          <div className="mgr-section__head">
            <h2 className="mgr-section__title">Best Sellers (90d)</h2>
            <Link to="/manager/analytics" className="mgr-section__link">Full report →</Link>
          </div>
          {sellers.length === 0 ? (
            <p className="muted">No sales data yet.</p>
          ) : (
            <div className="best-sellers-list">
              {sellers.map((s, i) => (
                <div key={s.product_id} className="best-seller-row">
                  <span className="best-seller-row__rank">#{i + 1}</span>
                  <div className="best-seller-row__info">
                    <p className="best-seller-row__name">{s.product_name}</p>
                    <p className="muted" style={{ fontSize: '0.78rem' }}>{s.brand_name} · {s.category_name}</p>
                  </div>
                  <div className="best-seller-row__stats">
                    <p>{s.total_units_sold} units</p>
                    <p className="brand-text">{formatCurrency(s.total_revenue)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
