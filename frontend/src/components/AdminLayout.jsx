import { NavLink, Outlet, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Button from './Button';

export default function AdminLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar card">
        <Link to="/admin" className="admin-sidebar__brand">
          Admin Panel
        </Link>
        <p className="admin-sidebar__user">{user?.email}</p>
        <nav className="admin-sidebar__nav">
          <NavLink to="/admin" end>
            Dashboard
          </NavLink>
          <NavLink to="/admin/products">Products</NavLink>
          <NavLink to="/admin/categories">Categories</NavLink>
          <NavLink to="/admin/suppliers">Suppliers</NavLink>
          <NavLink to="/admin/orders">Orders</NavLink>
        </nav>
        <Button variant="secondary" onClick={logout}>
          Logout
        </Button>
      </aside>

      <section className="admin-content">
        <Outlet />
      </section>
    </div>
  );
}
