import { useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV_ITEMS = [
  { to: '/manager',           icon: 'dashboard',  label: 'Dashboard', end: true },
  { to: '/manager/products',  icon: 'products',   label: 'Products' },
  { to: '/manager/orders',    icon: 'orders',     label: 'Orders' },
  { to: '/manager/customers', icon: 'customers',  label: 'Customers' },
  { to: '/manager/inventory', icon: 'inventory',  label: 'Inventory' },
  { to: '/manager/coupons',   icon: 'coupons',    label: 'Coupons' },
  { to: '/manager/reviews',   icon: 'reviews',    label: 'Reviews' },
  { to: '/manager/categories',icon: 'categories', label: 'Categories' },
  { to: '/manager/suppliers', icon: 'suppliers',  label: 'Suppliers' },
  { to: '/manager/analytics', icon: 'analytics',  label: 'Analytics' },
];

function NavIcon({ name }) {
  const icons = {
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    products: <><path d="m4 7 8-4 8 4-8 4-8-4Z" /><path d="m4 7 8 4 8-4v10l-8 4-8-4V7Z" /><path d="M12 11v10" /></>,
    orders: <><path d="M6 3h12v18H6z" /><path d="M9 7h6M9 11h6M9 15h4" /></>,
    customers: <><circle cx="9" cy="8" r="3" /><path d="M3 21v-2a6 6 0 0 1 12 0v2M16 4a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 5v2" /></>,
    inventory: <><path d="M3 7h18v14H3zM3 7l3-4h12l3 4M8 11h8" /></>,
    coupons: <><path d="M3 8a2 2 0 0 0 0 4v4h18v-4a2 2 0 0 0 0-4V4H3v4Z" /><path d="M13 4v12" /></>,
    reviews: <><path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z" /></>,
    categories: <><rect x="3" y="3" width="8" height="8" rx="1" /><rect x="13" y="3" width="8" height="8" rx="1" /><rect x="3" y="13" width="8" height="8" rx="1" /><rect x="13" y="13" width="8" height="8" rx="1" /></>,
    suppliers: <><path d="M3 6h11v11H3zM14 10h4l3 3v4h-7z" /><circle cx="7" cy="19" r="2" /><circle cx="18" cy="19" r="2" /></>,
    analytics: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2" /></>,
    store: <><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18" /></>,
    logout: <><path d="M10 4H4v16h6M14 8l4 4-4 4M18 12H8" /></>,
  };

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
      {icons[name]}
    </svg>
  );
}

export default function ManagerLayout() {
  const { user, logout } = useAuth();
  const navigate         = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  function handleLogout() {
    logout();
    navigate('/manager/login', { replace: true });
  }

  const displayName = user?.first_name
    ? `${user.first_name} ${user.last_name || ''}`.trim()
    : user?.email?.split('@')[0] || 'Manager';

  return (
    <div className={`mgr-shell${collapsed ? ' mgr-shell--collapsed' : ''}`}>
      {/* ── Sidebar ── */}
      <aside className="mgr-sidebar">
        <div className="mgr-sidebar__brand">
          <Link to="/manager" className="mgr-brand">
            <span className="mgr-brand__icon">G</span>
            {!collapsed && <span className="mgr-brand__name">GoDrip</span>}
          </Link>
          <button
            className="mgr-collapse-btn"
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? 'Expand' : 'Collapse sidebar'}
          >
            {collapsed ? '›' : '‹'}
          </button>
        </div>

        <nav className="mgr-nav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `mgr-nav__item${isActive ? ' mgr-nav__item--active' : ''}`
              }
              title={collapsed ? item.label : undefined}
            >
              <span className="mgr-nav__icon"><NavIcon name={item.icon} /></span>
              {!collapsed && <span className="mgr-nav__label">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="mgr-sidebar__footer">
          <Link
            to="/"
            className="mgr-nav__item"
            title={collapsed ? 'View Store' : undefined}
          >
            <span className="mgr-nav__icon"><NavIcon name="store" /></span>
            {!collapsed && <span className="mgr-nav__label">View Store</span>}
          </Link>
          <button
            className="mgr-nav__item mgr-nav__item--logout"
            onClick={handleLogout}
            title={collapsed ? 'Logout' : undefined}
          >
            <span className="mgr-nav__icon"><NavIcon name="logout" /></span>
            {!collapsed && <span className="mgr-nav__label">Logout</span>}
          </button>
        </div>
      </aside>

      {/* ── Main content area ── */}
      <div className="mgr-content">
        {/* Top bar */}
        <header className="mgr-topbar">
          <div className="mgr-topbar__left">
            <h2 className="mgr-topbar__context">GoDrip Admin</h2>
          </div>
          <div className="mgr-topbar__right">
            <div className="mgr-user-chip">
              <span className="mgr-user-chip__avatar">
                {displayName.charAt(0).toUpperCase()}
              </span>
              <span className="mgr-user-chip__name">{displayName}</span>
              <span className="mgr-user-chip__badge">Manager</span>
            </div>
          </div>
        </header>

        <main className="mgr-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
