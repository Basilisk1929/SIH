import React, { useEffect, useState, useRef, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Badge } from '../components/common/Badge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorMessage } from '../components/common/ErrorMessage';
import { CashoutPredictionCard } from '../components/investigation/CashoutPredictionCard';
import { GeoService } from '../services/geo';
import { SpatialHotspotCluster, NearestATM, PredictedATM } from '../types';

export const Map: React.FC = () => {
  const [clusters, setClusters] = useState<SpatialHotspotCluster[]>([]);
  const [h3GeoJson, setH3GeoJson] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tileError, setTileError] = useState(false);

  // Active view mode
  const [viewMode, setViewMode] = useState<'HOTSPOTS' | 'ATMS' | 'CASHOUT'>('HOTSPOTS');

  // Selected hotspot cluster
  const [selectedCluster, setSelectedCluster] = useState<SpatialHotspotCluster | null>(null);

  // Nearest ATMs query
  const [atms, setAtms] = useState<NearestATM[]>([]);
  const [atmLoading, setAtmLoading] = useState(false);

  // Predicted cash-outs (Phase 11C)
  const [predictions, setPredictions] = useState<PredictedATM[]>([]);

  // Filters
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [h3Resolution, setH3Resolution] = useState<number>(7);

  // Leaflet map refs
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const hasInitialFitRef = useRef<boolean>(false);

  // Layer groups
  const h3LayerRef = useRef<L.GeoJSON | null>(null);
  const clusterLayerRef = useRef<L.LayerGroup | null>(null);
  const radiusLayerRef = useRef<L.LayerGroup | null>(null);
  const atmLayerRef = useRef<L.LayerGroup | null>(null);
  const predictionLayerRef = useRef<L.LayerGroup | null>(null);

  // Helper: Determine cluster risk severity
  const getClusterSeverity = (c: any): 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' => {
    const fraudAmt = c.total_loss_inr ?? c.total_amount_inr ?? 0;
    const count = c.incident_count ?? c.point_count ?? 0;
    if (fraudAmt > 25000000 || count >= 500) return 'CRITICAL';
    if (fraudAmt > 10000000 || count >= 200) return 'HIGH';
    if (fraudAmt > 2000000 || count >= 50) return 'MEDIUM';
    return 'LOW';
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return '#ef4444'; // Red
      case 'HIGH':
        return '#f97316'; // Orange/red
      case 'MEDIUM':
        return '#f59e0b'; // Amber
      case 'LOW':
      default:
        return '#10b981'; // Green
    }
  };

  const getH3Color = (riskBand: string): string => {
    switch (riskBand?.toUpperCase()) {
      case 'CRITICAL':
        return '#ef4444';
      case 'HIGH':
        return '#f97316';
      case 'MEDIUM':
        return '#f59e0b';
      case 'LOW':
      default:
        return '#10b981';
    }
  };

  // 1. Initial Data Ingestion
  const loadGeospatialData = async () => {
    try {
      setLoading(true);
      setError(null);
      setTileError(false);

      const [hotspotsRes, h3Res] = await Promise.allSettled([
        GeoService.getHotspots(),
        GeoService.getH3GeoJson(0.0),
      ]);

      let loadedClusters: SpatialHotspotCluster[] = [];

      if (hotspotsRes.status === 'fulfilled' && hotspotsRes.value?.clusters) {
        loadedClusters = (hotspotsRes.value.clusters as any[]).map((c: any) => ({
          ...c,
          incident_count: c.incident_count ?? c.point_count ?? 0,
          total_loss_inr: c.total_loss_inr ?? c.total_amount_inr ?? 0,
          reference_hub_name: c.reference_hub_name || c.nearest_reference_hub || `Cyber Hub #${c.cluster_id}`,
        }));
        setClusters(loadedClusters);
      } else {
        throw new Error('Geospatial intelligence temporarily unavailable.');
      }

      if (h3Res.status === 'fulfilled' && h3Res.value) {
        setH3GeoJson(h3Res.value);
      }

      if (loadedClusters.length > 0) {
        const initial = loadedClusters[0];
        setSelectedCluster(initial);
        loadNearestAtms(initial.centroid_lat, initial.centroid_lng);
        loadCashoutPredictions(initial.centroid_lat, initial.centroid_lng);
      }
    } catch (err: any) {
      console.error('Failed to load geospatial intelligence:', err);
      setError('Geospatial intelligence temporarily unavailable.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGeospatialData();
  }, []);

  const loadNearestAtms = async (lat: number, lng: number) => {
    try {
      setAtmLoading(true);
      const res = await GeoService.getNearestAtms(lat, lng, 6, 30.0);
      setAtms(res.nearest_atms || []);
    } catch (err) {
      console.warn('ATM proximity query notice:', err);
    } finally {
      setAtmLoading(false);
    }
  };

  const loadCashoutPredictions = async (lat: number, lng: number) => {
    try {
      const res = await GeoService.predictCashoutLocation({
        account_id: 'SYN_DEMO_VICTIM_4011',
        current_latitude: lat,
        current_longitude: lng,
        candidate_radius_km: 25.0,
        top_k: 5,
      });
      setPredictions(res.predicted_atms || []);
    } catch (err) {
      console.warn('Prediction engine note:', err);
    }
  };

  const handleSelectCluster = useCallback((c: SpatialHotspotCluster) => {
    setSelectedCluster(c);
    loadNearestAtms(c.centroid_lat, c.centroid_lng);
    loadCashoutPredictions(c.centroid_lat, c.centroid_lng);

    if (mapInstanceRef.current) {
      mapInstanceRef.current.panTo([c.centroid_lat, c.centroid_lng], { animate: true });
    }
  }, []);

  // 2. Initialize Leaflet Map (container is permanently mounted in DOM)
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    // Clear stale Leaflet container id if remounting
    if ((mapContainerRef.current as any)._leaflet_id) {
      delete (mapContainerRef.current as any)._leaflet_id;
    }

    // Center on India National Corridor
    const map = L.map(mapContainerRef.current, {
      center: [22.5937, 78.9629],
      zoom: 5,
      zoomControl: false,
      minZoom: 4,
      maxZoom: 18,
    });

    // Dark Matter Free Tiles (CartoDB / OpenStreetMap, ₹0 API key)
    const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    });

    tileLayer.on('tileerror', () => {
      console.warn('CartoDB tile loading warning — geospatial intelligence remains available.');
      setTileError(true);
    });

    tileLayer.addTo(map);

    // Create Layer Groups
    h3LayerRef.current = L.geoJSON(null).addTo(map);
    radiusLayerRef.current = L.layerGroup().addTo(map);
    clusterLayerRef.current = L.layerGroup().addTo(map);
    atmLayerRef.current = L.layerGroup().addTo(map);
    predictionLayerRef.current = L.layerGroup().addTo(map);

    mapInstanceRef.current = map;

    // Trigger initial invalidateSize after DOM layout stabilizes
    const initTimer = setTimeout(() => {
      map.invalidateSize();
    }, 150);

    return () => {
      clearTimeout(initTimer);
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Recalculate dimensions on window resize and after data loads
  useEffect(() => {
    if (!loading && mapInstanceRef.current) {
      const timer = setTimeout(() => {
        mapInstanceRef.current?.invalidateSize();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [loading]);

  useEffect(() => {
    const handleResize = () => {
      mapInstanceRef.current?.invalidateSize();
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 3. Render H3 Hexagonal Risk Polygons
  useEffect(() => {
    if (!mapInstanceRef.current || !h3LayerRef.current) return;

    h3LayerRef.current.clearLayers();

    if (h3GeoJson && h3GeoJson.features) {
      const filteredFeatures = h3GeoJson.features.filter((f: any) => {
        if (severityFilter === 'ALL') return true;
        const band = f.properties?.risk_band?.toUpperCase();
        return band === severityFilter;
      });

      h3LayerRef.current.addData({
        type: 'FeatureCollection',
        features: filteredFeatures,
      } as any);

      h3LayerRef.current.setStyle((feature: any) => {
        const band = feature?.properties?.risk_band || 'LOW';
        const color = getH3Color(band);
        return {
          fillColor: color,
          fillOpacity: 0.28,
          color: color,
          weight: 1.5,
          dashArray: '2, 4',
        };
      });

      h3LayerRef.current.eachLayer((layer: any) => {
        const p = layer.feature?.properties || {};
        const lossLakh = ((p.total_complaint_loss || 0) / 100000).toFixed(1);
        const color = getH3Color(p.risk_band);

        layer.bindTooltip(
          `<div style="font-family: var(--font-sans); font-size: 11px;">
            <div style="color: ${color}; font-weight: 700; margin-bottom: 2px;">H3 CELL: ${p.h3_cell}</div>
            <div>Risk Band: <b>${p.risk_band || 'UNKNOWN'}</b> (${p.risk_score ?? 0}%)</div>
            <div>Complaints: <b>${p.complaint_count || 0}</b></div>
            <div>Financial Loss: <b>₹${lossLakh} Lakh</b></div>
            <div>Surveillance Hub: <b>${p.nearest_cyber_hub || 'National Sector'}</b></div>
          </div>`,
          { sticky: true, className: 'leaflet-dark-tooltip' }
        );
      });
    }
  }, [h3GeoJson, severityFilter]);

  // 4. Render DBSCAN Threat Clusters & Radius
  useEffect(() => {
    if (!mapInstanceRef.current || !clusterLayerRef.current || !radiusLayerRef.current) return;

    clusterLayerRef.current.clearLayers();
    radiusLayerRef.current.clearLayers();

    const filteredClusters = clusters.filter((c) => {
      if (severityFilter === 'ALL') return true;
      const sev = getClusterSeverity(c);
      return sev === severityFilter;
    });

    filteredClusters.forEach((c) => {
      const isSelected = selectedCluster?.cluster_id === c.cluster_id;
      const severity = getClusterSeverity(c);
      const color = getSeverityColor(severity);
      const hubName = c.reference_hub_name || (c as any).nearest_reference_hub || `Cyber Hub #${c.cluster_id}`;
      const count = c.incident_count ?? (c as any).point_count ?? 0;
      const lossLakh = (((c.total_loss_inr ?? (c as any).total_amount_inr) || 0) / 100000).toFixed(1);

      // Distinct Marker using L.divIcon
      const clusterIcon = L.divIcon({
        className: 'custom-cluster-marker',
        html: `
          <div style="position: relative; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
            ${isSelected ? `<div style="position: absolute; width: 44px; height: 44px; border-radius: 50%; border: 2px solid ${color}; animation: marker-pulse 1.8s infinite; pointer-events: none;"></div>` : ''}
            <div style="width: 26px; height: 26px; border-radius: 50%; background: ${color}; border: 2px solid #ffffff; box-shadow: 0 0 12px ${color}; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 800; color: #ffffff;">
              ${c.cluster_id}
            </div>
          </div>
        `,
        iconSize: [34, 34],
        iconAnchor: [17, 17],
      });

      const marker = L.marker([c.centroid_lat, c.centroid_lng], { icon: clusterIcon });

      marker.on('click', () => {
        handleSelectCluster(c);
      });

      marker.bindPopup(`
        <div style="font-family: var(--font-sans); color: #f5f5f5; min-width: 190px;">
          <div style="font-size: 10px; text-transform: uppercase; color: ${color}; font-weight: 800; margin-bottom: 2px;">
            DBSCAN THREAT CLUSTER #${c.cluster_id} • ${severity}
          </div>
          <div style="font-size: 13px; font-weight: 700; color: #ffffff; margin-bottom: 6px;">
            ${hubName}
          </div>
          <div style="font-size: 11px; color: #a0a0a0; line-height: 1.5;">
            <div>Incident Volume: <b style="color: #ffffff;">${count} complaints</b></div>
            <div>Exposure: <b style="color: #ef4444;">₹${lossLakh} Lakh</b></div>
            <div>Pattern: <b style="color: #0088ff;">${c.dominant_pattern || 'phishing'}</b></div>
            <div>Centroid: <code>${c.centroid_lat.toFixed(4)}, ${c.centroid_lng.toFixed(4)}</code></div>
          </div>
        </div>
      `);

      clusterLayerRef.current?.addLayer(marker);
    });

    // Draw Cluster Radius Circle (only if radius > 0)
    if (selectedCluster && selectedCluster.radius_km && selectedCluster.radius_km > 0) {
      const radiusCircle = L.circle([selectedCluster.centroid_lat, selectedCluster.centroid_lng], {
        radius: selectedCluster.radius_km * 1000,
        color: getSeverityColor(getClusterSeverity(selectedCluster)),
        fillColor: getSeverityColor(getClusterSeverity(selectedCluster)),
        fillOpacity: 0.12,
        weight: 1.5,
        dashArray: '4, 4',
      });
      radiusLayerRef.current.addLayer(radiusCircle);
    }

    // Auto-fit bounds on initial cluster load
    if (!hasInitialFitRef.current && filteredClusters.length > 0 && mapInstanceRef.current) {
      const latLngs = filteredClusters.map((c) => [c.centroid_lat, c.centroid_lng] as [number, number]);
      const bounds = L.latLngBounds(latLngs);
      if (bounds.isValid()) {
        mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
        hasInitialFitRef.current = true;
      }
    }
  }, [clusters, selectedCluster, severityFilter, handleSelectCluster]);

  // 5. Render RBI ATM Proximity Markers
  useEffect(() => {
    if (!mapInstanceRef.current || !atmLayerRef.current) return;

    atmLayerRef.current.clearLayers();

    if (viewMode === 'ATMS' && atms.length > 0) {
      atms.forEach((atm) => {
        const atmIcon = L.divIcon({
          className: 'custom-atm-marker',
          html: `
            <div style="background: #042f2e; border: 1.5px solid #10b981; border-radius: 4px; padding: 2px 6px; color: #6ee7b7; font-size: 10px; font-weight: 700; display: flex; align-items: center; gap: 4px; white-space: nowrap; box-shadow: 0 2px 8px rgba(0,0,0,0.8); cursor: pointer;">
              <span>🏧</span> ${atm.bank_name ? atm.bank_name.slice(0, 10) : 'ATM'}
            </div>
          `,
          iconSize: [85, 22],
          iconAnchor: [42, 11],
        });

        const marker = L.marker([atm.latitude, atm.longitude], { icon: atmIcon });

        const locationStr = [atm.city, atm.district, atm.state].filter(Boolean).join(', ') || 'N/A';
        const distStr = atm.distance_km != null ? `${atm.distance_km.toFixed(2)} km` : 'Proximity linked';

        marker.bindPopup(`
          <div style="font-family: var(--font-sans); color: #f5f5f5; min-width: 190px;">
            <div style="font-size: 10px; color: #10b981; font-weight: 800; text-transform: uppercase; margin-bottom: 2px;">
              RBI OPERATIONAL ATM OUTLET
            </div>
            <div style="font-size: 13px; font-weight: 700; color: #ffffff; margin-bottom: 6px;">
              🏧 ${atm.bank_name || 'ATM Outlet'}
            </div>
            <div style="font-size: 11px; color: #a0a0a0; line-height: 1.5;">
              <div>Bank Name: <b style="color: #ffffff;">${atm.bank_name}</b></div>
              <div>ATM Type: <b style="color: #6ee7b7;">${atm.outlet_type || 'ATM'}</b></div>
              <div>Distance from Hotspot: <b style="color: #10b981;">${distStr}</b></div>
              <div>Location: <b>${locationStr}</b></div>
            </div>
          </div>
        `);

        atmLayerRef.current?.addLayer(marker);
      });
    }
  }, [atms, viewMode]);

  // 6. Render Predictive Cash-Out Markers (Phase 11C)
  useEffect(() => {
    if (!mapInstanceRef.current || !predictionLayerRef.current) return;

    predictionLayerRef.current.clearLayers();

    if (viewMode === 'CASHOUT' && predictions.length > 0) {
      predictions.forEach((pred) => {
        const predIcon = L.divIcon({
          className: 'custom-pred-marker',
          html: `
            <div style="background: #3b0764; border: 1.5px solid #a855f7; border-radius: 4px; padding: 2px 6px; color: #f3e8ff; font-size: 10px; font-weight: 700; display: flex; align-items: center; gap: 4px; white-space: nowrap; box-shadow: 0 0 10px rgba(168, 85, 247, 0.7); cursor: pointer;">
              <span style="background: #a855f7; color: #000000; font-size: 8px; padding: 1px 3px; border-radius: 2px; font-weight: 900;">PREDICTED</span>
              <span>${pred.bank_name ? pred.bank_name.slice(0, 10) : 'ATM'} #${pred.rank}</span>
            </div>
          `,
          iconSize: [115, 22],
          iconAnchor: [57, 11],
        });

        const marker = L.marker([pred.latitude, pred.longitude], { icon: predIcon });

        const locationStr = [pred.city, pred.district, pred.state].filter(Boolean).join(', ') || 'N/A';

        marker.bindPopup(`
          <div style="font-family: var(--font-sans); color: #f5f5f5; min-width: 220px;">
            <div style="display: inline-block; background: #a855f7; color: #000; font-size: 9px; font-weight: 900; padding: 2px 5px; border-radius: 3px; margin-bottom: 6px;">
              PREDICTED CASH-OUT LOCATION
            </div>
            <div style="font-size: 13px; font-weight: 700; color: #e9d5ff; margin-bottom: 6px;">
              ${pred.bank_name} (Rank #${pred.rank})
            </div>
            <div style="font-size: 11px; color: #a0a0a0; line-height: 1.5;">
              <div>Predicted Location: <b style="color: #ffffff;">${locationStr}</b></div>
              <div>Tactical Risk Score: <b style="color: #c084fc;">${pred.prediction_score}%</b></div>
              <div>Associated Account: <code style="color: var(--accent-cyan);">SYN_DEMO_VICTIM_4011</code></div>
              <div>Associated Cluster: <b style="color: #ffffff;">${selectedCluster?.reference_hub_name || 'Cyber Hub'}</b></div>
              <div>Proximity: <b>${pred.distance_km?.toFixed(2)} km</b></div>
            </div>
            <div style="margin-top: 8px; font-size: 10px; color: #fbbf24; border-top: 1px solid #262626; padding-top: 4px; line-height: 1.3;">
              ⚠️ Tactical prediction based on spatial proximity & H3 density. Not a confirmed crime event.
            </div>
          </div>
        `);

        predictionLayerRef.current?.addLayer(marker);
      });
    }
  }, [predictions, viewMode, selectedCluster]);

  // Filtered clusters by severity
  const filteredClusters = clusters.filter((c) => {
    if (severityFilter === 'ALL') return true;
    const sev = getClusterSeverity(c);
    return sev === severityFilter;
  });

  // Compact Map Controls Handlers
  const handleZoomIn = () => {
    mapInstanceRef.current?.zoomIn();
  };

  const handleZoomOut = () => {
    mapInstanceRef.current?.zoomOut();
  };

  const handleResetView = () => {
    if (!mapInstanceRef.current) return;
    mapInstanceRef.current.setView([22.5937, 78.9629], 5, { animate: true });
  };

  const handleFitThreats = () => {
    if (!mapInstanceRef.current) return;
    const target = filteredClusters.length > 0 ? filteredClusters : clusters;
    if (target.length === 0) return;
    const latLngs = target.map((c) => [c.centroid_lat, c.centroid_lng] as [number, number]);
    const bounds = L.latLngBounds(latLngs);
    if (bounds.isValid()) {
      mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50], animate: true });
    }
  };

  // Selected Cluster metrics
  const selectedSeverity = selectedCluster ? getClusterSeverity(selectedCluster) : 'HIGH';
  const selectedCount = selectedCluster ? (selectedCluster.incident_count ?? (selectedCluster as any).point_count ?? 0) : 0;
  const selectedLoss = selectedCluster ? (((selectedCluster.total_loss_inr ?? (selectedCluster as any).total_amount_inr) || 0) / 100000).toFixed(1) : '0.0';
  const selectedHubName = selectedCluster ? (selectedCluster.reference_hub_name || (selectedCluster as any).nearest_reference_hub || `Cyber Hub #${selectedCluster.cluster_id}`) : 'National Threat Cluster';

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

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            className="btn-action"
            onClick={() => setViewMode('HOTSPOTS')}
            style={{
              background: viewMode === 'HOTSPOTS' ? '#0088ff' : '#141414',
              color: viewMode === 'HOTSPOTS' ? '#ffffff' : '#a0a0a0',
              fontWeight: 600,
              padding: '8px 14px',
              borderRadius: 6,
              fontSize: '0.82rem',
              border: viewMode === 'HOTSPOTS' ? '1px solid #0088ff' : '1px solid #202020',
              cursor: 'pointer',
            }}
          >
            🔥 DBSCAN Hotspots
          </button>
          <button
            className="btn-action"
            onClick={() => setViewMode('ATMS')}
            style={{
              background: viewMode === 'ATMS' ? '#0088ff' : '#141414',
              color: viewMode === 'ATMS' ? '#ffffff' : '#a0a0a0',
              fontWeight: 600,
              padding: '8px 14px',
              borderRadius: 6,
              fontSize: '0.82rem',
              border: viewMode === 'ATMS' ? '1px solid #0088ff' : '1px solid #202020',
              cursor: 'pointer',
            }}
          >
            🏧 RBI ATM Proximity
          </button>
          <button
            className="btn-action"
            onClick={() => setViewMode('CASHOUT')}
            style={{
              background: viewMode === 'CASHOUT' ? '#0088ff' : '#141414',
              color: viewMode === 'CASHOUT' ? '#ffffff' : '#a0a0a0',
              fontWeight: 600,
              padding: '8px 14px',
              borderRadius: 6,
              fontSize: '0.82rem',
              border: viewMode === 'CASHOUT' ? '1px solid #0088ff' : '1px solid #202020',
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
            <option value="CRITICAL">Critical (&gt; ₹2.5 Cr / &gt; 500 Incidents)</option>
            <option value="HIGH">High (&gt; ₹1.0 Cr / &gt; 200 Incidents)</option>
            <option value="MEDIUM">Medium (&gt; ₹20 L / &gt; 50 Incidents)</option>
            <option value="LOW">Low Risk Baseline</option>
          </select>
        </div>

        <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginLeft: 'auto' }}>
          <button
            className="btn-action"
            onClick={loadGeospatialData}
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Main Map View & Side Inspector (Responsive Grid) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: 20,
          alignItems: 'start',
        }}
      >
        {/* Real Interactive Leaflet Map Container */}
        <div
          className="stat-card"
          style={{
            position: 'relative',
            minHeight: 560,
            height: 560,
            overflow: 'hidden',
            padding: 0,
            background: '#050505',
            border: '1px solid #202020',
            borderRadius: 10,
          }}
        >
          {/* Map DOM Element — Permanently mounted so Leaflet initializes reliably on mount */}
          <div
            ref={mapContainerRef}
            id="leaflet-threat-map"
            style={{
              width: '100%',
              height: '100%',
              minHeight: 560,
              backgroundColor: '#050505',
            }}
          />

          {/* Compact Map Controls [ + ] [ − ] [ Reset ] [ Fit Threats ] */}
          <div
            style={{
              position: 'absolute',
              top: 14,
              right: 14,
              zIndex: 1000,
              display: 'flex',
              gap: 6,
              background: 'rgba(10, 10, 10, 0.88)',
              padding: 4,
              borderRadius: 8,
              border: '1px solid #262626',
              backdropFilter: 'blur(4px)',
            }}
          >
            <button
              className="btn-action"
              onClick={handleZoomIn}
              style={{ padding: '4px 9px', fontSize: '0.85rem', minWidth: 28 }}
              title="Zoom In"
            >
              +
            </button>
            <button
              className="btn-action"
              onClick={handleZoomOut}
              style={{ padding: '4px 9px', fontSize: '0.85rem', minWidth: 28 }}
              title="Zoom Out"
            >
              −
            </button>
            <button
              className="btn-action"
              onClick={handleResetView}
              style={{ padding: '4px 10px', fontSize: '0.78rem' }}
              title="Reset View to National Extent"
            >
              Reset
            </button>
            <button
              className="btn-action"
              onClick={handleFitThreats}
              style={{ padding: '4px 10px', fontSize: '0.78rem' }}
              title="Fit All Threats"
            >
              Fit Threats
            </button>
          </div>

          {/* H3 Risk Legend */}
          <div
            style={{
              position: 'absolute',
              bottom: 20,
              left: 20,
              background: 'rgba(10, 10, 10, 0.88)',
              border: '1px solid #262626',
              borderRadius: 6,
              padding: '8px 12px',
              fontSize: '0.74rem',
              color: '#d4d4d4',
              zIndex: 1000,
              backdropFilter: 'blur(4px)',
              boxShadow: '0 4px 14px rgba(0,0,0,0.8)',
            }}
          >
            <div style={{ fontWeight: 700, marginBottom: 4, letterSpacing: '0.5px', color: '#ffffff' }}>
              H3 RISK
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ color: '#10b981', fontSize: '0.85rem' }}>●</span> Low
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ color: '#f59e0b', fontSize: '0.85rem' }}>●</span> Medium
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ color: '#f97316', fontSize: '0.85rem' }}>●</span> High
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ color: '#ef4444', fontSize: '0.85rem' }}>●</span> Critical
              </div>
            </div>
          </div>

          {/* Map Tile Fallback Notice */}
          {tileError && (
            <div
              style={{
                position: 'absolute',
                top: 14,
                left: 14,
                background: 'rgba(245, 158, 11, 0.18)',
                border: '1px solid #f59e0b',
                color: '#fbbf24',
                padding: '6px 12px',
                borderRadius: 6,
                fontSize: '0.74rem',
                zIndex: 1000,
                fontWeight: 600,
                backdropFilter: 'blur(4px)',
              }}
            >
              Map tiles unavailable — geospatial intelligence data is still available.
            </div>
          )}

          {/* Top-Left Coverage Badge */}
          {!tileError && (
            <div
              style={{
                position: 'absolute',
                top: 14,
                left: 14,
                background: 'rgba(7, 10, 18, 0.85)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 6,
                padding: '5px 10px',
                fontSize: '0.74rem',
                color: 'var(--text-secondary)',
                zIndex: 1000,
                backdropFilter: 'blur(4px)',
              }}
            >
              India National Cybercrime Corridor • {filteredClusters.length} of {clusters.length} DBSCAN Clusters Active
            </div>
          )}

          {/* Empty Filter Notification */}
          {!loading && !error && filteredClusters.length === 0 && (
            <div
              style={{
                position: 'absolute',
                top: 54,
                left: '50%',
                transform: 'translateX(-50%)',
                zIndex: 1001,
                background: 'rgba(15, 15, 15, 0.92)',
                border: '1px solid #333333',
                borderRadius: 8,
                padding: '8px 16px',
                color: '#e5e5e5',
                fontSize: '0.82rem',
                fontWeight: 600,
                boxShadow: '0 4px 16px rgba(0,0,0,0.8)',
                backdropFilter: 'blur(4px)',
              }}
            >
              No geospatial events available for the current filters.
            </div>
          )}

          {/* Loading Overlay */}
          {loading && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                zIndex: 1002,
                background: 'rgba(5, 5, 5, 0.82)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backdropFilter: 'blur(3px)',
              }}
            >
              <LoadingSpinner text="Loading geospatial intelligence..." minHeight={200} />
            </div>
          )}

          {/* Error Overlay */}
          {error && !loading && (
            <div
              style={{
                position: 'absolute',
                inset: 0,
                zIndex: 1002,
                background: 'rgba(5, 5, 5, 0.9)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 40,
              }}
            >
              <ErrorMessage message={error} onRetry={loadGeospatialData} />
            </div>
          )}
        </div>

        {/* Right Inspector Panel — Synchronized with selected cluster */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {selectedCluster && (
            <div className="stat-card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    DBSCAN Hotspot Cluster #{selectedCluster.cluster_id}
                  </div>
                  <h3 style={{ margin: '4px 0 0 0', fontSize: '1.15rem', color: 'var(--accent-cyan)' }}>
                    {selectedHubName}
                  </h3>
                </div>
                <Badge variant={selectedSeverity === 'CRITICAL' ? 'CRITICAL' : selectedSeverity === 'HIGH' ? 'HIGH' : 'LOW'}>
                  {selectedSeverity} RISK
                </Badge>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 14 }}>
                <div style={{ background: 'var(--bg-primary)', padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Incident Volume</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {selectedCount} reports
                  </div>
                </div>
                <div style={{ background: 'var(--bg-primary)', padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Financial Exposure</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--accent-rose)' }}>
                    ₹{selectedLoss} Lakh
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: 14 }}>
                <div>
                  Centroid: <code>{selectedCluster.centroid_lat.toFixed(4)}, {selectedCluster.centroid_lng.toFixed(4)}</code>
                </div>
                <div>
                  Dispersion Radius:{' '}
                  <strong>
                    {selectedCluster.radius_km && selectedCluster.radius_km > 0
                      ? `${selectedCluster.radius_km.toFixed(1)} km`
                      : 'N/A (Point Concentration)'}
                  </strong>
                </div>
                <div>
                  Dominant Modus Operandi:{' '}
                  <strong style={{ color: 'var(--accent-cyan)' }}>
                    {selectedCluster.dominant_pattern || 'phishing'}
                  </strong>
                </div>
              </div>

              {/* Nearest Operational ATMs */}
              <div>
                <h4
                  style={{
                    fontSize: '0.88rem',
                    margin: '0 0 8px 0',
                    color: 'var(--text-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span>🏧</span> Nearest Operational RBI ATMs ({atms.length})
                </h4>
                {atmLoading ? (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Querying RBI registry...</div>
                ) : atms.length === 0 ? (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No RBI ATMs linked within range.</div>
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
                          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                            {atm.city || 'District Outpost'} • {atm.outlet_type || 'ATM'}
                          </div>
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
              accountId="SYN_DEMO_VICTIM_4011"
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
