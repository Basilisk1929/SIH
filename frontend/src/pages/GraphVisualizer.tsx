import React, { useEffect, useState } from 'react';
import { ApiService } from '../services/api';
import { SubgraphData } from '../types';

export const GraphVisualizer: React.FC = () => {
  const [targetAccount, setTargetAccount] = useState('SYN9810482019');
  const [graphData, setGraphData] = useState<SubgraphData | null>(null);

  useEffect(() => {
    async function loadGraph() {
      const data = await ApiService.getAccountSubgraph(targetAccount);
      setGraphData(data);
    }
    loadGraph();
  }, [targetAccount]);

  return (
    <div className="content-body">
      <div className="stat-card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <label style={{ fontSize: '0.88rem', fontWeight: 600 }}>Center Suspect Account / VPA:</label>
          <input
            type="text"
            value={targetAccount}
            onChange={(e) => setTargetAccount(e.target.value)}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '8px 14px',
              borderRadius: 6,
              fontFamily: 'var(--font-mono)',
              width: 280,
            }}
          />
          <button className="btn-action">Expand Neighborhood (Depth 2)</button>
        </div>
      </div>

      <div className="stat-card" style={{ minHeight: 420, position: 'relative', overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
          <h3 style={{ fontSize: '1rem', color: 'var(--accent-cyan)' }}>
            🕸️ Multi-Hop Money Flow & Shared Identifier Network Topology
          </h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Detected Nodes: {graphData?.node_count || 0} | Relationships: {graphData?.edge_count || 0}
          </span>
        </div>

        {/* Visual Mock representation of Graph Network for Prototype Demonstration */}
        <div
          style={{
            background: 'radial-gradient(circle at center, #0f172a 0%, #070a12 100%)',
            border: '1px dashed var(--border-subtle)',
            borderRadius: 8,
            padding: 32,
            minHeight: 340,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 24,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 40 }}>
            {/* Victim Origin */}
            <div style={{ textAlign: 'center' }}>
              <div style={{ padding: '16px 20px', borderRadius: 8, background: 'rgba(239, 68, 68, 0.2)', border: '1px solid #ef4444' }}>
                <div style={{ fontSize: '0.75rem', color: '#fca5a5' }}>ORIGIN VICTIM</div>
                <strong style={{ fontFamily: 'var(--font-mono)' }}>VIC_MUMBAI_01</strong>
              </div>
            </div>

            <div style={{ color: 'var(--accent-cyan)', fontSize: '1.2rem' }}>—[UPI ₹50,000]→</div>

            {/* Layer 1 Mule */}
            <div style={{ textAlign: 'center' }}>
              <div style={{ padding: '16px 20px', borderRadius: 8, background: 'rgba(245, 158, 11, 0.2)', border: '1px solid #f59e0b' }}>
                <div style={{ fontSize: '0.75rem', color: '#fcd34d' }}>LAYER-1 MULE</div>
                <strong style={{ fontFamily: 'var(--font-mono)' }}>{targetAccount}</strong>
              </div>
            </div>

            <div style={{ color: 'var(--accent-cyan)', fontSize: '1.2rem' }}>—[IMPS ₹48,000 (3 min)]→</div>

            {/* Layer 2 Distributor */}
            <div style={{ textAlign: 'center' }}>
              <div style={{ padding: '16px 20px', borderRadius: 8, background: 'rgba(99, 102, 241, 0.2)', border: '1px solid #6366f1' }}>
                <div style={{ fontSize: '0.75rem', color: '#c7d2fe' }}>LAYER-2 MULE</div>
                <strong style={{ fontFamily: 'var(--font-mono)' }}>MULE_L2_SYN_09</strong>
              </div>
            </div>

            <div style={{ color: 'var(--accent-cyan)', fontSize: '1.2rem' }}>—[NEFT ₹46,500]→</div>

            {/* Layer 3 Cashout */}
            <div style={{ textAlign: 'center' }}>
              <div style={{ padding: '16px 20px', borderRadius: 8, background: 'rgba(16, 185, 129, 0.2)', border: '1px solid #10b981' }}>
                <div style={{ fontSize: '0.75rem', color: '#6ee7b7' }}>CASHOUT / CRYPTO GATEWAY</div>
                <strong style={{ fontFamily: 'var(--font-mono)' }}>EXCHANGE_DEPOSIT_ACC</strong>
              </div>
            </div>
          </div>

          <div style={{ marginTop: 24, padding: 12, borderRadius: 6, background: 'rgba(0, 242, 254, 0.05)', border: '1px solid rgba(0, 242, 254, 0.2)', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            ⚡ <strong>Detection Rule Fired:</strong> Rapid pass-through velocity (&lt; 5 minutes per hop) across 3 accounts sharing device IMEI <code>8630910482103</code>.
          </div>
        </div>
      </div>
    </div>
  );
};
