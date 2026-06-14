import { createContext, useContext, useEffect, useState } from 'react';
import { getCurrentUserRequest, loginRequest, registerRequest } from '../services/authService';
import { getStoredToken, setAuthToken } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      setLoading(false);
      return;
    }

    setAuthToken(token);
    getCurrentUserRequest()
      .then((currentUser) => {
        setUser(currentUser);
      })
      .catch(() => {
        setAuthToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  async function hydrateSession(token) {
    setAuthToken(token);
    const currentUser = await getCurrentUserRequest();
    setUser(currentUser);
    setLoading(false);
    return currentUser;
  }

  async function login(email, password) {
    const response = await loginRequest(email, password);
    return hydrateSession(response.access_token);
  }

  async function register(payload) {
    const response = await registerRequest(payload);
    return hydrateSession(response.access_token);
  }

  function logout() {
    setAuthToken(null);
    setUser(null);
  }

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    isAdmin: Boolean(user?.is_admin),
    login,
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
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
