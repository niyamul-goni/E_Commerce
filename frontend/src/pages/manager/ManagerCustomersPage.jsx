import { useEffect, useState } from 'react';
import ErrorState from '../../components/ErrorState';
import Loader from '../../components/Loader';
import { getAllCustomersRequest } from '../../services/managerService';
import { formatCurrency, formatDate } from '../../utils/format';

export default function ManagerCustomersPage() {
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    getAllCustomersRequest()
      .then((data) => setCustomers(data.filter((customer) => !customer.is_manager)))
      .catch((e) => setError(e?.response?.data?.detail || 'Failed to load customers.'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = customers.filter((c) =>
    !search ||
    (c.email||'').toLowerCase().includes(search.toLowerCase()) ||
    ((c.first_name||'')+' '+(c.last_name||'')).toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <Loader label="Loading customers" />;
  if (error)   return <ErrorState message={error} />;

  const totalRevenue = customers.reduce((s, c) => s + c.total_spend, 0);

  return (
    <div className="mgr-page">
      <div className="mgr-page__header">
        <div>
          <h1 className="mgr-page__title">Customers</h1>
          <p className="mgr-page__sub">{customers.length} registered · {formatCurrency(totalRevenue)} total spend</p>
        </div>
      </div>

      <div className="mgr-toolbar">
        <input className="mgr-search" placeholder="Search by name or email…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <span className="muted">{filtered.length} result{filtered.length !== 1 ? 's' : ''}</span>
      </div>

      <div className="card mgr-table-card">
        <div className="mgr-table-wrap">
          <table className="mgr-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Orders</th>
                <th>Total Spend</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id}>
                  <td>
                    <div className="customer-chip">
                      <div className="customer-chip__avatar">
                        {(c.first_name || c.email || '?').charAt(0).toUpperCase()}
                      </div>
                      <span>{c.first_name ? `${c.first_name} ${c.last_name||''}`.trim() : '—'}</span>
                    </div>
                  </td>
                  <td className="muted">{c.email}</td>
                  <td className="muted">{c.phone || '—'}</td>
                  <td>{c.order_count}</td>
                  <td>
                    <span className={c.total_spend > 1000 ? 'brand-text' : ''}>{formatCurrency(c.total_spend)}</span>
                  </td>
                  <td className="muted">{formatDate(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
