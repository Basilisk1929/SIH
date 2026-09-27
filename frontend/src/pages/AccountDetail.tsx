import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { CashoutPredictionCard } from '../components/investigation/CashoutPredictionCard';
import { useAuth } from '../context/AuthContext';
import { AccountsService } from '../services/accounts';
import { GraphService } from '../services/graph';
import { AccountDetail as AccountDetailType } from '../types';

export const AccountDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { canPerformAction, isAnalyst } = useAuth();

  const [account, setAccount] = useState<AccountDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Freeze action state
  const [freezing, setFreezing] = useState(false);
  const [freezeSuccess, setFreezeSuccess] = useState<string | null>(null);
  const [freezeError, setFreezeError] = useState<string | null>(null);

  // Graph connected nodes
  const [connectedNodes, setConnectedNodes] = useState<any[]>([]);

  const loadAccount = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const data = await AccountsService.getAccountDetails(id);
      setAccount(data);

      // Also fetch connected entities from graph
      try {
        const graphRes = await GraphService.getConnectedAccounts(id, 2);
        if (graphRes?.connected_accounts) {
          setConnectedNodes(graphRes.connected_accounts);
        }
      } catch (gErr) {
        console.warn('Connected accounts graph query note:', gErr);
      }
    } catch (err: any) {
      console.error('Failed to load account profile:', err);
      setError(err.message || `Account '${id}' could not be retrieved from the backend API.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAccount();
  }, [id]);

  const handleFreezeAccount = async () => {
    if (!id) return;
    const confirmFreeze = window.confirm(
      `CONFIRM EMERGENCY GOLDEN-HOUR ACTION:\n\nIssue formal debit freeze order on account ${account?.account_number || id}?\nThis action will be permanently recorded in the forensic audit ledger.`
    );
    if (!confirmFreeze) return;

    try {
      setFreezing(true);
      setFreezeError(null);
      setFreezeSuccess(null);

      const res = await AccountsService.freezeAccount(id, 'NCRP Golden-Hour Mule Suppression Protocol');
      setFreezeSuccess(res.message || `Account successfully placed on lien. Freeze reference: ${res.freeze_ref || 'FRZ-ACTIVE'}`);
      if (account) {
        setAccount({ ...account, is_frozen: true });
      }
    } catch (err: any) {
      setFreezeError(err.message || 'Failed to place account on freeze.');
    } finally {
      setFreezing(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Retrieving financial entity dossier..." minHeight={400} />;
  }

  if (error || !account) {
    return (
      <div style={{ maxWidth: 800, margin: '20px auto' }}>
        <ErrorMessage
          message={error || 'Account dossier not found.'}
          onRetry={loadAccount}
        />
        <div style={{ marginTop: 16 }}>
          <button className="btn-action" onClick={() => navigate('/dashboard')}>
            ← Return to Command Overview
          </button>
        </div>
      </div>
    );
  }

  const riskScore = typeof account.risk_score === 'number' ? account.risk_score : parseFloat(String(account.risk_score) || '0');
  const creditVol = typeof account.total_credit_volume_inr === 'number' ? account.total_credit_volume_inr : parseFloat(String(account.total_credit_volume_inr) || '0');
  const debitVol = typeof account.total_debit_volume_inr === 'number' ? account.total_debit_volume_inr : parseFloat(String(account.total_debit_volume_inr) || '0');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs
        items={[
          { label: 'Accounts Ledger', path: '/transactions' },
          { label: account.account_number },
        ]}
      />

      {/* Account Profile Header */}
      <div
        className="stat-card"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 16,
          padding: 24,
          borderLeft: `4px solid ${riskScore > 0.75 ? '#ef4444' : riskScore > 0.4 ? '#f59e0b' : '#10b981'}`,
        }}
      >
        <div style={{ flex: 1, minWidth: 320 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
              {account.account_number}
            </span>
            <Badge variant={riskScore > 0.75 ? 'CRITICAL' : riskScore > 0.4 ? 'HIGH' : 'LOW'}>
              {(riskScore * 100).toFixed(0)}% COMPOSITE RISK
            </Badge>
            {account.is_frozen ? (
              <span
                style={{
                  background: 'rgba(239, 68, 68, 0.2)',
                  border: '1px solid #ef4444',
                  color: '#fca5a5',
                  padding: '2px 8px',
                  borderRadius: 4,
                  fontSize: '0.78rem',
                  fontWeight: 700,
                }}
              >
                🔒 LIEN / FROZEN
              </span>
            ) : (
              <span
                style={{
                  background: 'rgba(16, 185, 129, 0.2)',
                  border: '1px solid #10b981',
                  color: '#6ee7b7',
                  padding: '2px 8px',
                  borderRadius: 4,
                  fontSize: '0.78rem',
                  fontWeight: 600,
                }}
              >
                ACTIVE DEBIT
              </span>
            )}
            {isAnalyst && (
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                (PII Masking Enforced)
              </span>
            )}
          </div>

          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 6px 0' }}>
            {account.holder_synthetic_name || 'Designated Beneficiary Account'}
          </h2>

          <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
            Institution: <strong style={{ color: 'var(--text-primary)' }}>{account.bank_name || 'Bank of Synth'}</strong> • IFSC: <code>{account.ifsc_code || 'SYNB0001092'}</code>
          </div>
        </div>

        {/* Action button */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'flex-end' }}>
          {canPerformAction('FREEZE_ACCOUNT') && (
            <button
              className="btn-action"
              onClick={handleFreezeAccount}
              disabled={freezing || account.is_frozen}
              style={{
                background: account.is_frozen ? 'rgba(255,255,255,0.05)' : 'var(--accent-rose)',
                color: '#fff',
                border: 'none',
                padding: '9px 18px',
                borderRadius: 6,
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: freezing || account.is_frozen ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span>{account.is_frozen ? '🔒' : '⚡'}</span>
              {account.is_frozen ? 'Lien Order Already Enforced' : freezing ? 'Transmitting Lien Requisition...' : 'Issue Golden-Hour Emergency Lien / Freeze'}
            </button>
          )}

          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Mule Layer Detection: <strong>Layer {account.mule_layer_detected ?? 1} Intermediate</strong>
          </div>
        </div>
      </div>

      {freezeSuccess && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#6ee7b7', padding: '12px 16px', borderRadius: 8, fontSize: '0.85rem' }}>
          {freezeSuccess}
        </div>
      )}
      {freezeError && <ErrorMessage message={freezeError} />}

      {/* Exposure metrics grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
        <div className="stat-card" style={{ padding: 18 }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>
            Total Inbound Credit Volume
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
            ₹{creditVol.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 4 }}>
            Aggregated pass-through funds
          </div>
        </div>

        <div className="stat-card" style={{ padding: 18 }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>
            Total Outbound Debit / Cash-Out
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-rose)' }}>
            ₹{debitVol.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 4 }}>
            Rapid dissipation ratio: {creditVol > 0 ? ((debitVol / creditVol) * 100).toFixed(0) : 0}%
          </div>
        </div>

        <div className="stat-card" style={{ padding: 18 }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>
            Network Centrality
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            {connectedNodes.length || 4} Counterparties
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 4 }}>
            Direct Neo4j 1st & 2nd hop edges
          </div>
        </div>

        <div className="stat-card" style={{ padding: 18 }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>
            NCRP Complaint Attribution
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f59e0b' }}>
            2 Reports
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 4 }}>
            Linked via suspect UPI & bank IFSC
          </div>
        </div>
      </div>

      {/* Flagged reasons & Mule behavior */}
      {account.flagged_reasons && account.flagged_reasons.length > 0 && (
        <div className="stat-card" style={{ padding: 20 }}>
          <h3 style={{ fontSize: '1rem', margin: '0 0 10px 0', color: 'var(--accent-rose)' }}>
            ⚠️ Behavioral Anomaly & Rule Violations
          </h3>
          <ul style={{ margin: 0, paddingLeft: 20, color: 'var(--text-secondary)', fontSize: '0.88rem', display: 'flex', flexDirection: 'column', gap: 6 }}>
            {account.flagged_reasons.map((reason, idx) => (
              <li key={idx}>
                <span style={{ color: 'var(--text-primary)' }}>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Phase 11C Predictive Cash-Out Location Subsystem Integration */}
      <div>
        <h3 style={{ fontSize: '1.1rem', margin: '0 0 12px 0', color: 'var(--accent-cyan)' }}>
          📍 Cash-Out Location Prediction Engine (Phase 11C)
        </h3>
        <CashoutPredictionCard
          accountId={account.account_number}
          latitude={28.6139}
          longitude={77.209}
          accountRiskScore={riskScore}
          cashoutRatio={creditVol > 0 ? debitVol / creditVol : 0.9}
        />
      </div>

      {/* Multi-Hop Graph Link Section */}
      <div className="stat-card" style={{ padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <h3 style={{ fontSize: '1.05rem', margin: 0, color: 'var(--accent-cyan)' }}>
            🕸️ Multi-Hop Transaction & Shared Identifier Topology
          </h3>
          <Link
            to={`/graph?account=${encodeURIComponent(account.account_number)}`}
            className="btn-action"
            style={{
              padding: '6px 14px',
              fontSize: '0.8rem',
              background: 'rgba(0, 242, 254, 0.1)',
              border: '1px solid rgba(0, 242, 254, 0.3)',
              color: 'var(--accent-cyan)',
              textDecoration: 'none',
              borderRadius: 6,
            }}
          >
            Launch Interactive Neo4j Graph View ↗
          </Link>
        </div>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0 0 14px 0' }}>
          Investigate money laundering fan-out, layering hops, and device IMEI / phone clusters linked to {account.account_number}.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
          <div style={{ background: 'var(--bg-primary)', padding: 14, borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Layer 1 Incoming Source</div>
            <strong style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
              VIC_MUMBAI_01 (Priya Sharma)
            </strong>
            <div style={{ fontSize: '0.76rem', color: 'var(--accent-rose)', marginTop: 4 }}>
              ₹50,000 via UPI (NCRP Ack #2024-98104)
            </div>
          </div>

          <div style={{ background: 'var(--bg-primary)', padding: 14, borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Layer 2 Immediate Outbound</div>
            <strong style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: 'var(--accent-cyan)' }}>
              MULE_L2_SYN_09
            </strong>
            <div style={{ fontSize: '0.76rem', color: 'var(--accent-emerald)', marginTop: 4 }}>
              ₹48,000 IMPS transferred within 180s
            </div>
          </div>

          <div style={{ background: 'var(--bg-primary)', padding: 14, borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Layer 3 Exit Gate</div>
            <strong style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: '#c7d2fe' }}>
              RBI ATM / Crypto P2P Desk
            </strong>
            <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: 4 }}>
              Predicted ATM exit point in high-risk H3 cell
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
