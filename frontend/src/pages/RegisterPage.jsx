import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import ErrorState from '../components/ErrorState';
import FormField from '../components/FormField';
import { useAuth } from '../context/AuthContext';
import {
  createEmptyErrors,
  validateEmail,
  validatePassword,
  validatePhone,
  validateRequired,
} from '../utils/validators';

export default function RegisterPage() {
  const navigate    = useNavigate();
  const { register } = useAuth();

  const [form, setForm]     = useState({
    first_name: '', last_name: '', email: '', phone: '', password: '', confirm_password: '',
  });
  const [errors, setErrors]     = useState(createEmptyErrors());
  const [submitting, setSubmitting] = useState(false);
  const [error, setError]       = useState('');

  function validateForm() {
    const nextErrors = {
      first_name:       validateRequired(form.first_name, 'First name'),
      last_name:        validateRequired(form.last_name, 'Last name'),
      email:            validateEmail(form.email),
      phone:            validatePhone(form.phone),
      password:         validatePassword(form.password),
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
        last_name:  form.last_name,
        email:      form.email,
        phone:      form.phone || null,
        password:   form.password,
      });
      navigate('/', { replace: true });
    } catch (registerError) {
      setError(registerError?.response?.data?.detail || registerError?.message || 'Unable to register.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-card card">
        <h2 className="auth-card__title">Create your account</h2>

        {error ? <ErrorState title="Registration failed" message={error} /> : null}
        <form className="form-grid" onSubmit={handleSubmit}>
          <FormField
            label="First name" value={form.first_name}
            onChange={(e) => setForm({ ...form, first_name: e.target.value })}
            error={errors.first_name} placeholder="Aarav"
          />
          <FormField
            label="Last name" value={form.last_name}
            onChange={(e) => setForm({ ...form, last_name: e.target.value })}
            error={errors.last_name} placeholder="Sharma"
          />
          <FormField
            label="Email" type="email" value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            error={errors.email} placeholder="you@example.com"
          />
          <FormField
            label="Phone (11 digits)" type="tel" value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value.replace(/\D/g, '').slice(0, 11) })}
            error={errors.phone} placeholder="01775529619"
            maxLength={11}
          />

          <FormField
            label="Password" type="password" value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            error={errors.password} placeholder="At least 8 characters"
          />
          <FormField
            label="Confirm password" type="password" value={form.confirm_password}
            onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
            error={errors.confirm_password} placeholder="Repeat your password"
          />
          <div className="form-grid__full">
            <Button type="submit" loading={submitting}>
              Create Customer Account
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
