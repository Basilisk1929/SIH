import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Header } from '../components/layout/Header';
import { Sidebar } from '../components/layout/Sidebar';
import { useAlertStream } from '../hooks/useAlertStream';

export const MainLayout: React.FC = () => {
  const location = useLocation();
  const { isConnected, unreadCount } = useAlertStream({ autoConnect: true });

  const getPageTitle = (pathname: string): string => {
    if (pathname.startsWith('/alerts/')) return 'Alert Incident Dossier & Forensic Triage';
    if (pathname === '/alerts') return 'Real-Time Alert Intelligence Stream';
    if (pathname.startsWith('/cases/')) return 'Case Docket Investigation & Evidentiary File';
    if (pathname === '/cases') return 'Investigation Case Dockets Management';
    if (pathname.startsWith('/accounts/')) return 'Bank Account Forensic Audit & Mule Linkage';
    if (pathname === '/transactions') return 'Financial Transaction Risk Detection & XGBoost Engine';
    if (pathname === '/complaints') return 'NCRP 1930 Citizen Cybercrime Reports & NLP Engine';
    if (pathname === '/graph') return 'Mule Network Topology & Link Analysis Visualizer';
    if (pathname === '/map') return 'Geospatial Intelligence, H3 Risk Cells & Cash-Out Prediction';
    return 'Cybercrime Intelligence Command Overview';
  };

  return (
    <div className="app-container">
      <Sidebar unreadAlertCount={unreadCount} />
      <main className="main-content" style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0, overflowY: 'auto' }}>
        <Header
          title={getPageTitle(location.pathname)}
          isWsConnected={isConnected}
          unreadAlertCount={unreadCount}
        />
        <div style={{ padding: '24px 32px', flex: 1 }}>
          <Outlet />
        </div>
      </main>
    </div>
  );
};
