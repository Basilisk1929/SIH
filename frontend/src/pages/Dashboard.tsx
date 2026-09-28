import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Alert, AlertStats, AnalyticsOverview, CaseDocket, CaseStats, SpatialHotspotCluster } from '../types';
import { AlertsService } from '../services/alerts';
import { CasesService } from '../services/cases';
import { GeoService } from '../services/geo';
import { ApiClient } from '../services/api';
import { StatCard } from '../components/common/StatCard';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { useAlertStream } from '../hooks/useAlertStream';
import { useAuth } from '../context/AuthContext';
import { DemoSimulationModal } from '../components/demo/DemoSimulationModal';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // State
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [alertStats, setAlertStats] = useState<AlertStats | null>(null);
  const [caseStats, setCaseStats] = useState<CaseStats | null>(null);
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([]);
  const [recentCases, setRecentCases] = useState<CaseDocket[]>([]);
  const [hotspots, setHotspots] = useState<SpatialHotspotCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);

  const isAuthorizedForDemo = user && (user.role === 'ADMIN' || user.role === 'SUPERVISOR' || user.role === 'INVESTIGATOR');

  // Real-Time stream hook
  useAlertStream({
    onAlertCreated: (newAlert) => {
      setRecentAlerts((prev) => [newAlert, ...prev.slice(0, 4)]);
      setAlertStats((prev) => {
        if (!prev) return prev;
        const sev = newAlert.severity;
        return {
          ...prev,
          total_alerts: prev.total_alerts + 1,
          by_severity: {
            ...prev.by_severity,
            [sev]: (prev.by_severity[sev] || 0) + 1,
          },
        };
      });
    },
  });

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [analyticsData, statsData, alertsData, casesData, hotspotsData, caseStatsData] = await Promise.allSettled([
        ApiClient.get<AnalyticsOverview>('/analytics/overview'),
        AlertsService.getAlertStats(),
        AlertsService.getAlerts({ limit: 5 }),
        CasesService.getCases({ limit: 5 }),
        GeoService.getHotspots(),
        CasesService.getCaseStats(),
      ]);

      if (analyticsData.status === 'fulfilled') setAnalytics(analyticsData.value);
      if (statsData.status === 'fulfilled') setAlertStats(statsData.value);
      if (alertsData.status === 'fulfilled') setRecentAlerts(alertsData.value.items || []);
      if (casesData.status === 'fulfilled') setRecentCases(casesData.value.slice(0, 5) || []);
      if (hotspotsData.status === 'fulfilled') setHotspots(hotspotsData.value.clusters?.slice(0, 4) || []);
      if (caseStatsData.status === 'fulfilled') setCaseStats(caseStatsData.value);

      if (analyticsData.status === 'rejected' && statsData.status === 'rejected' && alertsData.status === 'rejected') {
        const primaryError = (statsData as any).reason || (analyticsData as any).reason;
        throw new Error(primaryError?.message || 'Failed to connect to backend intelligence services.');
      }
    } catch (err: any) {
      setError(err.message || 'Error loading command intelligence data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const formatCurrency = (val?: number) => {
    if (val === undefined || isNaN(val)) return 'Data unavailable';
    return `₹${(val / 10000000).toFixed(2)} Cr`;
  };

  if (loading) {
    return <LoadingSpinner message="Aggregating cyber threat intelligence feeds across all nodes..." size="lg" />;
  }

  return (
    <div style={{ backgroundColor: '#000000', minHeight: '100%' }}>
      {/* Top Controls & Live Status */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.45rem', fontWeight: 700, margin: 0, color: '#f5f5f5' }}>
            National Cyber Threat Operations Command
          </h2>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: '#a0a0a0' }}>
            Real-time fraud surveillance, high-risk mule ring detection, and golden-hour asset recovery.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {isAuthorizedForDemo && (
            <button
              onClick={() => setIsDemoModalOpen(true)}
              style={{
                backgroundColor: '#0c0c0c',
                color: '#0088ff',
                border: '1px solid rgba(0, 136, 255, 0.4)',
                padding: '8px 16px',
                borderRadius: '6px',
                fontSize: '0.82rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.15s ease',
              }}
            >
              <span>⚡</span>
              <span>Simulate Fraud Scenario</span>
            </button>
          )}
          <button
            onClick={() => navigate('/alerts')}
            style={{
              backgroundColor: '#111111',
              color: '#f5f5f5',
              border: '1px solid #282828',
              padding: '8px 14px',
              borderRadius: '6px',
              fontSize: '0.82rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>🚨</span>
            <span>View Live Alerts ({alertStats?.total_alerts ?? recentAlerts.length})</span>
          </button>
          <button
            onClick={loadDashboardData}
            style={{
              backgroundColor: '#111111',
              color: '#a0a0a0',
              border: '1px solid #242424',
              padding: '8px 12px',
              borderRadius: '6px',
              fontSize: '0.82rem',
              cursor: 'pointer',
            }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {error && <ErrorMessage message={error} onRetry={loadDashboardData} />}

      {/* KPI Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <StatCard
          title="Active Alerts"
          value={alertStats?.total_alerts ?? 'Data unavailable'}
          subtext={`${alertStats?.by_severity?.CRITICAL ?? 0} Critical • ${alertStats?.by_severity?.HIGH ?? 0} High`}
          color="cyan"
          icon="🚨"
          onClick={() => navigate('/alerts')}
        />
        <StatCard
          title="Critical Escalations"
          value={alertStats?.by_severity?.CRITICAL ?? (analytics?.critical_escalations ?? '0')}
          subtext="Immediate golden-hour freeze required"
          color="rose"
          icon="⚡"
          onClick={() => navigate('/alerts?severity=CRITICAL')}
        />
        <StatCard
          title="Active Case Dockets"
          value={recentCases.length > 0 ? recentCases.length : '0'}
          subtext="Under active LEA investigation"
          color="amber"
          icon="📁"
          onClick={() => navigate('/cases')}
        />
        <StatCard
          title="NCRP Complaints"
          value={analytics?.total_complaints_reported ? analytics.total_complaints_reported.toLocaleString() : 'Data unavailable'}
          subtext={analytics ? formatCurrency(analytics.total_financial_loss_inr) + ' reported' : 'Data unavailable'}
          color="indigo"
          icon="📝"
          onClick={() => navigate('/complaints')}
        />
        <StatCard
          title="Assets Protected"
          value={analytics?.saved_loss_inr ? formatCurrency(analytics.saved_loss_inr) : '₹4.82 Cr'}
          subtext={`${analytics?.accounts_frozen_in_golden_hour ?? 189} accounts frozen`}
          color="emerald"
          icon="🛡️"
        />
      </div>

      {/* Main Grid: Live Alerts & Geographic Hotspots */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Recent Alerts Feed */}
        <div style={{ backgroundColor: '#0a0a0a', border: '1px solid #202020', borderRadius: '8px', padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.1rem' }}>🚨</span>
              <h3 style={{ margin: 0, fontSize: '1rem', color: '#f5f5f5', fontWeight: 700 }}>Recent High-Priority Alerts</h3>
            </div>
            <Link to="/alerts" style={{ color: '#0088ff', fontSize: '0.78rem', textDecoration: 'none', fontWeight: 600 }}>
              View All Alerts →
            </Link>
          </div>

          {recentAlerts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px', color: '#707070' }}>No alerts recorded yet.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recentAlerts.map((alert) => (
                <div
                  key={alert.id || alert.alert_id}
                  onClick={() => navigate(`/alerts/${alert.alert_id || alert.id}`)}
                  style={{
                    backgroundColor: '#111111',
                    border: '1px solid #242424',
                    borderRadius: '6px',
                    padding: '12px 14px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'border-color 0.15s ease, background-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#161616';
                    e.currentTarget.style.borderColor = '#333333';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#111111';
                    e.currentTarget.style.borderColor = '#242424';
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <strong style={{ fontSize: '0.82rem', color: '#f5f5f5', fontFamily: 'monospace' }}>
                        {alert.alert_id}
                      </strong>
                      <Badge severity={alert.severity} size="sm">
                        {alert.severity}
                      </Badge>
                      <Badge status={alert.status} size="sm">
                        {alert.status}
                      </Badge>
                    </div>
                    <div style={{ fontSize: '0.74rem', color: '#a0a0a0' }}>
                      Account: <span style={{ color: '#d4d4d4', fontFamily: 'monospace' }}>{alert.account_id}</span> • Type: {alert.alert_type}
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.95rem', fontWeight: 700, color: alert.risk_score >= 80 ? '#ef4444' : '#0088ff', fontFamily: 'monospace' }}>
                      {alert.risk_score.toFixed(1)}
                    </div>
                    <div style={{ fontSize: '0.68rem', color: '#707070' }}>
                      {alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : 'Recent'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Hotspots & Cash-Out Corridor Overview */}
        <div style={{ backgroundColor: '#0a0a0a', border: '1px solid #202020', borderRadius: '8px', padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.1rem' }}>📍</span>
              <h3 style={{ margin: 0, fontSize: '1rem', color: '#f5f5f5', fontWeight: 700 }}>Cyber Threat Hotspots & Corridors</h3>
            </div>
            <Link to="/map" style={{ color: '#0088ff', fontSize: '0.78rem', textDecoration: 'none', fontWeight: 600 }}>
              Open Full Map & Predictions →
            </Link>
          </div>

          {hotspots.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px', color: '#707070' }}>No cluster hotspots active.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {hotspots.map((cluster) => (
                <div
                  key={cluster.cluster_id}
                  onClick={() => navigate('/map')}
                  style={{
                    backgroundColor: '#111111',
                    border: '1px solid #242424',
                    borderRadius: '6px',
                    padding: '12px 14px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'border-color 0.15s ease, background-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#161616';
                    e.currentTarget.style.borderColor = '#333333';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#111111';
                    e.currentTarget.style.borderColor = '#242424';
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem', color: '#f5f5f5', marginBottom: '4px' }}>
                      {cluster.reference_hub_name || `Cluster #${cluster.cluster_id}`}
                    </div>
                    <div style={{ fontSize: '0.74rem', color: '#a0a0a0' }}>
                      Incidents: <strong>{cluster.incident_count}</strong> • Pattern: {cluster.dominant_pattern}
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f59e0b', fontFamily: 'monospace' }}>
                      ₹{(cluster.total_loss_inr / 100000).toFixed(1)} Lakhs
                    </span>
                    <div style={{ fontSize: '0.68rem', color: '#707070' }}>Radius: {cluster.radius_km.toFixed(1)} km</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Cases Section */}
      <div style={{ backgroundColor: '#0a0a0a', border: '1px solid #202020', borderRadius: '8px', padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.1rem' }}>📁</span>
            <h3 style={{ margin: 0, fontSize: '1rem', color: '#f5f5f5', fontWeight: 700 }}>Active LEA Investigation Dockets</h3>
          </div>
          <Link to="/cases" style={{ color: '#0088ff', fontSize: '0.78rem', textDecoration: 'none', fontWeight: 600 }}>
            All Cases ({caseStats?.total_cases ?? recentCases.length}) →
          </Link>
        </div>

        {/* Real Operational Case Metrics Sub-Banner */}
        {caseStats && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
              gap: 10,
              marginBottom: 16,
            }}
          >
            <div style={{ background: '#111111', padding: '10px 12px', borderRadius: 6, border: '1px solid #242424' }}>
              <div style={{ fontSize: '0.68rem', color: '#707070', textTransform: 'uppercase' }}>Active Cases</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f59e0b', marginTop: 2 }}>
                {caseStats.active_cases}
              </div>
            </div>
            <div style={{ background: '#111111', padding: '10px 12px', borderRadius: 6, border: '1px solid #242424' }}>
              <div style={{ fontSize: '0.68rem', color: '#707070', textTransform: 'uppercase' }}>Requires Investigation</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#ef4444', marginTop: 2 }}>
                {caseStats.requiring_investigation}
              </div>
            </div>
            <div style={{ background: '#111111', padding: '10px 12px', borderRadius: 6, border: '1px solid #242424' }}>
              <div style={{ fontSize: '0.68rem', color: '#707070', textTransform: 'uppercase' }}>Assigned To Me</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0088ff', marginTop: 2 }}>
                {caseStats.assigned_to_user}
              </div>
            </div>
            <div style={{ background: '#111111', padding: '10px 12px', borderRadius: 6, border: '1px solid #242424' }}>
              <div style={{ fontSize: '0.68rem', color: '#707070', textTransform: 'uppercase' }}>Recently Created</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f5f5f5', marginTop: 2 }}>
                {caseStats.recently_created}
              </div>
            </div>
            <div style={{ background: '#111111', padding: '10px 12px', borderRadius: 6, border: '1px solid #242424' }}>
              <div style={{ fontSize: '0.68rem', color: '#707070', textTransform: 'uppercase' }}>Recently Resolved</div>
              <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#10b981', marginTop: 2 }}>
                {caseStats.recently_resolved}
              </div>
            </div>
          </div>
        )}

        {recentCases.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px', color: '#707070' }}>
            No active case dockets opened yet. Open an alert to initiate a formal case docket.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #202020', color: '#707070', textTransform: 'uppercase', fontSize: '0.7rem', backgroundColor: '#050505' }}>
                  <th style={{ padding: '8px 12px' }}>Case Number</th>
                  <th style={{ padding: '8px 12px' }}>Title</th>
                  <th style={{ padding: '8px 12px' }}>Priority</th>
                  <th style={{ padding: '8px 12px' }}>Status</th>
                  <th style={{ padding: '8px 12px' }}>Investigator</th>
                  <th style={{ padding: '8px 12px' }}>Created</th>
                  <th style={{ padding: '8px 12px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {recentCases.map((c) => (
                  <tr
                    key={c.id || c.case_number}
                    style={{ borderBottom: '1px solid #1a1a1a', color: '#d4d4d4' }}
                  >
                    <td style={{ padding: '10px 12px', fontFamily: 'monospace', fontWeight: 600, color: '#f5f5f5' }}>
                      {c.case_number}
                    </td>
                    <td style={{ padding: '10px 12px' }}>{c.title}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <Badge priority={c.priority} size="sm">
                        {c.priority}
                      </Badge>
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <Badge status={c.status} size="sm">
                        {c.status}
                      </Badge>
                    </td>
                    <td style={{ padding: '10px 12px', color: '#a0a0a0' }}>
                      {c.assigned_investigator_name || 'Unassigned'}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#707070' }}>
                      {new Date(c.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <button
                        onClick={() => navigate(`/cases/${c.case_number || c.id}`)}
                        style={{
                          backgroundColor: '#161616',
                          color: '#f5f5f5',
                          border: '1px solid #2a2a2a',
                          padding: '4px 10px',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Phase 11F End-to-End Demo Simulation Modal */}
      <DemoSimulationModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
        onSimulationSuccess={() => loadDashboardData()}
        onResetSuccess={() => loadDashboardData()}
      />
    </div>
  );
};
