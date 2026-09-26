import React from 'react';

interface HeaderProps {
  currentTab: string;
}

export const Header: React.FC<HeaderProps> = ({ currentTab }) => {
  return (
    <>
      <div className="compliance-banner">
        <span>⚠️ SMART INDIA HACKATHON EVALUATION ENVIRONMENT • STRICT SYNTHETIC DATA MODE ONLY</span>
        <span className="compliance-badge">ZERO REAL NCRP / BANK PII</span>
      </div>
      <header className="top-navbar">
        <h1 className="page-title">{currentTab}</h1>
        <div className="officer-badge">
          <div className="officer-avatar">RS</div>
          <span>Inspector R. Sharma (State Cyber Cell STF)</span>
        </div>
      </header>
    </>
  );
};
