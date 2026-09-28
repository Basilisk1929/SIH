import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter, MemoryRouter, Routes, Route } from 'react-router-dom';
import { Login } from '../pages/Login';
import { AccountDetail } from '../pages/AccountDetail';
import { Map } from '../pages/Map';
import { AccountsService } from '../services/accounts';
import { GeoService } from '../services/geo';
import * as AuthContextModule from '../context/AuthContext';

// Mock Leaflet in JSDOM environment
vi.mock('leaflet', () => {
  const dummyLayerGroup = {
    addTo: vi.fn().mockReturnThis(),
    clearLayers: vi.fn().mockReturnThis(),
    addLayer: vi.fn().mockReturnThis(),
    removeLayer: vi.fn().mockReturnThis(),
  };

  const dummyGeoJSON = {
    ...dummyLayerGroup,
    addData: vi.fn().mockReturnThis(),
    setStyle: vi.fn().mockReturnThis(),
    eachLayer: vi.fn().mockReturnThis(),
  };

  return {
    default: {
      map: vi.fn().mockReturnValue({
        setView: vi.fn().mockReturnThis(),
        zoomIn: vi.fn().mockReturnThis(),
        zoomOut: vi.fn().mockReturnThis(),
        panTo: vi.fn().mockReturnThis(),
        fitBounds: vi.fn().mockReturnThis(),
        remove: vi.fn(),
      }),
      tileLayer: vi.fn().mockReturnValue({
        addTo: vi.fn().mockReturnThis(),
        on: vi.fn(),
      }),
      layerGroup: vi.fn().mockReturnValue(dummyLayerGroup),
      geoJSON: vi.fn().mockReturnValue(dummyGeoJSON),
      marker: vi.fn().mockReturnValue({
        on: vi.fn().mockReturnThis(),
        bindPopup: vi.fn().mockReturnThis(),
        addTo: vi.fn().mockReturnThis(),
      }),
      circle: vi.fn().mockReturnValue({
        addTo: vi.fn().mockReturnThis(),
      }),
      divIcon: vi.fn().mockReturnValue({}),
      latLngBounds: vi.fn().mockReturnValue({
        isValid: vi.fn().mockReturnValue(true),
      }),
    },
  };
});

// Mock AuthContext
vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: any) => <div>{children}</div>,
}));

// Mock AccountsService
vi.mock('../services/accounts', () => ({
  AccountsService: {
    getAccountDetails: vi.fn(),
    freezeAccount: vi.fn(),
  },
}));

// Mock GraphService
vi.mock('../services/graph', () => ({
  GraphService: {
    getConnectedAccounts: vi.fn().mockResolvedValue({ connected_accounts: [] }),
  },
}));

// Mock GeoService
vi.mock('../services/geo', () => ({
  GeoService: {
    getHotspots: vi.fn(),
    getH3GeoJson: vi.fn(),
    getNearestAtms: vi.fn(),
    predictCashoutLocation: vi.fn(),
  },
}));

describe('CYBERSHIELD-INTEL FOUR TARGETED FIXES', () => {
  beforeEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();

    // Default mock for Phase 11C predictive cashout card
    (GeoService.predictCashoutLocation as any).mockResolvedValue({
      account_id: 'SYN_DEMO_VICTIM_4011',
      prediction_timestamp: new Date().toISOString(),
      anchor_location: { latitude: 28.6139, longitude: 77.209, source: 'explicit' },
      candidate_radius_km: 15,
      total_candidates_evaluated: 1,
      predicted_atms: [],
      urgency_level: 'STANDARD',
      disclaimer: 'Synthetic test disclaimer',
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // TASK 1 & TASK 4: LOGIN PAGE TESTS
  describe('Task 1 & Task 4: Login Page Logo & Render Free-Tier Disclaimer', () => {
    it('renders clean official CyberShield logo and Render free-tier cold-start disclaimer', () => {
      (AuthContextModule.useAuth as any).mockReturnValue({
        login: vi.fn(),
        isLoading: false,
        isAuthenticated: false,
        user: null,
      });

      render(
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      );

      // Task 1: Check logo presence and source
      const logoImg = screen.getByAltText(/CyberShield Official Logo/i);
      expect(logoImg).toBeInTheDocument();
      expect(logoImg).toHaveAttribute('src', '/cybershield-logo.png');

      // Task 4: Check Render cold-start notice
      expect(screen.getByText(/Demo Environment Notice/i)).toBeInTheDocument();
      expect(screen.getByText(/The backend runs on Render's free tier and may take 30–60 seconds to wake up/i)).toBeInTheDocument();
    });

    it('shows dynamic waking up message if login takes longer than 6 seconds', async () => {
      vi.useFakeTimers();

      let resolveLogin: () => void = () => {};
      const loginPromise = new Promise<void>((res) => {
        resolveLogin = res;
      });

      (AuthContextModule.useAuth as any).mockReturnValue({
        login: vi.fn().mockReturnValue(loginPromise),
        isLoading: false,
        isAuthenticated: false,
        user: null,
      });

      render(
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      );

      const submitBtn = screen.getByRole('button', { name: /Authorize Secure Access/i });
      fireEvent.click(submitBtn);

      // Initial loading state
      const initialMessages = screen.getAllByText(/Connecting to CyberShield backend.../i);
      expect(initialMessages.length).toBeGreaterThan(0);

      // Fast-forward 6.5s inside act
      await act(async () => {
        vi.advanceTimersByTime(6500);
      });

      // Cold start waking up notice
      expect(screen.getByText(/Backend is waking up — this can take up to 30–60 seconds/i)).toBeInTheDocument();

      resolveLogin();
      vi.useRealTimers();
    });
  });

  // TASK 2: GOLDEN-HOUR FREEZE SIMULATION
  describe('Task 2: Golden-Hour Emergency Freeze Demo Simulation', () => {
    it('executes simulated freeze with 404 fallback in SIH demo mode without raising API Not Found', async () => {
      vi.useRealTimers();
      vi.spyOn(window, 'confirm').mockImplementation(() => true);

      (AuthContextModule.useAuth as any).mockReturnValue({
        user: { email: 'evaluator@sih.gov.in', role: 'ADMIN' },
        isAuthenticated: true,
        canPerformAction: vi.fn().mockReturnValue(true),
        isAnalyst: false,
      });

      (AccountsService.getAccountDetails as any).mockResolvedValue({
        account_number: 'SYN_DEMO_VICTIM_4011',
        holder_synthetic_name: 'Priya Sharma (Synthetic Victim)',
        bank_name: 'State Bank of India',
        ifsc_code: 'SBIN0001234',
        risk_score: 0.85,
        total_credit_volume_inr: 500000,
        total_debit_volume_inr: 480000,
        is_frozen: false,
        flagged_reasons: ['Velocity anomaly', 'Rapid dissipation'],
      });

      // Backend returns 404 Not Found for freeze endpoint
      (AccountsService.freezeAccount as any).mockRejectedValue(new Error('Not Found'));

      render(
        <MemoryRouter initialEntries={['/accounts/SYN_DEMO_VICTIM_4011']}>
          <Routes>
            <Route path="/accounts/:id" element={<AccountDetail />} />
          </Routes>
        </MemoryRouter>
      );

      // Wait for account to load
      await waitFor(() => {
        expect(screen.getAllByText(/SYN_DEMO_VICTIM_4011/i).length).toBeGreaterThan(0);
      });

      const freezeBtn = screen.getByRole('button', { name: /Issue Golden-Hour Emergency Lien \/ Freeze/i });
      expect(freezeBtn).toBeInTheDocument();

      fireEvent.click(freezeBtn);

      // Verify simulated success banner appears
      await waitFor(
        () => {
          expect(screen.getByText(/Golden-Hour Emergency Freeze Simulated Successfully/i)).toBeInTheDocument();
        },
        { timeout: 4000 }
      );

      // Verify UI badge updates to simulated freeze
      expect(screen.getByText(/EMERGENCY FREEZE — SIMULATED/i)).toBeInTheDocument();

      // Verify button updates to simulated freeze and is disabled
      const updatedBtn = screen.getByRole('button', { name: /✓ Emergency Freeze Simulated/i });
      expect(updatedBtn).toBeDisabled();

      // Verify audit timeline displays entry
      expect(screen.getByText(/Action: GOLDEN_HOUR_FREEZE_SIMULATED/i)).toBeInTheDocument();
      expect(screen.getByText(/SIH SYNTHETIC DEMO/i)).toBeInTheDocument();

      // Verify "API Intelligence Failure" / "Not Found" does NOT appear
      expect(screen.queryByText(/API Intelligence Failure/i)).not.toBeInTheDocument();
    });
  });

  // TASK 3: REAL INTERACTIVE MAP
  describe('Task 3: Real Interactive Geographic Map', () => {
    it('renders Leaflet map container, compact controls, and H3 risk legend', async () => {
      (GeoService.getHotspots as any).mockResolvedValue({
        total_clusters: 2,
        clusters: [
          {
            cluster_id: 0,
            centroid_lat: 23.9614,
            centroid_lng: 86.8016,
            incident_count: 564,
            total_loss_inr: 29343613.69,
            dominant_pattern: 'phishing',
            radius_km: 12.0,
            reference_hub_name: 'Jamtara-Karmatanr Hub',
          },
        ],
      });

      (GeoService.getH3GeoJson as any).mockResolvedValue({
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            geometry: {
              type: 'Polygon',
              coordinates: [[[86.81, 23.95], [86.81, 23.96], [86.79, 23.97], [86.78, 23.96], [86.81, 23.95]]],
            },
            properties: {
              h3_cell: '873ca91adffffff',
              risk_band: 'CRITICAL',
              risk_score: 95,
              complaint_count: 564,
              total_complaint_loss: 29343613,
            },
          },
        ],
      });

      (GeoService.getNearestAtms as any).mockResolvedValue({
        query_point: { latitude: 23.9614, longitude: 86.8016 },
        total_found: 1,
        nearest_atms: [
          {
            outlet_id: 'ATM_1',
            bank_name: 'State Bank of India',
            outlet_type: 'ON_SITE_ATM',
            city: 'Jamtara',
            latitude: 23.962,
            longitude: 86.801,
            distance_km: 0.15,
          },
        ],
      });

      (GeoService.predictCashoutLocation as any).mockResolvedValue({
        account_id: 'SYN_DEMO_VICTIM_4011',
        prediction_timestamp: new Date().toISOString(),
        anchor_location: {
          latitude: 23.9614,
          longitude: 86.8016,
          source: 'explicit',
        },
        candidate_radius_km: 25.0,
        total_candidates_evaluated: 5,
        predicted_atms: [
          {
            atm_id: 'ATM_PRED_1',
            bank_name: 'Punjab National Bank',
            latitude: 23.963,
            longitude: 86.802,
            distance_km: 0.23,
            prediction_score: 80.9,
            rank: 1,
            city: 'Jamtara',
            explanations: ['High proximity'],
          },
        ],
        urgency_level: 'STANDARD',
        disclaimer: 'Investigative prototype.',
      });

      render(
        <BrowserRouter>
          <Map />
        </BrowserRouter>
      );

      // Verify page title
      expect(screen.getByText(/Geospatial Threat Hotspots & ATM Proximity Map/i)).toBeInTheDocument();

      // Wait for data load to complete and compact controls to appear
      await waitFor(() => {
        expect(screen.getByRole('button', { name: '+' })).toBeInTheDocument();
      });
      expect(screen.getByRole('button', { name: '−' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Reset' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Fit Threats' })).toBeInTheDocument();

      // Verify H3 Legend
      expect(screen.getByText('H3 RISK')).toBeInTheDocument();
      expect(screen.getAllByText(/Low/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Medium/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/High/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Critical/i).length).toBeGreaterThan(0);

      // Verify right inspector panel synchronized with cluster
      await waitFor(() => {
        expect(screen.getByText(/Jamtara-Karmatanr Hub/i)).toBeInTheDocument();
        expect(screen.getByText(/564 reports/i)).toBeInTheDocument();
      });
    });
  });
});
