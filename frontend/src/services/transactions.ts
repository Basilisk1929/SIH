/**
 * Transactions and ML Risk Assessment API service.
 */

import { Transaction, TransactionRiskAssessment } from '../types';
import { ApiClient } from './api';

export interface TransactionPipelineInput {
  sender_account: string;
  receiver_account: string;
  amount: number;
  rail_type?: string;
  sender_upi?: string;
  receiver_upi?: string;
  latitude?: number;
  longitude?: number;
  transactions_last_1h?: number;
  transactions_last_24h?: number;
  cashout_ratio?: number;
  graph_degree?: number;
  complaint_link_count?: number;
}

export interface TransactionPipelineOutput {
  transaction_id: string;
  txn_ref_no: string;
  sender_account: string;
  receiver_account: string;
  amount: number;
  rail_type: string;
  timestamp: string;
  risk_assessment: TransactionRiskAssessment;
  graph_evidence?: any;
  geospatial_intelligence?: any;
  alert?: any;
  pipeline_status: string;
}

export const TransactionsService = {
  async getRecentTransactions(limit = 25): Promise<Transaction[]> {
    return ApiClient.get<Transaction[]>(`/transactions?limit=${limit}`);
  },

  async evaluatePipeline(payload: TransactionPipelineInput): Promise<TransactionPipelineOutput> {
    return ApiClient.post<TransactionPipelineOutput>('/transactions/', payload);
  },

  async predictRiskDirect(features: Record<string, any>): Promise<any> {
    return ApiClient.post<any>('/risk/predict', { features });
  },
};
