import React from 'react';
import { AlertSeverity, AlertStatus, CasePriority, CaseStatus, UserRole } from '../../types';

interface BadgeProps {
  children: React.ReactNode;
  variant?:
    | 'default'
    | 'severity'
    | 'status'
    | 'role'
    | 'outline'
    | 'neutral'
    | AlertSeverity
    | CasePriority
    | AlertStatus
    | CaseStatus
    | UserRole
    | string;
  severity?: AlertSeverity;
  status?: AlertStatus | CaseStatus;
  role?: UserRole;
  priority?: CasePriority;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  severity,
  status,
  role,
  priority,
  size = 'md',
  className = '',
}) => {
  const getStyle = (): React.CSSProperties => {
    // 1. Severity / Priority styling
    const vUpper = String(variant).toUpperCase();
    const effectiveSeverity =
      severity ||
      priority ||
      (['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].includes(vUpper) ? (vUpper as AlertSeverity) : undefined);
    if (effectiveSeverity) {
      switch (effectiveSeverity) {
        case 'CRITICAL':
          return { backgroundColor: 'rgba(239, 68, 68, 0.12)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.35)' };
        case 'HIGH':
          return { backgroundColor: 'rgba(245, 158, 11, 0.12)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.35)' };
        case 'MEDIUM':
          return { backgroundColor: 'rgba(0, 136, 255, 0.12)', color: '#60a5fa', border: '1px solid rgba(0, 136, 255, 0.35)' };
        case 'LOW':
        default:
          return { backgroundColor: 'rgba(16, 185, 129, 0.12)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.35)' };
      }
    }

    // 2. Status styling
    if (status) {
      switch (status as string) {
        case 'NEW':
        case 'OPEN':
          return { backgroundColor: 'rgba(99, 102, 241, 0.12)', color: '#a5b4fc', border: '1px solid rgba(99, 102, 241, 0.35)' };
        case 'INVESTIGATING':
        case 'UNDER_INVESTIGATION':
          return { backgroundColor: 'rgba(245, 158, 11, 0.12)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.35)' };
        case 'ACKNOWLEDGED':
          return { backgroundColor: 'rgba(0, 136, 255, 0.12)', color: '#60a5fa', border: '1px solid rgba(0, 136, 255, 0.35)' };
        case 'RESOLVED':
        case 'CLOSED':
          return { backgroundColor: 'rgba(16, 185, 129, 0.12)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.35)' };
        case 'FROZEN':
          return { backgroundColor: 'rgba(239, 68, 68, 0.18)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.45)' };
        case 'FALSE_POSITIVE':
          return { backgroundColor: 'rgba(115, 115, 115, 0.15)', color: '#d4d4d4', border: '1px solid rgba(115, 115, 115, 0.3)' };
      }
    }

    // 3. User Role styling
    if (role) {
      switch (role) {
        case 'ADMIN':
          return { backgroundColor: 'rgba(239, 68, 68, 0.12)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.35)' };
        case 'SUPERVISOR':
          return { backgroundColor: 'rgba(168, 85, 247, 0.12)', color: '#c084fc', border: '1px solid rgba(168, 85, 247, 0.35)' };
        case 'INVESTIGATOR':
          return { backgroundColor: 'rgba(0, 136, 255, 0.12)', color: '#60a5fa', border: '1px solid rgba(0, 136, 255, 0.35)' };
        case 'ANALYST':
          return { backgroundColor: 'rgba(59, 130, 246, 0.12)', color: '#93c5fd', border: '1px solid rgba(59, 130, 246, 0.35)' };
      }
    }

    if (variant === 'outline') {
      return { backgroundColor: 'transparent', color: '#a0a0a0', border: '1px solid #262626' };
    }

    return { backgroundColor: '#141414', color: '#d4d4d4', border: '1px solid #242424' };
  };

  const sizeStyles: Record<string, React.CSSProperties> = {
    sm: { padding: '1px 6px', fontSize: '0.65rem', borderRadius: '4px' },
    md: { padding: '2px 8px', fontSize: '0.75rem', borderRadius: '6px' },
    lg: { padding: '4px 12px', fontSize: '0.85rem', borderRadius: '8px' },
  };

  return (
    <span
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        fontFamily: 'monospace',
        whiteSpace: 'nowrap',
        ...sizeStyles[size],
        ...getStyle(),
      }}
    >
      {children}
    </span>
  );
};
