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

// ── Role card component ───────────────────────────────────────────────────────
function RoleCard({ id, icon, title, description, features, selected, onSelect, gradient }) {
  return (
    <button
      type="button"
      id={`role-${id}`}
      className={`role-card${selected ? ' role-card--selected' : ''}`}
      onClick={() => onSelect(id)}
      style={{ '--role-gradient': gradient }}
    >
      <div className="role-card__icon">{icon}</div>
      <h3 className="role-card__title">{title}</h3>
      <p className="role-card__desc">{description}</p>
      <ul className="role-card__features">
        {features.map((f) => <li key={f}>✓ {f}</li>)}
      </ul>
      {selected && <div className="role-card__check">✓ Selected</div>}
    </button>
  );
}

export default function RegisterPage() {
  const navigate    = useNavigate();
  const { register } = useAuth();

  const [role, setRole]     = useState('customer');
  const [step, setStep]     = useState(1); // 1 = role select, 2 = form
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
        role,
      });
      // Redirect based on role
      navigate(role === 'manager' ? '/manager' : '/', { replace: true });
    } catch (registerError) {
      setError(registerError?.response?.data?.detail || registerError?.message || 'Unable to register.');
    } finally {
      setSubmitting(false);
    }
  }

  // ── Step 1: Role selection ──────────────────────────────────────────────────
  if (step === 1) {
    return (
      <div className="auth-page auth-page--wide">
        <div className="role-select-page">
          <div className="role-select-header">
            <h1 className="role-select-title">Join NovaMart</h1>
            <p className="role-select-subtitle">Choose your account type to get started</p>
          </div>

          <div className="role-cards">
            <RoleCard
              id="customer"
              icon="🛍️"
              title="Shop as Customer"
              description="Browse thousands of products, track orders, and enjoy a personalised shopping experience."
              features={[
                'Browse & search products',
                'Wishlist & cart management',
                'Order tracking',
                'Reviews & ratings',
                'Saved addresses',
              ]}
              selected={role === 'customer'}
              onSelect={setRole}
              gradient="linear-gradient(135deg, #c9a96e22, #c9a96e08)"
            />
            <RoleCard
              id="manager"
              icon="🏪"
              title="Manage as Manager"
              description="Run your e-commerce store — manage products, orders, customers, inventory, and analytics."
              features={[
                'Full product & catalog management',
                'Order pipeline & status updates',
                'Customer insights & CLV',
                'Inventory & stock alerts',
                'Coupon & discount management',
                'Analytics & revenue reports',
              ]}
              selected={role === 'manager'}
              onSelect={setRole}
              gradient="linear-gradient(135deg, #6e8dc922, #6e8dc908)"
            />
          </div>

          <div className="role-select-action">
            <button
              id="continue-role-btn"
              className="button"
              style={{ padding: '0.875rem 3rem', fontSize: '1.05rem' }}
              onClick={() => setStep(2)}
            >
              Continue as {role === 'manager' ? 'Manager' : 'Customer'} →
            </button>
            <p className="auth-card__footer">
              Already have an account? <Link to="/login">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── Step 2: Registration form ───────────────────────────────────────────────
  return (
    <div className="auth-page">
      <section className="auth-card card">
        {/* Role pill */}
        <div className="role-pill">
          <span className="role-pill__icon">{role === 'manager' ? '🏪' : '🛍️'}</span>
          <span>{role === 'manager' ? 'Manager Account' : 'Customer Account'}</span>
          <button
            type="button"
            className="role-pill__change"
            onClick={() => setStep(1)}
          >
            Change
          </button>
        </div>

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
              Create {role === 'manager' ? 'Manager' : 'Customer'} Account
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
