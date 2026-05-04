/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import client from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);

  // Sync user profile on load to get fresh data (like center details)
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      client.get('/auth/me').then(res => {
        setUser(res.data);
        localStorage.setItem('user', JSON.stringify(res.data));
      }).catch(() => {});
    }
  }, []);

  const isAuthenticated = !!user;

  const login = useCallback(async (username, password) => {
    setLoading(true);
    try {
      const response = await client.post('/auth/login', { username, password });
      const { access_token, refresh_token, user: userData } = response.data;

      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);

      return userData;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await client.post('/auth/logout');
    } catch {
      // Ignore logout errors
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setUser(null);
    }
  }, []);

  const updateProfile = useCallback(async (data) => {
    const res = await client.put('/auth/me', data);
    setUser(res.data);
    localStorage.setItem('user', JSON.stringify(res.data));
    return res.data;
  }, []);

  const updatePassword = useCallback(async (data) => {
    const res = await client.put('/auth/me/password', data);
    return res.data;
  }, []);

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    updateProfile,
    updatePassword,
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

export default AuthContext;
