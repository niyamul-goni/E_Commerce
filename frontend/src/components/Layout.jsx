import { NavLink, Outlet, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from './Button';

export default function Layout() {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="site-header__brand">
          <Link to="/" className="brand-mark">
            NovaMart
          </Link>
          <span className="brand-tag">Commerce OS</span>
        </div>

        <nav className="site-nav">
          <NavLink to="/" end>
            Home
          </NavLink>
          <NavLink to="/products">Products</NavLink>
          <NavLink to="/orders">Orders</NavLink>
          <NavLink to="/reviews">Reviews</NavLink>
          <NavLink to="/cart">Cart</NavLink>
          {isAdmin ? <NavLink to="/admin">Admin</NavLink> : null}
        </nav>

        <div className="site-header__actions">
          {isAuthenticated ? (
            <>
              <span className="user-chip">{user?.first_name} {user?.last_name}</span>
              <Button variant="secondary" onClick={logout}>
                Logout
              </Button>
            </>
          ) : (
            <>
              <Link to="/login" className="button button--secondary">
                Login
              </Link>
              <Link to="/register" className="button">
                Register
              </Link>
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
