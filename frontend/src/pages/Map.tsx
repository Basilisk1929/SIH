import React, { useEffect, useState } from 'react';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { CashoutPredictionCard } from '../components/investigation/CashoutPredictionCard';
import { GeoService } from '../services/geo';
import { SpatialHotspotCluster, NearestATM } from '../types';

export const Map: React.FC = () => {
  const [clusters, setClusters] = useState<SpatialHotspotCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Active view mode
  const [viewMode, setViewMode] = useState<'HOTSPOTS' | 'ATMS' | 'CASHOUT'>('HOTSPOTS');

  // Selected hotspot cluster or coordinate
  const [selectedCluster, setSelectedCluster] = useState<SpatialHotspotCluster | null>(null);

  // Nearest ATMs query
  const [atms, setAtms] = useState<NearestATM[]>([]);
  const [atmLoading, setAtmLoading] = useState(false);

  // Filters
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [h3Resolution, setH3Resolution] = useState<number>(7);

  // Map pan/zoom
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const loadHotspots = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await GeoService.getHotspots();
      const list = res.clusters || [];
      setClusters(list);
      if (list.length > 0 && !selectedCluster) {
        setSelectedCluster(list[0]);
        loadNearestAtms(list[0].centroid_lat, list[0].centroid_lng);
      }
    } catch (err: any) {
      console.error('Failed to load spatial hotspots:', err);
      setError(err.message || 'Unable to retrieve geospatial clusters from backend API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHotspots();
  }, []);

  const loadNearestAtms = async (lat: number, lng: number) => {
    try {
      setAtmLoading(true);
      const res = await GeoService.getNearestAtms(lat, lng, 6, 30.0);
      setAtms(res.nearest_atms || []);
    } catch (err) {
      console.warn('ATM query note:', err);
    } finally {
      setAtmLoading(false);
    }
  };

  const handleSelectCluster = (c: SpatialHotspotCluster) => {
    setSelectedCluster(c);
    loadNearestAtms(c.centroid_lat, c.centroid_lng);
  };

  // Convert Indian geo coordinates (lat ~8-36, lng ~68-98) to SVG viewbox (860 x 540)
  const projectGeo = (lat: number, lng: number) => {
    const minLat = 8.0;
    const maxLat = 35.5;
    const minLng = 68.0;
    const maxLng = 96.0;

    const x = ((lng - minLng) / (maxLng - minLng)) * 800 + 40;
    const y = ((maxLat - lat) / (maxLat - minLat)) * 480 + 30;
    return { x, y };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            🗺️ Geospatial Threat Hotspots & ATM Proximity Map
          </h1>
          <p style={{ margin: '4px 0 0 0', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
            H3 hexagonal spatial indexing, DBSCAN complaint density clustering, and RBI cash-out infrastructure intelligence.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className="btn-action"
            onClick={() => setViewMode('HOTSPOTS')}
            style={{
              background: viewMode === 'HOTSPOTS' ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.06)',
              color: viewMode === 'HOTSPOTS' ? '#070a12' : 'var(--text-primary)',
              fontWeight: viewMode === 'HOTSPOTS' ? 700 : 500,
              padding: '8px 14px',
              borderRadius: 6,
              fontSize: '0.82rem',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            🔥 DBSCAN Hotspots
          </button>
          <button
            className="btn-action"
            onClick={() => setViewMode('ATMS')}
            style={{
              background: viewMode === 'ATMS' ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.06)',
              color: viewMode === 'ATMS' ? '#070a12' : 'var(--text-primary)',
              fontWeight: viewMode === 'ATMS' ? 700 : 500,
              padding: '8px 14px',
              borderRadius: 6,
              fontSize: '0.82rem',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            🏧 RBI ATM Proximity
          </button>
          <button
            className="btn-action"
            onClick={() => setViewMode('CASHOUT')}
            style={{
              background: viewMode === 'CASHOUT' ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.06)',
              color: viewMode === 'CASHOUT' ? '#070a12' : 'var(--text-primary)',
              fontWeight: viewMode === 'CASHOUT' ? 700 : 500,
              padding: '8px 14px',
              borderRadius: 6,
              fontSize: '0.82rem',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            📍 Predictive Cash-Out (Phase 11C)
          </button>
        </div>
      </div>

      {/* Filter toolbar */}
      <div
        className="stat-card"
        style={{
          display: 'flex',
          gap: 16,
          alignItems: 'center',
          flexWrap: 'wrap',
          padding: '12px 18px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>H3 Resolution:</label>
          <select
            value={h3Resolution}
            onChange={(e) => setH3Resolution(parseInt(e.target.value))}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '6px 10px',
              borderRadius: 6,
              fontSize: '0.85rem',
            }}
          >
            <option value={6}>Resolution 6 (~36 km² Hexagon)</option>
            <option value={7}>Resolution 7 (~5.1 km² Hexagon)</option>
            <option value={8}>Resolution 8 (~0.73 km² Hexagon)</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Risk Severity:</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              padding: '6px 10px',
              borderRadius: 6,
              fontSize: '0.85rem',
            }}
          >
            <option value="ALL">All Risk Levels</option>
            <option value="CRITICAL">Critical (&gt; 80% Risk)</option>
            <option value="HIGH">High (&gt; 50% Risk)</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginLeft: 'auto' }}>
          <button
            className="btn-action"
            onClick={() => setZoom((z) => Math.min(2.5, z + 0.2))}
            style={{ padding: '6px 10px', fontSize: '0.85rem' }}
          >
            🔍+
          </button>
          <button
            className="btn-action"
            onClick={() => setZoom((z) => Math.max(0.6, z - 0.2))}
            style={{ padding: '6px 10px', fontSize: '0.85rem' }}
          >
            🔍-
          </button>
          <button
            className="btn-action"
            onClick={() => {
              setZoom(1);
              setPan({ x: 0, y: 0 });
            }}
            style={{ padding: '6px 10px', fontSize: '0.8rem' }}
          >
            Reset
          </button>
          <button
            className="btn-action"
            onClick={loadHotspots}
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Main Map View & Side Inspector */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 20 }}>
        {/* SVG Map Canvas */}
        <div
          className="stat-card"
          style={{
            position: 'relative',
            minHeight: 560,
            overflow: 'hidden',
            padding: 0,
            background: 'radial-gradient(circle at center, #0f172a 0%, #070a12 100%)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 10,
            cursor: isDragging ? 'grabbing' : 'grab',
          }}
          onMouseDown={(e) => {
            if (e.button !== 0) return;
            setIsDragging(true);
            setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
          }}
          onMouseMove={(e) => {
            if (!isDragging) return;
            setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
          }}
          onMouseUp={() => setIsDragging(false)}
        >
          {loading ? (
            <LoadingSpinner text="Computing H3 spatial hexagons and DBSCAN clusters..." minHeight={560} />
          ) : error ? (
            <div style={{ padding: 40 }}>
              <ErrorMessage message={error} onRetry={loadHotspots} />
            </div>
          ) : (
            <svg
              width="100%"
              height="560"
              viewBox="0 0 860 540"
              style={{ display: 'block', userSelect: 'none' }}
            >
              <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                {/* Lat/Lng Reference Grid Lines */}
                {[10, 15, 20, 25, 30].map((lat) => {
                  const p1 = projectGeo(lat, 68);
                  const p2 = projectGeo(lat, 96);
                  return (
                    <line
                      key={`lat-${lat}`}
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke="rgba(255,255,255,0.04)"
                      strokeWidth="1"
                    />
                  );
                })}
                {[72, 78, 84, 90].map((lng) => {
                  const p1 = projectGeo(8, lng);
                  const p2 = projectGeo(35, lng);
                  return (
                    <line
                      key={`lng-${lng}`}
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke="rgba(255,255,255,0.04)"
                      strokeWidth="1"
                    />
                  );
                })}

                {/* DBSCAN Hotspots Render */}
                {clusters.map((c) => {
                  const pos = projectGeo(c.centroid_lat, c.centroid_lng);
                  const isSelected = selectedCluster?.cluster_id === c.cluster_id;
                  const radius = Math.max(14, Math.min(36, (c.radius_km || 15) * 1.2));

                  return (
                    <g
                      key={`cluster-${c.cluster_id}`}
                      transform={`translate(${pos.x}, ${pos.y})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectCluster(c);
                      }}
                      style={{ cursor: 'pointer' }}
                    >
                      {/* Halo radius */}
                      <circle
                        r={radius}
                        fill="rgba(239, 68, 68, 0.15)"
                        stroke="#ef4444"
                        strokeWidth={isSelected ? 2.5 : 1.2}
                        strokeDasharray={isSelected ? '4 2' : undefined}
                      />

                      {/* Core marker */}
                      <circle
                        r="8"
                        fill={isSelected ? '#00f2fe' : '#ef4444'}
                        stroke="#fff"
                        strokeWidth="1.5"
                      />

                      {/* Cluster label */}
                      <text
                        y="-14"
                        fill="#fff"
                        fontSize="10"
                        fontWeight="600"
                        textAnchor="middle"
                        style={{ textShadow: '0 1px 4px rgba(0,0,0,0.9)' }}
                      >
                        {c.reference_hub_name || `Cluster #${c.cluster_id}`}
                      </text>

                      <text
                        y="18"
                        fill="rgba(255,255,255,0.7)"
                        fontSize="8"
                        fontFamily="var(--font-mono)"
                        textAnchor="middle"
                      >
                        {c.incident_count} incidents • ₹{((c.total_loss_inr || 0) / 100000).toFixed(1)}L
                      </text>
                    </g>
                  );
                })}

                {/* Nearest ATMs Render if in ATM mode or cluster selected */}
                {(viewMode === 'ATMS' || viewMode === 'CASHOUT') &&
                  atms.map((atm, idx) => {
                    const pos = projectGeo(atm.latitude, atm.longitude);
                    return (
                      <g
                        key={`atm-${atm.outlet_id || idx}`}
                        transform={`translate(${pos.x}, ${pos.y})`}
                        style={{ cursor: 'pointer' }}
                      >
                        <circle r="5" fill="#10b981" stroke="#fff" strokeWidth="1" />
                        <text
                          y="-8"
                          fill="#6ee7b7"
                          fontSize="8"
                          fontFamily="var(--font-mono)"
                          textAnchor="middle"
                        >
                          🏧 {atm.bank_name?.slice(0, 10)} ({atm.distance_km?.toFixed(1)}km)
                        </text>
                      </g>
                    );
                  })}
              </g>
            </svg>
          )}

          {/* Map Overlay Badge */}
          <div
            style={{
              position: 'absolute',
              top: 12,
              left: 12,
              background: 'rgba(7, 10, 18, 0.85)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 6,
              padding: '6px 12px',
              fontSize: '0.78rem',
              color: 'var(--text-secondary)',
            }}
          >
            Spatial Coverage: India National Cybercrime Corridor • {clusters.length} DBSCAN Threat Clusters Detected
          </div>
        </div>

        {/* Right Inspector Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {selectedCluster && (
            <div className="stat-card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    DBSCAN Hotspot Cluster #{selectedCluster.cluster_id}
                  </div>
                  <h3 style={{ margin: '4px 0 0 0', fontSize: '1.15rem', color: 'var(--accent-cyan)' }}>
                    {selectedCluster.reference_hub_name || `Cyber Hub #${selectedCluster.cluster_id}`}
                  </h3>
                </div>
                <Badge variant="CRITICAL">HIGH RISK</Badge>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 14 }}>
                <div style={{ background: 'var(--bg-primary)', padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Incident Volume</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {selectedCluster.incident_count} reports
                  </div>
                </div>
                <div style={{ background: 'var(--bg-primary)', padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Financial Exposure</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--accent-rose)' }}>
                    ₹{((selectedCluster.total_loss_inr || 0) / 100000).toFixed(1)} Lakh
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.45, marginBottom: 14 }}>
                <div>Centroid Coordinates: <code>{selectedCluster.centroid_lat.toFixed(4)}, {selectedCluster.centroid_lng.toFixed(4)}</code></div>
                <div>Dispersion Radius: <strong>{selectedCluster.radius_km?.toFixed(1) || 15} km</strong></div>
                <div>Dominant Modus Operandi: <strong style={{ color: 'var(--accent-cyan)' }}>{selectedCluster.dominant_pattern || 'UPI Task Scam'}</strong></div>
              </div>

              {/* Nearest Operational ATMs */}
              <div>
                <h4 style={{ fontSize: '0.88rem', margin: '0 0 8px 0', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>🏧</span> Nearest Operational RBI ATMs ({atms.length})
                </h4>
                {atmLoading ? (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Querying RBI registry...</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {atms.slice(0, 4).map((atm, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: 'var(--bg-primary)',
                          padding: '8px 10px',
                          borderRadius: 6,
                          fontSize: '0.8rem',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <strong style={{ color: 'var(--text-primary)' }}>{atm.bank_name}</strong>
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{atm.city || 'District Outpost'} • {atm.outlet_type || 'ATM'}</div>
                        </div>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-emerald)', fontSize: '0.78rem' }}>
                          {atm.distance_km?.toFixed(1)} km
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Phase 11C Predictive Cash-Out Location Integration */}
          <div>
            <h3 style={{ fontSize: '1.05rem', margin: '0 0 10px 0', color: 'var(--accent-cyan)' }}>
              📍 Cash-Out Location Prediction Engine (Phase 11C)
            </h3>
            <CashoutPredictionCard
              accountId="SYN9810482019"
              latitude={selectedCluster?.centroid_lat || 28.6139}
              longitude={selectedCluster?.centroid_lng || 77.209}
              accountRiskScore={0.88}
              cashoutRatio={0.92}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
