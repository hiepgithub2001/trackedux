/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import client from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user') || sessionStorage.getItem('user');
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);
  const queryClient = useQueryClient();

  // Sync user profile on load to get fresh data (like center details)
  useEffect(() => {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    if (token) {
      client.get('/auth/me').then(res => {
        setUser(res.data);
        const storage = localStorage.getItem('access_token') ? localStorage : sessionStorage;
        storage.setItem('user', JSON.stringify(res.data));
      }).catch(() => { });
    }
  }, []);

  const isAuthenticated = !!user;

  const login = useCallback(async (username, password, rememberMe = true) => {
    setLoading(true);
    try {
      const response = await client.post('/auth/login', { username, password });
      const { access_token, refresh_token, user: userData } = response.data;

      const storage = rememberMe ? localStorage : sessionStorage;
      storage.setItem('access_token', access_token);
      storage.setItem('refresh_token', refresh_token);
      storage.setItem('user', JSON.stringify(userData));
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
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('refresh_token');
      sessionStorage.removeItem('user');
      setUser(null);
      queryClient.clear();
    }
  }, [queryClient]);

  const updateProfile = useCallback(async (data) => {
    const res = await client.put('/auth/me', data);
    setUser(res.data);
    const storage = localStorage.getItem('user') ? localStorage : sessionStorage;
    storage.setItem('user', JSON.stringify(res.data));
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
