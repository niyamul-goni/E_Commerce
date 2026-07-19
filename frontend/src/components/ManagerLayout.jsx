import { useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV_ITEMS = [
  { to: '/manager',           icon: '📊', label: 'Dashboard',  end: true },
  { to: '/manager/products',  icon: '📦', label: 'Products' },
  { to: '/manager/orders',    icon: '🛒', label: 'Orders' },
  { to: '/manager/customers', icon: '👥', label: 'Customers' },
  { to: '/manager/inventory', icon: '🏭', label: 'Inventory' },
  { to: '/manager/coupons',   icon: '🎟️', label: 'Coupons' },
  { to: '/manager/reviews',   icon: '⭐', label: 'Reviews' },
  { to: '/manager/categories',icon: '🗂️', label: 'Categories' },
  { to: '/manager/suppliers', icon: '🚚', label: 'Suppliers' },
  { to: '/manager/analytics', icon: '📈', label: 'Analytics' },
];

export default function ManagerLayout() {
  const { user, logout } = useAuth();
  const navigate         = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
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
            <span className="mgr-brand__icon">🏪</span>
            {!collapsed && <span className="mgr-brand__name">NovaMart</span>}
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
              <span className="mgr-nav__icon">{item.icon}</span>
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
            <span className="mgr-nav__icon">🌐</span>
            {!collapsed && <span className="mgr-nav__label">View Store</span>}
          </Link>
          <button
            className="mgr-nav__item mgr-nav__item--logout"
            onClick={handleLogout}
            title={collapsed ? 'Logout' : undefined}
          >
            <span className="mgr-nav__icon">⎋</span>
            {!collapsed && <span className="mgr-nav__label">Logout</span>}
          </button>
        </div>
      </aside>

      {/* ── Main content area ── */}
      <div className="mgr-content">
        {/* Top bar */}
        <header className="mgr-topbar">
          <div className="mgr-topbar__left">
            <h2 className="mgr-topbar__context">Manager Panel</h2>
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
