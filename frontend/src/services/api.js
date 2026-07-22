import axios from 'axios';

export const TOKEN_KEY = 'ecommerce_token';
// In development, Vite proxies /api to FastAPI. Keeping the browser request
// same-origin avoids localhost/127.0.0.1 CORS and IPv4/IPv6 mismatches.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    return;
  }

  localStorage.removeItem(TOKEN_KEY);
  delete api.defaults.headers.common.Authorization;
}

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}
