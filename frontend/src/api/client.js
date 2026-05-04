import axios from 'axios';

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
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
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

      const refreshToken = localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefresh } = res.data;
          const storage = localStorage.getItem('refresh_token') ? localStorage : sessionStorage;
          storage.setItem('access_token', access_token);
          storage.setItem('refresh_token', newRefresh);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return client(originalRequest);
        } catch (refreshError) {
          // Refresh failed — clear tokens and redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          sessionStorage.removeItem('access_token');
          sessionStorage.removeItem('refresh_token');
          sessionStorage.removeItem('user');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('refresh_token');
      sessionStorage.removeItem('user');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  },
);

export default client;
