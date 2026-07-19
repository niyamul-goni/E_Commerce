import { useEffect, useState } from 'react';
import Button from '../components/Button';
import ErrorState from '../components/ErrorState';
import FormField from '../components/FormField';
import Loader from '../components/Loader';
import PageHeader from '../components/PageHeader';
import {
  createAddressRequest,
  deleteAddressRequest,
  getAddressesRequest,
  getMyProfileRequest,
  updateAddressRequest,
  updateMyProfileRequest,
} from '../services/commerceService';

// ── Address Form ──────────────────────────────────────────────────────────────
function AddressForm({ initial = {}, onSave, onCancel }) {
  const [form, setForm] = useState({
    label: initial.label || 'Home',
    recipient_name: initial.recipient_name || '',
    phone: initial.phone || '',
    line1: initial.line1 || '',
    line2: initial.line2 || '',
    city: initial.city || '',
    state: initial.state || '',
    postal_code: initial.postal_code || '',
    country: initial.country || 'Bangladesh',
    is_default: initial.is_default || false,
  });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');

  function update(field) {
    return (e) => setForm({ ...form, [field]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.line1.trim() || !form.city.trim()) {
      setErr('Street address and city are required.');
      return;
    }
    setSaving(true);
    setErr('');
    try {
      await onSave(form);
    } catch (ex) {
      setErr(ex?.response?.data?.detail || 'Could not save address.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="address-form card" onSubmit={handleSubmit}>
      {err && <p className="inline-message">{err}</p>}
      <div className="form-row-2">
        <FormField
          label="Label"
          value={form.label}
          onChange={update('label')}
          placeholder="Home, Work, …"
        />
        <FormField
          label="Recipient Name"
          value={form.recipient_name}
          onChange={update('recipient_name')}
          placeholder="Full name"
        />
      </div>
      <FormField
        label="Street Address"
        value={form.line1}
        onChange={update('line1')}
        placeholder="House / flat, road, area"
      />
      <FormField
        label="Apartment / Floor (optional)"
        value={form.line2}
        onChange={update('line2')}
        placeholder="Apartment 3B"
      />
      <div className="form-row-3">
        <FormField label="City" value={form.city} onChange={update('city')} placeholder="Dhaka" />
        <FormField label="State / Division" value={form.state} onChange={update('state')} placeholder="Dhaka Division" />
        <FormField label="Postal Code" value={form.postal_code} onChange={update('postal_code')} placeholder="1200" />
      </div>
      <div className="form-row-2">
        <FormField label="Country" value={form.country} onChange={update('country')} placeholder="Bangladesh" />
        <FormField label="Phone" value={form.phone} onChange={update('phone')} placeholder="+880…" />
      </div>
      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={form.is_default}
          onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
        />
        <span>Set as default address</span>
      </label>
      <div className="form-actions">
        <Button type="submit" loading={saving}>Save Address</Button>
        {onCancel && (
          <button type="button" className="button button--secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

// ── Main Profile Page ─────────────────────────────────────────────────────────

export default function ProfilePage() {
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState('');
  const [profile, setProfile]         = useState(null);
  const [addresses, setAddresses]     = useState([]);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg]   = useState('');
  const [showAddAddr, setShowAddAddr] = useState(false);
  const [editAddr, setEditAddr]       = useState(null); // address object being edited

  const [profileForm, setProfileForm] = useState({
    first_name: '',
    last_name: '',
    phone: '',
  });

  async function loadAll() {
    try {
      setLoading(true);
      setError('');
      const [prof, addrs] = await Promise.all([
        getMyProfileRequest(),
        getAddressesRequest(),
      ]);
      setProfile(prof);
      setAddresses(addrs);
      setProfileForm({
        first_name: prof.first_name || '',
        last_name:  prof.last_name  || '',
        phone:      prof.phone      || '',
      });
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load profile.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadAll(); }, []);

  async function handleProfileSave(e) {
    e.preventDefault();
    setProfileSaving(true);
    setProfileMsg('');
    try {
      await updateMyProfileRequest(profileForm);
      setProfileMsg('✓ Profile updated!');
    } catch (err) {
      setProfileMsg(err?.response?.data?.detail || 'Could not update profile.');
    } finally {
      setProfileSaving(false);
    }
  }

  async function handleAddAddress(form) {
    await createAddressRequest(form);
    setShowAddAddr(false);
    const addrs = await getAddressesRequest();
    setAddresses(addrs);
  }

  async function handleUpdateAddress(form) {
    await updateAddressRequest(editAddr.id, form);
    setEditAddr(null);
    const addrs = await getAddressesRequest();
    setAddresses(addrs);
  }

  async function handleDeleteAddress(id) {
    if (!window.confirm('Remove this address?')) return;
    await deleteAddressRequest(id);
    setAddresses((prev) => prev.filter((a) => a.id !== id));
  }

  if (loading) return <Loader label="Loading profile" />;
  if (error)   return <ErrorState message={error} onRetry={loadAll} />;

  return (
    <div className="page-stack">
      <PageHeader title="My Profile" subtitle="Manage your personal information and saved addresses." />

      {/* ── Personal Info ── */}
      <section className="profile-section card">
        <h2 className="profile-section__title">Personal Information</h2>
        <p className="muted" style={{ marginBottom: '1.5rem' }}>Email: {profile?.email}</p>
        <form onSubmit={handleProfileSave}>
          <div className="form-row-2">
            <FormField
              label="First Name"
              value={profileForm.first_name}
              onChange={(e) => setProfileForm({ ...profileForm, first_name: e.target.value })}
              placeholder="Your first name"
            />
            <FormField
              label="Last Name"
              value={profileForm.last_name}
              onChange={(e) => setProfileForm({ ...profileForm, last_name: e.target.value })}
              placeholder="Your last name"
            />
          </div>
          <FormField
            label="Phone"
            value={profileForm.phone}
            onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
            placeholder="+880…"
          />
          {profileMsg && (
            <p className={`inline-message${profileMsg.startsWith('✓') ? ' inline-message--success' : ''}`}>
              {profileMsg}
            </p>
          )}
          <Button type="submit" loading={profileSaving}>Save Changes</Button>
        </form>
      </section>

      {/* ── Addresses ── */}
      <section className="profile-section">
        <div className="profile-section__header">
          <h2 className="profile-section__title">Saved Addresses</h2>
          {!showAddAddr && !editAddr && (
            <button
              id="add-address-btn"
              className="button button--secondary"
              onClick={() => setShowAddAddr(true)}
            >
              + Add Address
            </button>
          )}
        </div>

        {showAddAddr && (
          <AddressForm
            onSave={handleAddAddress}
            onCancel={() => setShowAddAddr(false)}
          />
        )}

        {editAddr && (
          <div>
            <h3 style={{ marginBottom: '1rem', color: 'var(--brand)' }}>
              Editing: {editAddr.label}
            </h3>
            <AddressForm
              initial={editAddr}
              onSave={handleUpdateAddress}
              onCancel={() => setEditAddr(null)}
            />
          </div>
        )}

        {addresses.length === 0 && !showAddAddr ? (
          <p className="muted">No saved addresses yet. Add one to speed up checkout.</p>
        ) : (
          <div className="addresses-grid">
            {addresses.map((addr) => (
              <article key={addr.id} className={`address-card card${addr.is_default ? ' address-card--default' : ''}`}>
                {addr.is_default && <div className="address-card__badge">Default</div>}
                <p className="address-card__label">{addr.label}</p>
                {addr.recipient_name && <p className="address-card__name">{addr.recipient_name}</p>}
                <p className="address-card__lines">
                  {addr.line1}
                  {addr.line2 && <>, {addr.line2}</>}
                  <br />
                  {addr.city}{addr.state && `, ${addr.state}`} {addr.postal_code}
                  <br />
                  {addr.country}
                </p>
                {addr.phone && <p className="address-card__phone">{addr.phone}</p>}
                <div className="address-card__actions">
                  <button
                    className="button button--secondary"
                    id={`edit-addr-${addr.id}`}
                    onClick={() => { setShowAddAddr(false); setEditAddr(addr); }}
                  >
                    Edit
                  </button>
                  <button
                    className="button button--danger"
                    id={`delete-addr-${addr.id}`}
                    onClick={() => handleDeleteAddress(addr.id)}
                  >
                    Remove
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
