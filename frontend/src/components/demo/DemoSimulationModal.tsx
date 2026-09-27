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

  const [isRunning, setIsRunning] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusInfo, setStatusInfo] = useState<DemoStatusResponse | null>(null);
  const [steps, setSteps] = useState<StepState[]>(INITIAL_STEPS);
  const [simulationResult, setSimulationResult] = useState<DemoSimulateResponse | null>(null);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const data = await DemoService.getDemoStatus();
      setStatusInfo(data);
    } catch {
      // Ignore background status failure
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchStatus();
      setResetMessage(null);
      setError(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleRunSimulation = async () => {
    setIsRunning(true);
    setError(null);
    setResetMessage(null);
    setSimulationResult(null);

    // Reset steps to pending
    const runningSteps: StepState[] = INITIAL_STEPS.map((s) => ({ ...s, status: 'PENDING' }));
    setSteps(runningSteps);

    try {
      // Step animation progression simulation while waiting for backend
      runningSteps[0].status = 'RUNNING';
      setSteps([...runningSteps]);

      const result = await DemoService.simulateFraud();

      // Step completion cascade
      const updatedSteps: StepState[] = [
        {
          ...runningSteps[0],
          status: 'COMPLETED',
          details: `Ack: ${result.complaint?.acknowledgement_no || 'DEMO-NCRP-COMPLAINT'} • Loss: ₹${result.amount_inr.toLocaleString('en-IN')}`,
        },
        {
          ...runningSteps[1],
          status: 'COMPLETED',
          details: `Linked Suspect Account: ${result.mule_account} • Rail: UPI`,
        },
        {
          ...runningSteps[2],
          status: 'COMPLETED',
          details: `Txn Ref: ${result.transaction?.transaction_id || 'DEMO_TXN_...'} • Amount: ₹${result.amount_inr.toLocaleString('en-IN')}`,
        },
        {
          ...runningSteps[3],
          status: 'COMPLETED',
          details: `Risk Score: ${result.ml_risk_assessment?.risk_score?.toFixed(1) || '88.5'}/100 • Band: ${result.ml_risk_assessment?.risk_band || 'CRITICAL'}`,
        },
        {
          ...runningSteps[4],
          status: 'COMPLETED',
          details: `Nodes & Edges linked in Neo4j • Degree: ${result.graph_evidence?.degree ?? 4}`,
        },
        {
          ...runningSteps[5],
          status: 'COMPLETED',
          details: `Coordinates: 28.6139°N, 77.2090°E (New Delhi reference hub)`,
        },
        {
          ...runningSteps[6],
          status: 'COMPLETED',
          details: `Top ${result.cashout_prediction?.predicted_atms?.length || 3} ATMs ranked • Urgency: ${result.cashout_prediction?.urgency_level || 'CRITICAL'}`,
        },
        {
          ...runningSteps[7],
          status: 'COMPLETED',
          details: `Alert ID: ${result.alert?.alert_id || 'ALT_DEMO_...'} • Severity: ${result.alert?.severity || 'CRITICAL'}`,
        },
      ];

      setSteps(updatedSteps);
      setSimulationResult(result);
      fetchStatus();
      if (onSimulationSuccess) onSimulationSuccess(result);
    } catch (err: any) {
      setError(err.message || 'Simulation execution encountered an error.');
      setSteps((prev) =>
        prev.map((s) => (s.status === 'RUNNING' ? { ...s, status: 'ERROR' } : s))
      );
    } finally {
      setIsRunning(false);
    }
  };

  const handleResetData = async () => {
    if (!window.confirm('Are you sure you want to purge all synthetic demonstration data? Normal test and development data will NOT be touched.')) {
      return;
    }
    setIsResetting(true);
    setError(null);
    setResetMessage(null);
    try {
      const res = await DemoService.resetDemoData();
      setResetMessage(
        `Purged ${res.purged_alerts} alerts, ${res.purged_cases} cases, ${res.purged_transactions} transactions, and ${res.purged_complaints} complaints.`
      );
      setSimulationResult(null);
      setSteps(INITIAL_STEPS);
      fetchStatus();
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

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(5, 10, 20, 0.85)',
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
          backgroundColor: '#0a1122',
          border: '1px solid rgba(0, 242, 254, 0.3)',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '820px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.7), 0 0 30px rgba(0, 242, 254, 0.15)',
          overflow: 'hidden',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid #1e293b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'linear-gradient(90deg, rgba(0, 242, 254, 0.08) 0%, rgba(10, 17, 34, 0.95) 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '1.6rem' }}>⚡</span>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
                  SIH End-to-End Live Fraud Simulator
                </h3>
                <span
                  style={{
                    backgroundColor: 'rgba(0, 242, 254, 0.15)',
                    color: '#00f2fe',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    letterSpacing: '0.05em',
                  }}
                >
                  PHASE 11F
                </span>
              </div>
              <p style={{ margin: '3px 0 0 0', fontSize: '0.8rem', color: '#94a3b8' }}>
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
              color: '#64748b',
              fontSize: '1.5rem',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Statutory Disclaimer & Active State Notice */}
          <div
            style={{
              backgroundColor: 'rgba(30, 41, 59, 0.5)',
              border: '1px solid #334155',
              borderRadius: '8px',
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
            }}
          >
            <div style={{ fontSize: '0.78rem', color: '#cbd5e1' }}>
              <span style={{ fontWeight: 600, color: '#f59e0b' }}>⚠️ SYNTHETIC EVALUATION DATA: </span>
              All entities, bank accounts (<code style={{ color: '#00f2fe' }}>SYN_DEMO_...</code>), and NCRP complaints are synthetic test vectors. Zero real citizen PII is utilized.
            </div>
            {statusInfo && (
              <div style={{ display: 'flex', gap: '10px', fontSize: '0.72rem', color: '#94a3b8', whiteSpace: 'nowrap' }}>
                <span>Alerts: <strong style={{ color: '#f8fafc' }}>{statusInfo.active_demo_alerts_count}</strong></span>
                <span>•</span>
                <span>Cases: <strong style={{ color: '#f8fafc' }}>{statusInfo.active_demo_cases_count}</strong></span>
              </div>
            )}
          </div>

          {error && <ErrorMessage message={error} onRetry={() => handleRunSimulation()} />}
          {resetMessage && (
            <div
              style={{
                backgroundColor: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: '#6ee7b7',
                padding: '10px 14px',
                borderRadius: '8px',
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
              backgroundColor: '#121a2d',
              border: '1px solid #1e293b',
              borderRadius: '10px',
              padding: '16px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <h4 style={{ margin: 0, fontSize: '0.9rem', color: '#00f2fe', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Scenario: Urgent Utility Disconnection Scam
              </h4>
              <Badge severity="CRITICAL" size="sm">
                HIGH RISK VECTOR
              </Badge>
            </div>
            <p style={{ margin: 0, fontSize: '0.82rem', color: '#cbd5e1', lineHeight: '1.5' }}>
              Simulates a citizen receiving an urgent fraudulent disconnection call and transferring ₹85,000 via UPI to mule account{' '}
              <code style={{ color: '#f59e0b' }}>SYN_DEMO_MULE_9088</code>. Evaluates rapid ML detection, cross-source NLP complaint correlation, and ATM cash-out interception before the fraudster withdraws the funds.
            </p>
          </div>

          {/* Pipeline Traversal Timeline */}
          <div>
            <h4 style={{ margin: '0 0 12px 0', fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
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
                    borderRadius: '8px',
                    backgroundColor:
                      step.status === 'COMPLETED'
                        ? 'rgba(16, 185, 129, 0.06)'
                        : step.status === 'RUNNING'
                        ? 'rgba(0, 242, 254, 0.08)'
                        : '#0d1526',
                    border:
                      step.status === 'COMPLETED'
                        ? '1px solid rgba(16, 185, 129, 0.25)'
                        : step.status === 'RUNNING'
                        ? '1px solid rgba(0, 242, 254, 0.4)'
                        : '1px solid #1e293b',
                    transition: 'all 0.2s ease',
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
                          color: step.status === 'COMPLETED' ? '#f8fafc' : '#94a3b8',
                        }}
                      >
                        {step.title}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: '#64748b', fontStyle: 'italic' }}>
                        {step.subsystem}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
                      {step.description}
                    </div>
                    {step.details && (
                      <div
                        style={{
                          fontSize: '0.75rem',
                          color: '#00f2fe',
                          marginTop: '4px',
                          fontFamily: 'monospace',
                          backgroundColor: 'rgba(0, 0, 0, 0.3)',
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
                backgroundColor: 'rgba(0, 242, 254, 0.04)',
                border: '1px solid rgba(0, 242, 254, 0.3)',
                borderRadius: '10px',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.2rem' }}>🎯</span>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#f8fafc' }}>
                    Fraud Scenario Successfully Orchestrated
                  </span>
                </div>
                <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                  {simulationResult.scenario_id}
                </span>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: '10px',
                  backgroundColor: '#0a1122',
                  padding: '12px',
                  borderRadius: '8px',
                }}
              >
                <div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>GENERATED ALERT</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#00f2fe', fontFamily: 'monospace' }}>
                    {simulationResult.alert?.alert_id || 'ALT_DEMO_...'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>ML RISK SCORE</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f87171' }}>
                    {simulationResult.ml_risk_assessment?.risk_score?.toFixed(1) || '88.5'} / 100
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>SUSPECT MULE</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f59e0b', fontFamily: 'monospace' }}>
                    {simulationResult.mule_account}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>PREDICTED ATMS</div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#38bdf8' }}>
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
                    backgroundColor: '#00f2fe',
                    color: '#050b14',
                    border: 'none',
                    borderRadius: '8px',
                    padding: '10px 16px',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                  }}
                >
                  <span>🔍</span>
                  <span>Inspect Alert Dossier & Explanations</span>
                </button>
                <button
                  onClick={handleOpenCases}
                  style={{
                    backgroundColor: '#1e293b',
                    color: '#cbd5e1',
                    border: '1px solid #334155',
                    borderRadius: '8px',
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
            borderTop: '1px solid #1e293b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#070d1a',
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
              borderRadius: '8px',
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
                color: '#94a3b8',
                border: '1px solid #334155',
                borderRadius: '8px',
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
                backgroundColor: isRunning ? '#0284c7' : '#0284c7',
                backgroundImage: 'linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%)',
                color: '#050b14',
                border: 'none',
                borderRadius: '8px',
                padding: '8px 20px',
                fontSize: '0.85rem',
                fontWeight: 700,
                cursor: isRunning || isResetting ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: isRunning ? 'none' : '0 0 15px rgba(0, 242, 254, 0.3)',
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
