import React, { useEffect, useState } from 'react';
import { RiskBadge } from '../components/common/RiskBadge';
import { ApiService, formatINR, maskIdentifier } from '../services/api';
import { Complaint } from '../types';

export const Workbench: React.FC = () => {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [selectedComplaint, setSelectedComplaint] = useState<Complaint | null>(null);
  const [frozenStatus, setFrozenStatus] = useState<Record<string, boolean>>({});

  useEffect(() => {
    async function loadComplaints() {
      const res = await ApiService.getComplaints(15);
      setComplaints(res.items);
      if (res.items.length > 0) {
        setSelectedComplaint(res.items[0]);
      }
    }
    loadComplaints();
  }, []);

  const handleSimulatedFreeze = (ack: string) => {
    setFrozenStatus((prev) => ({ ...prev, [ack]: true }));
  };

  return (
    <div className="content-body" style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 24 }}>
      {/* List Panel */}
      <div className="data-table-card">
        <div className="table-header">
          <h2 className="table-title">1930 / NCRP Priority Triage Queue</h2>
        </div>
        <table>
          <thead>
            <tr>
              <th>Ack Number</th>
              <th>Category</th>
              <th>Loss</th>
              <th>Risk</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {complaints.map((c) => (
              <tr
                key={c.id}
                onClick={() => setSelectedComplaint(c)}
                style={{
                  cursor: 'pointer',
                  backgroundColor: selectedComplaint?.id === c.id ? 'var(--bg-card-hover)' : undefined,
                }}
              >
                <td style={{ fontFamily: 'var(--font-mono)' }}>{c.acknowledgement_no}</td>
                <td>{c.category}</td>
                <td>{formatINR(c.reported_loss_inr)}</td>
                <td><RiskBadge score={c.risk_score} /></td>
                <td>
                  <button className="btn-action" onClick={(e) => { e.stopPropagation(); setSelectedComplaint(c); }}>
                    Inspect
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail / Forensic Inspection Panel */}
      {selectedComplaint && (
        <div className="stat-card" style={{ height: 'fit-content' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: '1.1rem' }}>Forensic Case Dossier</h3>
            <span className="badge badge-high">{selectedComplaint.status}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: '0.88rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Ack Number: </span>
              <strong style={{ fontFamily: 'var(--font-mono)' }}>{selectedComplaint.acknowledgement_no}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Modus Operandi: </span>
              <strong>{selectedComplaint.subcategory || selectedComplaint.category}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Reported Loss: </span>
              <strong style={{ color: 'var(--accent-rose)', fontSize: '1.1rem' }}>
                {formatINR(selectedComplaint.reported_loss_inr)}
              </strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Jurisdiction: </span>
              <strong>{selectedComplaint.victim_district}, {selectedComplaint.victim_state}</strong>
            </div>

            <hr style={{ borderColor: 'var(--border-subtle)', margin: '8px 0' }} />

            <div>
              <h4 style={{ fontSize: '0.9rem', color: 'var(--accent-cyan)', marginBottom: 6 }}>
                Suspect Financial Identifiers (NLP Extracted)
              </h4>
              <div style={{ background: 'var(--bg-primary)', padding: 12, borderRadius: 6, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div>UPI VPA: <code style={{ color: 'var(--accent-cyan)' }}>{selectedComplaint.suspect_upi || 'N/A'}</code></div>
                <div>Account: <code>{selectedComplaint.suspect_account_number || 'N/A'}</code></div>
                <div>IFSC: <code>{selectedComplaint.suspect_ifsc || 'N/A'}</code></div>
                <div>Phone: <code>{maskIdentifier(selectedComplaint.suspect_phone)}</code></div>
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: 4 }}>Incident Narrative</h4>
              <p style={{ background: 'rgba(255, 255, 255, 0.02)', padding: 10, borderRadius: 6, fontSize: '0.8rem', lineHeight: 1.4 }}>
                {selectedComplaint.description_synthetic}
              </p>
            </div>

            <div style={{ marginTop: 12 }}>
              {frozenStatus[selectedComplaint.acknowledgement_no] ? (
                <div style={{ color: 'var(--accent-emerald)', fontWeight: 600, padding: 8, background: 'rgba(16, 185, 129, 0.1)', borderRadius: 6, textAlign: 'center' }}>
                  ✓ Bank Notified: Simulated Golden-Hour Freeze Issued
                </div>
              ) : (
                <button
                  className="btn-action"
                  style={{ width: '100%', padding: '10px', background: 'var(--accent-rose)', color: '#fff', borderColor: 'var(--accent-rose)' }}
                  onClick={() => handleSimulatedFreeze(selectedComplaint.acknowledgement_no)}
                >
                  ⚡ Issue Simulated Emergency Golden-Hour Lien / Freeze
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
