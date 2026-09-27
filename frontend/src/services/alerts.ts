/**
 * Alerts and Real-Time Triage API service.
 */

import { Alert, AlertSeverity, AlertStats, AlertStatus, PaginatedResponse } from '../types';
import { ApiClient } from './api';

export interface AlertFilterParams {
  limit?: number;
  offset?: number;
  page?: number;
  severity?: AlertSeverity;
  status?: AlertStatus;
  alert_type?: string;
  account_id?: string;
}

export const AlertsService = {
  async getAlerts(params: AlertFilterParams = {}): Promise<PaginatedResponse<Alert>> {
    const query = new URLSearchParams();
    if (params.limit) query.set('limit', String(params.limit));
    if (params.offset !== undefined) query.set('offset', String(params.offset));
    if (params.page !== undefined) query.set('page', String(params.page));
    if (params.severity) query.set('severity', params.severity);
    if (params.status) query.set('status', params.status);
    if (params.alert_type) query.set('alert_type', params.alert_type);
    if (params.account_id) query.set('account_id', params.account_id);

    const qs = query.toString();
    const endpoint = `/alerts${qs ? `?${qs}` : ''}`;
    return ApiClient.get<PaginatedResponse<Alert>>(endpoint);
  },

  async getAlertById(alertIdOrUuid: string): Promise<Alert> {
    return ApiClient.get<Alert>(`/alerts/${encodeURIComponent(alertIdOrUuid)}`);
  },

  async updateAlertStatus(
    alertIdOrUuid: string,
    status: AlertStatus,
    resolutionNotes?: string,
    investigatorId?: string
  ): Promise<Alert> {
    return ApiClient.patch<Alert>(`/alerts/${encodeURIComponent(alertIdOrUuid)}/status`, {
      status,
      resolution_notes: resolutionNotes,
      investigator_id: investigatorId,
    });
  },

  async getAlertStats(): Promise<AlertStats> {
    return ApiClient.get<AlertStats>('/alerts/stats');
  },

  async createAlertFromEvent(eventPayload: {
    event: {
      account_id: string;
      transaction_id?: string;
      amount?: number;
      ml_risk_score?: number;
      cashout_ratio?: number;
      transactions_last_1h?: number;
      latitude?: number;
      longitude?: number;
      graph_degree?: number;
      complaint_link_count?: number;
    };
    notes?: string;
  }): Promise<Alert> {
    return ApiClient.post<Alert>('/alerts', eventPayload);
  },
};
