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
    <aside className="sidebar" style={{ backgroundColor: '#000000', borderRight: '1px solid #1f1f1f' }}>
      <div className="brand-header" style={{ backgroundColor: '#000000', borderBottom: '1px solid #1f1f1f' }}>
        <img
          src="/cybershield-icon.png"
          alt="CyberShield Official Emblem"
          className="brand-logo-img"
          style={{ width: '38px', height: '38px', objectFit: 'contain' }}
        />
        <div>
          <div className="brand-title" style={{ color: '#f5f5f5', fontWeight: 700, letterSpacing: '-0.02em', fontSize: '1.05rem' }}>
            CyberShield
          </div>
          <div className="brand-subtitle" style={{ color: '#707070', fontSize: '0.7rem', letterSpacing: '0.08em', fontWeight: 600 }}>
            SIH Intel Platform
          </div>
        </div>
      </div>

      <nav style={{ padding: '16px 0', flex: 1, backgroundColor: '#000000' }}>
        <ul className="nav-menu" style={{ listStyle: 'none' }}>
          {navItems.map((item) => (
            <li key={item.to} style={{ margin: '3px 10px' }}>
              <NavLink
                to={item.to}
                className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '9px 12px',
                  borderRadius: '6px',
                  color: isActive ? '#f5f5f5' : '#a0a0a0',
                  backgroundColor: isActive ? '#141414' : 'transparent',
                  border: isActive ? '1px solid #242424' : '1px solid transparent',
                  borderLeft: isActive ? '3px solid #0088ff' : '3px solid transparent',
                  textDecoration: 'none',
                  fontSize: '0.85rem',
                  fontWeight: isActive ? 600 : 500,
                  transition: 'all 0.15s ease',
                })}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '1rem' }}>{item.icon}</span>
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
          borderTop: '1px solid #1f1f1f',
          backgroundColor: '#000000',
          fontSize: '0.72rem',
          color: '#707070',
          lineHeight: 1.4,
        }}
      >
        <div>
          <span>Role: </span>
          <strong style={{ color: '#d4d4d4' }}>{user?.role || 'UNAUTHENTICATED'}</strong>
        </div>
        <div style={{ marginTop: '4px' }}>
          <span>Classification: </span>
          <span style={{ color: '#f59e0b', fontWeight: 600 }}>LAW ENFORCEMENT RESTRICTED</span>
        </div>
      </div>
    </aside>
  );
};
