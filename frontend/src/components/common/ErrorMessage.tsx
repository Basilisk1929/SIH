import React from 'react';

interface ErrorMessageProps {
  title?: string;
  message: string;
  statusCode?: number;
  onRetry?: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({
  title = 'API Intelligence Failure',
  message,
  statusCode,
  onRetry,
}) => {
  return (
    <div
      style={{
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: '8px',
        padding: '20px',
        margin: '16px 0',
        color: '#f8fafc',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <span style={{ color: '#ef4444', fontSize: '1.2rem' }}>⚠️</span>
        <h4 style={{ margin: 0, fontSize: '1rem', color: '#fca5a5' }}>
          {title} {statusCode ? `(HTTP ${statusCode})` : ''}
        </h4>
      </div>
      <p style={{ margin: '0 0 16px 0', fontSize: '0.875rem', color: '#cbd5e1' }}>{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.2)',
            color: '#fca5a5',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            padding: '6px 14px',
            borderRadius: '6px',
            fontSize: '0.8rem',
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          Retry Connection
        </button>
      )}
    </div>
  );
};
