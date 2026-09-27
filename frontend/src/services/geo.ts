/**
 * Geospatial Intelligence and Cash-Out Location Prediction API service.
 */

import {
  CashoutPredictionResult,
  NearestATM,
  SpatialHotspotCluster,
  SpatialRiskCell,
} from '../types';
import { ApiClient } from './api';

export interface CashoutPredictionInput {
  account_id: string;
  current_latitude?: number;
  current_longitude?: number;
  candidate_radius_km?: number;
  top_k?: number;
  account_risk_score?: number;
  cashout_ratio?: number;
  transactions_last_1h?: number;
  recent_transactions?: any[];
}

export const GeoService = {
  async getCellAnalysis(h3Cell: string): Promise<SpatialRiskCell> {
    return ApiClient.post<SpatialRiskCell>('/geo/cell-analysis', { h3_cell: h3Cell });
  },

  async getCoordinateAnalysis(latitude: number, longitude: number, resolution = 7): Promise<SpatialRiskCell> {
    return ApiClient.post<SpatialRiskCell>('/geo/coordinate-analysis', {
      latitude,
      longitude,
      resolution,
    });
  },

  async getNearestAtms(latitude: number, longitude: number, topK = 5, maxRadiusKm = 25.0): Promise<{
    query_point: { latitude: number; longitude: number };
    total_found: number;
    nearest_atms: NearestATM[];
  }> {
    return ApiClient.get(`/geo/nearest-atms?lat=${latitude}&lng=${longitude}&top_k=${topK}&max_radius_km=${maxRadiusKm}`);
  },

  async getHotspots(): Promise<{ total_clusters: number; clusters: SpatialHotspotCluster[] }> {
    return ApiClient.get('/geo/hotspots');
  },

  async getTemporalAnalysis(): Promise<any> {
    return ApiClient.get('/geo/temporal');
  },

  async getH3GeoJson(minRiskScore = 0.0): Promise<any> {
    return ApiClient.get(`/geo/geojson/h3-cells?min_risk_score=${minRiskScore}`);
  },

  async getAtmsGeoJson(maxRecords = 300): Promise<any> {
    return ApiClient.get(`/geo/geojson/atms?max_records=${maxRecords}`);
  },

  async getHotspotsGeoJson(): Promise<any> {
    return ApiClient.get('/geo/geojson/hotspots');
  },

  /**
   * Cash-Out Location Prediction Subsystem (Phase 11C)
   * Predicts and ranks candidate RBI ATMs for an investigated account.
   */
  async predictCashoutLocation(payload: CashoutPredictionInput): Promise<CashoutPredictionResult> {
    return ApiClient.post<CashoutPredictionResult>('/geo/predict-cashout-location', payload);
  },

  async getCashoutLinkageMetadata(): Promise<any> {
    return ApiClient.get('/geo/prediction/linkage-metadata');
  },
};
