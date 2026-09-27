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
    // If variant is a severity, priority, status or role token
    const vUpper = String(variant).toUpperCase();
    const effectiveSeverity =
      severity ||
      priority ||
      (['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].includes(vUpper) ? (vUpper as AlertSeverity) : undefined);
    if (effectiveSeverity) {
      switch (effectiveSeverity) {
        case 'CRITICAL':
          return { backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.4)' };
        case 'HIGH':
          return { backgroundColor: 'rgba(245, 158, 11, 0.2)', color: '#fcd34d', border: '1px solid rgba(245, 158, 11, 0.4)' };
        case 'MEDIUM':
          return { backgroundColor: 'rgba(0, 242, 254, 0.15)', color: '#67e8f9', border: '1px solid rgba(0, 242, 254, 0.3)' };
        case 'LOW':
        default:
          return { backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#6ee7b7', border: '1px solid rgba(16, 185, 129, 0.3)' };
      }
    }

    // 2. Status styling
    if (status) {
      switch (status as string) {
        case 'NEW':
        case 'OPEN':
          return { backgroundColor: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', border: '1px solid rgba(99, 102, 241, 0.4)' };
        case 'INVESTIGATING':
        case 'UNDER_INVESTIGATION':
          return { backgroundColor: 'rgba(245, 158, 11, 0.2)', color: '#fcd34d', border: '1px solid rgba(245, 158, 11, 0.4)' };
        case 'ACKNOWLEDGED':
          return { backgroundColor: 'rgba(56, 189, 248, 0.2)', color: '#7dd3fc', border: '1px solid rgba(56, 189, 248, 0.4)' };
        case 'RESOLVED':
        case 'CLOSED':
          return { backgroundColor: 'rgba(16, 185, 129, 0.2)', color: '#6ee7b7', border: '1px solid rgba(16, 185, 129, 0.4)' };
        case 'FROZEN':
          return { backgroundColor: 'rgba(239, 68, 68, 0.25)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.5)' };
        case 'FALSE_POSITIVE':
          return { backgroundColor: 'rgba(100, 116, 139, 0.2)', color: '#cbd5e1', border: '1px solid rgba(100, 116, 139, 0.4)' };
      }
    }

    // 3. User Role styling
    if (role) {
      switch (role) {
        case 'ADMIN':
          return { backgroundColor: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.4)' };
        case 'SUPERVISOR':
          return { backgroundColor: 'rgba(168, 85, 247, 0.2)', color: '#d8b4fe', border: '1px solid rgba(168, 85, 247, 0.4)' };
        case 'INVESTIGATOR':
          return { backgroundColor: 'rgba(0, 242, 254, 0.2)', color: '#67e8f9', border: '1px solid rgba(0, 242, 254, 0.4)' };
        case 'ANALYST':
          return { backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#93c5fd', border: '1px solid rgba(59, 130, 246, 0.4)' };
      }
    }

    if (variant === 'outline') {
      return { backgroundColor: 'transparent', color: '#94a3b8', border: '1px solid #334155' };
    }

    return { backgroundColor: '#1e293b', color: '#cbd5e1', border: '1px solid #334155' };
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
