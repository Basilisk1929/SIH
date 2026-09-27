import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Badge } from '../common/Badge';
import { DemoSimulationModal } from '../demo/DemoSimulationModal';

interface HeaderProps {
  title?: string;
  isWsConnected?: boolean;
  unreadAlertCount?: number;
}

export const Header: React.FC<HeaderProps> = ({
  title = 'Cybercrime Intelligence Command Platform',
  isWsConnected = false,
  unreadAlertCount = 0,
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const isAuthorizedForDemo = user && (user.role === 'ADMIN' || user.role === 'SUPERVISOR' || user.role === 'INVESTIGATOR');

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getInitials = (name?: string, email?: string) => {
    if (name) {
      const parts = name.trim().split(/\s+/);
      if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      return name.slice(0, 2).toUpperCase();
    }
    if (email) return email.slice(0, 2).toUpperCase();
    return 'OF';
  };

  return (
    <>
      <div className="compliance-banner">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>⚠️ SMART INDIA HACKATHON EVALUATION ENVIRONMENT</span>
          <span style={{ color: '#94a3b8' }}>•</span>
          <span>STRICT SYNTHETIC DATA MODE (ZERO REAL NCRP/BANK PII)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.7rem' }}>
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: isWsConnected ? '#10b981' : '#f59e0b',
                display: 'inline-block',
                boxShadow: isWsConnected ? '0 0 8px #10b981' : 'none',
              }}
            />
            <span style={{ color: isWsConnected ? '#6ee7b7' : '#fcd34d' }}>
              {isWsConnected ? 'LIVE FEED (WEBSOCKET)' : 'OFFLINE STREAM'}
            </span>
          </div>
          <span className="compliance-badge">CERT-IN SEC-2026 COMPLIANT</span>
        </div>
      </div>

      <header className="top-navbar" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h1 className="page-title">{title}</h1>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* SIH Demo Mode Button */}
          {isAuthorizedForDemo && (
            <button
              onClick={() => setIsDemoModalOpen(true)}
              title="Run controlled synthetic fraud scenario through complete live platform"
              style={{
                background: 'linear-gradient(135deg, rgba(0, 242, 254, 0.2) 0%, rgba(59, 130, 246, 0.2) 100%)',
                color: '#00f2fe',
                border: '1px solid rgba(0, 242, 254, 0.5)',
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                boxShadow: '0 0 10px rgba(0, 242, 254, 0.2)',
                letterSpacing: '0.04em',
              }}
            >
              <span>⚡</span>
              <span>SIH DEMO MODE</span>
            </button>
          )}

          {/* Notification counter */}
          {unreadAlertCount > 0 && (
            <button
              onClick={() => navigate('/alerts')}
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                color: '#f87171',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                padding: '4px 10px',
                borderRadius: '16px',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <span>🚨</span>
              <span>{unreadAlertCount} NEW ALERT{unreadAlertCount > 1 ? 'S' : ''}</span>
            </button>
          )}

          {/* User profile & badge */}
          {user && (
            <div className="officer-badge" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div className="officer-avatar">{getInitials(user.full_name, user.email)}</div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{user.full_name || user.email}</span>
                  <Badge role={user.role} size="sm">
                    {user.role}
                  </Badge>
                </div>
                <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
                  {user.badge_number ? `Badge #${user.badge_number} • ` : ''}
                  {user.department || 'Cyber Crime Division'}
                </span>
              </div>

              {/* Logout button */}
              <button
                onClick={handleLogout}
                title="Sign out of investigation session"
                style={{
                  backgroundColor: 'transparent',
                  border: '1px solid #334155',
                  color: '#94a3b8',
                  borderRadius: '6px',
                  padding: '4px 8px',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  marginLeft: '8px',
                }}
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Phase 11F Live Demo Simulation Modal */}
      <DemoSimulationModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
      />
    </>
  );
};
