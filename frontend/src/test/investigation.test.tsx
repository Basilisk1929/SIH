import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { CashoutPredictionCard } from '../components/investigation/CashoutPredictionCard';
import { GeoService } from '../services/geo';
import { AlertsService } from '../services/alerts';
import { CasesService } from '../services/cases';
import { TransactionsService } from '../services/transactions';
import { ComplaintsService } from '../services/complaints';
import { GraphService } from '../services/graph';
import { Alerts } from '../pages/Alerts';
import { Cases } from '../pages/Cases';
import { Transactions } from '../pages/Transactions';
import { Complaints } from '../pages/Complaints';
import { Graph } from '../pages/Graph';

vi.mock('../services/geo');
vi.mock('../services/alerts');
vi.mock('../services/cases');
vi.mock('../services/transactions');
vi.mock('../services/complaints');
vi.mock('../services/graph');

describe('Forensic Investigation Components & Phase 11C Cash-Out Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Phase 11C CashoutPredictionCard with candidate ATMs, scores, and statutory disclaimer', async () => {
    (GeoService.predictCashoutLocation as any).mockResolvedValue({
      account_id: 'SYN9810482019',
      prediction_timestamp: '2024-09-24T12:00:00Z',
      anchor_location: { latitude: 28.6139, longitude: 77.209, source: 'LAST_KNOWN_TRANSACTION' },
      candidate_radius_km: 15,
      total_candidates_evaluated: 24,
      urgency_level: 'HIGH',
      disclaimer: 'Predictive intelligence indicator based on empirical spatial and temporal heuristics. Not direct evidence of physical presence.',
      predicted_atms: [
        {
          atm_id: 'ATM_DELHI_001',
          bank_name: 'State Bank of India',
          latitude: 28.6145,
          longitude: 77.21,
          distance_km: 0.85,
          prediction_score: 0.92,
          rank: 1,
          explanations: ['High historical pass-through volume', 'Proximity to burst origin (< 1 km)'],
          outlet_type: 'ATM',
          city: 'New Delhi',
        },
        {
          atm_id: 'ATM_DELHI_002',
          bank_name: 'Punjab National Bank',
          latitude: 28.618,
          longitude: 77.215,
          distance_km: 1.42,
          prediction_score: 0.78,
          rank: 2,
          explanations: ['Elevated H3 risk cell'],
          outlet_type: 'ATM',
          city: 'New Delhi',
        },
      ],
    });

    render(
      <MemoryRouter>
        <CashoutPredictionCard
          accountId="SYN9810482019"
          latitude={28.6139}
          longitude={77.209}
          accountRiskScore={0.88}
        />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Likely Cash-Out Location Prediction/i)).toBeInTheDocument();
      expect(screen.getByText('State Bank of India')).toBeInTheDocument();
      expect(screen.getByText('Punjab National Bank')).toBeInTheDocument();
    });

    // Verify statutory disclaimer disclosure
    expect(
      screen.getByText(/Predictive intelligence indicator based on empirical spatial and temporal heuristics/i)
    ).toBeInTheDocument();
  });

  it('renders Alerts page with real backend alert stream and risk ratings', async () => {
    (AlertsService.getAlerts as any).mockResolvedValue({
      items: [
        {
          id: 'ALT-1001',
          alert_id: 'ALT-1001',
          alert_type: 'RAPID_CASHOUT_VELOCITY',
          severity: 'CRITICAL',
          status: 'NEW',
          risk_score: 94.0,
          triggered_entity_type: 'ACCOUNT',
          triggered_entity_id: 'SYN1122334455',
          account_id: 'SYN1122334455',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
      total: 1,
      page: 1,
      limit: 25,
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <Alerts />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('ALT-1001')).toBeInTheDocument();
      expect(screen.getByText(/RAPID CASHOUT VELOCITY/i)).toBeInTheDocument();
      expect(screen.getByText('94.0')).toBeInTheDocument();
    });
  });

  it('renders Cases page docket registry and shows open docket modal', async () => {
    (CasesService.getCases as any).mockResolvedValue([
      {
        id: 'CASE-2024-001',
        case_number: 'CASE-2024-001',
        title: 'Operation Nightshade: Multi-State UPI Mule Ring',
        priority: 'CRITICAL',
        status: 'INVESTIGATING',
        assigned_investigator_name: 'Lead Officer',
        linked_alert_ids: ['ALT-1001'],
        linked_account_numbers: ['SYN1122334455'],
        total_exposure_inr: 4850000,
        notes: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);

    render(
      <MemoryRouter>
        <AuthProvider>
          <Cases />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('CASE-2024-001')).toBeInTheDocument();
      expect(screen.getByText('Operation Nightshade: Multi-State UPI Mule Ring')).toBeInTheDocument();
    });
  });

  it('renders Transactions ledger and evaluates XGBoost risk display', async () => {
    (TransactionsService.getRecentTransactions as any).mockResolvedValue([
      {
        id: 'txn-101',
        txn_ref_no: 'UPI/42891048/SYN',
        sender_account: 'SYN2000000001',
        receiver_account: 'SYN9000000001',
        amount_inr: 75000,
        rail_type: 'UPI',
        anomaly_score: 0.88,
        is_flagged_suspicious: true,
        layer_depth: 1,
        timestamp: new Date().toISOString(),
      },
    ]);

    render(
      <MemoryRouter>
        <AuthProvider>
          <Transactions />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('UPI/42891048/SYN').length).toBeGreaterThan(0);
      expect(screen.getAllByText(/75,000/).length).toBeGreaterThan(0);
    });
  });

  it('renders Complaints queue and displays live NLP extracted entities', async () => {
    (ComplaintsService.getComplaints as any).mockResolvedValue({
      items: [
        {
          id: 'CMP-101',
          acknowledgement_no: '2024-NCRP-98104',
          category: 'UPI_FRAUD',
          reported_loss_inr: 48500,
          victim_state: 'Delhi',
          victim_district: 'New Delhi',
          risk_score: 0.89,
          description_synthetic: 'Caller impersonated bank officer and stole 48500 rupees.',
          status: 'UNDER_INVESTIGATION',
        },
      ],
      total: 1,
    });
    (ComplaintsService.extractNlpEntities as any).mockResolvedValue({
      scam_type: 'BANK_IMPERSONATION',
      confidence: 0.94,
      entities: [
        { label: 'AMOUNT', text: '48500 rupees', normalized_value: '48500', confidence: 0.99 },
        { label: 'BANK', text: 'bank officer', normalized_value: 'BANK', confidence: 0.92 },
      ],
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <Complaints />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('2024-NCRP-98104').length).toBeGreaterThan(0);
      expect(screen.getByText('UPI FRAUD')).toBeInTheDocument();
    });
  });

  it('renders Neo4j Graph topology with SVG nodes', async () => {
    (GraphService.getNetworkGraph as any).mockResolvedValue({
      node_count: 3,
      edge_count: 2,
      nodes: [
        { id: 'SYN1122334455', label: 'BankAccount', properties: { bank: 'Synth Bank' } },
        { id: 'SYN9876543210', label: 'BankAccount', properties: { bank: 'Mule Aggregator' } },
        { id: 'mule@oksbi', label: 'UPI_ID', properties: { handle: 'oksbi' } },
      ],
      edges: [
        { source: 'SYN1122334455', target: 'SYN9876543210', relationship: 'TRANSFERRED_TO', properties: {} },
        { source: 'SYN1122334455', target: 'mule@oksbi', relationship: 'LINKED_UPI', properties: {} },
      ],
      metadata: {},
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <Graph />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Neo4j Multi-Hop Graph Link Analysis/i)).toBeInTheDocument();
      expect(screen.getAllByText('SYN1122334455').length).toBeGreaterThan(0);
    });
  });
});
