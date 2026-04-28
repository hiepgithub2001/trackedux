import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { message } from 'antd';

export default function SuperadminRoute({ children }) {
  const { isAuthenticated, user } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (user?.role !== 'superadmin') {
    message.error("Access Denied: Superadmin only");
    return <Navigate to="/" replace />;
  }

  return children;
}
