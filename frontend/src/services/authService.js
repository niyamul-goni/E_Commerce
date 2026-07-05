import { api } from './api';
import { supabase } from './supabaseClient';

export async function registerRequest(payload) {
  // Register through the backend API which uses the Supabase service-role key
  // to create the user with auto-confirmed email, then logs them in.
  const response = await api.post('/auth/register', payload);
  return response.data;
}

export async function loginRequest(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    throw error;
  }

  if (!data.session?.access_token) {
    throw new Error('Unable to establish a Supabase session.');
  }

  return { access_token: data.session.access_token };
}

export async function getCurrentUserRequest() {
  const { data } = await api.get('/auth/me');
  return data;
}
