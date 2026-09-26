import React from 'react';

interface RiskBadgeProps {
  score: number;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ score }) => {
  let badgeClass = 'badge-low';
  let label = 'LOW RISK';

  if (score >= 0.8) {
    badgeClass = 'badge-critical';
    label = `CRITICAL (${Math.round(score * 100)}%)`;
  } else if (score >= 0.6) {
    badgeClass = 'badge-high';
    label = `HIGH (${Math.round(score * 100)}%)`;
  } else if (score >= 0.4) {
    badgeClass = 'badge-medium';
    label = `MEDIUM (${Math.round(score * 100)}%)`;
  } else {
    badgeClass = 'badge-low';
    label = `LOW (${Math.round(score * 100)}%)`;
  }

  return <span className={`badge ${badgeClass}`}>{label}</span>;
};
