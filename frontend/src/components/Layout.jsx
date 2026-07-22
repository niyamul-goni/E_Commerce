import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Layout() {
  const { user, isAuthenticated, isManager, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  const displayName = user?.first_name || user?.email?.split('@')[0] || 'Account';

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="site-header__brand">
          <Link to="/" className="brand-mark">GoDrip</Link>
          <span className="brand-tag">Commerce</span>
        </div>

        <nav className="site-nav">
          <NavLink to="/" end>Home</NavLink>
          <NavLink to="/products">Products</NavLink>
          {isAuthenticated && !isManager && (
            <>
              <NavLink to="/cart">Cart</NavLink>
              <NavLink to="/orders">Orders</NavLink>
              <NavLink to="/wishlist">Wishlist</NavLink>
              <NavLink to="/reviews">Reviews</NavLink>
            </>
          )}
          {/* Managers get a shortcut to their panel */}
          {isManager && (
            <NavLink to="/manager">Manager Panel ↗</NavLink>
          )}
        </nav>

        <div className="site-header__actions">
          {isAuthenticated ? (
            <>
              {!isManager && (
                <Link to="/profile" className="user-chip">
                  {displayName}
                </Link>
              )}
              <button className="button button--secondary" onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/manager/login" className="manager-entry-link">Manager</Link>
              <Link to="/login"    className="button button--secondary">Login</Link>
              <Link to="/register" className="button">Register</Link>
            </>
          )}
        </div>
      </header>

      <main className="site-main">
        <Outlet />
      </main>
    </div>
  );
}
