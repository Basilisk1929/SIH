import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon?: string;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  color?: 'cyan' | 'rose' | 'amber' | 'emerald' | 'indigo';
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtext,
  icon,
  trend,
  trendDirection,
  color = 'cyan',
  onClick,
}) => {
  const colorMap = {
    cyan: { border: 'rgba(0, 242, 254, 0.3)', glow: 'rgba(0, 242, 254, 0.1)', text: '#00f2fe' },
    rose: { border: 'rgba(239, 68, 68, 0.3)', glow: 'rgba(239, 68, 68, 0.1)', text: '#ef4444' },
    amber: { border: 'rgba(245, 158, 11, 0.3)', glow: 'rgba(245, 158, 11, 0.1)', text: '#f59e0b' },
    emerald: { border: 'rgba(16, 185, 129, 0.3)', glow: 'rgba(16, 185, 129, 0.1)', text: '#10b981' },
    indigo: { border: 'rgba(99, 102, 241, 0.3)', glow: 'rgba(99, 102, 241, 0.1)', text: '#6366f1' },
  };

  const c = colorMap[color];

  return (
    <div
      onClick={onClick}
      style={{
        backgroundColor: '#121a2d',
        border: `1px solid ${c.border}`,
        borderRadius: '10px',
        padding: '20px',
        boxShadow: `0 4px 16px ${c.glow}`,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.15s ease, border-color 0.15s ease',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
          {title}
        </span>
        {icon && <span style={{ fontSize: '1.25rem' }}>{icon}</span>}
      </div>

      <div style={{ fontSize: '1.85rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'monospace', letterSpacing: '-0.02em', margin: '4px 0' }}>
        {value}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px', fontSize: '0.75rem' }}>
        {subtext && <span style={{ color: '#64748b' }}>{subtext}</span>}
        {trend && (
          <span
            style={{
              color: trendDirection === 'up' ? '#ef4444' : trendDirection === 'down' ? '#10b981' : '#94a3b8',
              fontWeight: 600,
            }}
          >
            {trend}
          </span>
        )}
      </div>
    </div>
  );
};
