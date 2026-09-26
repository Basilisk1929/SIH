/**
 * API service client for CyberShield Intel Backend.
 */

import { AnalyticsOverview, Complaint, SubgraphData, Transaction } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const ApiService = {
  async getAnalyticsOverview(): Promise<AnalyticsOverview> {
    try {
      const res = await fetch(`${API_BASE}/analytics/overview`);
      if (!res.ok) throw new Error('Network error');
      return await res.json();
    } catch {
      // Fallback synthetic data
      return {
        total_complaints_reported: 14280,
        total_financial_loss_inr: 284500000.0,
        active_mule_rings_detected: 42,
        accounts_frozen_in_golden_hour: 189,
        saved_loss_inr: 48200000.0,
        critical_escalations: 37,
        compliance_mode: "Strict Synthetic Simulation (SIH)",
      };
    }
  },

  async getComplaints(limit = 25, offset = 0): Promise<{ items: Complaint[]; total: number }> {
    try {
      const res = await fetch(`${API_BASE}/complaints?limit=${limit}&offset=${offset}`);
      if (!res.ok) throw new Error('Network error');
      return await res.json();
    } catch {
      // Fallback mock complaints
      return {
        items: [
          {
            id: "syn-c-1",
            acknowledgement_no: "NCRP-SYN-2024-10024",
            category: "Financial Fraud",
            subcategory: "UPI QR Code & Impersonation Scam",
            victim_state: "Maharashtra",
            victim_district: "Mumbai Suburban",
            reported_loss_inr: 48000,
            suspect_upi: "mule.849@synthaxis",
            suspect_account_number: "SYN9810482019",
            suspect_ifsc: "SYNB000101",
            suspect_phone: "+9198******12",
            incident_timestamp: new Date().toISOString(),
            status: "UNDER_INVESTIGATION",
            triage_priority: "HIGH",
            risk_score: 0.88,
            description_synthetic: "Victim scanned fraud merchant QR sent via WhatsApp to receive used car payment.",
          },
          {
            id: "syn-c-2",
            acknowledgement_no: "NCRP-SYN-2024-10025",
            category: "Task / Job Fraud",
            subcategory: "Telegram Rating Scam",
            victim_state: "Karnataka",
            victim_district: "Bengaluru Urban",
            reported_loss_inr: 125000,
            suspect_upi: "task.crypto@synthaxis",
            suspect_account_number: "SYN8820491023",
            suspect_ifsc: "SYNB000202",
            suspect_phone: "+9198******94",
            incident_timestamp: new Date().toISOString(),
            status: "ESCALATED",
            triage_priority: "CRITICAL",
            risk_score: 0.94,
            description_synthetic: "Promised 40% returns on completing YouTube channel reviews, trapped in layering tasks.",
          }
        ],
        total: 2,
      };
    }
  },

  async getRecentTransactions(): Promise<Transaction[]> {
    try {
      const res = await fetch(`${API_BASE}/transactions?limit=15`);
      if (!res.ok) throw new Error('Network error');
      return await res.json();
    } catch {
      return [
        {
          id: "txn-1",
          txn_ref_no: "UPI/42890184/SYN",
          amount_inr: 48000,
          rail_type: "UPI",
          timestamp: new Date().toISOString(),
          layer_depth: 1,
          is_flagged_suspicious: true,
          anomaly_score: 0.88,
          sender_upi: "victim@synthbank",
          receiver_upi: "mule.849@synthaxis",
        }
      ];
    }
  },

  async getAccountSubgraph(accountNumber: string): Promise<SubgraphData> {
    try {
      const res = await fetch(`${API_BASE}/graph/subgraph/${encodeURIComponent(accountNumber)}`);
      if (!res.ok) throw new Error('Network error');
      return await res.json();
    } catch {
      return {
        nodes: [
          { id: accountNumber, label: "BankAccount", properties: { account: accountNumber, risk: 0.88 } },
          { id: "MULE_L2_SYN", label: "BankAccount", properties: { account: "MULE_L2_SYN", risk: 0.79 } },
          { id: "CASHOUT_ATM", label: "BankAccount", properties: { account: "CASHOUT_GATEWAY", risk: 0.94 } }
        ],
        edges: [
          { source: accountNumber, target: "MULE_L2_SYN", relationship: "TRANSFERRED_TO", properties: { amount: 45000 } },
          { source: "MULE_L2_SYN", target: "CASHOUT_ATM", relationship: "TRANSFERRED_TO", properties: { amount: 42000 } }
        ],
        node_count: 3,
        edge_count: 2
      };
    }
  }
};

/**
 * PII masking utility to ensure sensitive identifiers are never rendered in cleartext.
 */
export function maskIdentifier(identifier: string | undefined): string {
  if (!identifier) return 'N/A';
  if (identifier.length <= 4) return '****';
  const start = identifier.slice(0, 2);
  const end = identifier.slice(-2);
  return `${start}${'*'.repeat(Math.max(4, identifier.length - 4))}${end}`;
}

export function formatINR(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}
