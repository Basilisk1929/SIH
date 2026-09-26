import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  subtext?: string;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, subtext }) => {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {subtext && <div className="stat-subtext">{subtext}</div>}
    </div>
  );
};
