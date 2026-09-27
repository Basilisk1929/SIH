import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { CaseDetail } from '../pages/CaseDetail';
import { CasesService } from '../services/cases';
import { GeoService } from '../services/geo';

vi.mock('../services/cases');
vi.mock('../services/geo');

describe('Phase 11E Case Management & Investigation Workflow Frontend', () => {
  const mockCaseDocket = {
    id: 'e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101',
    case_number: 'CASE-2026-9821',
    alert_id: 'ALT_20260926_A1B2C3D4',
    title: 'Operation Swift Recovery: UPI Syndicate',
    description: 'High-velocity cashout across nationalized bank ATMs',
    priority: 'CRITICAL',
    status: 'INVESTIGATING',
    total_fraud_amount_inr: 450000,
    recovered_amount_inr: 120000,
    assigned_to: 'inspector.sharma@cybercell.gov.in',
    assigned_investigator: 'inspector.sharma@cybercell.gov.in',
    assigned_at: '2026-09-26T10:00:00Z',
    assigned_by: 'supervisor@cybercell.gov.in',
    created_by: 'admin@cybercell.gov.in',
    created_at: '2026-09-26T09:30:00Z',
    updated_at: '2026-09-26T10:15:00Z',
    linked_alert_ids: ['ALT_20260926_A1B2C3D4'],
    linked_account_numbers: ['SYN9810482019'],
    linked_complaint_ids: ['CMP-99881'],
    notes_count: 2,
    evidence_count: 2,
    notes: [
      {
        id: 'n-1',
        case_id: 'e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101',
        author: 'inspector.sharma@cybercell.gov.in',
        author_id: 'inspector.sharma@cybercell.gov.in',
        author_name: 'Inspector Sharma',
        author_role: 'INVESTIGATOR',
        content: 'Section 91 CrPC notice issued to payment aggregator.',
        is_internal: true,
        created_at: '2026-09-26T09:45:00Z',
        timestamp: '2026-09-26T09:45:00Z',
      },
    ],
    evidence: [
      {
        id: 'ev-1',
        case_id: 'e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101',
        evidence_type: 'TRANSACTION',
        evidence_reference_id: 'TXN-998811',
        title: 'Initial Layer Rapid Hop',
        description: 'INR 45,000 transferred in 12s',
        metadata_json: { rail: 'UPI', amount: 45000 },
        added_by: 'system',
        created_at: '2026-09-26T09:31:00Z',
      },
    ],
    timeline: [
      {
        id: 'tl-1',
        case_id: 'e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101',
        event_type: 'CASE_CREATED',
        title: 'Case Docket Registered',
        description: 'Formal investigation initiated',
        actor_id: 'admin@cybercell.gov.in',
        actor_role: 'ADMIN',
        timestamp: '2026-09-26T09:30:00Z',
      },
      {
        id: 'tl-2',
        case_id: 'e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101',
        event_type: 'CASE_ASSIGNED',
        title: 'Lead Investigator Assigned',
        description: 'Assigned to inspector.sharma@cybercell.gov.in',
        actor_id: 'supervisor@cybercell.gov.in',
        actor_role: 'SUPERVISOR',
        timestamp: '2026-09-26T10:00:00Z',
      },
    ],
    linked_alert: {
      alert_id: 'ALT_20260926_A1B2C3D4',
      severity: 'CRITICAL',
      risk_score: 96.5,
      alert_type: 'HIGH_VELOCITY_DRAIN',
      account_id: 'SYN9810482019',
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (CasesService.getCaseById as any).mockResolvedValue(mockCaseDocket);
    (CasesService.getNotes as any).mockResolvedValue(mockCaseDocket.notes);
    (CasesService.getEvidence as any).mockResolvedValue(mockCaseDocket.evidence);
    (CasesService.getTimeline as any).mockResolvedValue(mockCaseDocket.timeline);
    (GeoService.predictCashoutLocation as any).mockResolvedValue({
      account_id: 'SYN9810482019',
      prediction_timestamp: '2026-09-26T12:00:00Z',
      anchor_location: { latitude: 28.6139, longitude: 77.209, source: 'TRANSACTION' },
      candidate_radius_km: 15,
      total_candidates_evaluated: 12,
      urgency_level: 'HIGH',
      disclaimer: 'Predictive intelligence heuristic.',
      predicted_atms: [],
    });
  });

  it('renders CaseDetail with case summary, alert telemetry, and operational tabs', async () => {
    render(
      <MemoryRouter initialEntries={['/cases/e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101']}>
        <AuthProvider>
          <Routes>
            <Route path="/cases/:id" element={<CaseDetail />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('CASE-2026-9821').length).toBeGreaterThan(0);
      expect(screen.getByText('Operation Swift Recovery: UPI Syndicate')).toBeInTheDocument();
      expect(screen.getAllByText(/CRITICAL/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/INVESTIGATING/i).length).toBeGreaterThan(0);
    });

    // Check investigation tabs
    expect(screen.getByText(/Case Summary & Directive/i)).toBeInTheDocument();
    expect(screen.getByText(/Evidentiary Dossier/i)).toBeInTheDocument();
    expect(screen.getByText(/Investigation Notes/i)).toBeInTheDocument();
    expect(screen.getByText(/Investigation Timeline/i)).toBeInTheDocument();
    expect(screen.getByText(/Legal Findings & Disposition/i)).toBeInTheDocument();
  });

  it('allows switching to Timeline tab to inspect verified timestamps and events', async () => {
    render(
      <MemoryRouter initialEntries={['/cases/e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101']}>
        <AuthProvider>
          <Routes>
            <Route path="/cases/:id" element={<CaseDetail />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('CASE-2026-9821').length).toBeGreaterThan(0);
    });

    // Switch to Timeline Tab
    const timelineTab = screen.getByText(/Investigation Timeline/i);
    fireEvent.click(timelineTab);

    await waitFor(() => {
      expect(screen.getByText('Case Docket Registered')).toBeInTheDocument();
      expect(screen.getByText('Lead Investigator Assigned')).toBeInTheDocument();
    });
  });

  it('allows switching to Notes tab and appends investigation notes', async () => {
    (CasesService.addNote as any).mockResolvedValue({
      id: 'n-2',
      case_id: 'e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101',
      author: 'inspector.sharma@cybercell.gov.in',
      author_id: 'inspector.sharma@cybercell.gov.in',
      author_name: 'Inspector Sharma',
      author_role: 'INVESTIGATOR',
      content: 'Mule bank branch verified by field team.',
      is_internal: true,
      created_at: new Date().toISOString(),
      timestamp: new Date().toISOString(),
    });

    render(
      <MemoryRouter initialEntries={['/cases/e4a1a5b8-5cf2-4c22-93e1-5efaa8d70101']}>
        <AuthProvider>
          <Routes>
            <Route path="/cases/:id" element={<CaseDetail />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('CASE-2026-9821').length).toBeGreaterThan(0);
    });

    // Switch to Notes Tab
    const notesTab = screen.getByText(/INVESTIGATION NOTES/i);
    fireEvent.click(notesTab);

    await waitFor(() => {
      expect(screen.getByText(/Section 91 CrPC notice issued to payment aggregator/i)).toBeInTheDocument();
    });
  });
});
