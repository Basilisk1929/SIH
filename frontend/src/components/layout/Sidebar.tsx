import React from 'react';

interface SidebarProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Command Overview', icon: '📊' },
    { id: 'workbench', label: '1930 Incident Triage', icon: '🚨' },
    { id: 'graph', label: 'Mule Graph Visualizer', icon: '🕸️' },
    { id: 'hotspots', label: 'Cyber Threat Hotspots', icon: '📍' },
  ];

  return (
    <aside className="sidebar">
      <div className="brand-header">
        <div className="brand-icon">⚡</div>
        <div>
          <div className="brand-title">CyberShield</div>
          <div className="brand-subtitle">SIH Intel Platform</div>
        </div>
      </div>
      <nav>
        <ul className="nav-menu">
          {menuItems.map((item) => (
            <li
              key={item.id}
              className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
              onClick={() => onSelectTab(item.id)}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
};
