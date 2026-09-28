import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DemoService } from '../../services/demo';
import { DemoResetResponse, DemoSimulateResponse, DemoStatusResponse } from '../../types';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';
import { Badge } from '../common/Badge';

interface DemoSimulationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSimulationSuccess?: (result: DemoSimulateResponse) => void;
  onResetSuccess?: (result: DemoResetResponse) => void;
}

interface StepState {
  title: string;
  description: string;
  subsystem: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'ERROR';
  details?: string;
}

const INITIAL_STEPS: StepState[] = [
  {
    title: '1. Ingest Synthetic NCRP Citizen Complaint',
    description: 'NCRP 1930 report of electricity bill scam (₹85,000)',
    subsystem: 'NCRP / Citizen Ingestion',
    status: 'PENDING',
  },
  {
    title: '2. spaCy NLP Entity Extraction & Linking',
    description: 'Extract suspect UPI handle, bank account, and phone entity mentions',
    subsystem: 'NLP Intelligence',
    status: 'PENDING',
  },
  {
    title: '3. High-Velocity UPI Transaction Ingestion',
    description: 'Ingest suspicious transfer: SYN_DEMO_VICTIM_4011 → SYN_DEMO_MULE_9088',
    subsystem: 'Financial Ingestion & PostgreSQL',
    status: 'PENDING',
  },
  {
    title: '4. XGBoost ML Risk Inference',
    description: 'Evaluate 14 behavioral features, cashout ratio, velocity, and compute risk score',
    subsystem: 'ML Risk Engine',
    status: 'PENDING',
  },
  {
    title: '5. Neo4j Graph Topology & Entity Linking',
    description: 'Link victim node to suspect mule account and prior complaint records',
    subsystem: 'Neo4j Graph Database',
    status: 'PENDING',
  },
  {
    title: '6. H3 Geospatial Hotspot & Proximity Mapping',
    description: 'Correlate transaction coordinates with New Delhi Cyber Crime reference cluster',
    subsystem: 'H3 Spatial Engine',
    status: 'PENDING',
  },
  {
    title: '7. Phase 11C Predictive Cash-Out Location Engine',
    description: 'Rank nearby candidate ATMs by spatial proximity, bank affinity, and cashout urgency',
    subsystem: 'Predictive Cash-Out Model',
    status: 'PENDING',
  },
  {
    title: '8. Real-Time Alert Engine & WebSocket Broadcast',
    description: 'Generate high-severity incident dossier and broadcast to active dashboards',
    subsystem: 'Alert Engine & SSE/WebSocket',
    status: 'PENDING',
  },
];

export const DemoSimulationModal: React.FC<DemoSimulationModalProps> = ({
  isOpen,
  onClose,
  onSimulationSuccess,
  onResetSuccess,
}) => {
  const navigate = useNavigate();
  const [steps, setSteps] = useState<StepState[]>(INITIAL_STEPS);
  const [isRunning, setIsRunning] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [simulationResult, setSimulationResult] = useState<DemoSimulateResponse | null>(null);
  const [statusInfo, setStatusInfo] = useState<DemoStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadStatus();
      setSteps(INITIAL_STEPS);
      setError(null);
      setResetMessage(null);
    }
  }, [isOpen]);

  const loadStatus = async () => {
    try {
      const s = await DemoService.getDemoStatus();
      setStatusInfo(s);
    } catch {
      // Ignored
    }
  };

  const handleRunSimulation = async () => {
    setIsRunning(true);
    setError(null);
    setResetMessage(null);
    setSimulationResult(null);

    setSteps(INITIAL_STEPS.map((s, idx) => ({ ...s, status: idx === 0 ? 'RUNNING' : 'PENDING' })));

    let timerIdx = 0;
    const interval = setInterval(() => {
      timerIdx += 1;
      setSteps((prev) =>
        prev.map((step, idx) => {
          if (idx < timerIdx) return { ...step, status: 'COMPLETED' };
          if (idx === timerIdx) return { ...step, status: 'RUNNING' };
          return step;
        })
      );
      if (timerIdx >= 7) clearInterval(interval);
    }, 450);

    try {
      const res = await DemoService.simulateFraud();
      clearInterval(interval);
      setSimulationResult(res);

      setSteps((prev) =>
        prev.map((s, idx) => {
          let details: string | undefined;
          if (idx === 0) details = `NCRP Ack: ${res.complaint?.acknowledgement_no || 'DEMO-NCRP-...'}`;
          if (idx === 1) details = `Scam Type: ${res.complaint?.nlp_extraction?.classification?.scam_type || 'ELECTRICITY_BILL'}`;
          if (idx === 2) details = `Txn: ${res.transaction?.transaction_id || res.transaction?.id || 'TXN-DEMO'} (₹${res.amount_inr?.toLocaleString('en-IN') || '85,000'})`;
          if (idx === 3) details = `ML Risk: ${res.ml_risk_assessment?.risk_score?.toFixed(1) || '88.5'} / 100 (${res.ml_risk_assessment?.risk_band || 'CRITICAL'})`;
          if (idx === 4) details = `Live Neo4j Sync: ${res.graph_evidence?.live_neo4j_synced ? 'OK' : 'SYNTHETIC'}`;
          if (idx === 5) details = `H3 Cell: ${res.geospatial_intelligence?.h3_cell || '873da1146ffffff'}`;
          if (idx === 6) details = `Top ATM: ${res.cashout_prediction?.predicted_atms?.[0]?.bank_name || 'IndusInd Bank'}`;
          if (idx === 7) details = `Alert Dossier: ${res.alert?.alert_id || 'ALT_DEMO_...'}`;
          return { ...s, status: 'COMPLETED', details };
        })
      );

      await loadStatus();
      if (onSimulationSuccess) onSimulationSuccess(res);
    } catch (err: any) {
      clearInterval(interval);
      setError(err.message || 'Simulation pipeline failed. Please check backend connection.');
      setSteps((prev) =>
        prev.map((s) => (s.status === 'RUNNING' ? { ...s, status: 'ERROR' } : s))
      );
    } finally {
      setIsRunning(false);
    }
  };

  const handleResetData = async () => {
    setIsResetting(true);
    setError(null);
    setResetMessage(null);
    try {
      const res = await DemoService.resetDemoData();
      setResetMessage(`Reset complete. Purged ${res.purged_alerts} alerts, ${res.purged_cases} cases.`);
      setSimulationResult(null);
      setSteps(INITIAL_STEPS);
      await loadStatus();
      if (onResetSuccess) onResetSuccess(res);
    } catch (err: any) {
      setError(err.message || 'Failed to reset demo data.');
    } finally {
      setIsResetting(false);
    }
  };

  const handleOpenAlert = () => {
    if (simulationResult?.alert?.alert_id) {
      onClose();
      navigate(`/alerts/${simulationResult.alert.alert_id}`);
    } else {
      onClose();
      navigate('/alerts');
    }
  };

  const handleOpenCases = () => {
    onClose();
    navigate('/cases');
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: '20px',
      }}
    >
      <div
        style={{
          backgroundColor: '#0a0a0a',
          border: '1px solid #202020',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '820px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.9), 0 0 0 1px #1a1a1a',
          overflow: 'hidden',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid #1f1f1f',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#050505',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '1.4rem' }}>⚡</span>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: '#f5f5f5' }}>
                  SIH End-to-End Live Fraud Simulator
                </h3>
                <span
                  style={{
                    backgroundColor: '#141414',
                    color: '#a0a0a0',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    letterSpacing: '0.05em',
                    border: '1px solid #282828',
                  }}
                >
                  PHASE 11F
                </span>
              </div>
              <p style={{ margin: '3px 0 0 0', fontSize: '0.78rem', color: '#707070' }}>
                Executes complete pipeline: Ingestion → ML Risk → Neo4j Graph → H3 Geo → Cash-Out Prediction → Alert Engine → Cases.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isRunning || isResetting}
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              color: '#707070',
              fontSize: '1.4rem',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '18px', backgroundColor: '#0a0a0a' }}>
          {/* Statutory Disclaimer & Active State Notice */}
          <div
            style={{
              backgroundColor: '#0f0f0f',
              border: '1px solid #222222',
              borderRadius: '6px',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
            }}
          >
            <div style={{ fontSize: '0.78rem', color: '#a0a0a0' }}>
              <span style={{ fontWeight: 600, color: '#f59e0b' }}>⚠️ SYNTHETIC EVALUATION DATA: </span>
              All entities, bank accounts (<code style={{ color: '#d4d4d4' }}>SYN_DEMO_...</code>), and NCRP complaints are synthetic test vectors. Zero real citizen PII is utilized.
            </div>
            {statusInfo && (
              <div style={{ display: 'flex', gap: '10px', fontSize: '0.72rem', color: '#707070', whiteSpace: 'nowrap' }}>
                <span>Alerts: <strong style={{ color: '#f5f5f5' }}>{statusInfo.active_demo_alerts_count}</strong></span>
                <span>•</span>
                <span>Cases: <strong style={{ color: '#f5f5f5' }}>{statusInfo.active_demo_cases_count}</strong></span>
              </div>
            )}
          </div>

          {error && <ErrorMessage message={error} onRetry={() => handleRunSimulation()} />}
          {resetMessage && (
            <div
              style={{
                backgroundColor: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: '#34d399',
                padding: '10px 14px',
                borderRadius: '6px',
                fontSize: '0.82rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span>✅</span>
              <span>{resetMessage}</span>
            </div>
          )}

          {/* Scenario Overview Card */}
          <div
            style={{
              backgroundColor: '#0f0f0f',
              border: '1px solid #202020',
              borderRadius: '8px',
              padding: '16px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h4 style={{ margin: 0, fontSize: '0.85rem', color: '#f5f5f5', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                Scenario: Urgent Utility Disconnection Scam
              </h4>
              <Badge severity="CRITICAL" size="sm">
                HIGH RISK VECTOR
              </Badge>
            </div>
            <p style={{ margin: 0, fontSize: '0.82rem', color: '#a0a0a0', lineHeight: '1.5' }}>
              Simulates a citizen receiving an urgent fraudulent disconnection call and transferring ₹85,000 via UPI to mule account{' '}
              <code style={{ color: '#f59e0b' }}>SYN_DEMO_MULE_9088</code>. Evaluates rapid ML detection, cross-source NLP complaint correlation, and ATM cash-out interception before the fraudster withdraws the funds.
            </p>
          </div>

          {/* Pipeline Traversal Timeline */}
          <div>
            <h4 style={{ margin: '0 0 10px 0', fontSize: '0.8rem', color: '#707070', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>
              Full Platform Execution Pipeline
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {steps.map((step, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '10px 14px',
                    borderRadius: '6px',
                    backgroundColor:
                      step.status === 'COMPLETED'
                        ? '#0c140d'
                        : step.status === 'RUNNING'
                        ? '#141414'
                        : '#0e0e0e',
                    border:
                      step.status === 'COMPLETED'
                        ? '1px solid rgba(16, 185, 129, 0.3)'
                        : step.status === 'RUNNING'
                        ? '1px solid rgba(0, 136, 255, 0.4)'
                        : '1px solid #1f1f1f',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ marginTop: '2px', fontSize: '1rem', minWidth: '20px' }}>
                    {step.status === 'COMPLETED' && '✅'}
                    {step.status === 'RUNNING' && '⏳'}
                    {step.status === 'ERROR' && '❌'}
                    {step.status === 'PENDING' && '⚪'}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span
                        style={{
                          fontSize: '0.85rem',
                          fontWeight: 600,
                          color: step.status === 'COMPLETED' ? '#f5f5f5' : '#a0a0a0',
                        }}
                      >
                        {step.title}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: '#707070', fontStyle: 'italic' }}>
                        {step.subsystem}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#707070', marginTop: '2px' }}>
                      {step.description}
                    </div>
                    {step.details && (
                      <div
                        style={{
                          fontSize: '0.74rem',
                          color: '#0088ff',
                          marginTop: '4px',
                          fontFamily: 'monospace',
                          backgroundColor: '#000000',
                          border: '1px solid #202020',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          display: 'inline-block',
                        }}
                      >
                        {step.details}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Result Card (When Completed) */}
          {simulationResult && (
            <div
              style={{
                backgroundColor: '#0f0f0f',
                border: '1px solid #262626',
                borderRadius: '8px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.2rem' }}>🎯</span>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#f5f5f5' }}>
                    Fraud Scenario Successfully Orchestrated
                  </span>
                </div>
                <span style={{ fontSize: '0.75rem', color: '#707070', fontFamily: 'monospace' }}>
                  {simulationResult.scenario_id}
                </span>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: '10px',
                  backgroundColor: '#070707',
                  border: '1px solid #1a1a1a',
                  padding: '12px',
                  borderRadius: '6px',
                }}
              >
                <div>
                  <div style={{ fontSize: '0.68rem', color: '#707070', textTransform: 'uppercase' }}>GENERATED ALERT</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f5f5f5', fontFamily: 'monospace' }}>
                    {simulationResult.alert?.alert_id || 'ALT_DEMO_...'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.68rem', color: '#707070', textTransform: 'uppercase' }}>ML RISK SCORE</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ef4444' }}>
                    {simulationResult.ml_risk_assessment?.risk_score?.toFixed(1) || '88.5'} / 100
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.68rem', color: '#707070', textTransform: 'uppercase' }}>SUSPECT MULE</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f59e0b', fontFamily: 'monospace' }}>
                    {simulationResult.mule_account}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.68rem', color: '#707070', textTransform: 'uppercase' }}>PREDICTED ATMS</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#0088ff' }}>
                    {simulationResult.cashout_prediction?.predicted_atms?.length || 3} Locations
                  </div>
                </div>
              </div>

              {/* Action Buttons for deep investigation */}
              <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
                <button
                  onClick={handleOpenAlert}
                  style={{
                    flex: 1,
                    backgroundColor: '#161616',
                    color: '#f5f5f5',
                    border: '1px solid #0088ff',
                    borderRadius: '6px',
                    padding: '10px 16px',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span>🔍</span>
                  <span>Inspect Alert Dossier & Explanations</span>
                </button>
                <button
                  onClick={handleOpenCases}
                  style={{
                    backgroundColor: '#141414',
                    color: '#d4d4d4',
                    border: '1px solid #282828',
                    borderRadius: '6px',
                    padding: '10px 16px',
                    fontWeight: 600,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                  }}
                >
                  <span>📁</span>
                  <span>View Case Management</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer Controls */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid #1f1f1f',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#050505',
          }}
        >
          <button
            data-testid="reset-demo-btn"
            onClick={handleResetData}
            disabled={isRunning || isResetting}
            title="Purge all synthetic demonstration records from memory"
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.12)',
              color: '#f87171',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '6px',
              padding: '8px 14px',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: isRunning || isResetting ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            {isResetting ? 'Purging Demo Artifacts...' : '🧹 Purge Demo Data (Clean Reset)'}
          </button>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={onClose}
              disabled={isRunning || isResetting}
              style={{
                backgroundColor: 'transparent',
                color: '#a0a0a0',
                border: '1px solid #262626',
                borderRadius: '6px',
                padding: '8px 16px',
                fontSize: '0.85rem',
                cursor: 'pointer',
              }}
            >
              Close
            </button>
            <button
              data-testid="simulate-fraud-btn"
              onClick={handleRunSimulation}
              disabled={isRunning || isResetting}
              style={{
                backgroundColor: '#161616',
                color: '#f5f5f5',
                border: '1px solid #0088ff',
                borderRadius: '6px',
                padding: '8px 20px',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: isRunning || isResetting ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: isRunning ? 'none' : '0 0 12px rgba(0, 136, 255, 0.15)',
                transition: 'all 0.15s ease',
              }}
            >
              {isRunning ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>Executing Pipeline...</span>
                </>
              ) : (
                <>
                  <span>🚀</span>
                  <span>Run Live Fraud Scenario</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
