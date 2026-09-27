import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
  text?: string;
  size?: 'sm' | 'md' | 'lg';
  minHeight?: number | string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message,
  text,
  size = 'md',
  minHeight = 'auto',
}) => {
  const displayMessage = text || message || 'Retrieving intelligence stream...';
  const pixelSize = size === 'sm' ? 20 : size === 'lg' ? 44 : 32;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
        minHeight: typeof minHeight === 'number' ? `${minHeight}px` : minHeight,
        color: '#94a3b8',
        gap: '12px',
      }}
    >
      <div
        style={{
          width: `${pixelSize}px`,
          height: `${pixelSize}px`,
          border: '3px solid rgba(0, 242, 254, 0.15)',
          borderTopColor: '#00f2fe',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      <span style={{ fontSize: '0.85rem', letterSpacing: '0.05em' }}>{displayMessage}</span>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
