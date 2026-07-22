import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Loader from '../components/Loader';

export default function AdminRoute({ children }) {
  const { isAuthenticated, isAdmin, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <Loader label="Checking admin access" />;
  }

  if (!isAuthenticated || !isAdmin) {
    return <Navigate to="/manager/login" replace state={{ from: location }} />;
  }

  return children;
}
