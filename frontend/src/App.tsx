import React, { useState } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Workbench } from './pages/Workbench';
import { GraphVisualizer } from './pages/GraphVisualizer';
import { HotspotMap } from './pages/HotspotMap';
import './styles/theme.css';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  const getPageTitle = (tab: string) => {
    switch (tab) {
      case 'dashboard':
        return 'Cybercrime Intelligence Command Overview';
      case 'workbench':
        return 'NCRP / 1930 Incident Triage & Forensic Workbench';
      case 'graph':
        return 'Mule Account Link Analysis & Flow Tracing';
      case 'hotspots':
        return 'Spatial Cybercrime Cluster Heatmap';
      default:
        return 'CyberShield Intelligence Platform';
    }
  };

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} />
      <main className="main-content">
        <Header currentTab={getPageTitle(activeTab)} />
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'workbench' && <Workbench />}
        {activeTab === 'graph' && <GraphVisualizer />}
        {activeTab === 'hotspots' && <HotspotMap />}
      </main>
    </div>
  );
};

export default App;
