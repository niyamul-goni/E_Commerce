import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import ErrorState from '../components/ErrorState';
import FormField from '../components/FormField';
import PageHeader from '../components/PageHeader';
import { useAuth } from '../context/AuthContext';
import {
  createEmptyErrors,
  validateEmail,
  validatePassword,
  validateRequired,
} from '../utils/validators';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
  });
  const [errors, setErrors] = useState(createEmptyErrors());
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  function validateForm() {
    const nextErrors = {
      first_name: validateRequired(form.first_name, 'First name'),
      last_name: validateRequired(form.last_name, 'Last name'),
      email: validateEmail(form.email),
      password: validatePassword(form.password),
      confirm_password: form.password === form.confirm_password ? '' : 'Passwords do not match',
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
      await register({
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        phone: form.phone || null,
        password: form.password,
      });
      navigate('/', { replace: true });
    } catch (registerError) {
      setError(registerError?.response?.data?.detail || 'Unable to register.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-card card">
        <PageHeader title="Create account" subtitle="Register to place orders and write reviews." />
        {error ? <ErrorState title="Registration failed" message={error} /> : null}
        <form className="form-grid" onSubmit={handleSubmit}>
          <FormField
            label="First name"
            value={form.first_name}
            onChange={(event) => setForm({ ...form, first_name: event.target.value })}
            error={errors.first_name}
            placeholder="Aarav"
          />
          <FormField
            label="Last name"
            value={form.last_name}
            onChange={(event) => setForm({ ...form, last_name: event.target.value })}
            error={errors.last_name}
            placeholder="Sharma"
          />
          <FormField
            label="Email"
            type="email"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            error={errors.email}
            placeholder="you@example.com"
          />
          <FormField
            label="Phone"
            value={form.phone}
            onChange={(event) => setForm({ ...form, phone: event.target.value })}
            placeholder="Optional"
          />
          <FormField
            label="Password"
            type="password"
            value={form.password}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
            error={errors.password}
            placeholder="At least 8 characters"
          />
          <FormField
            label="Confirm password"
            type="password"
            value={form.confirm_password}
            onChange={(event) => setForm({ ...form, confirm_password: event.target.value })}
            error={errors.confirm_password}
            placeholder="Repeat your password"
          />
          <div className="form-grid__full">
            <Button type="submit" loading={submitting}>
              Register
            </Button>
          </div>
        </form>
        <p className="auth-card__footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </section>
    </div>
  );
}
