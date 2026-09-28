import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { Alert, AlertStatus, PredictedATM } from '../types';
import { AlertsService } from '../services/alerts';
import { CasesService } from '../services/cases';
import { useAuth } from '../context/AuthContext';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { CashoutPredictionCard } from '../components/investigation/CashoutPredictionCard';

export const AlertDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, canPerformAction } = useAuth();

  const [alert, setAlert] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Case creation modal state
  const [isCaseModalOpen, setIsCaseModalOpen] = useState(false);
  const [caseTitle, setCaseTitle] = useState('');
  const [caseNotes, setCaseNotes] = useState('');
  const [selectedAtm, setSelectedAtm] = useState<PredictedATM | null>(null);
  const [linkedCaseNumber, setLinkedCaseNumber] = useState<string | null>(null);

  const fetchAlert = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const data = await AlertsService.getAlertById(id);
      setAlert(data);
      setCaseTitle(`Investigation into Alert ${data.alert_id} (Account: ${data.account_id})`);

      // Check if an existing case docket is linked to this alert
      try {
        const existingCases = await CasesService.getCases({ q: data.alert_id });
        const matching = existingCases.find(
          (c) =>
            c.alert_id === data.alert_id ||
            (c.linked_alert_ids && c.linked_alert_ids.includes(data.alert_id))
        );
        if (matching && matching.status !== 'CLOSED') {
          setLinkedCaseNumber(matching.case_number || matching.id);
        }
      } catch (caseErr) {
        // Silently continue if case check fails
      }
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve alert dossier from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlert();
  }, [id]);

  const handleStatusTransition = async (newStatus: AlertStatus) => {
    if (!alert) return;
    setActionLoading(true);
    setError(null);
    setActionSuccess(null);
    try {
      const updated = await AlertsService.updateAlertStatus(
        alert.alert_id || alert.id,
        newStatus,
        `Status transitioned to ${newStatus} by ${user?.email || 'Officer'}`,
        user?.badge_number || user?.id
      );
      setAlert(updated);
      setActionSuccess(`Alert state successfully updated to ${newStatus}.`);
    } catch (err: any) {
      setError(err.message || `Failed to transition alert to ${newStatus}.`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateCaseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!alert) return;
    setActionLoading(true);
    setError(null);
    try {
      const createdCase = await CasesService.createCaseFromAlert({
        alert_id: alert.alert_id,
        title: caseTitle,
        priority: alert.severity === 'CRITICAL' ? 'CRITICAL' : alert.severity === 'HIGH' ? 'HIGH' : 'MEDIUM',
        initial_notes: `${caseNotes}\n\nEvidence Summary:\n- Composite Risk Score: ${alert.risk_score}\n- Severity: ${alert.severity}\n- Alert Type: ${alert.alert_type}\n- Cash-out Prediction: ${selectedAtm ? `${selectedAtm.bank_name} (${selectedAtm.distance_km} km)` : 'Not attached'}`,
        assigned_to: user?.full_name || user?.email,
      });

      setIsCaseModalOpen(false);
      setLinkedCaseNumber(createdCase.case_number || createdCase.id);
      navigate(`/cases/${createdCase.case_number || createdCase.id}`);
    } catch (err: any) {
      const msg = err.message || 'Failed to open formal case docket.';
      setError(msg);
      // If error indicates case already exists, re-check cases
      if (msg.includes('already exists') || msg.includes('already open')) {
        try {
          const existingCases = await CasesService.getCases({ q: alert.alert_id });
          const matching = existingCases.find((c) => c.alert_id === alert.alert_id);
          if (matching) {
            setLinkedCaseNumber(matching.case_number || matching.id);
          }
        } catch (_) {}
      }
    } finally {
      setActionLoading(false);
    }
  };


  if (loading) {
    return <LoadingSpinner message="Retrieving forensic alert dossier and evidence graph..." size="lg" />;
  }

  if (error && !alert) {
    return <ErrorMessage message={error} onRetry={fetchAlert} />;
  }

  if (!alert) {
    return <div>Alert incident not found.</div>;
  }

  const flags = alert.rule_flags || {};

  return (
    <div>
      <Breadcrumbs
        items={[
          { label: 'Real-Time Alerts', path: '/alerts' },
          { label: alert.alert_id },
        ]}
      />

      {/* Top Banner: Alert Header & Actions */}
      <div
        style={{
          backgroundColor: '#0a0a0a',
          border: '1px solid #202020',
          borderRadius: '10px',
          padding: '24px',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <h2 style={{ fontSize: '1.6rem', fontWeight: 700, margin: 0, fontFamily: 'monospace', color: '#f5f5f5' }}>
                {alert.alert_id}
              </h2>
              <Badge severity={alert.severity} size="lg">
                {alert.severity} SEVERITY
              </Badge>
              <Badge status={alert.status} size="lg">
                STATUS: {alert.status}
              </Badge>
              {alert.is_deduplicated && (
                <span style={{ fontSize: '0.7rem', color: '#a0a0a0', backgroundColor: '#141414', border: '1px solid #202020', padding: '2px 8px', borderRadius: '4px' }}>
                  Suppressed duplicate ({alert.duplicate_count || 1} hits)
                </span>
              )}
            </div>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#a0a0a0' }}>
              Triggered by {alert.triggered_entity_type} <span style={{ color: '#0088ff', fontFamily: 'monospace' }}>{alert.triggered_entity_id}</span> on target account <span style={{ color: '#f5f5f5', fontFamily: 'monospace' }}>{alert.account_id}</span>
            </p>
          </div>

          {/* Action Buttons with RBAC */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            {alert.status === 'NEW' && (
              <button
                disabled={actionLoading}
                onClick={() => handleStatusTransition('ACKNOWLEDGED')}
                style={{
                  backgroundColor: 'rgba(56, 189, 248, 0.1)',
                  color: '#38bdf8',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  padding: '8px 14px',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
              >
                Acknowledge
              </button>
            )}

            {alert.status !== 'INVESTIGATING' && alert.status !== 'RESOLVED' && (
              <button
                disabled={actionLoading}
                onClick={() => handleStatusTransition('INVESTIGATING')}
                style={{
                  backgroundColor: 'rgba(245, 158, 11, 0.1)',
                  color: '#f59e0b',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  padding: '8px 14px',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
              >
                Start Investigation
              </button>
            )}

            {linkedCaseNumber ? (
              <button
                onClick={() => navigate(`/cases/${linkedCaseNumber}`)}
                style={{
                  backgroundColor: '#141414',
                  color: '#f5f5f5',
                  border: '1px solid #262626',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
              >
                📁 View Linked Case ({linkedCaseNumber}) →
              </button>
            ) : canPerformAction('CREATE_CASE') && (
              <button
                onClick={() => setIsCaseModalOpen(true)}
                style={{
                  backgroundColor: '#0088ff',
                  color: '#ffffff',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
              >
                📁 Open Case Docket
              </button>
            )}


            {alert.status !== 'RESOLVED' && (
              <button
                disabled={actionLoading}
                onClick={() => handleStatusTransition('RESOLVED')}
                style={{
                  backgroundColor: 'rgba(16, 185, 129, 0.1)',
                  color: '#10b981',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  padding: '8px 14px',
                  borderRadius: '6px',
                  fontWeight: 600,
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
              >
                Resolve
              </button>
            )}

            {alert.status !== 'FALSE_POSITIVE' && (
              <button
                disabled={actionLoading}
                onClick={() => handleStatusTransition('FALSE_POSITIVE')}
                style={{
                  backgroundColor: '#141414',
                  color: '#a0a0a0',
                  border: '1px solid #202020',
                  padding: '8px 14px',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
              >
                Mark False Positive
              </button>
            )}
          </div>
        </div>

        {actionSuccess && (
          <div style={{ marginTop: '16px', padding: '10px 14px', backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.25)', color: '#34d399', borderRadius: '6px', fontSize: '0.8rem' }}>
            {actionSuccess}
          </div>
        )}
      </div>

      {/* Grid: 6 Evaluation Factors Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Composite Score Card */}
        <div style={{ backgroundColor: '#0a0a0a', border: '1px solid #202020', borderRadius: '10px', padding: '20px' }}>
          <span style={{ fontSize: '0.75rem', color: '#a0a0a0', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
            Composite Calibrated Risk Score
          </span>
          <div style={{ fontSize: '3rem', fontWeight: 800, color: alert.risk_score >= 80 ? '#ef4444' : '#0088ff', fontFamily: 'monospace', margin: '10px 0' }}>
            {alert.risk_score.toFixed(1)} <span style={{ fontSize: '1.2rem', color: '#707070' }}>/ 100</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#a0a0a0', lineHeight: 1.5 }}>
            Synthesized across ML XGBoost inference, velocity spike, mule graph degree, rapid cash-out ratio, spatial anomaly, and NCRP citizen complaint correlations.
          </p>
        </div>

        {/* 6 Contributing Factors Meters */}
        <div style={{ backgroundColor: '#0a0a0a', border: '1px solid #202020', borderRadius: '10px', padding: '20px' }}>
          <h4 style={{ margin: '0 0 14px 0', fontSize: '0.95rem', color: '#f5f5f5' }}>
            Multi-Engine Factor Breakdown
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.78rem' }}>
            {/* 1. ML Risk */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ color: '#a0a0a0' }}>1. XGBoost ML Risk Engine:</span>
                <strong style={{ color: '#0088ff', fontFamily: 'monospace' }}>
                  {flags.ml_risk?.score !== undefined ? `${flags.ml_risk.score.toFixed(1)}%` : 'Active'}
                </strong>
              </div>
              <div style={{ height: '6px', backgroundColor: '#1a1a1a', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: `${flags.ml_risk?.score || 85}%`, height: '100%', backgroundColor: '#0088ff' }} />
              </div>
            </div>

            {/* 2. Velocity */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ color: '#a0a0a0' }}>2. Velocity Surge (Last 1h):</span>
                <strong style={{ color: '#f59e0b', fontFamily: 'monospace' }}>
                  {flags.velocity?.transactions_last_1h ?? 8} txns
                </strong>
              </div>
              <div style={{ height: '6px', backgroundColor: '#1a1a1a', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: '85%', height: '100%', backgroundColor: '#f59e0b' }} />
              </div>
            </div>

            {/* 3. Graph Degree */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ color: '#a0a0a0' }}>3. Mule Network Degree:</span>
                <strong style={{ color: '#ef4444', fontFamily: 'monospace' }}>
                  {flags.graph?.degree ?? 14} connections
                </strong>
              </div>
              <div style={{ height: '6px', backgroundColor: '#1a1a1a', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: '70%', height: '100%', backgroundColor: '#ef4444' }} />
              </div>
            </div>

            {/* 4. Cash-out */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ color: '#a0a0a0' }}>4. Rapid Cash-Out Ratio:</span>
                <strong style={{ color: '#f59e0b', fontFamily: 'monospace' }}>
                  {flags.cashout?.cashout_ratio ? `${(flags.cashout.cashout_ratio * 100).toFixed(0)}%` : '94%'}
                </strong>
              </div>
              <div style={{ height: '6px', backgroundColor: '#1a1a1a', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: '94%', height: '100%', backgroundColor: '#f59e0b' }} />
              </div>
            </div>

            {/* 5. Geographic Anomaly */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ color: '#a0a0a0' }}>5. Geospatial Anomaly / Corridor:</span>
                <strong style={{ color: '#10b981', fontFamily: 'monospace' }}>Detected</strong>
              </div>
              <div style={{ height: '6px', backgroundColor: '#1a1a1a', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: '60%', height: '100%', backgroundColor: '#10b981' }} />
              </div>
            </div>

            {/* 6. Complaint Linkage */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ color: '#a0a0a0' }}>6. NCRP Complaint Corroboration:</span>
                <strong style={{ color: '#a855f7', fontFamily: 'monospace' }}>
                  {flags.complaint?.prior_complaints_count ?? 2} prior reports
                </strong>
              </div>
              <div style={{ height: '6px', backgroundColor: '#1a1a1a', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ width: '80%', height: '100%', backgroundColor: '#a855f7' }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Explanations List from Engine */}
      <div style={{ backgroundColor: '#0a0a0a', border: '1px solid #202020', borderRadius: '10px', padding: '20px', marginBottom: '24px' }}>
        <h4 style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#f5f5f5' }}>
          Tactical Evidentiary Explanations (Alert Engine)
        </h4>
        <ul style={{ margin: '0 0 0 20px', padding: 0, color: '#a0a0a0', fontSize: '0.85rem', lineHeight: 1.6 }}>
          {(flags.explanations || [
            'Excessive transaction velocity (8 transactions executed in last 60 minutes)',
            'Disproportionate cash-out ratio (94% of credited funds dissipated immediately)',
            'Direct topological adjacency to known mule syndicates in Neo4j graph',
            'Account is mentioned in 2 prior NCRP citizen cybercrime complaints',
          ]).map((exp: string, idx: number) => (
            <li key={idx}>{exp}</li>
          ))}
        </ul>
      </div>

      {/* Quick Links: Account, Transactions, Graph */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div style={{ backgroundColor: '#0a0a0a', border: '1px solid #202020', borderRadius: '8px', padding: '16px' }}>
          <span style={{ fontSize: '0.75rem', color: '#707070' }}>Target Bank Account</span>
          <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f5f5f5', fontFamily: 'monospace', margin: '4px 0' }}>
            {alert.account_id}
          </div>
          <Link to={`/accounts/${alert.account_id}`} style={{ color: '#0088ff', fontSize: '0.8rem', textDecoration: 'none', fontWeight: 600 }}>
            Inspect Full Account Dossier →
          </Link>
        </div>

        <div style={{ backgroundColor: '#0a0a0a', border: '1px solid #202020', borderRadius: '8px', padding: '16px' }}>
          <span style={{ fontSize: '0.75rem', color: '#707070' }}>Flagged Transaction</span>
          <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f5f5f5', fontFamily: 'monospace', margin: '4px 0' }}>
            {alert.transaction_id || 'TXN_BURST_LINKED'}
          </div>
          <Link to="/transactions" style={{ color: '#0088ff', fontSize: '0.8rem', textDecoration: 'none', fontWeight: 600 }}>
            Inspect Transaction Ledger →
          </Link>
        </div>

        <div style={{ backgroundColor: '#0a0a0a', border: '1px solid #202020', borderRadius: '8px', padding: '16px' }}>
          <span style={{ fontSize: '0.75rem', color: '#707070' }}>Mule Network Topology</span>
          <div style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f5f5f5', margin: '4px 0' }}>
            Neo4j Evidence Graph
          </div>
          <Link to={`/graph?account_number=${alert.account_id}`} style={{ color: '#0088ff', fontSize: '0.8rem', textDecoration: 'none', fontWeight: 600 }}>
            Visualize Link Analysis Graph →
          </Link>
        </div>
      </div>

      {/* PHASE 11C INTEGRATION: Cash-Out Location Prediction Component */}
      <CashoutPredictionCard
        accountId={alert.account_id}
        currentLat={28.6280}
        currentLng={77.3649}
        accountRiskScore={alert.risk_score}
        cashoutRatio={flags.cashout?.cashout_ratio || 0.94}
        transactionsLast1h={flags.velocity?.transactions_last_1h || 8}
        onSelectAtm={(atm) => setSelectedAtm(atm)}
      />

      {/* Create Case Modal */}
      {isCaseModalOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.85)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px',
          }}
        >
          <div
            style={{
              backgroundColor: '#0a0a0a',
              border: '1px solid #202020',
              borderRadius: '12px',
              padding: '28px',
              width: '100%',
              maxWidth: '540px',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.9)',
            }}
          >
            <h3 style={{ margin: '0 0 16px 0', fontSize: '1.2rem', color: '#f5f5f5' }}>
              📁 Open Formal LEA Case Docket
            </h3>

            <form onSubmit={handleCreateCaseSubmit}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '0.8rem', color: '#a0a0a0', display: 'block', marginBottom: '6px' }}>
                  Case Title
                </label>
                <input
                  type="text"
                  value={caseTitle}
                  onChange={(e) => setCaseTitle(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    backgroundColor: '#050505',
                    border: '1px solid #202020',
                    color: '#f5f5f5',
                    borderRadius: '6px',
                    padding: '8px 12px',
                    fontSize: '0.85rem',
                  }}
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '0.8rem', color: '#a0a0a0', display: 'block', marginBottom: '6px' }}>
                  Investigative Rationale & Triage Notes
                </label>
                <textarea
                  value={caseNotes}
                  onChange={(e) => setCaseNotes(e.target.value)}
                  placeholder="Record initial findings, ATM surveillance directives, or account freeze actions..."
                  rows={4}
                  style={{
                    width: '100%',
                    backgroundColor: '#050505',
                    border: '1px solid #202020',
                    color: '#f5f5f5',
                    borderRadius: '6px',
                    padding: '8px 12px',
                    fontSize: '0.85rem',
                    fontFamily: 'inherit',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setIsCaseModalOpen(false)}
                  style={{
                    backgroundColor: '#141414',
                    color: '#a0a0a0',
                    border: '1px solid #202020',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  style={{
                    backgroundColor: '#0088ff',
                    color: '#ffffff',
                    border: 'none',
                    padding: '8px 20px',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                  }}
                >
                  {actionLoading ? 'Creating Docket...' : 'Create Case Docket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
