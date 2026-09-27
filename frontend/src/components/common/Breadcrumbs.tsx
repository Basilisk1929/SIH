import React from 'react';
import { Link } from 'react-router-dom';

export interface BreadcrumbItem {
  label: string;
  path?: string;
}

export const Breadcrumbs: React.FC<{ items: BreadcrumbItem[] }> = ({ items }) => {
  return (
    <nav aria-label="Breadcrumb" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#64748b', marginBottom: '16px' }}>
      <Link to="/dashboard" style={{ color: '#94a3b8', textDecoration: 'none' }}>
        Dashboard
      </Link>
      {items.map((item, idx) => {
        const isLast = idx === items.length - 1;
        return (
          <React.Fragment key={idx}>
            <span>/</span>
            {isLast || !item.path ? (
              <span style={{ color: '#f8fafc', fontWeight: 600 }}>{item.label}</span>
            ) : (
              <Link to={item.path} style={{ color: '#94a3b8', textDecoration: 'none' }}>
                {item.label}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};
