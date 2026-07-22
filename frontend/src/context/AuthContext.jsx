import { createContext, useContext, useEffect, useState } from 'react';
import {
  getCurrentUserRequest,
  loginRequest,
  managerLoginRequest,
  registerRequest,
} from '../services/authService';
import { getStoredToken, setAuthToken } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function hydrateFromStorage() {
      const token = getStoredToken();
      if (!token) { setLoading(false); return; }

      setAuthToken(token);
      try {
        const currentUser = await getCurrentUserRequest();
        if (!active) return;
        setUser(currentUser);
      } catch {
        setAuthToken(null);
        setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    }

    hydrateFromStorage();
    return () => { active = false; };
  }, []);

  async function hydrateSession(token) {
    setAuthToken(token);
    try {
      const currentUser = await getCurrentUserRequest();
      setUser(currentUser);
      setLoading(false);
      return currentUser;
    } catch (err) {
      setAuthToken(null);
      setUser(null);
      setLoading(false);
      throw err;
    }
  }

  async function login(email, password) {
    const response = await loginRequest(email, password);
    return hydrateSession(response.access_token);
  }

  async function managerLogin(email, password) {
    const response = await managerLoginRequest(email, password);
    const currentUser = await hydrateSession(response.access_token);
    if (!currentUser?.is_admin) {
      setAuthToken(null);
      setUser(null);
      throw new Error('This account does not have manager access.');
    }
    return currentUser;
  }

  async function register(payload) {
    const response = await registerRequest(payload);
    return hydrateSession(response.access_token);
  }

  function logout() {
    setAuthToken(null);
    setUser(null);
  }

  const isManager = Boolean(user?.is_admin);

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    isAdmin:         isManager,  // backward compat
    isManager,                   // semantic alias
    role:            isManager ? 'manager' : 'customer',
    login,
    managerLogin,
    register,
    logout,
    setUser,
    refreshUser: async () => {
      const currentUser = await getCurrentUserRequest();
      setUser(currentUser);
      return currentUser;
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
}
