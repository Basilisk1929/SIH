import React from 'react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  message?: string;
  icon?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Records Found',
  description,
  message,
  icon = '📁',
  actionLabel,
  onAction,
}) => {
  const displayText = description || message || 'No data available.';
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        textAlign: 'center',
        backgroundColor: '#0d1322',
        border: '1px dashed #1e293b',
        borderRadius: '8px',
        margin: '16px 0',
      }}
    >
      <div style={{ fontSize: '2rem', marginBottom: '12px' }}>{icon}</div>
      <h3 style={{ margin: '0 0 6px 0', fontSize: '1rem', color: '#f8fafc' }}>{title}</h3>
      <p style={{ margin: '0 0 16px 0', fontSize: '0.85rem', color: '#94a3b8', maxWidth: '400px' }}>{displayText}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          style={{
            backgroundColor: 'rgba(0, 242, 254, 0.15)',
            color: '#00f2fe',
            border: '1px solid rgba(0, 242, 254, 0.3)',
            padding: '8px 16px',
            borderRadius: '6px',
            fontSize: '0.85rem',
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};
