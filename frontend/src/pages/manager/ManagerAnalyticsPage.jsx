import { useEffect, useState } from 'react';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import {
  getManagerKPIsRequest,
  getMonthlyRevenueRequest,
  getBestSellingProductsRequest,
  getRevenueByCategoryRequest,
  getTopRatedProductsRequest,
  getSupplierPerformanceRequest,
} from '../../services/managerService';
import { formatCurrency } from '../../utils/format';

function StatRow({ label, value, sub }) {
  return (
    <div className="stat-row">
      <span className="stat-row__label">{label}</span>
      <span className="stat-row__value">{value}</span>
      {sub && <span className="stat-row__sub">{sub}</span>}
    </div>
  );
}

function formatMonthLabel(monthLabel) {
  const parsed = new Date(`${monthLabel}-01T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) return monthLabel;
  return parsed.toLocaleDateString(undefined, { month:'short', year:'2-digit', timeZone:'UTC' });
}

export default function ManagerAnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const [kpis,    setKpis]    = useState(null);
  const [monthly, setMonthly] = useState([]);
  const [monthlyError, setMonthlyError] = useState('');
  const [sellers, setSellers] = useState([]);
  const [byCat,   setByCat]   = useState([]);
  const [topRated,setTopRated]= useState([]);
  const [suppliers,setSuppliers]=useState([]);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [k, monthlyResult, s, c, r, sup] = await Promise.all([
          getManagerKPIsRequest().catch(() => null),
          getMonthlyRevenueRequest(6)
            .then((data) => ({ data, error:'' }))
            .catch((requestError) => ({
              data:[],
              error:requestError?.response?.data?.detail || 'Monthly revenue could not be loaded.',
            })),
          getBestSellingProductsRequest(10).catch(() => []),
          getRevenueByCategoryRequest().catch(() => []),
          getTopRatedProductsRequest(5).catch(() => []),
          getSupplierPerformanceRequest().catch(() => []),
        ]);
        if (!active) return;
        setKpis(k);
        setMonthly(monthlyResult.data);
        setMonthlyError(monthlyResult.error);
        setSellers(s); setByCat(c); setTopRated(r); setSuppliers(sup);
      } catch (e) {
        if (!active) return;
        setError(e?.response?.data?.detail || 'Failed to load analytics.');
      } finally { if (active) setLoading(false); }
    }
    load();
    return () => { active = false; };
  }, []);

  if (loading) return <Loader label="Loading analytics" />;
  if (error)   return <ErrorState message={error} />;

  // Compute max revenue for bar chart
  const maxRevenue = Math.max(...monthly.map((m) => Number(m.total_revenue) || 0), 1);

  return (
    <div className="mgr-page">
      <div className="mgr-page__header">
        <h1 className="mgr-page__title">Analytics & Reports</h1>
      </div>

      {/* ── Overall KPIs ── */}
      {kpis && (
        <div className="analytics-kpi-row">
          <div className="card analytics-kpi-card">
            <p className="analytics-kpi-card__label">Total Revenue</p>
            <p className="analytics-kpi-card__value">{formatCurrency(kpis.total_revenue)}</p>
          </div>
          <div className="card analytics-kpi-card">
            <p className="analytics-kpi-card__label">Total Orders</p>
            <p className="analytics-kpi-card__value">{kpis.total_orders.toLocaleString()}</p>
          </div>
          <div className="card analytics-kpi-card">
            <p className="analytics-kpi-card__label">Avg Order Value</p>
            <p className="analytics-kpi-card__value">{formatCurrency(kpis.avg_order_value)}</p>
          </div>
          <div className="card analytics-kpi-card">
            <p className="analytics-kpi-card__label">Total Customers</p>
            <p className="analytics-kpi-card__value">{kpis.total_customers.toLocaleString()}</p>
          </div>
        </div>
      )}

      <div className="analytics-grid">
        {/* ── Monthly Revenue Bar Chart ── */}
        <div className="card mgr-section">
          <h2 className="mgr-section__title">Monthly Revenue (last 6 months)</h2>
          {monthlyError ? (
            <p className="text-danger">{monthlyError}</p>
          ) : monthly.length === 0 ? (
            <p className="muted">No monthly data yet.</p>
          ) : (
            <div className="bar-chart">
              {[...monthly].reverse().map((m) => {
                const revenue = Number(m.total_revenue) || 0;
                const pct = revenue > 0 ? Math.max(6, (revenue / maxRevenue) * 100) : 0;
                return (
                  <div key={m.month_label} className="bar-chart__bar-wrap">
                    <div className="bar-chart__plot">
                      <div
                        className={`bar-chart__bar${revenue === 0 ? ' bar-chart__bar--empty' : ''}`}
                        style={{ height: `${pct}%` }}
                        title={`${formatMonthLabel(m.month_label)}: ${formatCurrency(revenue)}`}
                      >
                        <span className="bar-chart__tooltip">{formatCurrency(revenue)}</span>
                      </div>
                    </div>
                    <span className="bar-chart__label">{formatMonthLabel(m.month_label)}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ── Revenue by Category ── */}
        <div className="card mgr-section">
          <h2 className="mgr-section__title">Revenue by Category</h2>
          <div className="stat-list">
            {byCat.slice(0,8).map((c) => (
              <StatRow key={c.category_name} label={c.category_name} value={formatCurrency(c.total_revenue)} sub={`${c.order_count} orders`} />
            ))}
            {byCat.length === 0 && <p className="muted">No data yet.</p>}
          </div>
        </div>

        {/* ── Best Sellers ── */}
        <div className="card mgr-section">
          <h2 className="mgr-section__title">Top 10 Best Sellers (90d)</h2>
          <div className="mgr-table-wrap">
            <table className="mgr-table">
              <thead><tr><th>#</th><th>Product</th><th>Units</th><th>Revenue</th></tr></thead>
              <tbody>
                {sellers.map((s, i) => (
                  <tr key={s.product_id}>
                    <td className="muted">#{i+1}</td>
                    <td><div><strong>{s.product_name}</strong><p className="muted" style={{fontSize:'0.78rem'}}>{s.brand_name}</p></div></td>
                    <td>{s.total_units_sold}</td>
                    <td className="brand-text">{formatCurrency(s.total_revenue)}</td>
                  </tr>
                ))}
                {sellers.length === 0 && <tr><td colSpan={4} className="muted">No sales data yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── Top Rated ── */}
        <div className="card mgr-section">
          <h2 className="mgr-section__title">Top Rated Products</h2>
          <div className="stat-list">
            {topRated.slice(0,6).map((p) => (
              <StatRow key={p.product_id} label={p.product_name}
                value={`★ ${Number(p.avg_rating).toFixed(1)}`}
                sub={`${p.review_count} reviews`} />
            ))}
            {topRated.length === 0 && <p className="muted">No ratings yet.</p>}
          </div>
        </div>

        {/* ── Supplier Performance ── */}
        <div className="card mgr-section">
          <h2 className="mgr-section__title">Supplier Performance</h2>
          <div className="mgr-table-wrap">
            <table className="mgr-table">
              <thead><tr><th>Supplier</th><th>Products</th><th>Revenue</th><th>Units</th></tr></thead>
              <tbody>
                {suppliers.slice(0,8).map((s) => (
                  <tr key={s.supplier_name}>
                    <td><strong>{s.supplier_name}</strong></td>
                    <td className="muted">{s.product_count}</td>
                    <td className="brand-text">{formatCurrency(s.total_revenue)}</td>
                    <td className="muted">{s.total_units_sold}</td>
                  </tr>
                ))}
                {suppliers.length === 0 && <tr><td colSpan={4} className="muted">No data yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
