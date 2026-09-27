import React, { useState, useEffect } from 'react';
import { CashoutPredictionResult, PredictedATM } from '../../types';
import { GeoService } from '../../services/geo';
import { Badge } from '../common/Badge';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { ErrorMessage } from '../common/ErrorMessage';

interface CashoutPredictionCardProps {
  accountId: string;
  currentLat?: number;
  currentLng?: number;
  latitude?: number;
  longitude?: number;
  recentTransactions?: any[];
  accountRiskScore?: number;
  cashoutRatio?: number;
  transactionsLast1h?: number;
  onSelectAtm?: (atm: PredictedATM) => void;
}

export const CashoutPredictionCard: React.FC<CashoutPredictionCardProps> = ({
  accountId,
  currentLat,
  currentLng,
  latitude,
  longitude,
  recentTransactions,
  accountRiskScore,
  cashoutRatio,
  transactionsLast1h,
  onSelectAtm,
}) => {
  const [prediction, setPrediction] = useState<CashoutPredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [radiusKm, setRadiusKm] = useState(15);
  const [topK, setTopK] = useState(3);
  const [selectedAtmId, setSelectedAtmId] = useState<string | null>(null);

  const effectiveLat = currentLat ?? latitude;
  const effectiveLng = currentLng ?? longitude;

  const fetchPrediction = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await GeoService.predictCashoutLocation({
        account_id: accountId,
        current_latitude: effectiveLat,
        current_longitude: effectiveLng,
        candidate_radius_km: radiusKm,
        top_k: topK,
        account_risk_score: accountRiskScore,
        cashout_ratio: cashoutRatio,
        transactions_last_1h: transactionsLast1h,
        recent_transactions: recentTransactions,
      });
      setPrediction(data);
      if (data.predicted_atms?.length > 0) {
        setSelectedAtmId(data.predicted_atms[0].atm_id);
        onSelectAtm?.(data.predicted_atms[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to predict cash-out locations from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrediction();
  }, [accountId, effectiveLat, effectiveLng, radiusKm, topK]);

  return (
    <div
      style={{
        backgroundColor: '#121a2d',
        border: '1px solid #1e293b',
        borderRadius: '10px',
        padding: '24px',
        margin: '16px 0',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.4rem' }}>🏧</span>
            <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#f8fafc' }}>
              Likely Cash-Out Location Prediction
            </h3>
            <span
              style={{
                fontSize: '0.65rem',
                backgroundColor: 'rgba(0, 242, 254, 0.15)',
                color: '#00f2fe',
                padding: '2px 8px',
                borderRadius: '4px',
                fontWeight: 700,
                letterSpacing: '0.05em',
                textTransform: 'uppercase',
                border: '1px solid rgba(0, 242, 254, 0.3)',
              }}
            >
              Phase 11C Engine
            </span>
          </div>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: '#94a3b8' }}>
            Predictive tactical ranking of operational Reserve Bank of India (RBI) ATMs based on spatial decay, H3 cybercrime risk, and velocity bursts.
          </p>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <select
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            style={{
              backgroundColor: '#0d1322',
              color: '#f8fafc',
              border: '1px solid #334155',
              padding: '6px 10px',
              borderRadius: '6px',
              fontSize: '0.8rem',
            }}
          >
            <option value={3}>Top 3 ATMs</option>
            <option value={5}>Top 5 ATMs</option>
            <option value={10}>Top 10 ATMs</option>
          </select>

          <select
            value={radiusKm}
            onChange={(e) => setRadiusKm(Number(e.target.value))}
            style={{
              backgroundColor: '#0d1322',
              color: '#f8fafc',
              border: '1px solid #334155',
              padding: '6px 10px',
              borderRadius: '6px',
              fontSize: '0.8rem',
            }}
          >
            <option value={5}>Radius: 5 km</option>
            <option value={10}>Radius: 10 km</option>
            <option value={15}>Radius: 15 km (Default)</option>
            <option value={25}>Radius: 25 km</option>
          </select>

          <button
            onClick={fetchPrediction}
            disabled={loading}
            style={{
              backgroundColor: 'rgba(0, 242, 254, 0.15)',
              color: '#00f2fe',
              border: '1px solid rgba(0, 242, 254, 0.4)',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Evaluating...' : 'Refresh Prediction'}
          </button>
        </div>
      </div>

      {/* Loading & Error States */}
      {loading && <LoadingSpinner message="Querying RBI ATM registry and computing multi-factor spatial likelihood..." />}
      {error && <ErrorMessage message={error} onRetry={fetchPrediction} />}

      {/* Predictions Content */}
      {!loading && !error && prediction && (
        <>
          {/* Metadata bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: '#0d1322',
              padding: '10px 16px',
              borderRadius: '6px',
              fontSize: '0.8rem',
              color: '#94a3b8',
              marginBottom: '16px',
              border: '1px solid #1e293b',
              flexWrap: 'wrap',
              gap: '8px',
            }}
          >
            <div>
              <span>Anchor Location: </span>
              <strong style={{ color: '#f8fafc', fontFamily: 'monospace' }}>
                {prediction.anchor_location.latitude.toFixed(4)}, {prediction.anchor_location.longitude.toFixed(4)}
              </strong>
              <span style={{ color: '#64748b', marginLeft: '6px' }}>({prediction.anchor_location.source})</span>
            </div>
            <div>
              <span>Candidates Evaluated: </span>
              <strong style={{ color: '#00f2fe' }}>{prediction.total_candidates_evaluated} operational ATMs</strong>
            </div>
            <div>
              <span>Urgency Level: </span>
              <Badge severity={prediction.urgency_level === 'CRITICAL' ? 'CRITICAL' : prediction.urgency_level === 'HIGH' ? 'HIGH' : 'MEDIUM'}>
                {prediction.urgency_level}
              </Badge>
            </div>
          </div>

          {/* ATMs Ranking List */}
          {prediction.predicted_atms.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '24px', color: '#64748b', fontSize: '0.85rem' }}>
              No operational RBI ATMs found within {radiusKm} km of anchor coordinates. Try increasing the search radius.
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
              {prediction.predicted_atms.map((atm) => {
                const isSelected = selectedAtmId === atm.atm_id;
                return (
                  <div
                    key={atm.atm_id}
                    onClick={() => {
                      setSelectedAtmId(atm.atm_id);
                      onSelectAtm?.(atm);
                    }}
                    style={{
                      backgroundColor: isSelected ? '#17223b' : '#0d1322',
                      border: isSelected ? '1px solid #00f2fe' : '1px solid #1e293b',
                      borderRadius: '8px',
                      padding: '16px',
                      cursor: 'pointer',
                      transition: 'border-color 0.15s ease, transform 0.15s ease',
                      boxShadow: isSelected ? '0 0 14px rgba(0, 242, 254, 0.2)' : 'none',
                    }}
                  >
                    {/* Top Row: Rank & Score */}
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span
                          style={{
                            width: '26px',
                            height: '26px',
                            borderRadius: '50%',
                            backgroundColor: atm.rank === 1 ? 'rgba(0, 242, 254, 0.2)' : 'rgba(255, 255, 255, 0.08)',
                            color: atm.rank === 1 ? '#00f2fe' : '#cbd5e1',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 800,
                            fontSize: '0.8rem',
                            border: atm.rank === 1 ? '1px solid #00f2fe' : '1px solid #334155',
                          }}
                        >
                          #{atm.rank}
                        </span>
                        <strong style={{ fontSize: '0.95rem', color: '#f8fafc' }}>{atm.bank_name}</strong>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.7rem', color: '#64748b', display: 'block' }}>Likelihood</span>
                        <span
                          style={{
                            fontSize: '1.05rem',
                            fontWeight: 700,
                            color: atm.prediction_score >= 80 ? '#ef4444' : atm.prediction_score >= 60 ? '#f59e0b' : '#00f2fe',
                            fontFamily: 'monospace',
                          }}
                        >
                          {atm.prediction_score.toFixed(1)} / 100
                        </span>
                      </div>
                    </div>

                    {/* Distance & Infrastructure Details */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '10px' }}>
                      <span>📍 <strong>{atm.distance_km.toFixed(2)} km</strong> away</span>
                      <span>•</span>
                      <span>{atm.outlet_type?.replace(/_/g, ' ') || 'ATM'}</span>
                      {atm.city && (
                        <>
                          <span>•</span>
                          <span>{atm.city}</span>
                        </>
                      )}
                    </div>

                    {/* Explanations List */}
                    <div style={{ backgroundColor: 'rgba(0, 0, 0, 0.25)', borderRadius: '6px', padding: '10px 12px' }}>
                      <span style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
                        Tactical Rationale:
                      </span>
                      <ul style={{ margin: '6px 0 0 16px', padding: 0, fontSize: '0.75rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                        {atm.explanations.map((reason, idx) => (
                          <li key={idx}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Statutory Data Limitation Disclaimer Notice */}
          <div
            style={{
              marginTop: '16px',
              padding: '12px 16px',
              backgroundColor: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              borderRadius: '6px',
              fontSize: '0.72rem',
              color: '#fcd34d',
              lineHeight: 1.45,
            }}
          >
            <strong>EVIDENTIARY DISCLOSURE:</strong> {prediction.disclaimer}
          </div>
        </>
      )}
    </div>
  );
};
