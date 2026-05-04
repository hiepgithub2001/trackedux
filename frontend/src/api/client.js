import axios from 'axios';
import { setPersistentItem, getPersistentItem, removePersistentItem, setSessionItem, getSessionItem, removeSessionItem } from '../utils/storage';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor — attach JWT token
client.interceptors.request.use(
  (config) => {
    const token = getPersistentItem('access_token') || getSessionItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Response interceptor — handle 401 and token refresh
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Do not handle 401 globally for the login endpoint
      if (originalRequest.url?.includes('/auth/login')) {
        return Promise.reject(error);
      }

      const refreshToken = getPersistentItem('refresh_token') || getSessionItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefresh } = res.data;
          if (getPersistentItem('refresh_token')) {
            setPersistentItem('access_token', access_token);
            setPersistentItem('refresh_token', newRefresh);
          } else {
            setSessionItem('access_token', access_token);
            setSessionItem('refresh_token', newRefresh);
          }

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return client(originalRequest);
        } catch (refreshError) {
          // If it's a network error (like waking up PWA without internet), do NOT wipe tokens
          if (!refreshError.response) {
            return Promise.reject(refreshError);
          }
          
          // Refresh failed with a true server error (e.g. 401) — clear tokens and redirect to login
          removePersistentItem('access_token');
          removePersistentItem('refresh_token');
          removePersistentItem('user');
          removeSessionItem('access_token');
          removeSessionItem('refresh_token');
          removeSessionItem('user');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      removePersistentItem('access_token');
      removePersistentItem('refresh_token');
      removePersistentItem('user');
      removeSessionItem('access_token');
      removeSessionItem('refresh_token');
      removeSessionItem('user');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  },
);

export default client;
