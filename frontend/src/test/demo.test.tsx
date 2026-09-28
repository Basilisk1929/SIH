import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { DemoSimulationModal } from '../components/demo/DemoSimulationModal';

describe('Phase 11F: DemoSimulationModal UI Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    const mockFetch = vi.fn().mockImplementation(async (url: string, _init?: RequestInit) => {
      const urlStr = String(url);
      if (urlStr.includes('/demo/status')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            is_demo_mode_enabled: true,
            active_demo_alerts_count: 1,
            active_demo_cases_count: 0,
            active_demo_transactions_count: 1,
            active_demo_complaints_count: 1,
            disclaimer: 'SIH Demonstration Mode active.',
          }),
        };
      }
      if (urlStr.includes('/demo/simulate-fraud')) {
        return {
          ok: true,
          status: 201,
          json: async () => ({
            scenario_id: 'SCENARIO_SIH_TEST_1001',
            status: 'COMPLETED',
            is_demo: true,
            narrative_summary: 'Simulation executed.',
            victim_account: 'SYN_DEMO_VICTIM_4011',
            mule_account: 'SYN_DEMO_MULE_9088',
            amount_inr: 85000,
            complaint: { acknowledgement_no: 'DEMO-NCRP-2026-TEST' },
            transaction: { transaction_id: 'DEMO_TXN_TEST_1001' },
            ml_risk_assessment: {
              risk_score: 88.5,
              risk_band: 'CRITICAL',
              is_suspicious: true,
              feature_explanations: [],
              disclaimer: 'Synthetic',
            },
            graph_evidence: { degree: 4 },
            cashout_prediction: {
              account_id: 'SYN_DEMO_MULE_9088',
              prediction_timestamp: new Date().toISOString(),
              anchor_location: { latitude: 28.6139, longitude: 77.209, source: 'TXN' },
              candidate_radius_km: 15,
              total_candidates_evaluated: 10,
              predicted_atms: [
                {
                  atm_id: 'ATM_DEMO_1',
                  bank_name: 'State Bank of India',
                  latitude: 28.614,
                  longitude: 77.21,
                  distance_km: 0.8,
                  prediction_score: 0.92,
                  rank: 1,
                  explanations: [],
                },
              ],
              urgency_level: 'CRITICAL',
              disclaimer: 'Synthetic test',
            },
            alert: {
              id: 99,
              alert_id: 'ALT_DEMO_TEST_99',
              account_id: 'SYN_DEMO_MULE_9088',
              amount_inr: 85000,
              severity: 'CRITICAL',
              alert_type: 'RAPID_MOVEMENT',
              status: 'OPEN',
              created_at: new Date().toISOString(),
              description: 'Demo alert',
              risk_score: 88.5,
              confidence_score: 0.95,
              triggered_entity_type: 'ACCOUNT',
              triggered_entity_id: 'SYN_DEMO_MULE_9088',
              assigned_to: 'investigator@demo.gov.in',
            },
            created_at: new Date().toISOString(),
          }),
        };
      }
      if (urlStr.includes('/demo/reset')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            status: 'SUCCESS',
            purged_alerts: 1,
            purged_transactions: 1,
            purged_complaints: 1,
            purged_cases: 0,
            purged_graph_edges: 2,
            message: 'Purged test demo artifacts.',
            reset_at: new Date().toISOString(),
          }),
        };
      }

      return {
        ok: true,
        status: 200,
        json: async () => ({}),
      };
    });

    (globalThis as any).fetch = mockFetch as any;
  });

  it('renders modal with statutory disclaimer and initial 8 pipeline steps when open', async () => {
    render(
      <BrowserRouter>
        <DemoSimulationModal isOpen={true} onClose={() => {}} />
      </BrowserRouter>
    );

    expect(screen.getByText(/SIH End-to-End Live Fraud Simulator/i)).toBeInTheDocument();
    expect(screen.getByText(/SYNTHETIC EVALUATION DATA/i)).toBeInTheDocument();
    expect(screen.getByText(/1. Ingest Synthetic NCRP Citizen Complaint/i)).toBeInTheDocument();
    expect(screen.getByText(/4. XGBoost ML Risk Inference/i)).toBeInTheDocument();
    expect(screen.getByText(/7. Phase 11C Predictive Cash-Out Location Engine/i)).toBeInTheDocument();
    expect(screen.getByText(/8. Real-Time Alert Engine & WebSocket Broadcast/i)).toBeInTheDocument();
  });

  it('orchestrates complete simulation flow when "Run Live Fraud Scenario" is clicked', async () => {
    render(
      <BrowserRouter>
        <DemoSimulationModal isOpen={true} onClose={() => {}} />
      </BrowserRouter>
    );

    const runBtn = screen.getByTestId('simulate-fraud-btn');
    fireEvent.click(runBtn);

    await waitFor(
      () => {
        expect(screen.getByText(/Fraud Scenario Successfully Orchestrated/i)).toBeInTheDocument();
        expect(screen.getByText('ALT_DEMO_TEST_99')).toBeInTheDocument();
        expect(screen.getAllByText(/SYN_DEMO_MULE_9088/).length).toBeGreaterThan(0);
        expect(screen.getByText(/Inspect Alert Dossier & Explanations/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('triggers safe demo purge when clean reset is invoked', async () => {
    vi.spyOn(window, 'confirm').mockImplementation(() => true);

    render(
      <BrowserRouter>
        <DemoSimulationModal isOpen={true} onClose={() => {}} />
      </BrowserRouter>
    );

    const resetBtn = screen.getByTestId('reset-demo-btn');
    fireEvent.click(resetBtn);

    await waitFor(() => {
      expect(screen.getByText(/Purged 1 alerts, 0 cases/i)).toBeInTheDocument();
    });
  });
});
