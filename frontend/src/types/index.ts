/**
 * Shared TypeScript type definitions for the CyberShield Platform.
 */

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
  incident_timestamp: string;
  status: 'NEW' | 'UNDER_INVESTIGATION' | 'ESCALATED' | 'FROZEN' | 'CLOSED';
  triage_priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_score: number;
  description_synthetic?: string;
}

export interface Transaction {
  id: string;
  txn_ref_no: string;
  sender_account?: string;
  receiver_account?: string;
  sender_upi?: string;
  receiver_upi?: string;
  amount_inr: number;
  rail_type: 'UPI' | 'IMPS' | 'NEFT' | 'RTGS';
  timestamp: string;
  layer_depth: number;
  is_flagged_suspicious: boolean;
  anomaly_score: number;
}

export interface RiskFactor {
  name: string;
  weight: number;
  score: number;
  description: string;
}

export interface RiskAssessment {
  entity_id: string;
  entity_type: string;
  overall_risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'SEVERE';
  is_mule_candidate: boolean;
  recommended_action: 'ALLOW' | 'MONITOR' | 'MANUAL_REVIEW' | 'EMERGENCY_FREEZE';
  contributing_factors: RiskFactor[];
}

export interface GraphNode {
  id: string;
  label: string;
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

export interface AnalyticsOverview {
  total_complaints_reported: number;
  total_financial_loss_inr: number;
  active_mule_rings_detected: number;
  accounts_frozen_in_golden_hour: number;
  saved_loss_inr: number;
  critical_escalations: number;
  compliance_mode: string;
}
