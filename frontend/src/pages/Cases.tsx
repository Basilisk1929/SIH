import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import { useAuth } from '../context/AuthContext';
import { CasesService, CreateCasePayload } from '../services/cases';
import { CaseDocket, CasePriority, CaseStats } from '../types';


export const Cases: React.FC = () => {
  const navigate = useNavigate();
  const { user, canPerformAction } = useAuth();

  const [cases, setCases] = useState<CaseDocket[]>([]);
  const [stats, setStats] = useState<CaseStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [investigatorFilter, setInvestigatorFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Modal for new case
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [newCase, setNewCase] = useState<CreateCasePayload>({
    title: '',
    priority: CasePriority.HIGH,
    alert_id: '',
    initial_notes: '',
    assigned_investigator_name: user?.full_name || '',
    assigned_investigator_id: user?.id || '',
    linked_alert_ids: [],
    linked_account_numbers: [],
    linked_complaint_ids: [],
    total_exposure_inr: 0,
  });

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [casesData, statsData] = await Promise.allSettled([
        CasesService.getCases({
          status: statusFilter,
          priority: priorityFilter,
          severity: severityFilter,
          investigator: investigatorFilter,
          q: searchQuery,
          limit: 100,
        }),
        CasesService.getCaseStats(),
      ]);

      if (casesData.status === 'fulfilled') {
        setCases(casesData.value || []);
      } else {
        throw new Error('Failed to load case records from backend API.');
      }

      if (statsData.status === 'fulfilled') {
        setStats(statsData.value);
      }
    } catch (err: any) {
      console.error('Failed to load cases:', err);
      setError(err.message || 'Unable to retrieve case records from backend API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter, priorityFilter, severityFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleResetFilters = () => {
    setStatusFilter('ALL');
    setPriorityFilter('ALL');
    setSeverityFilter('ALL');
    setInvestigatorFilter('');
    setStartDate('');
    setEndDate('');
    setSearchQuery('');
  };

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCase.title.trim()) {
      setCreateError('Case title is required.');
      return;
    }

    try {
      setCreating(true);
      setCreateError(null);
      const created = await CasesService.createCase(newCase);
      setShowCreateModal(false);
      setNewCase({
        title: '',
        priority: CasePriority.HIGH,
        alert_id: '',
        initial_notes: '',
        assigned_investigator_name: user?.full_name || '',
        assigned_investigator_id: user?.id || '',
      });
      navigate(`/cases/${created.case_number || created.id}`);
    } catch (err: any) {
      setCreateError(err.message || 'Failed to initialize case docket.');
    } finally {
      setCreating(false);
    }
  };

  // Client-side date filter if specified
  const filteredCases = cases.filter((c) => {
    if (startDate) {
      const cDate = new Date(c.created_at).getTime();
      const sDate = new Date(startDate).getTime();
      if (cDate < sDate) return false;
    }
    if (endDate) {
      const cDate = new Date(c.created_at).getTime();
      const eDate = new Date(endDate).getTime() + 86400000;
      if (cDate > eDate) return false;
    }
    if (investigatorFilter.trim()) {
      const invQ = investigatorFilter.toLowerCase();
      const assigned = (c.assigned_investigator || c.assigned_to || c.assigned_investigator_name || '').toLowerCase();
      if (!assigned.includes(invQ)) return false;
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            📁 Official Case Docket Registry
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
            Statutory law enforcement investigation files, evidentiary tracking, and multi-agency coordination dockets.
          </p>
        </div>

        {canPerformAction('CREATE_CASE') && (
          <button
            className="btn-action"
            style={{
              background: 'linear-gradient(135deg, #00f2fe, #4facfe)',
              color: '#070a12',
              fontWeight: 700,
              border: 'none',
              padding: '10px 18px',
              borderRadius: 6,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              boxShadow: '0 0 14px rgba(0, 242, 254, 0.25)',
            }}
            onClick={() => setShowCreateModal(true)}
          >
            <span>➕</span> Open New Case Docket
          </button>
        )}
      </div>

      {/* Metrics Bar */}
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14 }}>
          <div className="stat-card" style={{ padding: '14px 18px', borderLeft: '3px solid #00f2fe' }}>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Total Case Dockets
            </div>
            <div style={{ fontSize: '1.45rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
              {stats.total_cases}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: 2 }}>
              Across all LEA jurisdictions
            </div>
          </div>

          <div className="stat-card" style={{ padding: '14px 18px', borderLeft: '3px solid #f59e0b' }}>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Active Investigations
            </div>
            <div style={{ fontSize: '1.45rem', fontWeight: 700, color: '#f59e0b', marginTop: 4 }}>
              {stats.active_cases}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: 2 }}>
              Under active detective inquiry
            </div>
          </div>

          <div className="stat-card" style={{ padding: '14px 18px', borderLeft: '3px solid #ef4444' }}>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Requires Action / Unassigned
            </div>
            <div style={{ fontSize: '1.45rem', fontWeight: 700, color: '#ef4444', marginTop: 4 }}>
              {stats.requiring_investigation}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: 2 }}>
              Open dockets needing investigator
            </div>
          </div>

          <div className="stat-card" style={{ padding: '14px 18px', borderLeft: '3px solid #10b981' }}>
            <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Resolved (Last 7 Days)
            </div>
            <div style={{ fontSize: '1.45rem', fontWeight: 700, color: '#10b981', marginTop: 4 }}>
              {stats.recently_resolved}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: 2 }}>
              Disposed with legal findings
            </div>
          </div>
        </div>
      )}

      {/* Filter toolbar */}
      <div
        className="stat-card"
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          padding: '16px 20px',
        }}
      >
        <form
          onSubmit={handleSearchSubmit}
          style={{
            display: 'flex',
            gap: 12,
            alignItems: 'center',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ flex: 1, minWidth: 260 }}>
            <input
              type="text"
              placeholder="Search by Case ID, Alert ID, title, or account number..."
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

          <button
            type="submit"
            className="btn-action"
            style={{
              background: 'var(--accent-cyan)',
              color: '#070a12',
              fontWeight: 700,
              border: 'none',
              padding: '8px 16px',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: '0.85rem',
            }}
          >
            🔍 Search
          </button>
        </form>

        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginRight: 6 }}>Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                padding: '6px 10px',
                borderRadius: 6,
                fontSize: '0.82rem',
              }}
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="ASSIGNED">ASSIGNED</option>
              <option value="INVESTIGATING">INVESTIGATING</option>
              <option value="ON_HOLD">ON HOLD</option>
              <option value="RESOLVED">RESOLVED</option>
              <option value="CLOSED">CLOSED</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginRight: 6 }}>Priority:</label>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              style={{
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                padding: '6px 10px',
                borderRadius: 6,
                fontSize: '0.82rem',
              }}
            >
              <option value="ALL">All Priorities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="LOW">LOW</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginRight: 6 }}>Investigator:</label>
            <input
              type="text"
              placeholder="Filter by officer name/badge"
              value={investigatorFilter}
              onChange={(e) => setInvestigatorFilter(e.target.value)}
              style={{
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                padding: '6px 10px',
                borderRadius: 6,
                fontSize: '0.82rem',
                width: 180,
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginRight: 6 }}>From:</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                padding: '5px 8px',
                borderRadius: 6,
                fontSize: '0.82rem',
              }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginRight: 6 }}>To:</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={{
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                padding: '5px 8px',
                borderRadius: 6,
                fontSize: '0.82rem',
              }}
            />
          </div>

          <button
            type="button"
            onClick={handleResetFilters}
            style={{
              background: 'none',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-muted)',
              padding: '6px 12px',
              borderRadius: 6,
              fontSize: '0.82rem',
              cursor: 'pointer',
            }}
          >
            Clear Filters
          </button>

          <button
            type="button"
            className="btn-action"
            onClick={loadData}
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '6px 12px',
              borderRadius: 6,
              fontSize: '0.82rem',
              cursor: 'pointer',
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Main cases table */}
      {loading ? (
        <LoadingSpinner text="Retrieving evidentiary case registry..." minHeight={300} />
      ) : error ? (
        <ErrorMessage message={error} onRetry={loadData} />
      ) : filteredCases.length === 0 ? (
        <EmptyState
          title="No Case Dockets Found"
          message={
            searchQuery || statusFilter !== 'ALL' || priorityFilter !== 'ALL' || investigatorFilter
              ? 'No cases match your active filter parameters.'
              : 'No formal case dockets have been registered yet. Create a case from high-risk alerts or use the button above.'
          }
          actionLabel={canPerformAction('CREATE_CASE') ? 'Open First Case Docket' : undefined}
          onAction={canPerformAction('CREATE_CASE') ? () => setShowCreateModal(true) : undefined}
        />
      ) : (
        <div className="data-table-card">
          <table>
            <thead>
              <tr>
                <th>Case Identifier</th>
                <th>Title / Incident Summary</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Originating Alert</th>
                <th>Lead Investigator</th>
                <th>Evidence Items</th>
                <th>Created Timestamp</th>
                <th>Updated</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredCases.map((c) => (
                <tr
                  key={c.id || c.case_number}
                  onClick={() => navigate(`/cases/${c.case_number || c.id}`)}
                  style={{ cursor: 'pointer' }}
                >
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                    {c.case_number || c.id.slice(0, 12)}
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{c.title}</div>
                    {c.total_fraud_amount_inr || c.total_exposure_inr ? (
                      <div style={{ fontSize: '0.78rem', color: 'var(--accent-rose)' }}>
                        Loss Exposure: ₹{(c.total_fraud_amount_inr || c.total_exposure_inr || 0).toLocaleString('en-IN')}
                      </div>
                    ) : null}
                  </td>
                  <td>
                    <Badge variant={c.priority as any}>{c.priority}</Badge>
                  </td>
                  <td>
                    <Badge variant={c.status === 'RESOLVED' || c.status === 'CLOSED' ? 'LOW' : 'HIGH'}>
                      {c.status.replace(/_/g, ' ')}
                    </Badge>
                  </td>
                  <td>
                    {c.alert_id ? (
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>
                        {c.alert_id}
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Direct Docket</span>
                    )}
                  </td>
                  <td>
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {c.assigned_investigator || c.assigned_to || c.assigned_investigator_name || 'Unassigned'}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    {(c.evidence?.length || c.evidence_count || 0)} items • {(c.notes?.length || c.notes_count || 0)} notes
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {new Date(c.created_at).toLocaleDateString('en-IN', {
                      day: '2-digit',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {c.updated_at
                      ? new Date(c.updated_at).toLocaleDateString('en-IN', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric',
                        })
                      : '—'}
                  </td>
                  <td>
                    <button
                      className="btn-action"
                      style={{
                        padding: '6px 12px',
                        fontSize: '0.78rem',
                        background: 'rgba(0, 242, 254, 0.1)',
                        border: '1px solid rgba(0, 242, 254, 0.3)',
                        color: 'var(--accent-cyan)',
                        borderRadius: 4,
                        cursor: 'pointer',
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/cases/${c.case_number || c.id}`);
                      }}
                    >
                      Inspect Docket →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal: Open Case Docket */}
      {showCreateModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(7, 10, 18, 0.85)',
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
              maxWidth: 600,
              width: '100%',
              background: '#0d1322',
              border: '1px solid var(--border-subtle)',
              borderRadius: 12,
              padding: 24,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontSize: '1.2rem', margin: 0, color: 'var(--text-primary)' }}>
                📂 Initialize Official Case Docket
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
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

            {createError && <ErrorMessage message={createError} />}

            <form onSubmit={handleCreateCase} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Case Docket Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Operation CyberMule - Syndicate Alpha Phishing Ring"
                  value={newCase.title}
                  onChange={(e) => setNewCase({ ...newCase, title: e.target.value })}
                  style={{
                    width: '100%',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 6,
                    padding: '8px 12px',
                    color: 'var(--text-primary)',
                    fontSize: '0.88rem',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                    Priority Rating
                  </label>
                  <select
                    value={newCase.priority}
                    onChange={(e) => setNewCase({ ...newCase, priority: e.target.value as CasePriority })}
                    style={{
                      width: '100%',
                      background: 'var(--bg-primary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 6,
                      padding: '8px 12px',
                      color: 'var(--text-primary)',
                      fontSize: '0.88rem',
                    }}
                  >
                    <option value={CasePriority.CRITICAL}>CRITICAL</option>
                    <option value={CasePriority.HIGH}>HIGH</option>
                    <option value={CasePriority.MEDIUM}>MEDIUM</option>
                    <option value={CasePriority.LOW}>LOW</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                    Lead Investigator
                  </label>
                  <input
                    type="text"
                    placeholder="Officer name or badge"
                    value={newCase.assigned_investigator_name || ''}
                    onChange={(e) => setNewCase({ ...newCase, assigned_investigator_name: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--bg-primary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 6,
                      padding: '8px 12px',
                      color: 'var(--text-primary)',
                      fontSize: '0.88rem',
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                    Estimated Exposure (₹ INR)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="1000"
                    placeholder="0"
                    value={newCase.total_exposure_inr || ''}
                    onChange={(e) => setNewCase({ ...newCase, total_exposure_inr: parseFloat(e.target.value) || 0 })}
                    style={{
                      width: '100%',
                      background: 'var(--bg-primary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 6,
                      padding: '8px 12px',
                      color: 'var(--text-primary)',
                      fontSize: '0.88rem',
                    }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                    Originating Alert ID (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. ALT-2024-9001"
                    value={newCase.alert_id || ''}
                    onChange={(e) => setNewCase({ ...newCase, alert_id: e.target.value })}
                    style={{
                      width: '100%',
                      background: 'var(--bg-primary)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 6,
                      padding: '8px 12px',
                      color: 'var(--text-primary)',
                      fontSize: '0.88rem',
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Initial Forensic Notes & Legal Basis
                </label>
                <textarea
                  rows={4}
                  placeholder="Enter initial investigation brief, section of IT Act / BNS, and immediate action directives..."
                  value={newCase.initial_notes}
                  onChange={(e) => setNewCase({ ...newCase, initial_notes: e.target.value })}
                  style={{
                    width: '100%',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 6,
                    padding: '8px 12px',
                    color: 'var(--text-primary)',
                    fontSize: '0.88rem',
                    resize: 'vertical',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
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
                  disabled={creating}
                  className="btn-action"
                  style={{
                    background: 'var(--accent-cyan)',
                    color: '#070a12',
                    fontWeight: 700,
                    border: 'none',
                    padding: '8px 20px',
                    borderRadius: 6,
                    cursor: creating ? 'not-allowed' : 'pointer',
                  }}
                >
                  {creating ? 'Registering Docket...' : 'Create Case Docket'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
