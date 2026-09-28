import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Alert, AlertSeverity, AlertStatus } from '../types';
import { AlertsService } from '../services/alerts';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import { Breadcrumbs } from '../components/common/Breadcrumbs';

export const Alerts: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Filters from query params
  const initialSeverity = (searchParams.get('severity') as AlertSeverity) || undefined;
  const initialStatus = (searchParams.get('status') as AlertStatus) || undefined;

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedSeverity, setSelectedSeverity] = useState<string>(initialSeverity || 'ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>(initialStatus || 'ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const limit = 20;

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await AlertsService.getAlerts({
        limit,
        offset: (page - 1) * limit,
        severity: selectedSeverity !== 'ALL' ? (selectedSeverity as AlertSeverity) : undefined,
        status: selectedStatus !== 'ALL' ? (selectedStatus as AlertStatus) : undefined,
        account_id: searchTerm.trim() ? searchTerm.trim() : undefined,
      });
      setAlerts(data.items || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      setError(err.message || 'Failed to load real-time alerts from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [selectedSeverity, selectedStatus, page]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchAlerts();
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div>
      <Breadcrumbs items={[{ label: 'Real-Time Alerts' }]} />

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, margin: 0, color: '#f8fafc' }}>
            Real-Time Alert Intelligence Stream
          </h2>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>
            Multi-factor evaluated fraud signals from ML Risk, Graph topology, velocity, and citizen complaint correlations.
          </p>
        </div>

        <button
          onClick={fetchAlerts}
          style={{
            backgroundColor: '#141414',
            color: '#f5f5f5',
            border: '1px solid #262626',
            padding: '8px 14px',
            borderRadius: '6px',
            fontSize: '0.8rem',
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          🔄 Refresh Stream
        </button>
      </div>

      {/* Filters Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          backgroundColor: '#0a0a0a',
          border: '1px solid #202020',
          borderRadius: '8px',
          padding: '12px 16px',
          marginBottom: '20px',
          flexWrap: 'wrap',
        }}
      >
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '8px', flex: 1, minWidth: '240px' }}>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Account Number or Alert ID..."
            style={{
              flex: 1,
              backgroundColor: '#050505',
              border: '1px solid #202020',
              color: '#f5f5f5',
              borderRadius: '6px',
              padding: '8px 12px',
              fontSize: '0.85rem',
            }}
          />
          <button
            type="submit"
            style={{
              backgroundColor: '#141414',
              color: '#f5f5f5',
              border: '1px solid #262626',
              padding: '8px 14px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              cursor: 'pointer',
            }}
          >
            Search
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '0.75rem', color: '#a0a0a0' }}>Severity:</label>
          <select
            value={selectedSeverity}
            onChange={(e) => {
              setSelectedSeverity(e.target.value);
              setPage(1);
            }}
            style={{
              backgroundColor: '#050505',
              color: '#f5f5f5',
              border: '1px solid #202020',
              padding: '6px 10px',
              borderRadius: '6px',
              fontSize: '0.8rem',
            }}
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '0.75rem', color: '#a0a0a0' }}>Status:</label>
          <select
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value);
              setPage(1);
            }}
            style={{
              backgroundColor: '#050505',
              color: '#f5f5f5',
              border: '1px solid #202020',
              padding: '6px 10px',
              borderRadius: '6px',
              fontSize: '0.8rem',
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="NEW">NEW</option>
            <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="FALSE_POSITIVE">FALSE POSITIVE</option>
          </select>
        </div>
      </div>

      {/* Loading and Error */}
      {loading && <LoadingSpinner message="Filtering alert intelligence records..." />}
      {error && <ErrorMessage message={error} onRetry={fetchAlerts} />}

      {/* Alerts Table */}
      {!loading && !error && alerts.length === 0 && (
        <EmptyState
          title="No Alerts Match Filters"
          description="There are currently no alert records matching the selected severity, status, or search query."
          actionLabel="Reset Filters"
          onAction={() => {
            setSelectedSeverity('ALL');
            setSelectedStatus('ALL');
            setSearchTerm('');
            setPage(1);
          }}
        />
      )}

      {!loading && !error && alerts.length > 0 && (
        <div style={{ backgroundColor: '#0a0a0a', border: '1px solid #202020', borderRadius: '10px', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: '#050505', borderBottom: '1px solid #202020', color: '#707070', textTransform: 'uppercase', fontSize: '0.7rem' }}>
                <th style={{ padding: '12px 16px' }}>Alert ID</th>
                <th style={{ padding: '12px 16px' }}>Severity</th>
                <th style={{ padding: '12px 16px' }}>Score</th>
                <th style={{ padding: '12px 16px' }}>Classification</th>
                <th style={{ padding: '12px 16px' }}>Target Account</th>
                <th style={{ padding: '12px 16px' }}>Status</th>
                <th style={{ padding: '12px 16px' }}>Created</th>
                <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert) => (
                <tr
                  key={alert.id || alert.alert_id}
                  onClick={() => navigate(`/alerts/${alert.alert_id || alert.id}`)}
                  style={{
                    borderBottom: '1px solid #1a1a1a',
                    cursor: 'pointer',
                    transition: 'background-color 0.1s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#141414')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  <td style={{ padding: '14px 16px', fontFamily: 'monospace', fontWeight: 600, color: '#f5f5f5' }}>
                    {alert.alert_id}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <Badge severity={alert.severity}>{alert.severity}</Badge>
                  </td>
                  <td style={{ padding: '14px 16px', fontFamily: 'monospace', fontWeight: 700, color: alert.risk_score >= 80 ? '#ef4444' : '#0088ff' }}>
                    {alert.risk_score.toFixed(1)}
                  </td>
                  <td style={{ padding: '14px 16px', color: '#a0a0a0' }}>
                    {alert.alert_type?.replace(/_/g, ' ')}
                  </td>
                  <td style={{ padding: '14px 16px', fontFamily: 'monospace', color: '#707070' }}>
                    {alert.account_id}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <Badge status={alert.status}>{alert.status}</Badge>
                  </td>
                  <td style={{ padding: '14px 16px', color: '#707070', fontSize: '0.75rem' }}>
                    {new Date(alert.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/alerts/${alert.alert_id || alert.id}`);
                      }}
                      style={{
                        backgroundColor: '#141414',
                        color: '#f5f5f5',
                        border: '1px solid #262626',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        fontSize: '0.75rem',
                        cursor: 'pointer',
                        fontWeight: 600,
                      }}
                    >
                      Investigate →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 16px',
              backgroundColor: '#050505',
              borderTop: '1px solid #202020',
              fontSize: '0.8rem',
              color: '#a0a0a0',
            }}
          >
            <div>
              Showing {alerts.length} of {total} total alerts (Page {page} of {totalPages})
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(p - 1, 1))}
                style={{
                  backgroundColor: '#0a0a0a',
                  color: page <= 1 ? '#404040' : '#f5f5f5',
                  border: '1px solid #202020',
                  padding: '4px 12px',
                  borderRadius: '4px',
                  cursor: page <= 1 ? 'not-allowed' : 'pointer',
                }}
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                style={{
                  backgroundColor: '#0a0a0a',
                  color: page >= totalPages ? '#404040' : '#f5f5f5',
                  border: '1px solid #202020',
                  padding: '4px 12px',
                  borderRadius: '4px',
                  cursor: page >= totalPages ? 'not-allowed' : 'pointer',
                }}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
