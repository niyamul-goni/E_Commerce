import { api } from './api';

export async function registerRequest(payload) {
  // Register through the backend API which uses the Supabase service-role key
  // to create the user with auto-confirmed email, then logs them in.
  const response = await api.post('/auth/register', payload);
  return response.data;
}

export async function loginRequest(email, password) {
  // The backend /auth/login uses OAuth2PasswordRequestForm which requires
  // application/x-www-form-urlencoded, NOT JSON.
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  const response = await api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return response.data;
}

export async function getCurrentUserRequest() {
  const { data } = await api.get('/auth/me');
  return data;
}
