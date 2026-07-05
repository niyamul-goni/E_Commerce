import { createContext, useContext, useEffect, useState } from 'react';
import { getCurrentUserRequest, loginRequest, registerRequest } from '../services/authService';
import { setAuthToken } from '../services/api';
import { supabase } from '../services/supabaseClient';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function hydrateFromSupabase() {
      const { data, error } = await supabase.auth.getSession();
      if (!active) return;

      const session = data.session;
      if (error || !session?.access_token) {
        setAuthToken(null);
        setUser(null);
        setLoading(false);
        return;
      }

      setAuthToken(session.access_token);
      try {
        const currentUser = await getCurrentUserRequest();
        if (!active) return;
        setUser(currentUser);
      } catch {
        await supabase.auth.signOut();
        setAuthToken(null);
        setUser(null);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    hydrateFromSupabase();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      if (!active) return;

      if (!session?.access_token) {
        setAuthToken(null);
        setUser(null);
        setLoading(false);
        return;
      }

      setAuthToken(session.access_token);
      try {
        const currentUser = await getCurrentUserRequest();
        if (!active) return;
        setUser(currentUser);
      } catch {
        setAuthToken(null);
        setUser(null);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
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
    supabase.auth.signOut();
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
