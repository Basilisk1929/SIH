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
  const accentColors = {
    cyan: '#0088ff',
    rose: '#ef4444',
    amber: '#f59e0b',
    emerald: '#10b981',
    indigo: '#6366f1',
  };

  const accentColor = accentColors[color];

  return (
    <div
      onClick={onClick}
      style={{
        backgroundColor: '#0a0a0a',
        border: '1px solid #202020',
        borderTop: `2px solid ${accentColor}`,
        borderRadius: '8px',
        padding: '18px 20px',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.7)',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.15s ease, border-color 0.15s ease, background-color 0.15s ease',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
      onMouseEnter={(e) => {
        if (onClick) {
          e.currentTarget.style.backgroundColor = '#121212';
          e.currentTarget.style.borderColor = '#333333';
          e.currentTarget.style.borderTopColor = accentColor;
        }
      }}
      onMouseLeave={(e) => {
        if (onClick) {
          e.currentTarget.style.backgroundColor = '#0a0a0a';
          e.currentTarget.style.borderColor = '#202020';
          e.currentTarget.style.borderTopColor = accentColor;
        }
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontSize: '0.75rem', color: '#707070', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>
          {title}
        </span>
        {icon && <span style={{ fontSize: '1.2rem' }}>{icon}</span>}
      </div>

      <div style={{ fontSize: '1.85rem', fontWeight: 700, color: '#f5f5f5', fontFamily: 'monospace', letterSpacing: '-0.02em', margin: '4px 0' }}>
        {value}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px', fontSize: '0.75rem' }}>
        {subtext && <span style={{ color: '#707070' }}>{subtext}</span>}
        {trend && (
          <span
            style={{
              color: trendDirection === 'up' ? '#ef4444' : trendDirection === 'down' ? '#10b981' : '#a0a0a0',
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
