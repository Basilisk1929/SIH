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
        backgroundColor: '#0a0a0a',
        border: '1px dashed #202020',
        borderRadius: '8px',
        margin: '16px 0',
      }}
    >
      <div style={{ fontSize: '2rem', marginBottom: '12px' }}>{icon}</div>
      <h3 style={{ margin: '0 0 6px 0', fontSize: '1rem', color: '#f5f5f5' }}>{title}</h3>
      <p style={{ margin: '0 0 16px 0', fontSize: '0.85rem', color: '#a0a0a0', maxWidth: '400px' }}>{displayText}</p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          style={{
            backgroundColor: '#141414',
            color: '#f5f5f5',
            border: '1px solid #262626',
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
