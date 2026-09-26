import React from 'react';

export const HotspotMap: React.FC = () => {
  const hubs = [
    {
      name: "Mewat - Nuh Corridor",
      state: "Haryana / Rajasthan Border",
      risk: 0.92,
      primaryModus: "OLX Vehicle & Armed Impersonation Phishing",
      activeSuspects: 142,
    },
    {
      name: "Jamtara - Karmatanr Cluster",
      state: "Jharkhand",
      risk: 0.94,
      primaryModus: "Bank Executive Vishing & Screen Share APKs",
      activeSuspects: 98,
    },
    {
      name: "Bharatpur - Deeg Belt",
      state: "Rajasthan",
      risk: 0.88,
      primaryModus: "Sextortion & Fake Job Portals",
      activeSuspects: 115,
    },
    {
      name: "Cyberabad - Hitec City Zone",
      state: "Telangana",
      risk: 0.78,
      primaryModus: "Telegram Investment & Crypto Ponzi Tasks",
      activeSuspects: 64,
    },
    {
      name: "Noida Sector 62 / Greater Noida",
      state: "Uttar Pradesh",
      risk: 0.84,
      primaryModus: "Illegal Call Centers / Foreign Impersonation",
      activeSuspects: 82,
    },
  ];

  return (
    <div className="content-body">
      <div className="stat-card" style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: '1rem', color: 'var(--accent-cyan)', marginBottom: 8 }}>
          📍 Spatial Cyber Threat Cluster Intelligence (Simulated Indian Reference Hubs)
        </h3>
        <p style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
          Benchmark spatial clustering analyzing incident location density, suspect mobile towers, and synthetic device IP centroids.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
        {hubs.map((hub) => (
          <div key={hub.name} className="stat-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <strong style={{ fontSize: '1.05rem', color: 'var(--text-primary)' }}>{hub.name}</strong>
              <span className={`badge ${hub.risk > 0.9 ? 'badge-critical' : 'badge-high'}`}>
                Risk: {Math.round(hub.risk * 100)}%
              </span>
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div>State / Region: <strong style={{ color: 'var(--text-primary)' }}>{hub.state}</strong></div>
              <div>Primary Modus Operandi: <span style={{ color: 'var(--accent-cyan)' }}>{hub.primaryModus}</span></div>
              <div>Active Synthetic Suspects: <span style={{ fontFamily: 'var(--font-mono)' }}>{hub.activeSuspects}</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
