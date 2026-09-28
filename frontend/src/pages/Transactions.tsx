import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import { TransactionsService, TransactionPipelineInput, TransactionPipelineOutput } from '../services/transactions';
import { Transaction } from '../types';

export const Transactions: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [railFilter, setRailFilter] = useState<string>('ALL');
  const [suspiciousOnly, setSuspiciousOnly] = useState(false);

  // Selected Transaction for Drawer / Detail
  const [selectedTxn, setSelectedTxn] = useState<Transaction | null>(null);

  // Live Pipeline Evaluation Modal (Demonstration of XGBoost, Graph, Geo, and Alert pipeline)
  const [showEvaluateModal, setShowEvaluateModal] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<TransactionPipelineOutput | null>(null);
  const [evalError, setEvalError] = useState<string | null>(null);

  const [evalForm, setEvalForm] = useState<TransactionPipelineInput>({
    sender_account: 'SYN1000004465',
    receiver_account: 'SYN1000002170',
    amount: 85000,
    rail_type: 'UPI',
    sender_upi: 'victim_priya@synthaxis',
    receiver_upi: 'fastmule_88@synthaxis',
    latitude: 28.6139,
    longitude: 77.209,
    transactions_last_1h: 6,
    transactions_last_24h: 18,
    cashout_ratio: 0.94,
    graph_degree: 5,
    complaint_link_count: 2,
  });

  const loadTransactions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await TransactionsService.getRecentTransactions(35);
      setTransactions(data || []);
      if (data && data.length > 0 && !selectedTxn) {
        setSelectedTxn(data[0]);
      }
    } catch (err: any) {
      console.error('Failed to load transactions:', err);
      setError(err.message || 'Unable to retrieve transactions from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, []);

  const handleRunPipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setEvaluating(true);
      setEvalError(null);
      setEvalResult(null);

      const res = await TransactionsService.evaluatePipeline(evalForm);
      setEvalResult(res);
      // Reload recent transactions to include new evaluation if stored
      loadTransactions();
    } catch (err: any) {
      setEvalError(err.message || 'Pipeline evaluation encountered a backend error.');
    } finally {
      setEvaluating(false);
    }
  };

  const filteredTxns = transactions.filter((t) => {
    if (railFilter !== 'ALL' && t.rail_type !== railFilter) return false;
    if (suspiciousOnly && !t.is_flagged_suspicious && (t.anomaly_score || 0) < 0.7) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchId = t.id?.toLowerCase().includes(q) || t.txn_ref_no?.toLowerCase().includes(q);
      const matchSender = t.sender_account?.toLowerCase().includes(q) || t.sender_upi?.toLowerCase().includes(q);
      const matchReceiver = t.receiver_account?.toLowerCase().includes(q) || t.receiver_upi?.toLowerCase().includes(q);
      if (!matchId && !matchSender && !matchReceiver) return false;
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            💳 High-Velocity Transaction Ledger
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
            Real-time interbank transaction stream analyzed with XGBoost anomaly detection and multi-hop velocity tracking.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            className="btn-action"
            style={{
              background: '#0088ff',
              color: '#ffffff',
              fontWeight: 600,
              border: 'none',
              padding: '9px 16px',
              borderRadius: 6,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
            onClick={() => setShowEvaluateModal(true)}
          >
            <span>⚡</span> Evaluate Transaction Pipeline
          </button>
        </div>
      </div>

      {/* Filter toolbar */}
      <div
        className="stat-card"
        style={{
          display: 'flex',
          gap: 16,
          alignItems: 'center',
          flexWrap: 'wrap',
          padding: '14px 18px',
        }}
      >
        <div style={{ flex: 1, minWidth: 240 }}>
          <input
            type="text"
            placeholder="Search by Txn Ref, Account, or UPI VPA..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 6,
              padding: '8px 14px',
              color: 'var(--text-primary)',
              fontSize: '0.88rem',
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Rail:</label>
          <select
            value={railFilter}
            onChange={(e) => setRailFilter(e.target.value)}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '7px 12px',
              borderRadius: 6,
              fontSize: '0.85rem',
            }}
          >
            <option value="ALL">All Payment Rails</option>
            <option value="UPI">UPI</option>
            <option value="IMPS">IMPS</option>
            <option value="NEFT">NEFT</option>
            <option value="RTGS">RTGS</option>
            <option value="ATM">ATM Cashout</option>
          </select>

          <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={suspiciousOnly}
              onChange={(e) => setSuspiciousOnly(e.target.checked)}
            />
            Flagged Suspicious Only
          </label>

          <button
            className="btn-action"
            onClick={loadTransactions}
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '7px 14px',
              borderRadius: 6,
              fontSize: '0.85rem',
              cursor: 'pointer',
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Main split grid: Ledger table on left, Inspection card on right */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedTxn ? '1.4fr 1fr' : '1fr', gap: 20 }}>
        {/* Ledger Table */}
        <div>
          {loading ? (
            <LoadingSpinner text="Streaming transaction ledger..." minHeight={300} />
          ) : error ? (
            <ErrorMessage message={error} onRetry={loadTransactions} />
          ) : filteredTxns.length === 0 ? (
            <EmptyState
              title="No Transactions Found"
              message="No transactions match your search filter criteria."
            />
          ) : (
            <div className="data-table-card">
              <table>
                <thead>
                  <tr>
                    <th>Ref / Identifier</th>
                    <th>Rail</th>
                    <th>Sender</th>
                    <th>Beneficiary</th>
                    <th>Amount (INR)</th>
                    <th>XGBoost Score</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTxns.map((t) => {
                    const isSelected = selectedTxn?.id === t.id;
                    const score = t.anomaly_score ?? 0;
                    return (
                      <tr
                        key={t.id}
                        onClick={() => setSelectedTxn(t)}
                        style={{
                          cursor: 'pointer',
                          backgroundColor: isSelected ? '#141414' : undefined,
                          borderLeft: isSelected ? '3px solid #0088ff' : '3px solid transparent',
                        }}
                      >
                        <td>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                            {t.txn_ref_no || t.id}
                          </div>
                          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                            {t.timestamp ? new Date(t.timestamp).toLocaleTimeString() : 'Recent'}
                          </div>
                        </td>
                        <td>
                          <span
                            style={{
                              padding: '2px 8px',
                              borderRadius: 4,
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              background: t.rail_type === 'UPI' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                              color: t.rail_type === 'UPI' ? '#c7d2fe' : '#6ee7b7',
                            }}
                          >
                            {t.rail_type || 'UPI'}
                          </span>
                        </td>
                        <td>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                            {t.sender_account}
                          </div>
                          {t.sender_upi && (
                            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{t.sender_upi}</div>
                          )}
                        </td>
                        <td>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--accent-cyan)' }}>
                            {t.receiver_account}
                          </div>
                          {t.receiver_upi && (
                            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{t.receiver_upi}</div>
                          )}
                        </td>
                        <td style={{ fontWeight: 700, color: (t.amount_inr ?? (t as any).amount ?? 0) > 50000 ? 'var(--accent-rose)' : 'var(--text-primary)' }}>
                          ₹{(t.amount_inr ?? (t as any).amount ?? 0).toLocaleString('en-IN')}
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <div
                              style={{
                                width: 44,
                                height: 6,
                                background: 'rgba(255,255,255,0.1)',
                                borderRadius: 3,
                                overflow: 'hidden',
                              }}
                            >
                              <div
                                style={{
                                  width: `${Math.round(score * 100)}%`,
                                  height: '100%',
                                  background: score > 0.8 ? '#ef4444' : score > 0.5 ? '#f59e0b' : '#10b981',
                                }}
                              />
                            </div>
                            <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                              {(score * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                        <td>
                          {t.is_flagged_suspicious || score > 0.7 ? (
                            <Badge variant="HIGH">FLAGGED</Badge>
                          ) : (
                            <Badge variant="LOW">NORMAL</Badge>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Selected Transaction Forensic Inspection Drawer */}
        {selectedTxn && (
          <div className="stat-card" style={{ height: 'fit-content', padding: 22 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Forensic Transaction Inspection
                </div>
                <h3 style={{ margin: '4px 0 0 0', fontSize: '1.15rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                  {selectedTxn.txn_ref_no || selectedTxn.id}
                </h3>
              </div>
              <Badge variant={(selectedTxn.anomaly_score || 0) > 0.75 ? 'CRITICAL' : (selectedTxn.anomaly_score || 0) > 0.4 ? 'HIGH' : 'LOW'}>
                {((selectedTxn.anomaly_score || 0) * 100).toFixed(0)}% ANOMALY
              </Badge>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14, fontSize: '0.86rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div style={{ background: 'var(--bg-primary)', padding: 12, borderRadius: 6 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Originating Account</div>
                  <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                    {selectedTxn.sender_account}
                  </strong>
                  {selectedTxn.sender_upi && (
                    <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                      {selectedTxn.sender_upi}
                    </div>
                  )}
                  <div style={{ marginTop: 8 }}>
                    <Link
                      to={`/accounts/${encodeURIComponent(selectedTxn.sender_account || '')}`}
                      style={{ fontSize: '0.78rem', color: 'var(--accent-cyan)', textDecoration: 'none' }}
                    >
                      Inspect Account →
                    </Link>
                  </div>
                </div>

                <div style={{ background: 'var(--bg-primary)', padding: 12, borderRadius: 6 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Beneficiary Account</div>
                  <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                    {selectedTxn.receiver_account}
                  </strong>
                  {selectedTxn.receiver_upi && (
                    <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                      {selectedTxn.receiver_upi}
                    </div>
                  )}
                  <div style={{ marginTop: 8 }}>
                    <Link
                      to={`/accounts/${encodeURIComponent(selectedTxn.receiver_account || '')}`}
                      style={{ fontSize: '0.78rem', color: 'var(--accent-cyan)', textDecoration: 'none' }}
                    >
                      Inspect Account →
                    </Link>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.02)', borderRadius: 6 }}>
                <span style={{ color: 'var(--text-muted)' }}>Transferred Volume:</span>
                <strong style={{ color: 'var(--accent-rose)', fontSize: '1.1rem' }}>
                  ₹{(selectedTxn.amount_inr ?? (selectedTxn as any).amount ?? 0).toLocaleString('en-IN')}
                </strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.02)', borderRadius: 6 }}>
                <span style={{ color: 'var(--text-muted)' }}>Settlement Rail:</span>
                <strong style={{ color: 'var(--text-primary)' }}>{selectedTxn.rail_type || 'UPI Rail'}</strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.02)', borderRadius: 6 }}>
                <span style={{ color: 'var(--text-muted)' }}>Mule Layer Depth:</span>
                <strong>Layer {selectedTxn.layer_depth || 1} Intermediary</strong>
              </div>

              {/* Real ML explanation box */}
              <div style={{ background: '#141414', border: '1px solid #202020', borderRadius: 6, padding: 12 }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.85rem', marginBottom: 6 }}>
                  🤖 XGBoost Inference & Risk Attribution
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                  {(selectedTxn.anomaly_score || 0) > 0.7
                    ? 'Anomaly triggered by high burst velocity (multiple credits within 10 minutes) followed by rapid outbound pass-through to mule layer 2. Disproportionate volume against historical average.'
                    : 'Standard transaction velocity. Model confidence within baseline parameters for this entity archetype.'}
                </div>
              </div>

              {/* Action Links */}
              <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
                <Link
                  to={`/graph?account=${encodeURIComponent(selectedTxn.receiver_account || '')}`}
                  className="btn-action"
                  style={{
                    flex: 1,
                    textAlign: 'center',
                    padding: '8px',
                    fontSize: '0.82rem',
                    background: 'rgba(255,255,255,0.06)',
                    color: 'var(--text-primary)',
                    textDecoration: 'none',
                    borderRadius: 6,
                  }}
                >
                  🕸️ View Graph
                </Link>
                <Link
                  to={`/map?lat=28.6139&lng=77.2090`}
                  className="btn-action"
                  style={{
                    flex: 1,
                    textAlign: 'center',
                    padding: '8px',
                    fontSize: '0.82rem',
                    background: 'rgba(255,255,255,0.06)',
                    color: 'var(--text-primary)',
                    textDecoration: 'none',
                    borderRadius: 6,
                  }}
                >
                  🗺️ View Geo Hotspot
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Evaluate Transaction Pipeline Modal */}
      {showEvaluateModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 20,
          }}
        >
          <div
            className="stat-card"
            style={{
              maxWidth: 700,
              width: '100%',
              background: '#0a0a0a',
              border: '1px solid #202020',
              borderRadius: 12,
              padding: 24,
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <h2 style={{ fontSize: '1.2rem', margin: 0, color: '#f5f5f5' }}>
                  ⚡ End-to-End Transaction Pipeline Evaluation
                </h2>
                <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Simulates full flow: Ingestion → Validation → PostgreSQL → XGBoost ML → Neo4j → Geo H3 → Alert Engine
                </p>
              </div>
              <button
                onClick={() => {
                  setShowEvaluateModal(false);
                  setEvalResult(null);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  fontSize: '1.2rem',
                  cursor: 'pointer',
                }}
              >
                ✕
              </button>
            </div>

            {evalError && <ErrorMessage message={evalError} />}

            {evalResult ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', padding: 12, borderRadius: 8 }}>
                  <div style={{ fontWeight: 700, color: '#6ee7b7', fontSize: '0.95rem' }}>
                    ✓ Pipeline Executed Successfully: {evalResult.transaction_id}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 4 }}>
                    Evaluated at: {new Date(evalResult.timestamp || Date.now()).toLocaleTimeString()}
                  </div>
                </div>

                {/* Risk assessment result */}
                <div style={{ background: 'var(--bg-primary)', padding: 14, borderRadius: 8 }}>
                  <h4 style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: 'var(--accent-cyan)' }}>
                    🤖 XGBoost Risk Assessment Output
                  </h4>
                  <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 8 }}>
                    <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-rose)' }}>
                      {((evalResult.risk_assessment?.risk_score || 0) * 100).toFixed(1)}%
                    </div>
                    <Badge variant={(evalResult.risk_assessment?.risk_band as any) || 'CRITICAL'}>
                      {evalResult.risk_assessment?.risk_band || 'CRITICAL'}
                    </Badge>
                  </div>
                  {evalResult.risk_assessment?.reasons && (
                    <ul style={{ margin: 0, paddingLeft: 18, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {evalResult.risk_assessment.reasons.map((r: string, idx: number) => (
                        <li key={idx}>{r}</li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Alert triggered */}
                {evalResult.alert && (
                  <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', padding: 14, borderRadius: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong style={{ color: '#fca5a5', fontSize: '0.9rem' }}>
                        🚨 Real-Time Alert Engine Fired!
                      </strong>
                      <Badge variant={evalResult.alert.severity as any}>{evalResult.alert.severity}</Badge>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)', marginTop: 6 }}>
                      Alert ID: <code>{evalResult.alert.alert_id || evalResult.alert.id}</code> ({evalResult.alert.alert_type})
                    </div>
                    <div style={{ marginTop: 10 }}>
                      <Link
                        to={`/alerts/${evalResult.alert.id || evalResult.alert.alert_id}`}
                        className="btn-action"
                        style={{
                          fontSize: '0.8rem',
                          background: 'var(--accent-cyan)',
                          color: '#070a12',
                          textDecoration: 'none',
                          padding: '6px 14px',
                          borderRadius: 4,
                          fontWeight: 700,
                        }}
                      >
                        Inspect Generated Alert →
                      </Link>
                    </div>
                  </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                  <button
                    type="button"
                    onClick={() => setEvalResult(null)}
                    className="btn-action"
                    style={{
                      background: 'rgba(255,255,255,0.08)',
                      color: 'var(--text-primary)',
                      padding: '8px 16px',
                      borderRadius: 6,
                    }}
                  >
                    Evaluate Another Scenario
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowEvaluateModal(false)}
                    className="btn-action"
                    style={{
                      background: 'var(--accent-cyan)',
                      color: '#070a12',
                      padding: '8px 16px',
                      borderRadius: 6,
                      fontWeight: 700,
                    }}
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleRunPipeline} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                      Sender Account
                    </label>
                    <input
                      type="text"
                      required
                      value={evalForm.sender_account}
                      onChange={(e) => setEvalForm({ ...evalForm, sender_account: e.target.value })}
                      style={{
                        width: '100%',
                        background: 'var(--bg-primary)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 6,
                        padding: '8px 12px',
                        color: 'var(--text-primary)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.85rem',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                      Beneficiary Account (Mule)
                    </label>
                    <input
                      type="text"
                      required
                      value={evalForm.receiver_account}
                      onChange={(e) => setEvalForm({ ...evalForm, receiver_account: e.target.value })}
                      style={{
                        width: '100%',
                        background: 'var(--bg-primary)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 6,
                        padding: '8px 12px',
                        color: 'var(--text-primary)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.85rem',
                      }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                      Amount (₹ INR)
                    </label>
                    <input
                      type="number"
                      required
                      value={evalForm.amount}
                      onChange={(e) => setEvalForm({ ...evalForm, amount: parseFloat(e.target.value) || 0 })}
                      style={{
                        width: '100%',
                        background: 'var(--bg-primary)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 6,
                        padding: '8px 12px',
                        color: 'var(--text-primary)',
                        fontSize: '0.85rem',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                      Rail Type
                    </label>
                    <select
                      value={evalForm.rail_type}
                      onChange={(e) => setEvalForm({ ...evalForm, rail_type: e.target.value })}
                      style={{
                        width: '100%',
                        background: 'var(--bg-primary)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 6,
                        padding: '8px 12px',
                        color: 'var(--text-primary)',
                        fontSize: '0.85rem',
                      }}
                    >
                      <option value="UPI">UPI</option>
                      <option value="IMPS">IMPS</option>
                      <option value="NEFT">NEFT</option>
                      <option value="RTGS">RTGS</option>
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                      Cashout Ratio (0.0 - 1.0)
                    </label>
                    <input
                      type="number"
                      step="0.05"
                      min="0"
                      max="1"
                      value={evalForm.cashout_ratio}
                      onChange={(e) => setEvalForm({ ...evalForm, cashout_ratio: parseFloat(e.target.value) || 0 })}
                      style={{
                        width: '100%',
                        background: 'var(--bg-primary)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 6,
                        padding: '8px 12px',
                        color: 'var(--text-primary)',
                        fontSize: '0.85rem',
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>
                      Txn Velocity (Last 1 Hour)
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={evalForm.transactions_last_1h}
                      onChange={(e) => setEvalForm({ ...evalForm, transactions_last_1h: parseInt(e.target.value) || 0 })}
                      style={{
                        width: '100%',
                        background: 'var(--bg-primary)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 6,
                        padding: '8px 12px',
                        color: 'var(--text-primary)',
                        fontSize: '0.85rem',
                      }}
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
                  <button
                    type="button"
                    onClick={() => setShowEvaluateModal(false)}
                    style={{
                      background: 'none',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-secondary)',
                      padding: '8px 16px',
                      borderRadius: 6,
                      cursor: 'pointer',
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={evaluating}
                    className="btn-action"
                    style={{
                      background: '#0088ff',
                      color: '#ffffff',
                      fontWeight: 600,
                      border: 'none',
                      padding: '8px 20px',
                      borderRadius: 6,
                      cursor: evaluating ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {evaluating ? 'Executing ML & Pipeline...' : 'Run Pipeline Inference'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
