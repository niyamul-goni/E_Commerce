import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import ErrorState from '../components/ErrorState';
import FormField from '../components/FormField';
import PageHeader from '../components/PageHeader';
import { useAuth } from '../context/AuthContext';
import { getCustomerAuthErrorMessage } from '../services/authService';
import { validateEmail, validatePassword, createEmptyErrors } from '../utils/validators';

export default function LoginPage() {
  const navigate  = useNavigate();
  const location  = useLocation();
  const { login, logout } = useAuth();
  const [form, setForm]         = useState({ email: '', password: '' });
  const [errors, setErrors]     = useState(createEmptyErrors());
  const [submitting, setSubmitting] = useState(false);
  const [error, setError]       = useState('');

  function validateForm() {
    const nextErrors = {
      email:    validateEmail(form.email),
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
      const loggedInUser = await login(form.email, form.password);

      // Role-based redirect
      if (loggedInUser?.is_admin) {
        logout();
        navigate('/manager/login', { replace: true });
      } else {
        const destination = location.state?.from?.pathname || '/';
        navigate(destination, { replace: true });
      }
    } catch (loginError) {
      setError(getCustomerAuthErrorMessage(loginError));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-card card">
        <PageHeader title="Welcome back" subtitle="Sign in to continue." />
        {error ? <ErrorState title="Login failed" message={error} /> : null}
        <form className="form-stack" onSubmit={handleSubmit}>
          <FormField
            label="Email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            error={errors.email}
            placeholder="you@example.com"
          />
          <FormField
            label="Password"
            type="password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            error={errors.password}
            placeholder="Enter your password"
          />
          <Button type="submit" loading={submitting}>Sign in</Button>
        </form>
        <p className="auth-card__footer">
          New here? <Link to="/register">Create an account</Link>
        </p>
        <p className="auth-card__footer auth-card__footer--manager">
          Store staff? <Link to="/manager/login">Use manager login</Link>
        </p>
      </section>
    </div>
  );
}
