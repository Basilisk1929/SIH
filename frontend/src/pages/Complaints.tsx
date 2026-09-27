import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { EmptyState } from '../components/common/EmptyState';
import { ComplaintsService } from '../services/complaints';
import { Complaint } from '../types';

export const Complaints: React.FC = () => {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected complaint for forensic dossier inspection
  const [selectedComplaint, setSelectedComplaint] = useState<Complaint | null>(null);

  // Live NLP Extraction state
  const [nlpLoading, setNlpLoading] = useState(false);
  const [nlpResult, setNlpResult] = useState<any | null>(null);
  const [nlpError, setNlpError] = useState<string | null>(null);

  // Interactive narrative analyzer modal / panel
  const [showAnalyzerModal, setShowAnalyzerModal] = useState(false);
  const [customNarrative, setCustomNarrative] = useState(
    'Sir, I received a call from 9876543210 claiming to be State Bank manager Ramesh Sharma. He asked me to update KYC immediately or card will block. He sent a link and asked to pay 10 rupees on UPI id quickmule99@oksbi. After clicking, 48,500 rupees was debited from my account 1122334455 via IMPS txn ref 428910482SYN. Please help freeze suspect account.'
  );

  const loadComplaints = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await ComplaintsService.getComplaints(30, 0);
      const items = res.items || [];
      setComplaints(items);
      if (items.length > 0 && !selectedComplaint) {
        setSelectedComplaint(items[0]);
        // Trigger live NLP extraction on the selected complaint description
        runNlpExtraction(items[0].description_synthetic || items[0].narrative || '');
      }
    } catch (err: any) {
      console.error('Failed to load complaints:', err);
      setError(err.message || 'Unable to retrieve citizen complaints from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadComplaints();
  }, []);

  const runNlpExtraction = async (text: string) => {
    if (!text || !text.trim()) return;
    try {
      setNlpLoading(true);
      setNlpError(null);
      const res = await ComplaintsService.extractNlpEntities(text);
      setNlpResult(res);
    } catch (err: any) {
      console.warn('NLP extraction API note:', err);
      setNlpError(err.message || 'NLP entity extraction failed.');
    } finally {
      setNlpLoading(false);
    }
  };

  const handleSelectComplaint = (c: Complaint) => {
    setSelectedComplaint(c);
    runNlpExtraction(c.description_synthetic || c.narrative || '');
  };

  const handleRunCustomNlp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customNarrative.trim()) return;
    try {
      setNlpLoading(true);
      setNlpError(null);
      const res = await ComplaintsService.extractNlpEntities(customNarrative);
      setNlpResult(res);
    } catch (err: any) {
      setNlpError(err.message || 'NLP entity extraction failed.');
    } finally {
      setNlpLoading(false);
    }
  };

  const filteredComplaints = complaints.filter((c) => {
    if (categoryFilter !== 'ALL' && c.category !== categoryFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchAck = c.acknowledgement_no?.toLowerCase().includes(q);
      const matchCat = c.category?.toLowerCase().includes(q) || c.subcategory?.toLowerCase().includes(q);
      const matchDesc = (c.description_synthetic || c.narrative || '').toLowerCase().includes(q);
      const matchUpi = c.suspect_upi?.toLowerCase().includes(q);
      if (!matchAck && !matchCat && !matchDesc && !matchUpi) return false;
    }
    return true;
  });

  const getEntityBadgeColor = (label: string) => {
    switch (label.toUpperCase()) {
      case 'ACCOUNT':
        return { bg: 'rgba(0, 242, 254, 0.15)', border: '#00f2fe', text: '#00f2fe' };
      case 'UPI_ID':
        return { bg: 'rgba(99, 102, 241, 0.15)', border: '#6366f1', text: '#c7d2fe' };
      case 'PHONE':
        return { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b', text: '#fcd34d' };
      case 'AMOUNT':
        return { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444', text: '#fca5a5' };
      case 'PERSON':
        return { bg: 'rgba(168, 85, 247, 0.15)', border: '#a855f7', text: '#e9d5ff' };
      case 'BANK':
        return { bg: 'rgba(16, 185, 129, 0.15)', border: '#10b981', text: '#6ee7b7' };
      case 'LOCATION':
        return { bg: 'rgba(236, 72, 153, 0.15)', border: '#ec4899', text: '#fbcfe8' };
      case 'TRANSACTION_ID':
        return { bg: 'rgba(14, 165, 233, 0.15)', border: '#0ea5e9', text: '#7dd3fc' };
      default:
        return { bg: 'rgba(255, 255, 255, 0.08)', border: 'var(--border-subtle)', text: 'var(--text-primary)' };
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            📝 NCRP 1930 Cybercrime Complaints & NLP Intelligence
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
            Citizen incident triage, automated entity extraction (PERSON, BANK, ACCOUNT, UPI, PHONE), and typology classification.
          </p>
        </div>

        <button
          className="btn-action"
          style={{
            background: 'linear-gradient(135deg, #00f2fe, #4facfe)',
            color: '#070a12',
            fontWeight: 700,
            border: 'none',
            padding: '9px 16px',
            borderRadius: 6,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
          onClick={() => setShowAnalyzerModal(true)}
        >
          <span>🧠</span> Live NLP Narrative Analyzer
        </button>
      </div>

      {/* Filter Toolbar */}
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
            placeholder="Search complaints by Ack Number, narrative keywords, or UPI..."
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

        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Category:</label>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '7px 12px',
              borderRadius: 6,
              fontSize: '0.85rem',
            }}
          >
            <option value="ALL">All Categories</option>
            <option value="UPI_FRAUD">UPI / Payment Fraud</option>
            <option value="INVESTMENT_FRAUD">Investment / Task Ponzi</option>
            <option value="IDENTITY_THEFT">Identity Theft / Impersonation</option>
            <option value="LOAN_APP_EXTORTION">Illegal Loan App</option>
            <option value="JOB_SCAM">Part-Time Job Scam</option>
          </select>

          <button
            className="btn-action"
            onClick={loadComplaints}
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

      {/* Main split grid: Complaints list on left, Forensic Dossier & NLP Extraction on right */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedComplaint ? '1.2fr 1fr' : '1fr', gap: 20 }}>
        {/* Table panel */}
        <div>
          {loading ? (
            <LoadingSpinner text="Querying 1930 / NCRP national incident database..." minHeight={300} />
          ) : error ? (
            <ErrorMessage message={error} onRetry={loadComplaints} />
          ) : filteredComplaints.length === 0 ? (
            <EmptyState
              title="No Complaints Found"
              message="No incident records match the active search criteria."
            />
          ) : (
            <div className="data-table-card">
              <table>
                <thead>
                  <tr>
                    <th>Ack Number</th>
                    <th>Category</th>
                    <th>Reported Loss</th>
                    <th>State / District</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredComplaints.map((c) => {
                    const isSelected = selectedComplaint?.id === c.id;
                    const loss = c.reported_loss_inr || 0;
                    return (
                      <tr
                        key={c.id}
                        onClick={() => handleSelectComplaint(c)}
                        style={{
                          cursor: 'pointer',
                          backgroundColor: isSelected ? 'rgba(0, 242, 254, 0.08)' : undefined,
                          borderLeft: isSelected ? '3px solid var(--accent-cyan)' : '3px solid transparent',
                        }}
                      >
                        <td>
                          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
                            {c.acknowledgement_no}
                          </div>
                          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                            {c.incident_date ? new Date(c.incident_date).toLocaleDateString('en-IN') : 'Recent'}
                          </div>
                        </td>
                        <td>
                          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                            {c.category?.replace(/_/g, ' ')}
                          </div>
                          <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)' }}>
                            {c.subcategory || 'Standard Citizen Report'}
                          </div>
                        </td>
                        <td style={{ fontWeight: 700, color: loss > 50000 ? 'var(--accent-rose)' : 'var(--text-primary)' }}>
                          ₹{loss.toLocaleString('en-IN')}
                        </td>
                        <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                          {c.victim_district ? `${c.victim_district}, ` : ''}{c.victim_state || 'India'}
                        </td>
                        <td>
                          <Badge variant={(c.risk_score || 0) > 0.75 ? 'CRITICAL' : (c.risk_score || 0) > 0.4 ? 'HIGH' : 'LOW'}>
                            {((c.risk_score || 0.8) * 100).toFixed(0)}%
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Selected Complaint Dossier & Live NLP Extraction Display */}
        {selectedComplaint && (
          <div className="stat-card" style={{ height: 'fit-content', padding: 22, display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  NCRP Forensic Incident Dossier
                </div>
                <h3 style={{ margin: '4px 0 0 0', fontSize: '1.2rem', color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>
                  {selectedComplaint.acknowledgement_no}
                </h3>
              </div>
              <Badge variant={selectedComplaint.status === 'FROZEN' ? 'CRITICAL' : 'HIGH'}>
                {selectedComplaint.status || 'UNDER TRIAGE'}
              </Badge>
            </div>

            {/* Financial & Jurisdiction stats */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div style={{ background: 'var(--bg-primary)', padding: 12, borderRadius: 6 }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Reported Financial Loss</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--accent-rose)' }}>
                  ₹{(selectedComplaint.reported_loss_inr || 0).toLocaleString('en-IN')}
                </div>
              </div>
              <div style={{ background: 'var(--bg-primary)', padding: 12, borderRadius: 6 }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Jurisdiction</div>
                <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {selectedComplaint.victim_district || 'District Police'}, {selectedComplaint.victim_state || 'Nodal Agency'}
                </div>
              </div>
            </div>

            {/* Raw Narrative Box */}
            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>
                RAW CITIZEN COMPLAINT NARRATIVE:
              </div>
              <div
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 6,
                  padding: 12,
                  fontSize: '0.82rem',
                  lineHeight: 1.5,
                  color: 'var(--text-secondary)',
                  fontStyle: 'italic',
                }}
              >
                "{selectedComplaint.description_synthetic || selectedComplaint.narrative || 'Incident report filed with 1930 cyber helpline.'}"
              </div>
            </div>

            {/* REAL NLP Extracted Entities Box (Never hardcoded!) */}
            <div style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <h4 style={{ margin: 0, fontSize: '0.9rem', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>🧠</span> NLP Entity Extraction Intelligence (Live)
                </h4>
                {nlpLoading && <span style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)' }}>Analyzing NLP models...</span>}
              </div>

              {nlpError && <div style={{ fontSize: '0.78rem', color: 'var(--accent-rose)' }}>{nlpError}</div>}

              {nlpResult?.entities && nlpResult.entities.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {nlpResult.entities.map((e: any, idx: number) => {
                      const style = getEntityBadgeColor(e.label);
                      return (
                        <div
                          key={idx}
                          style={{
                            background: style.bg,
                            border: `1px solid ${style.border}`,
                            color: style.text,
                            padding: '4px 10px',
                            borderRadius: 6,
                            fontSize: '0.78rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                          }}
                        >
                          <span style={{ fontWeight: 700, fontSize: '0.7rem', opacity: 0.8 }}>
                            {e.label}:
                          </span>
                          <span style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                            {e.normalized_value || e.text}
                          </span>
                          <span style={{ fontSize: '0.68rem', opacity: 0.7 }}>
                            ({Math.round((e.confidence || 0.95) * 100)}%)
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {nlpResult.scam_type && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 4 }}>
                      Classified Typology: <strong style={{ color: 'var(--accent-cyan)' }}>{nlpResult.scam_type}</strong> (Confidence: {Math.round((nlpResult.confidence || 0.9) * 100)}%)
                    </div>
                  )}
                </div>
              ) : !nlpLoading ? (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Click below or open the live analyzer to re-parse this narrative through the NLP pipeline.
                </div>
              ) : null}

              <button
                className="btn-action"
                disabled={nlpLoading}
                onClick={() => runNlpExtraction(selectedComplaint.description_synthetic || selectedComplaint.narrative || '')}
                style={{
                  marginTop: 10,
                  width: '100%',
                  padding: '7px',
                  fontSize: '0.78rem',
                  background: 'rgba(0, 242, 254, 0.08)',
                  border: '1px solid rgba(0, 242, 254, 0.3)',
                  color: 'var(--accent-cyan)',
                  borderRadius: 4,
                  cursor: 'pointer',
                }}
              >
                {nlpLoading ? 'Running spaCy & Rule Extractors...' : '⚡ Re-Analyze Narrative via NLP Service'}
              </button>
            </div>

            {/* Linked Suspect Action Bar */}
            <div style={{ display: 'flex', gap: 10 }}>
              {selectedComplaint.suspect_account_number && (
                <Link
                  to={`/accounts/${encodeURIComponent(selectedComplaint.suspect_account_number)}`}
                  className="btn-action"
                  style={{
                    flex: 1,
                    textAlign: 'center',
                    padding: '8px',
                    fontSize: '0.82rem',
                    background: 'var(--accent-rose)',
                    color: '#fff',
                    textDecoration: 'none',
                    borderRadius: 6,
                    fontWeight: 600,
                  }}
                >
                  ⚡ Freeze Suspect Account
                </Link>
              )}

              <Link
                to={`/graph?account=${encodeURIComponent(selectedComplaint.suspect_account_number || selectedComplaint.suspect_upi || 'SYN9810482019')}`}
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
                🕸️ Graph Correlation
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Interactive NLP Narrative Analyzer Modal */}
      {showAnalyzerModal && (
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
              maxWidth: 760,
              width: '100%',
              background: '#0d1322',
              border: '1px solid var(--border-subtle)',
              borderRadius: 12,
              padding: 24,
              maxHeight: '90vh',
              overflowY: 'auto',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--accent-cyan)' }}>
                  🧠 Cybercrime NLP Narrative Extraction Engine
                </h2>
                <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  Evaluates unstructured police FIRs and citizen texts using spaCy NER, Indian financial regex patterns, and scam classifiers.
                </p>
              </div>
              <button
                onClick={() => setShowAnalyzerModal(false)}
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

            <form onSubmit={handleRunCustomNlp} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'block', marginBottom: 6 }}>
                  Input Incident Narrative / FIR Excerpt
                </label>
                <textarea
                  rows={5}
                  value={customNarrative}
                  onChange={(e) => setCustomNarrative(e.target.value)}
                  style={{
                    width: '100%',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 6,
                    padding: '10px 12px',
                    color: 'var(--text-primary)',
                    fontSize: '0.88rem',
                    lineHeight: 1.45,
                    resize: 'vertical',
                  }}
                />
              </div>

              {/* Sample buttons */}
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Load Prototype Scenarios:</span>
                <button
                  type="button"
                  className="btn-action"
                  onClick={() =>
                    setCustomNarrative(
                      'Sir, on 12-09-2024 I got a WhatsApp message for Telegram task job from +919810482019. They asked to like YouTube videos for 500 rupees. Then admin Priya Verma asked me to transfer Rs 85,000 to HDFC account 50100482910 IFSC HDFC0001092 or UPI telegram.vip@hdfc. Money never returned.'
                    )
                  }
                  style={{ fontSize: '0.75rem', padding: '4px 10px', background: 'rgba(255,255,255,0.06)' }}
                >
                  Telegram Task Ponzi
                </button>
                <button
                  type="button"
                  className="btn-action"
                  onClick={() =>
                    setCustomNarrative(
                      'Fraud caller impersonated CBI Officer Rajesh Kumar from phone 9123456789. Threatened digital arrest in drug parcel case. Forced transfer of Rs 2,50,000 to safe RBI account 9876543210 at Punjab National Bank via RTGS ref UTR891048291.'
                    )
                  }
                  style={{ fontSize: '0.75rem', padding: '4px 10px', background: 'rgba(255,255,255,0.06)' }}
                >
                  Digital Arrest Extortion
                </button>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                <button
                  type="submit"
                  disabled={nlpLoading}
                  className="btn-action"
                  style={{
                    background: 'var(--accent-cyan)',
                    color: '#070a12',
                    fontWeight: 700,
                    border: 'none',
                    padding: '9px 20px',
                    borderRadius: 6,
                    cursor: nlpLoading ? 'not-allowed' : 'pointer',
                  }}
                >
                  {nlpLoading ? 'Executing NLP Extraction Pipeline...' : '⚡ Extract Named Entities & Typology'}
                </button>
              </div>
            </form>

            {/* Results display inside modal */}
            {nlpResult && (
              <div style={{ marginTop: 20, background: 'var(--bg-primary)', padding: 18, borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--accent-cyan)' }}>
                    Extracted Financial & Identity Entities ({nlpResult.entities?.length || 0})
                  </h3>
                  <Badge variant="HIGH">
                    {nlpResult.scam_type || 'CYBER_FRAUD'} ({Math.round((nlpResult.confidence || 0.9) * 100)}%)
                  </Badge>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 10 }}>
                  {nlpResult.entities?.map((e: any, idx: number) => {
                    const badge = getEntityBadgeColor(e.label);
                    return (
                      <div
                        key={idx}
                        style={{
                          background: badge.bg,
                          border: `1px solid ${badge.border}`,
                          padding: '8px 12px',
                          borderRadius: 6,
                        }}
                      >
                        <div style={{ fontSize: '0.7rem', color: badge.text, fontWeight: 700 }}>
                          {e.label}
                        </div>
                        <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                          {e.normalized_value || e.text}
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>
                          Confidence: {Math.round((e.confidence || 0.95) * 100)}%
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
