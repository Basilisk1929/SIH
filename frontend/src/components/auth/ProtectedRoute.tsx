import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { UserRole } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
  children?: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ allowedRoles, children }) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#070a12' }}>
        <LoadingSpinner message="Verifying security credentials & cryptographic token..." size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: '#f8fafc' }}>
        <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🔒</div>
        <h2 style={{ color: '#ef4444' }}>Access Restricted (Role Authorization Error)</h2>
        <p style={{ color: '#94a3b8', maxWidth: '500px', margin: '12px auto' }}>
          Your active session role (<strong>{user.role}</strong>) does not possess statutory authorization to access this intelligence partition.
        </p>
        <button
          onClick={() => window.history.back()}
          style={{
            backgroundColor: '#141414',
            color: '#f5f5f5',
            border: '1px solid #262626',
            padding: '8px 20px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontWeight: 600,
            marginTop: '16px',
          }}
        >
          Return to Authorized Workspace
        </button>
      </div>
    );
  }

  return children ? <>{children}</> : <Outlet />;
};
