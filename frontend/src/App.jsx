import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import ManagerLayout from './components/ManagerLayout';
import ProtectedRoute from './routes/ProtectedRoute';
import AdminRoute from './routes/AdminRoute';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProductsPage from './pages/ProductsPage';
import ProductDetailsPage from './pages/ProductDetailsPage';
import CartPage from './pages/CartPage';
import CheckoutPage from './pages/CheckoutPage';
import OrdersPage from './pages/OrdersPage';
import ReviewsPage from './pages/ReviewsPage';
import WishlistPage from './pages/WishlistPage';
import ProfilePage from './pages/ProfilePage';
// Manager pages
import ManagerDashboardPage  from './pages/manager/ManagerDashboardPage';
import ManagerProductsPage   from './pages/manager/ManagerProductsPage';
import ManagerOrdersPage     from './pages/manager/ManagerOrdersPage';
import ManagerCustomersPage  from './pages/manager/ManagerCustomersPage';
import ManagerInventoryPage  from './pages/manager/ManagerInventoryPage';
import ManagerCouponsPage    from './pages/manager/ManagerCouponsPage';
import ManagerReviewsPage    from './pages/manager/ManagerReviewsPage';
import ManagerCategoriesPage from './pages/manager/ManagerCategoriesPage';
import ManagerSuppliersPage  from './pages/manager/ManagerSuppliersPage';
import ManagerAnalyticsPage  from './pages/manager/ManagerAnalyticsPage';
import ManagerLoginPage      from './pages/manager/ManagerLoginPage';

export default function App() {
  return (
    <Routes>
      {/* ── Customer Routes ── */}
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="products" element={<ProductsPage />} />
        <Route path="products/:productId" element={<ProductDetailsPage />} />
        <Route path="login"    element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />

        <Route path="cart"     element={<ProtectedRoute><CartPage /></ProtectedRoute>} />
        <Route path="checkout" element={<ProtectedRoute><CheckoutPage /></ProtectedRoute>} />
        <Route path="orders"   element={<ProtectedRoute><OrdersPage /></ProtectedRoute>} />
        <Route path="reviews"  element={<ProtectedRoute><ReviewsPage /></ProtectedRoute>} />
        <Route path="wishlist" element={<ProtectedRoute><WishlistPage /></ProtectedRoute>} />
        <Route path="profile"  element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
      </Route>

      {/* ── Manager Routes ── */}
      <Route path="manager/login" element={<ManagerLoginPage />} />
      <Route
        path="manager"
        element={<AdminRoute><ManagerLayout /></AdminRoute>}
      >
        <Route index                element={<ManagerDashboardPage />} />
        <Route path="products"      element={<ManagerProductsPage />} />
        <Route path="orders"        element={<ManagerOrdersPage />} />
        <Route path="customers"     element={<ManagerCustomersPage />} />
        <Route path="inventory"     element={<ManagerInventoryPage />} />
        <Route path="coupons"       element={<ManagerCouponsPage />} />
        <Route path="reviews"       element={<ManagerReviewsPage />} />
        <Route path="categories"    element={<ManagerCategoriesPage />} />
        <Route path="suppliers"     element={<ManagerSuppliersPage />} />
        <Route path="analytics"     element={<ManagerAnalyticsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
