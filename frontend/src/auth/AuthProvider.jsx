import { useState, useCallback, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { setPersistentItem, getPersistentItem, removePersistentItem, setSessionItem, getSessionItem, removeSessionItem } from '../utils/storage';
import client from '../api/client';
import { AuthContext } from './AuthContext';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = getPersistentItem('user') || getSessionItem('user');
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);
  const queryClient = useQueryClient();

  // Sync user profile on load to get fresh data (like center details)
  useEffect(() => {
    const token = getPersistentItem('access_token') || getSessionItem('access_token');
    if (token) {
      client.get('/auth/me').then(res => {
        setUser(res.data);
        if (getPersistentItem('access_token')) {
          setPersistentItem('user', JSON.stringify(res.data));
        } else {
          setSessionItem('user', JSON.stringify(res.data));
        }
      }).catch(() => { });
    }
  }, []);

  const isAuthenticated = !!user;

  const login = useCallback(async (username, password, rememberMe = true) => {
    setLoading(true);
    try {
      const response = await client.post('/auth/login', { username, password });
      const { access_token, refresh_token, user: userData } = response.data;

      if (rememberMe) {
        setPersistentItem('access_token', access_token);
        setPersistentItem('refresh_token', refresh_token);
        setPersistentItem('user', JSON.stringify(userData));
      } else {
        setSessionItem('access_token', access_token);
        setSessionItem('refresh_token', refresh_token);
        setSessionItem('user', JSON.stringify(userData));
      }
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
      removePersistentItem('access_token');
      removePersistentItem('refresh_token');
      removePersistentItem('user');
      removeSessionItem('access_token');
      removeSessionItem('refresh_token');
      removeSessionItem('user');
      setUser(null);
      queryClient.clear();
    }
  }, [queryClient]);

  const updateProfile = useCallback(async (data) => {
    const res = await client.put('/auth/me', data);
    setUser(res.data);
    if (getPersistentItem('user')) {
      setPersistentItem('user', JSON.stringify(res.data));
    } else {
      setSessionItem('user', JSON.stringify(res.data));
    }
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
