import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import Button from '../../components/Button';
import ErrorState from '../../components/ErrorState';
import FormField from '../../components/FormField';
import { useAuth } from '../../context/AuthContext';
import { createEmptyErrors, validateEmail, validatePassword } from '../../utils/validators';

export default function ManagerLoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    isAuthenticated,
    isManager,
    loading,
    logout,
    managerLogin,
  } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState(createEmptyErrors());
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!loading && isAuthenticated && isManager) {
    const requestedPath = location.state?.from?.pathname;
    const destination = requestedPath?.startsWith('/manager') && requestedPath !== '/manager/login'
      ? requestedPath
      : '/manager';
    return <Navigate to={destination} replace />;
  }

  function validateForm() {
    const nextErrors = {
      email: validateEmail(form.email),
      password: validatePassword(form.password),
    };
    setErrors(nextErrors);
    return !Object.values(nextErrors).some(Boolean);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!validateForm()) return;

    try {
      setSubmitting(true);
      setError('');
      await managerLogin(form.email, form.password);
      const requestedPath = location.state?.from?.pathname;
      const destination = requestedPath?.startsWith('/manager') && requestedPath !== '/manager/login'
        ? requestedPath
        : '/manager';
      navigate(destination, { replace: true });
    } catch (loginError) {
      setError(
        loginError?.response?.data?.detail
        || loginError?.message
        || 'Unable to sign in to the manager console.',
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="manager-login-page">
      <section className="manager-login-intro" aria-label="Manager console introduction">
        <Link to="/" className="manager-login-brand">GoDrip</Link>
        <span className="manager-login-kicker">Operations console</span>
        <h1>Manage the store from one protected workspace.</h1>
        <p>Products, product images, inventory, orders, customers, coupons, reviews, categories, suppliers, and analytics stay separate from the customer storefront.</p>
        <div className="manager-login-security">
          <span aria-hidden="true">🔒</span>
          <span>Only accounts already approved as managers can enter.</span>
        </div>
      </section>

      <section className="manager-login-panel">
        <div className="manager-login-card">
          <div>
            <span className="manager-login-kicker">Staff access</span>
            <h2>Manager sign in</h2>
            <p>Use your authorized manager credentials.</p>
          </div>

          {!loading && isAuthenticated && !isManager ? (
            <div className="manager-session-warning">
              <strong>A customer is currently signed in.</strong>
              <p>Sign out of that session before entering a manager account.</p>
              <Button type="button" variant="secondary" onClick={logout}>Sign out customer</Button>
            </div>
          ) : (
            <>
              {error ? <ErrorState title="Manager login failed" message={error} /> : null}
              <form className="form-stack" onSubmit={handleSubmit}>
                <FormField
                  label="Manager email"
                  type="email"
                  autoComplete="username"
                  value={form.email}
                  onChange={(event) => setForm({ ...form, email: event.target.value })}
                  error={errors.email}
                  placeholder="manager@example.com"
                />
                <FormField
                  label="Password"
                  type="password"
                  autoComplete="current-password"
                  value={form.password}
                  onChange={(event) => setForm({ ...form, password: event.target.value })}
                  error={errors.password}
                  placeholder="Enter your password"
                />
                <Button type="submit" loading={submitting}>Enter manager console</Button>
              </form>
            </>
          )}

          <div className="manager-login-links">
            <Link to="/">← Return to storefront</Link>
            <Link to="/login">Customer login</Link>
          </div>
        </div>
      </section>
    </main>
  );
}
