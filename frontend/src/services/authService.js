import { api } from './api';

export const CUSTOMER_AUTH_FALLBACK =
  'Something went wrong. Please try again later.';

export function getCustomerAuthErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  return typeof detail === 'string' && detail.trim()
    ? detail
    : CUSTOMER_AUTH_FALLBACK;
}

export async function registerRequest(payload) {
  // Register through the backend API which uses the Supabase service-role key
  // to create the user with auto-confirmed email, then logs them in.
  const response = await api.post('/auth/register', payload);
  return response.data;
}

export async function loginRequest(email, password) {
  // The customer-only backend login uses OAuth2PasswordRequestForm, which requires
  // application/x-www-form-urlencoded, NOT JSON.
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const response = await api.post('/auth/customer-login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return response.data;
}

export async function managerLoginRequest(email, password) {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const response = await api.post('/auth/manager-login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return response.data;
}

export async function getCurrentUserRequest() {
  const { data } = await api.get('/auth/me');
  return data;
}
