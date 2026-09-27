/**
 * Central TypeScript Type Definitions for CyberShield-Intel Frontend.
 */

// ==============================================================================
// 1. AUTHENTICATION & RBAC
// ==============================================================================

export type UserRole = 'ADMIN' | 'SUPERVISOR' | 'INVESTIGATOR' | 'ANALYST';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  badge_number?: string;
  department?: string;
  is_active: boolean;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  expires_in?: number;
  role?: UserRole;
  email?: string;
}

// ==============================================================================
// 2. ALERTS & REAL-TIME STREAMING
// ==============================================================================

export type AlertSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'NEW' | 'ACKNOWLEDGED' | 'INVESTIGATING' | 'RESOLVED' | 'FALSE_POSITIVE';

export interface AlertEvaluationBreakdown {
  ml_risk?: { score: number; band: string; weight: number };
  velocity?: { transactions_last_1h: number; transactions_last_24h: number; weight: number };
  graph?: { degree: number; hops_to_known_mule: number; weight: number };
  cashout?: { cashout_ratio: number; rapid_exit_flag: boolean; weight: number };
  geographic?: { anomaly_flag: boolean; distance_from_home_km: number; weight: number };
  complaint?: { prior_complaints_count: number; linked_loss_inr: number; weight: number };
  total_composite_score?: number;
  assigned_severity?: AlertSeverity;
  primary_alert_type?: string;
  explanations?: string[];
  [key: string]: any;
}

export interface Alert {
  id: string;
  alert_id: string;
  alert_type: string;
  severity: AlertSeverity;
  status: AlertStatus;
  risk_score: number;
  triggered_entity_type: string;
  triggered_entity_id: string;
  account_id: string;
  transaction_id?: string;
  rule_flags?: AlertEvaluationBreakdown;
  is_deduplicated?: boolean;
  duplicate_count?: number;
  investigator_id?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
  disclaimer?: string;
}

export interface AlertStats {
  total_alerts: number;
  by_severity: Record<AlertSeverity, number>;
  by_status: Record<AlertStatus, number>;
  deduplicated_suppressions: number;
}

// ==============================================================================
// 3. CASE DOCKET MANAGEMENT
// ==============================================================================

export const CaseStatus = {
  OPEN: 'OPEN' as const,
  ASSIGNED: 'ASSIGNED' as const,
  INVESTIGATING: 'INVESTIGATING' as const,
  IN_PROGRESS: 'IN_PROGRESS' as const,
  ON_HOLD: 'ON_HOLD' as const,
  PENDING_COURT_ORDER: 'PENDING_COURT_ORDER' as const,
  ESCALATED: 'ESCALATED' as const,
  FROZEN: 'FROZEN' as const,
  RESOLVED: 'RESOLVED' as const,
  CLOSED: 'CLOSED' as const,
  ACTIVE: 'ACTIVE' as const,
  UNDER_REVIEW: 'UNDER_REVIEW' as const,
};
export type CaseStatus = (typeof CaseStatus)[keyof typeof CaseStatus];

export const CasePriority = {
  LOW: 'LOW' as const,
  MEDIUM: 'MEDIUM' as const,
  HIGH: 'HIGH' as const,
  CRITICAL: 'CRITICAL' as const,
};
export type CasePriority = (typeof CasePriority)[keyof typeof CasePriority];

export interface CaseNoteItem {
  id: string;
  case_id: string;
  author_id: string;
  author_name: string;
  author_role: string;
  content: string;
  is_internal: boolean;
  created_at: string;
  updated_at?: string;
}

export interface CaseEvidenceItem {
  id: string;
  case_id: string;
  evidence_type: string;
  evidence_reference_id: string;
  title: string;
  description?: string;
  metadata_json?: Record<string, any>;
  added_by: string;
  created_at: string;
}

export interface CaseTimelineEventItem {
  id: string;
  case_id: string;
  event_type: string;
  title: string;
  description?: string;
  actor_id: string;
  actor_role: string;
  timestamp: string;
  details?: Record<string, any>;
}

export interface CaseStats {
  total_cases: number;
  active_cases: number;
  requiring_investigation: number;
  assigned_to_user: number;
  recently_created: number;
  recently_resolved: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
}

export interface CaseDocket {
  id: string;
  case_number: string;
  alert_id?: string;
  title: string;
  description?: string;
  priority: CasePriority;
  status: CaseStatus;
  total_fraud_amount_inr?: number;
  recovered_amount_inr?: number;
  assigned_to?: string;
  assigned_investigator?: string;
  assigned_investigator_id?: string;
  assigned_investigator_name?: string;
  assigned_at?: string;
  assigned_by?: string;
  created_by?: string;
  created_at: string;
  updated_at?: string;
  resolved_at?: string;
  resolved_by?: string;
  resolution_status?: string;
  resolution_category?: string;
  resolution_reason?: string;
  resolution_notes?: string;
  closed_at?: string;
  closed_by?: string;
  linked_alert_ids: string[];
  linked_account_numbers: string[];
  linked_complaint_ids: string[];
  total_exposure_inr?: number;
  notes?: CaseNoteItem[] | string[];
  evidence?: CaseEvidenceItem[];
  timeline?: CaseTimelineEventItem[];
  notes_count?: number;
  evidence_count?: number;
  linked_alert?: Record<string, any>;
}


// ==============================================================================
// 4. FINANCIAL TRANSACTIONS & ML RISK
// ==============================================================================

export type PaymentRail = 'UPI' | 'IMPS' | 'NEFT' | 'RTGS';

export interface Transaction {
  id: string;
  txn_ref_no: string;
  sender_account?: string;
  receiver_account?: string;
  sender_upi?: string;
  receiver_upi?: string;
  amount_inr: number;
  rail_type: PaymentRail;
  timestamp: string;
  layer_depth: number;
  is_flagged_suspicious: boolean;
  anomaly_score: number;
  latitude?: number;
  longitude?: number;
}

export interface RiskFeatureExplanation {
  feature_name: string;
  feature_value: number | string;
  contribution_direction: 'INCREASES_RISK' | 'DECREASES_RISK' | 'NEUTRAL';
  importance_weight: number;
  human_readable_summary: string;
}

export interface TransactionRiskAssessment {
  risk_score: number;
  risk_band: AlertSeverity;
  is_suspicious: boolean;
  feature_explanations: RiskFeatureExplanation[];
  reasons?: string[];
  disclaimer: string;
  [key: string]: any;
}

// ==============================================================================
// 5. ACCOUNTS & MULE IDENTIFICATION
// ==============================================================================

export interface ConnectedAccount {
  account_number: string;
  hop_distance: number;
  relationship: string;
  total_transferred_inr: number;
  risk_score: number;
}

export interface AccountDetail {
  account_number: string;
  bank_name: string;
  ifsc?: string;
  ifsc_code?: string;
  account_holder_name?: string;
  holder_synthetic_name?: string;
  phone_masked?: string;
  upi_handle?: string;
  risk_score: number;
  risk_band?: AlertSeverity;
  is_frozen: boolean;
  freeze_reason?: string;
  mule_layer_detected?: number;
  flagged_reasons?: string[];
  first_seen_timestamp?: string;
  last_activity_timestamp?: string;
  transactions_count?: number;
  total_inflow_inr?: number;
  total_outflow_inr?: number;
  total_credit_volume_inr?: number;
  total_debit_volume_inr?: number;
  cashout_ratio?: number;
  connected_accounts?: ConnectedAccount[];
  recent_transactions?: Transaction[];
  linked_complaints_count?: number;
  home_city?: string;
  home_state?: string;
  [key: string]: any;
}

// ==============================================================================
// 6. COMPLAINTS & NLP INTELLIGENCE
// ==============================================================================

export interface ExtractedEntity {
  label: 'PERSON' | 'BANK' | 'ACCOUNT' | 'PHONE' | 'UPI_ID' | 'AMOUNT' | 'LOCATION' | 'DATE' | 'TRANSACTION_ID' | 'SCAM_TYPE';
  raw_value: string;
  normalized_value: string | number;
  confidence: number;
  start_char?: number;
  end_char?: number;
}

export interface Complaint {
  id: string;
  acknowledgement_no: string;
  category: string;
  subcategory?: string;
  victim_state: string;
  victim_district?: string;
  reported_loss_inr: number;
  suspect_upi?: string;
  suspect_account_number?: string;
  suspect_ifsc?: string;
  suspect_phone?: string;
  incident_timestamp?: string;
  incident_date?: string;
  narrative?: string;
  status: 'NEW' | 'UNDER_INVESTIGATION' | 'ESCALATED' | 'FROZEN' | 'CLOSED' | string;
  triage_priority?: CasePriority;
  risk_score: number;
  description_synthetic?: string;
  extracted_entities?: Record<string, any>;
  scam_typology?: {
    scam_type: string;
    confidence: number;
  };
  [key: string]: any;
}

// ==============================================================================
// 7. GRAPH TOPOLOGY & EVIDENCE
// ==============================================================================

export interface GraphNode {
  id: string;
  label: string;
  entity_type: 'ACCOUNT' | 'TRANSACTION' | 'UPI' | 'PHONE' | 'COMPLAINT' | 'BANK' | 'LOCATION';
  properties: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  properties: Record<string, any>;
}

export interface SubgraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  node_count: number;
  edge_count: number;
  metadata?: Record<string, any>;
}

// ==============================================================================
// 8. GEOSPATIAL & CASHOUT PREDICTION
// ==============================================================================

export interface NearestATM {
  outlet_id: string;
  bank_name: string;
  bank_code?: string;
  outlet_type: string;
  city?: string;
  district?: string;
  state?: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  distance_meters?: number;
}

export interface PredictedATM {
  atm_id: string;
  bank_name: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  prediction_score: number;
  rank: number;
  explanations: string[];
  outlet_type?: string;
  bank_category?: string;
  h3_cell?: string;
  city?: string;
  district?: string;
  state?: string;
}

export interface CashoutPredictionResult {
  account_id: string;
  prediction_timestamp: string;
  anchor_location: {
    latitude: number;
    longitude: number;
    source: string;
  };
  candidate_radius_km: number;
  total_candidates_evaluated: number;
  predicted_atms: PredictedATM[];
  urgency_level: 'STANDARD' | 'ELEVATED' | 'HIGH' | 'CRITICAL';
  disclaimer: string;
}

export interface SpatialHotspotCluster {
  cluster_id: number;
  centroid_lat: number;
  centroid_lng: number;
  incident_count: number;
  total_loss_inr: number;
  radius_km: number;
  dominant_pattern: string;
  reference_hub_name?: string;
}

export interface SpatialRiskCell {
  h3_cell: string;
  latitude: number;
  longitude: number;
  transaction_count: number;
  complaint_count: number;
  fraud_count: number;
  fraud_ratio: number;
  total_transaction_amount: number;
  total_complaint_loss: number;
  risk_score: number;
  risk_band: AlertSeverity;
  hotspot_cluster: number;
  nearest_atms: NearestATM[];
  dominant_scam_type?: string;
  disclaimer: string;
}

// ==============================================================================
// 9. OVERVIEW ANALYTICS & PAGINATION
// ==============================================================================

export interface AnalyticsOverview {
  total_complaints_reported: number;
  total_financial_loss_inr: number;
  active_mule_rings_detected: number;
  accounts_frozen_in_golden_hour: number;
  saved_loss_inr: number;
  critical_escalations: number;
  compliance_mode: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page?: number;
  limit?: number;
  pages?: number;
}

// ==============================================================================
// 10. PHASE 11F DEMO SIMULATOR TYPES
// ==============================================================================

export interface DemoSimulateResponse {
  scenario_id: string;
  status: string;
  is_demo: boolean;
  disclaimer: string;
  narrative_summary: string;
  victim_account: string;
  mule_account: string;
  amount_inr: number;
  complaint?: Record<string, any>;
  transaction?: Record<string, any>;
  ml_risk_assessment?: TransactionRiskAssessment;
  graph_evidence?: Record<string, any>;
  geospatial_intelligence?: Record<string, any>;
  cashout_prediction?: CashoutPredictionResult;
  alert?: Alert;
  created_at: string;
}

export interface DemoResetResponse {
  status: string;
  purged_alerts: number;
  purged_transactions: number;
  purged_complaints: number;
  purged_cases: number;
  purged_graph_edges: number;
  message: string;
  reset_at: string;
}

export interface DemoStatusResponse {
  is_demo_mode_enabled: boolean;
  active_demo_alerts_count: number;
  active_demo_cases_count: number;
  active_demo_transactions_count: number;
  active_demo_complaints_count: number;
  disclaimer: string;
}
