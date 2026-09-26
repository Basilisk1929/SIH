import React, { useEffect, useState } from 'react';
import { StatCard } from '../components/common/StatCard';
import { RiskBadge } from '../components/common/RiskBadge';
import { ApiService, formatINR, maskIdentifier } from '../services/api';
import { AnalyticsOverview, Complaint, Transaction } from '../types';

export const Dashboard: React.FC = () => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [recentComplaints, setRecentComplaints] = useState<Complaint[]>([]);
  const [recentTxns, setRecentTxns] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [ovData, cData, txData] = await Promise.all([
          ApiService.getAnalyticsOverview(),
          ApiService.getComplaints(5),
          ApiService.getRecentTransactions(),
        ]);
        setOverview(ovData);
        setRecentComplaints(cData.items);
        setRecentTxns(txData);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <div style={{ padding: 32 }}>Loading CyberShield Intelligence Telemetry...</div>;
  }

  return (
    <div className="content-body">
      <div className="kpi-grid">
        <StatCard
          label="Total Incidents Reported"
          value={overview?.total_complaints_reported?.toLocaleString() || '14,280'}
          subtext="Simulated NCRP 1930 stream"
        />
        <StatCard
          label="Total Loss Tracked"
          value={formatINR(overview?.total_financial_loss_inr || 284500000)}
          subtext="Pan-India Cyber Fraud"
        />
        <StatCard
          label="Active Mule Rings Detected"
          value={overview?.active_mule_rings_detected || 42}
          subtext="Graph clustering analysis"
        />
        <StatCard
          label="Golden Hour Freezes"
          value={overview?.accounts_frozen_in_golden_hour || 189}
          subtext={`Saved: ${formatINR(overview?.saved_loss_inr || 48200000)}`}
        />
      </div>

      <div className="data-table-card" style={{ marginBottom: 32 }}>
        <div className="table-header">
          <h2 className="table-title">Live 1930 / NCRP Priority Inflow Feed (Synthetic)</h2>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Real-time triage</span>
        </div>
        <table>
          <thead>
            <tr>
              <th>Ack Number</th>
              <th>Category</th>
              <th>State</th>
              <th>Loss Amount</th>
              <th>Suspect VPA</th>
              <th>Risk Score</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {recentComplaints.map((c) => (
              <tr key={c.id}>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{c.acknowledgement_no}</td>
                <td>{c.category}</td>
                <td>{c.victim_state}</td>
                <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{formatINR(c.reported_loss_inr)}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{maskIdentifier(c.suspect_upi)}</td>
                <td><RiskBadge score={c.risk_score} /></td>
                <td><span style={{ fontSize: '0.8rem', fontWeight: 600 }}>{c.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="data-table-card">
        <div className="table-header">
          <h2 className="table-title">High-Velocity Transaction Anomalies</h2>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Mule Layering Detection</span>
        </div>
        <table>
          <thead>
            <tr>
              <th>Txn Reference</th>
              <th>Rail</th>
              <th>Amount</th>
              <th>Sender</th>
              <th>Receiver VPA</th>
              <th>Layer</th>
              <th>Anomaly</th>
            </tr>
          </thead>
          <tbody>
            {recentTxns.slice(0, 5).map((t) => (
              <tr key={t.id}>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{t.txn_ref_no}</td>
                <td><span className="badge badge-medium">{t.rail_type}</span></td>
                <td style={{ fontWeight: 600 }}>{formatINR(t.amount_inr)}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{maskIdentifier(t.sender_upi)}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{maskIdentifier(t.receiver_upi)}</td>
                <td>Layer {t.layer_depth}</td>
                <td><RiskBadge score={t.anomaly_score} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
