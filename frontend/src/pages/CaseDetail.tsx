import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { Breadcrumbs } from '../components/common/Breadcrumbs';
import { CashoutPredictionCard } from '../components/investigation/CashoutPredictionCard';
import { useAuth } from '../context/AuthContext';
import { CasesService } from '../services/cases';
import {
  CaseDocket,
  CaseEvidenceItem,
  CaseNoteItem,
  CasePriority,
  CaseStatus,
  CaseTimelineEventItem,
} from '../types';

export const CaseDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user, canPerformAction, isAdmin, isSupervisor } = useAuth();


  const [caseData, setCaseData] = useState<CaseDocket | null>(null);
  const [notes, setNotes] = useState<CaseNoteItem[]>([]);
  const [evidence, setEvidence] = useState<CaseEvidenceItem[]>([]);
  const [timeline, setTimeline] = useState<CaseTimelineEventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active section tab
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'EVIDENCE' | 'NOTES' | 'TIMELINE' | 'DISPOSITION'>('OVERVIEW');

  // Status & Note update state
  const [actionLoading, setActionLoading] = useState(false);
  const [newStatus, setNewStatus] = useState<CaseStatus>('INVESTIGATING');
  const [newPriority, setNewPriority] = useState<CasePriority>('HIGH');
  const [investigationNotes, setInvestigationNotes] = useState('');
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);


  // New Note Modal
  const [noteContent, setNoteContent] = useState('');
  const [noteInternal, setNoteInternal] = useState(true);

  // New Evidence Modal
  const [showEvidenceModal, setShowEvidenceModal] = useState(false);
  const [evidenceType, setEvidenceType] = useState('ACCOUNT');
  const [evidenceRef, setEvidenceRef] = useState('');
  const [evidenceTitle, setEvidenceTitle] = useState('');
  const [evidenceDesc, setEvidenceDesc] = useState('');

  // Resolution Modal
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolutionCategory, setResolutionCategory] = useState('CONFIRMED_FRAUD');
  const [resolutionReason, setResolutionReason] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');

  // Close Docket Modal
  const [showCloseModal, setShowCloseModal] = useState(false);
  const [closureReason, setClosureReason] = useState('Investigation completed and submitted to judicial authority');

  // Assignment Modal
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assigneeInput, setAssigneeInput] = useState('');
  const [assignNotes, setAssignNotes] = useState('');

  // Dossier Export state
  const [exportLoading, setExportLoading] = useState(false);
  const [exportResult, setExportResult] = useState<any | null>(null);
  const [showExportModal, setShowExportModal] = useState(false);

  // Cashout suspect account
  const [selectedSuspectAccount, setSelectedSuspectAccount] = useState<string>('');

  const loadCase = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const data = await CasesService.getCaseById(id);
      setCaseData(data);
      setNewStatus(data.status || 'INVESTIGATING');
      setNewPriority(data.priority || 'HIGH');


      // Load sub-resources (notes, evidence, timeline)
      const [notesRes, evRes, tlRes] = await Promise.allSettled([
        CasesService.getNotes(id),
        CasesService.getEvidence(id),
        CasesService.getTimeline(id),
      ]);

      if (notesRes.status === 'fulfilled') setNotes(notesRes.value || []);
      if (evRes.status === 'fulfilled') setEvidence(evRes.value || []);
      if (tlRes.status === 'fulfilled') setTimeline(tlRes.value || []);

      // Selected account for cashout exploration
      const linkedAcc =
        data.linked_account_numbers?.[0] ||
        (data as any).linked_accounts?.[0] ||
        (evRes.status === 'fulfilled' ? evRes.value.find((e) => e.evidence_type === 'ACCOUNT')?.evidence_reference_id : null);
      setSelectedSuspectAccount(linkedAcc || 'SYN1000004465');
    } catch (err: any) {
      console.error('Failed to load case docket:', err);
      setError(err.message || `Case docket '${id}' could not be retrieved from the backend API.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCase();
  }, [id]);

  const handleUpdateStatusAndPriority = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      setActionLoading(true);
      setActionError(null);
      setActionSuccess(null);

      const updated = await CasesService.updateCase(id, {
        status: newStatus,
        priority: newPriority,
        additional_notes: investigationNotes.trim() ? investigationNotes : undefined,
      });

      setCaseData(updated);
      setActionSuccess(`Case docket updated successfully (Status: ${newStatus}). Audit log dispatched.`);
      setInvestigationNotes('');
      // Reload sub-resources
      const [tlRes, notesRes] = await Promise.all([CasesService.getTimeline(id), CasesService.getNotes(id)]);
      setTimeline(tlRes);
      setNotes(notesRes);
    } catch (err: any) {
      setActionError(err.message || 'Failed to update case docket.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !noteContent.trim()) return;
    try {
      setActionLoading(true);
      setActionError(null);
      await CasesService.addNote(id, {
        content: noteContent.trim(),
        is_internal: noteInternal,
      });
      setNoteContent('');
      setActionSuccess('Forensic note appended to case docket.');
      const [nRes, tlRes] = await Promise.all([CasesService.getNotes(id), CasesService.getTimeline(id)]);
      setNotes(nRes);
      setTimeline(tlRes);
    } catch (err: any) {
      setActionError(err.message || 'Failed to add note.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !evidenceRef.trim() || !evidenceTitle.trim()) return;
    try {
      setActionLoading(true);
      setActionError(null);
      await CasesService.addEvidence(id, {
        evidence_type: evidenceType,
        evidence_reference_id: evidenceRef.trim(),
        title: evidenceTitle.trim(),
        description: evidenceDesc.trim() || undefined,
      });
      setShowEvidenceModal(false);
      setEvidenceRef('');
      setEvidenceTitle('');
      setEvidenceDesc('');
      setActionSuccess('Evidence reference attached to case docket.');
      const [eRes, tlRes] = await Promise.all([CasesService.getEvidence(id), CasesService.getTimeline(id)]);
      setEvidence(eRes);
      setTimeline(tlRes);
    } catch (err: any) {
      setActionError(err.message || 'Failed to attach evidence.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !assigneeInput.trim()) return;
    try {
      setActionLoading(true);
      setActionError(null);
      const updated = await CasesService.assignCase(id, {
        assigned_investigator: assigneeInput.trim(),
        notes: assignNotes.trim() || undefined,
      });
      setCaseData(updated);
      setShowAssignModal(false);
      setAssignNotes('');
      setActionSuccess(`Case successfully assigned to ${assigneeInput}.`);
      const tlRes = await CasesService.getTimeline(id);
      setTimeline(tlRes);
    } catch (err: any) {
      setActionError(err.message || 'Failed to assign case.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !resolutionNotes.trim()) return;
    try {
      setActionLoading(true);
      setActionError(null);
      const updated = await CasesService.resolveCase(id, {
        resolution_category: resolutionCategory,
        resolution_reason: resolutionReason.trim() || undefined,
        resolution_notes: resolutionNotes.trim(),
      });
      setCaseData(updated);
      setShowResolveModal(false);
      setResolutionNotes('');
      setActionSuccess(`Case formally resolved with disposition: ${resolutionCategory}.`);
      const [tlRes, nRes] = await Promise.all([CasesService.getTimeline(id), CasesService.getNotes(id)]);
      setTimeline(tlRes);
      setNotes(nRes);
    } catch (err: any) {
      setActionError(err.message || 'Failed to resolve case.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCloseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    try {
      setActionLoading(true);
      setActionError(null);
      const updated = await CasesService.closeCase(id, {
        closure_reason: closureReason.trim() || undefined,
      });
      setCaseData(updated);
      setShowCloseModal(false);
      setActionSuccess('Case docket formally archived and closed.');
      const tlRes = await CasesService.getTimeline(id);
      setTimeline(tlRes);
    } catch (err: any) {
      setActionError(err.message || 'Failed to close case.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleExportDossier = async () => {
    if (!id) return;
    try {
      setExportLoading(true);
      const res = await CasesService.exportDossier(id);
      setExportResult(res);
      setShowExportModal(true);
    } catch (err: any) {
      alert(`Export failed: ${err.message}`);
    } finally {
      setExportLoading(false);
    }
  };

  const downloadDossierJson = () => {
    if (!exportResult) return;
    const blob = new Blob([JSON.stringify(exportResult, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `DOSSIER_${exportResult.case_number || id}_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return <LoadingSpinner text="Retrieving evidentiary case docket..." minHeight={400} />;
  }

  if (error || !caseData) {
    return (
      <div style={{ maxWidth: 800, margin: '20px auto' }}>
        <ErrorMessage message={error || 'Case docket not found.'} onRetry={loadCase} />
        <div style={{ marginTop: 16 }}>
          <button className="btn-action" onClick={() => navigate('/cases')}>
            ← Return to Case Registry
          </button>
        </div>
      </div>
    );
  }

  const caseNum = caseData.case_number || caseData.id || id;
  const fraudAmount = caseData.total_fraud_amount_inr ?? caseData.total_exposure_inr ?? 0;
  const recoveredAmount = caseData.recovered_amount_inr ?? 0;
  const assignedTo = caseData.assigned_investigator || caseData.assigned_to || caseData.assigned_investigator_name || 'Unassigned';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs items={[{ label: 'Case Registry', path: '/cases' }, { label: caseNum || 'Case Docket' }]} />


      {/* Case Header Banner */}
      <div
        className="stat-card"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 16,
          padding: 24,
          borderLeft: '4px solid var(--accent-cyan)',
        }}
      >
        <div style={{ flex: 1, minWidth: 320 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
              {caseNum}
            </span>
            <Badge variant={caseData.priority as any}>{caseData.priority}</Badge>
            <Badge variant={caseData.status === 'RESOLVED' || caseData.status === 'CLOSED' ? 'LOW' : 'HIGH'}>
              {caseData.status}
            </Badge>
            {caseData.alert_id && (
              <Link
                to={`/alerts/${caseData.alert_id}`}
                style={{
                  fontSize: '0.8rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--accent-cyan)',
                  textDecoration: 'none',
                  background: 'rgba(0, 242, 254, 0.1)',
                  padding: '3px 8px',
                  borderRadius: 4,
                  border: '1px solid rgba(0, 242, 254, 0.3)',
                }}
              >
                Origin: {caseData.alert_id} ↗
              </Link>
            )}
          </div>

          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 10px 0' }}>
            {caseData.title}
          </h1>

          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5 }}>
            {caseData.description || 'Official investigative docket tracking multi-jurisdictional financial cybercrime.'}
          </p>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'flex-end' }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {(isAdmin || isSupervisor) && caseData.status !== 'CLOSED' && (
              <button
                className="btn-action"
                onClick={() => {
                  setAssigneeInput(assignedTo !== 'Unassigned' ? assignedTo : user?.email || '');
                  setShowAssignModal(true);
                }}

                style={{
                  background: 'rgba(56, 189, 248, 0.12)',
                  border: '1px solid rgba(56, 189, 248, 0.4)',
                  color: '#38bdf8',
                  padding: '8px 14px',
                  borderRadius: 6,
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                }}
              >
                👤 Assign Investigator
              </button>
            )}

            {canPerformAction('UPDATE_CASE') && caseData.status !== 'RESOLVED' && caseData.status !== 'CLOSED' && (
              <button
                className="btn-action"
                onClick={() => setShowResolveModal(true)}
                style={{
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid #10b981',
                  color: '#6ee7b7',
                  padding: '8px 14px',
                  borderRadius: 6,
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                }}
              >
                ⚖️ Record Resolution
              </button>
            )}

            {(isAdmin || isSupervisor) && caseData.status !== 'CLOSED' && (
              <button
                className="btn-action"
                onClick={() => setShowCloseModal(true)}
                style={{
                  background: 'rgba(239, 68, 68, 0.12)',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  color: '#f87171',
                  padding: '8px 14px',
                  borderRadius: 6,
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                }}
              >
                🔒 Close Docket
              </button>
            )}


            {canPerformAction('EXPORT_DATA') && (
              <button
                className="btn-action"
                onClick={handleExportDossier}
                disabled={exportLoading}
                style={{
                  background: 'linear-gradient(135deg, rgba(0,242,254,0.15), rgba(79,172,254,0.15))',
                  border: '1px solid rgba(0, 242, 254, 0.4)',
                  color: 'var(--accent-cyan)',
                  padding: '8px 14px',
                  borderRadius: 6,
                  fontWeight: 600,
                  fontSize: '0.82rem',
                  cursor: exportLoading ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span>📜</span> {exportLoading ? 'Hashing Dossier...' : 'Export Court Dossier'}
              </button>
            )}
          </div>

          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Docket Initialized:{' '}
            {new Date(caseData.created_at).toLocaleString('en-IN', {
              day: '2-digit',
              month: 'short',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
        </div>
      </div>

      {/* Global Alerts / Status Feedback */}
      {actionSuccess && (
        <div
          style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid #10b981',
            color: '#6ee7b7',
            padding: '10px 16px',
            borderRadius: 6,
            fontSize: '0.85rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <span>✓ {actionSuccess}</span>
          <button
            onClick={() => setActionSuccess(null)}
            style={{ background: 'none', border: 'none', color: '#6ee7b7', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}
      {actionError && <ErrorMessage message={actionError} />}

      {/* Financial Exposure & Assignment Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
        <div className="stat-card" style={{ padding: 18 }}>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
            Reported Financial Exposure
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-rose)' }}>
            ₹{fraudAmount.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: 2 }}>
            Aggregated across connected accounts
          </div>
        </div>

        <div className="stat-card" style={{ padding: 18 }}>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
            Recovered / Debit Lien Secured
          </div>
          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>
            ₹{recoveredAmount.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: 2 }}>
            Secured via Golden-Hour banking directive
          </div>
        </div>

        <div className="stat-card" style={{ padding: 18 }}>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
            Assigned Lead Detective
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', wordBreak: 'break-all' }}>
            {assignedTo}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: 2 }}>
            {caseData.assigned_at ? `Assigned: ${new Date(caseData.assigned_at).toLocaleDateString('en-IN')}` : 'Active jurisdiction'}
          </div>
        </div>

        <div className="stat-card" style={{ padding: 18 }}>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
            Evidence & Chain-of-Custody
          </div>
          <div style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
            {evidence.length} Items • {timeline.length} Events
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: 2 }}>
            BNS / IT Act 65B Compliant Audit Trail
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          gap: 4,
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: 2,
        }}
      >
        {[
          { key: 'OVERVIEW', label: '📊 Case Summary & Directive' },
          { key: 'EVIDENCE', label: `🔍 Evidentiary Dossier (${evidence.length})` },
          { key: 'NOTES', label: `📝 Investigation Notes (${notes.length})` },
          { key: 'TIMELINE', label: `⏳ Investigation Timeline (${timeline.length})` },
          { key: 'DISPOSITION', label: '⚖️ Legal Findings & Disposition' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            style={{
              background: activeTab === tab.key ? 'rgba(0, 242, 254, 0.12)' : 'none',
              border: 'none',
              borderBottom: activeTab === tab.key ? '2px solid var(--accent-cyan)' : '2px solid transparent',
              color: activeTab === tab.key ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              padding: '10px 16px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              borderRadius: '6px 6px 0 0',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: OVERVIEW & SUMMARY */}
      {activeTab === 'OVERVIEW' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 20 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Case Summary Card */}
            <div className="stat-card" style={{ padding: 20 }}>
              <h3 style={{ fontSize: '1.05rem', margin: '0 0 14px 0', color: 'var(--accent-cyan)' }}>
                📑 Case Docket Metadata
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, fontSize: '0.85rem' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Case Identifier:</span>
                  <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>
                    {caseNum}
                  </div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Current Status:</span>
                  <div style={{ marginTop: 2 }}>
                    <Badge variant={caseData.status === 'RESOLVED' || caseData.status === 'CLOSED' ? 'LOW' : 'HIGH'}>
                      {caseData.status}
                    </Badge>
                  </div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Priority Level:</span>
                  <div style={{ marginTop: 2 }}>
                    <Badge variant={caseData.priority as any}>{caseData.priority}</Badge>
                  </div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Lead Investigator:</span>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: 2 }}>{assignedTo}</div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Docket Initialized:</span>
                  <div style={{ color: 'var(--text-secondary)', marginTop: 2 }}>
                    {new Date(caseData.created_at).toLocaleString('en-IN')}
                  </div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Last Action / Update:</span>
                  <div style={{ color: 'var(--text-secondary)', marginTop: 2 }}>
                    {caseData.updated_at ? new Date(caseData.updated_at).toLocaleString('en-IN') : '—'}
                  </div>
                </div>
              </div>
            </div>

            {/* Linked Alert Summary */}
            {caseData.alert_id && (
              <div className="stat-card" style={{ padding: 20, borderLeft: '3px solid #f59e0b' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h3 style={{ fontSize: '1.05rem', margin: 0, color: '#f59e0b' }}>
                    🚨 Originating Alert: {caseData.alert_id}
                  </h3>
                  <Link to={`/alerts/${caseData.alert_id}`} style={{ color: 'var(--accent-cyan)', fontSize: '0.8rem', textDecoration: 'none' }}>
                    Open Alert Dossier →
                  </Link>
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  This formal docket was generated from automated real-time transaction surveillance.
                  Triggering conditions included rapid outflow velocity, multi-account structuring, and high ML anomaly signals.
                </div>
              </div>
            )}

            {/* Connected Accounts Quick Jump */}
            <div className="stat-card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                <h3 style={{ fontSize: '1.05rem', margin: 0, color: 'var(--accent-cyan)' }}>
                  🏦 Connected Mule Accounts & VPAs
                </h3>
                <Link
                  to={`/graph?account=${encodeURIComponent(selectedSuspectAccount)}`}
                  style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', textDecoration: 'none', fontWeight: 600 }}
                >
                  Inspect Graph Ring ↗
                </Link>
              </div>

              <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 12 }}>
                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Active Account:</span>
                <input
                  type="text"
                  value={selectedSuspectAccount}
                  onChange={(e) => setSelectedSuspectAccount(e.target.value)}
                  style={{
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 6,
                    padding: '6px 12px',
                    color: 'var(--text-primary)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.85rem',
                    width: 200,
                  }}
                />
                <Link
                  to={`/accounts/${encodeURIComponent(selectedSuspectAccount)}`}
                  className="btn-action"
                  style={{
                    padding: '6px 12px',
                    fontSize: '0.8rem',
                    background: 'rgba(255,255,255,0.06)',
                    color: 'var(--text-primary)',
                    textDecoration: 'none',
                    borderRadius: 6,
                  }}
                >
                  View Account Profile →
                </Link>
              </div>
            </div>

            {/* Phase 11C Cash-Out Prediction Integration */}
            <div>
              <CashoutPredictionCard
                accountId={selectedSuspectAccount || 'SYN1000004465'}
                latitude={28.6139}
                longitude={77.209}
                accountRiskScore={0.88}
                cashoutRatio={0.92}
              />
            </div>
          </div>

          {/* Right Column: Docket Directives & Quick Controls */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {canPerformAction('UPDATE_CASE') && caseData.status !== 'CLOSED' && (
              <div className="stat-card" style={{ padding: 20 }}>
                <h3 style={{ fontSize: '1.05rem', margin: '0 0 14px 0', color: 'var(--text-primary)' }}>
                  ⚙️ Update Docket State
                </h3>

                <form onSubmit={handleUpdateStatusAndPriority} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div>
                    <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                      Target Status
                    </label>
                    <select
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value as CaseStatus)}
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
                      <option value="OPEN">OPEN</option>
                      <option value="ASSIGNED">ASSIGNED</option>
                      <option value="INVESTIGATING">INVESTIGATING</option>
                      <option value="ON_HOLD">ON HOLD</option>
                      <option value="RESOLVED">RESOLVED</option>
                      <option value="CLOSED">CLOSED</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                      Priority Level
                    </label>
                    <select
                      value={newPriority}
                      onChange={(e) => setNewPriority(e.target.value as CasePriority)}
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
                      Note for Transition
                    </label>
                    <textarea
                      rows={3}
                      placeholder="Brief rationale for status transition..."
                      value={investigationNotes}
                      onChange={(e) => setInvestigationNotes(e.target.value)}
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

                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="btn-action"
                    style={{
                      background: 'var(--accent-cyan)',
                      color: '#070a12',
                      fontWeight: 700,
                      border: 'none',
                      padding: '10px 16px',
                      borderRadius: 6,
                      cursor: actionLoading ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {actionLoading ? 'Recording Directive...' : 'Commit Status Transition'}
                  </button>
                </form>
              </div>
            )}

            {/* Quick Evidence Links */}
            <div className="stat-card" style={{ padding: 20 }}>
              <h4 style={{ fontSize: '0.9rem', margin: '0 0 10px 0', color: 'var(--text-muted)' }}>
                Cross-Platform Forensic Links
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <Link to="/transactions" style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', textDecoration: 'none' }}>
                  💳 Query Transaction Ledger
                </Link>
                <Link to="/complaints" style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', textDecoration: 'none' }}>
                  📝 NCRP 1930 Citizen Complaint Triage
                </Link>
                <Link to="/map" style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', textDecoration: 'none' }}>
                  🗺️ Spatial Threat & Cash-Out Heatmap
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: EVIDENCE DOSSIER */}
      {activeTab === 'EVIDENCE' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem', margin: 0, color: 'var(--text-primary)' }}>
              Structured Evidentiary Chain of Custody
            </h3>
            {canPerformAction('UPDATE_CASE') && caseData.status !== 'CLOSED' && (
              <button
                className="btn-action"
                onClick={() => setShowEvidenceModal(true)}
                style={{
                  background: 'var(--accent-cyan)',
                  color: '#070a12',
                  fontWeight: 700,
                  border: 'none',
                  padding: '8px 14px',
                  borderRadius: 6,
                  cursor: 'pointer',
                  fontSize: '0.82rem',
                }}
              >
                ➕ Attach Evidence Item
              </button>
            )}
          </div>

          {evidence.length === 0 ? (
            <div className="stat-card" style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>
              No explicit evidence attached to this docket yet. Attach transaction, account, complaint, or geo items.
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 14 }}>
              {evidence.map((ev) => (
                <div
                  key={ev.id}
                  className="stat-card"
                  style={{
                    padding: 16,
                    borderLeft: `3px solid ${
                      ev.evidence_type === 'ALERT'
                        ? '#ef4444'
                        : ev.evidence_type === 'ACCOUNT'
                        ? '#00f2fe'
                        : ev.evidence_type === 'TRANSACTION'
                        ? '#f59e0b'
                        : '#10b981'
                    }`,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                      {ev.evidence_type}
                    </span>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      {new Date(ev.created_at).toLocaleDateString('en-IN')}
                    </span>
                  </div>

                  <div style={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--text-primary)', marginBottom: 4 }}>
                    {ev.title}
                  </div>

                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--accent-cyan)', marginBottom: 8 }}>
                    Ref: {ev.evidence_reference_id}
                  </div>

                  {ev.description && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                      {ev.description}
                    </div>
                  )}

                  <div style={{ marginTop: 10, fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    Attached by: {ev.added_by}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: INVESTIGATION NOTES */}
      {activeTab === 'NOTES' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: 20 }}>
          {/* Notes list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <h3 style={{ fontSize: '1.05rem', margin: 0, color: 'var(--text-primary)' }}>
              Chronological Case Notes & Log Entries ({notes.length})
            </h3>

            {notes.length === 0 ? (
              <div className="stat-card" style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)' }}>
                No investigation notes appended yet.
              </div>
            ) : (
              notes.map((n) => (
                <div
                  key={n.id}
                  className="stat-card"
                  style={{
                    padding: 16,
                    borderLeft: n.is_internal ? '3px solid #38bdf8' : '3px solid #10b981',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                        {n.author_name || n.author_id}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', background: 'var(--bg-primary)', padding: '2px 6px', borderRadius: 4 }}>
                        {n.author_role}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(n.created_at).toLocaleString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>

                  <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                    {n.content}
                  </p>
                </div>
              ))
            )}
          </div>

          {/* Append Note Box */}
          {canPerformAction('UPDATE_CASE') && caseData.status !== 'CLOSED' && (
            <div className="stat-card" style={{ padding: 20, height: 'fit-content' }}>
              <h3 style={{ fontSize: '1.05rem', margin: '0 0 12px 0', color: 'var(--text-primary)' }}>
                ✍️ Append Official Investigation Entry
              </h3>

              <form onSubmit={handleAddNote} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <textarea
                  rows={6}
                  required
                  placeholder="Record forensic actions, warrant application status, inter-bank communication, or suspect interrogations..."
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 6,
                    padding: '10px 12px',
                    color: 'var(--text-primary)',
                    fontSize: '0.85rem',
                  }}
                />

                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <input
                    type="checkbox"
                    id="internalNote"
                    checked={noteInternal}
                    onChange={(e) => setNoteInternal(e.target.checked)}
                  />
                  <label htmlFor="internalNote" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Internal LEA note (restricted access)
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={actionLoading || !noteContent.trim()}
                  className="btn-action"
                  style={{
                    background: 'var(--accent-cyan)',
                    color: '#070a12',
                    fontWeight: 700,
                    border: 'none',
                    padding: '8px 16px',
                    borderRadius: 6,
                    cursor: actionLoading || !noteContent.trim() ? 'not-allowed' : 'pointer',
                  }}
                >
                  {actionLoading ? 'Recording Note...' : 'Commit Note to Docket'}
                </button>
              </form>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: CASE TIMELINE */}
      {activeTab === 'TIMELINE' && (
        <div className="stat-card" style={{ padding: 24 }}>
          <h3 style={{ fontSize: '1.1rem', margin: '0 0 20px 0', color: 'var(--text-primary)' }}>
            Investigation Chronology & Chain of Events
          </h3>

          {timeline.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 24 }}>
              No timeline events recorded yet.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0, position: 'relative' }}>
              {timeline.map((evt, idx) => (
                <div
                  key={evt.id || idx}
                  style={{
                    display: 'flex',
                    gap: 16,
                    position: 'relative',
                    paddingBottom: idx === timeline.length - 1 ? 0 : 24,
                  }}
                >
                  {/* Vertical line indicator */}
                  {idx !== timeline.length - 1 && (
                    <div
                      style={{
                        position: 'absolute',
                        left: 11,
                        top: 24,
                        bottom: 0,
                        width: 2,
                        background: 'var(--border-subtle)',
                      }}
                    />
                  )}

                  {/* Bullet */}
                  <div
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      background: 'var(--bg-primary)',
                      border: '2px solid var(--accent-cyan)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.65rem',
                      color: 'var(--accent-cyan)',
                      flexShrink: 0,
                      zIndex: 1,
                    }}
                  >
                    ●
                  </div>

                  {/* Event content */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                        {evt.title}
                      </span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                        {evt.event_type}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {new Date(evt.timestamp).toLocaleString('en-IN', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        })}
                      </span>
                    </div>

                    {evt.description && (
                      <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        {evt.description}
                      </p>
                    )}

                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: 4 }}>
                      Actor: {evt.actor_id} ({evt.actor_role})
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 5: DISPOSITION & RESOLUTION */}
      {activeTab === 'DISPOSITION' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div className="stat-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: '1.1rem', margin: '0 0 14px 0', color: 'var(--text-primary)' }}>
              Legal Findings & Formal Disposition Status
            </h3>

            {caseData.resolution_status ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <Badge variant="LOW">{caseData.resolution_status}</Badge>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                    Category: {caseData.resolution_category}
                  </span>
                </div>

                {caseData.resolution_reason && (
                  <div>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Formal Reason: </span>
                    <strong style={{ fontSize: '0.88rem', color: 'var(--text-primary)' }}>
                      {caseData.resolution_reason}
                    </strong>
                  </div>
                )}

                <div>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                    Judicial / Investigator Notes:
                  </span>
                  <div
                    style={{
                      background: 'var(--bg-primary)',
                      padding: '12px 16px',
                      borderRadius: 6,
                      fontSize: '0.85rem',
                      color: 'var(--text-secondary)',
                      lineHeight: 1.5,
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {caseData.resolution_notes}
                  </div>
                </div>

                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Resolved By: {caseData.resolved_by} on{' '}
                  {caseData.resolved_at ? new Date(caseData.resolved_at).toLocaleString('en-IN') : '—'}
                </div>
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                This case docket is currently undergoing active investigation and has not yet been resolved.
                Authorized investigators and supervisors can record resolution findings using the button in the header.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal: Attach Evidence */}
      {showEvidenceModal && (
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
              maxWidth: 520,
              width: '100%',
              background: '#0d1322',
              border: '1px solid var(--border-subtle)',
              borderRadius: 12,
              padding: 24,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <h2 style={{ fontSize: '1.15rem', margin: 0, color: 'var(--text-primary)' }}>
                ➕ Link Structured Evidence
              </h2>
              <button
                onClick={() => setShowEvidenceModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddEvidence} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Evidence Classification
                </label>
                <select
                  value={evidenceType}
                  onChange={(e) => setEvidenceType(e.target.value)}
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
                  <option value="ACCOUNT">ACCOUNT (Mule Account / VPA)</option>
                  <option value="TRANSACTION">TRANSACTION (Financial Transaction)</option>
                  <option value="COMPLAINT">COMPLAINT (NCRP 1930 Incident)</option>
                  <option value="ALERT">ALERT (Intelligence Notification)</option>
                  <option value="CASHOUT_PREDICTION">CASHOUT_PREDICTION (Predicted ATM)</option>
                  <option value="GRAPH_ENTITY">GRAPH_ENTITY (Network Cluster)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Reference Identifier *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. SYN1000004465, TXN-99812, ALT-2024-001"
                  value={evidenceRef}
                  onChange={(e) => setEvidenceRef(e.target.value)}
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
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Evidence Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Mule Account First Inflow Node"
                  value={evidenceTitle}
                  onChange={(e) => setEvidenceTitle(e.target.value)}
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
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Description / Forensic Context
                </label>
                <textarea
                  rows={3}
                  placeholder="Explain why this item is evidentiary..."
                  value={evidenceDesc}
                  onChange={(e) => setEvidenceDesc(e.target.value)}
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

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
                <button
                  type="button"
                  onClick={() => setShowEvidenceModal(false)}
                  style={{ background: 'none', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', padding: '8px 14px', borderRadius: 6 }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="btn-action"
                  style={{
                    background: 'var(--accent-cyan)',
                    color: '#070a12',
                    fontWeight: 700,
                    border: 'none',
                    padding: '8px 18px',
                    borderRadius: 6,
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                  }}
                >
                  {actionLoading ? 'Attaching...' : 'Attach Evidence'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Assign Investigator */}
      {showAssignModal && (
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
              maxWidth: 500,
              width: '100%',
              background: '#0d1322',
              border: '1px solid var(--border-subtle)',
              borderRadius: 12,
              padding: 24,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <h2 style={{ fontSize: '1.15rem', margin: 0, color: 'var(--text-primary)' }}>
                👤 Assign Lead Investigator
              </h2>
              <button
                onClick={() => setShowAssignModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAssignSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Investigator Badge / Email / Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Agent R. K. Sharma (Badge #DL-8821)"
                  value={assigneeInput}
                  onChange={(e) => setAssigneeInput(e.target.value)}
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
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Assignment Instructions / Directives
                </label>
                <textarea
                  rows={3}
                  placeholder="Directives for assigned officer..."
                  value={assignNotes}
                  onChange={(e) => setAssignNotes(e.target.value)}
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

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
                <button
                  type="button"
                  onClick={() => setShowAssignModal(false)}
                  style={{ background: 'none', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', padding: '8px 14px', borderRadius: 6 }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="btn-action"
                  style={{
                    background: '#38bdf8',
                    color: '#070a12',
                    fontWeight: 700,
                    border: 'none',
                    padding: '8px 18px',
                    borderRadius: 6,
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                  }}
                >
                  {actionLoading ? 'Assigning...' : 'Commit Assignment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Record Formal Resolution */}
      {showResolveModal && (
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
              maxWidth: 540,
              width: '100%',
              background: '#0d1322',
              border: '1px solid var(--border-subtle)',
              borderRadius: 12,
              padding: 24,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <h2 style={{ fontSize: '1.15rem', margin: 0, color: 'var(--accent-emerald)' }}>
                ⚖️ Record Case Resolution Finding
              </h2>
              <button
                onClick={() => setShowResolveModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleResolveSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Resolution Category *
                </label>
                <select
                  value={resolutionCategory}
                  onChange={(e) => setResolutionCategory(e.target.value)}
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
                  <option value="CONFIRMED_FRAUD">CONFIRMED FRAUD (Crime Established)</option>
                  <option value="SUSPECTED_FRAUD">SUSPECTED FRAUD (High Probability)</option>
                  <option value="FALSE_POSITIVE">FALSE POSITIVE (Legitimate Activity)</option>
                  <option value="INSUFFICIENT_EVIDENCE">INSUFFICIENT EVIDENCE</option>
                  <option value="REFERRED">REFERRED (Inter-State / CBI Jurisdiction)</option>
                  <option value="OTHER">OTHER</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Disposition Summary / Primary Reason
                </label>
                <input
                  type="text"
                  placeholder="e.g. Syndicate mule ring dismantled and accounts frozen under Section 106 BNS"
                  value={resolutionReason}
                  onChange={(e) => setResolutionReason(e.target.value)}
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
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Official Findings & Investigator Notes *
                </label>
                <textarea
                  rows={4}
                  required
                  placeholder="Detailed findings and judicial disposition record..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
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

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
                <button
                  type="button"
                  onClick={() => setShowResolveModal(false)}
                  style={{ background: 'none', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', padding: '8px 14px', borderRadius: 6 }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading || !resolutionNotes.trim()}
                  className="btn-action"
                  style={{
                    background: 'var(--accent-emerald)',
                    color: '#070a12',
                    fontWeight: 700,
                    border: 'none',
                    padding: '8px 18px',
                    borderRadius: 6,
                    cursor: actionLoading || !resolutionNotes.trim() ? 'not-allowed' : 'pointer',
                  }}
                >
                  {actionLoading ? 'Recording Resolution...' : 'Submit Legal Resolution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Close Docket */}
      {showCloseModal && (
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
              maxWidth: 480,
              width: '100%',
              background: '#0d1322',
              border: '1px solid var(--border-subtle)',
              borderRadius: 12,
              padding: 24,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <h2 style={{ fontSize: '1.15rem', margin: 0, color: '#f87171' }}>
                🔒 Formally Close & Archive Docket
              </h2>
              <button
                onClick={() => setShowCloseModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCloseSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Closure Reason & Final Sign-Off
                </label>
                <textarea
                  rows={3}
                  value={closureReason}
                  onChange={(e) => setClosureReason(e.target.value)}
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

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
                <button
                  type="button"
                  onClick={() => setShowCloseModal(false)}
                  style={{ background: 'none', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', padding: '8px 14px', borderRadius: 6 }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="btn-action"
                  style={{
                    background: '#ef4444',
                    color: '#fff',
                    fontWeight: 700,
                    border: 'none',
                    padding: '8px 18px',
                    borderRadius: 6,
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                  }}
                >
                  {actionLoading ? 'Archiving...' : 'Confirm Closure'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Cryptographic Dossier Export Modal */}
      {showExportModal && exportResult && (
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
              maxWidth: 640,
              width: '100%',
              background: '#0d1322',
              border: '1px solid var(--border-subtle)',
              borderRadius: 12,
              padding: 24,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ fontSize: '1.2rem', margin: 0, color: 'var(--accent-cyan)' }}>
                ⚖️ Forensic Intelligence Dossier Export
              </h2>
              <button
                onClick={() => setShowExportModal(false)}
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

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: '0.88rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Export Reference ID: </span>
                <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                  {exportResult.export_id}
                </strong>
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)' }}>Case Number: </span>
                <strong style={{ fontFamily: 'var(--font-mono)' }}>{exportResult.case_number}</strong>
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)' }}>Exported By: </span>
                <strong>{exportResult.exported_by}</strong> ({exportResult.exported_role})
              </div>

              <div>
                <span style={{ color: 'var(--text-muted)' }}>Cryptographic SHA-256 Chain-of-Custody Hash:</span>
                <div
                  style={{
                    background: 'var(--bg-primary)',
                    padding: '8px 12px',
                    borderRadius: 6,
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.78rem',
                    color: '#6ee7b7',
                    wordBreak: 'break-all',
                    marginTop: 4,
                  }}
                >
                  {exportResult.chain_of_custody_hash}
                </div>
              </div>

              <div
                style={{
                  background: 'rgba(0, 242, 254, 0.05)',
                  border: '1px solid rgba(0, 242, 254, 0.2)',
                  borderRadius: 6,
                  padding: 10,
                  fontSize: '0.78rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.4,
                }}
              >
                🛡️ This dossier package includes full immutable metadata, linked accounts, ML risk indicators, and audit signatures complying with digital forensics chain-of-custody protocols (BNS / IT Act Section 65B).
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 12 }}>
                <button
                  type="button"
                  onClick={() => setShowExportModal(false)}
                  style={{
                    background: 'none',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                    padding: '8px 16px',
                    borderRadius: 6,
                    cursor: 'pointer',
                  }}
                >
                  Close
                </button>
                <button
                  type="button"
                  className="btn-action"
                  onClick={downloadDossierJson}
                  style={{
                    background: 'var(--accent-emerald)',
                    color: '#070a12',
                    fontWeight: 700,
                    border: 'none',
                    padding: '8px 18px',
                    borderRadius: 6,
                    cursor: 'pointer',
                  }}
                >
                  ⬇️ Download Signed Dossier (.JSON)
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
