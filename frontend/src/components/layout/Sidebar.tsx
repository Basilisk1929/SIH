import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  unreadAlertCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ unreadAlertCount = 0 }) => {
  const { user } = useAuth();

  const navItems = [
    { to: '/dashboard', label: 'Command Overview', icon: '📊' },
    { to: '/alerts', label: 'Real-Time Alerts', icon: '🚨', badge: unreadAlertCount },
    { to: '/cases', label: 'Case Management', icon: '📁' },
    { to: '/transactions', label: 'Transaction Intel', icon: '💳' },
    { to: '/complaints', label: 'NCRP Complaints', icon: '📝' },
    { to: '/graph', label: 'Mule Graph Visualizer', icon: '🕸️' },
    { to: '/map', label: 'Threat Map & Cash-Outs', icon: '📍' },
  ];

  return (
    <aside className="sidebar">
      <div className="brand-header">
        <div className="brand-icon">⚡</div>
        <div>
          <div className="brand-title">CyberShield</div>
          <div className="brand-subtitle">SIH Intel Platform</div>
        </div>
      </div>

      <nav style={{ padding: '16px 0', flex: 1 }}>
        <ul className="nav-menu" style={{ listStyle: 'none' }}>
          {navItems.map((item) => (
            <li key={item.to} style={{ margin: '4px 12px' }}>
              <NavLink
                to={item.to}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  color: isActive ? '#00f2fe' : '#94a3b8',
                  backgroundColor: isActive ? 'rgba(0, 242, 254, 0.1)' : 'transparent',
                  border: isActive ? '1px solid rgba(0, 242, 254, 0.3)' : '1px solid transparent',
                  textDecoration: 'none',
                  fontSize: '0.875rem',
                  fontWeight: isActive ? 600 : 500,
                  transition: 'all 0.15s ease',
                })}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '1.1rem' }}>{item.icon}</span>
                  <span>{item.label}</span>
                </div>

                {item.badge !== undefined && item.badge > 0 && (
                  <span
                    style={{
                      backgroundColor: '#ef4444',
                      color: '#ffffff',
                      borderRadius: '10px',
                      padding: '1px 6px',
                      fontSize: '0.65rem',
                      fontWeight: 700,
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Footer System Status */}
      <div
        style={{
          padding: '16px',
          borderTop: '1px solid #1e293b',
          fontSize: '0.72rem',
          color: '#64748b',
          lineHeight: 1.4,
        }}
      >
        <div>
          <span>Role: </span>
          <strong style={{ color: '#cbd5e1' }}>{user?.role || 'UNAUTHENTICATED'}</strong>
        </div>
        <div style={{ marginTop: '4px' }}>
          <span>Classification: </span>
          <span style={{ color: '#f59e0b' }}>LAW ENFORCEMENT RESTRICTED</span>
        </div>
      </div>
    </aside>
  );
};
