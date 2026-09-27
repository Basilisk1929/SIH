/**
 * Case Management and Forensic Dossier API service.
 */

import {
  CaseDocket,
  CaseEvidenceItem,
  CaseNoteItem,
  CasePriority,
  CaseStats,
  CaseStatus,
  CaseTimelineEventItem,
} from '../types';
import { ApiClient } from './api';

export interface CreateCasePayload {
  title: string;
  priority: CasePriority;
  alert_id?: string;
  linked_alert_ids?: string[];
  linked_account_numbers?: string[];
  linked_complaint_ids?: string[];
  initial_notes?: string;
  assigned_investigator_id?: string;
  assigned_investigator_name?: string;
  total_exposure_inr?: number;
}

export interface CreateCaseFromAlertPayload {
  alert_id: string;
  title?: string;
  priority?: CasePriority;
  assigned_to?: string;
  initial_notes?: string;
  attach_prediction?: boolean;
}

export interface UpdateCasePayload {
  title?: string;
  description?: string;
  status?: CaseStatus;
  priority?: CasePriority;
  recovered_amount_inr?: number;
  assigned_investigator_id?: string;
  assigned_investigator_name?: string;
  additional_notes?: string;
}

export interface CaseFilterParams {
  status?: string;
  priority?: string;
  investigator?: string;
  severity?: string;
  q?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  limit?: number;
}

export interface CaseListResult {
  cases: CaseDocket[];
  total: number;
  page: number;
  limit: number;
}

export const CasesService = {
  async getCases(params?: CaseFilterParams): Promise<CaseDocket[]> {
    const query = new URLSearchParams();
    if (params) {
      if (params.status && params.status !== 'ALL') query.set('status', params.status);
      if (params.priority && params.priority !== 'ALL') query.set('priority', params.priority);
      if (params.investigator) query.set('investigator', params.investigator);
      if (params.severity && params.severity !== 'ALL') query.set('severity', params.severity);
      if (params.q) query.set('q', params.q);
      if (params.page) query.set('page', String(params.page));
      if (params.limit) query.set('limit', String(params.limit));
    }

    const qs = query.toString();
    const endpoint = qs ? `/cases?${qs}` : '/cases';
    const res = await ApiClient.get<any>(endpoint);
    if (res && Array.isArray(res.cases)) {
      return res.cases;
    }
    if (Array.isArray(res)) {
      return res;
    }
    return [];
  },

  async getCasesWithPagination(params?: CaseFilterParams): Promise<CaseListResult> {
    const query = new URLSearchParams();
    if (params) {
      if (params.status && params.status !== 'ALL') query.set('status', params.status);
      if (params.priority && params.priority !== 'ALL') query.set('priority', params.priority);
      if (params.investigator) query.set('investigator', params.investigator);
      if (params.severity && params.severity !== 'ALL') query.set('severity', params.severity);
      if (params.q) query.set('q', params.q);
      if (params.page) query.set('page', String(params.page));
      if (params.limit) query.set('limit', String(params.limit));
    }

    const qs = query.toString();
    const endpoint = qs ? `/cases?${qs}` : '/cases';
    const res = await ApiClient.get<any>(endpoint);
    return {
      cases: res?.cases || [],
      total: res?.total || (res?.cases ? res.cases.length : 0),
      page: res?.page || 1,
      limit: res?.limit || 20,
    };
  },

  async getCaseStats(): Promise<CaseStats> {
    return ApiClient.get<CaseStats>('/cases/stats');
  },

  async getCaseById(caseId: string): Promise<CaseDocket> {
    return ApiClient.get<CaseDocket>(`/cases/${encodeURIComponent(caseId)}`);
  },

  async createCase(payload: CreateCasePayload): Promise<CaseDocket> {
    const backendPayload = {
      title: payload.title,
      description: payload.initial_notes || payload.title,
      priority: payload.priority || 'HIGH',
      alert_id: payload.alert_id,
      total_fraud_amount_inr: payload.total_exposure_inr || 0,
      assigned_to: payload.assigned_investigator_name || payload.assigned_investigator_id || 'investigator@cybercell.gov.in',
      initial_notes: payload.initial_notes,
      linked_alert_ids: payload.linked_alert_ids || [],
      linked_account_numbers: payload.linked_account_numbers || [],
      linked_complaint_ids: payload.linked_complaint_ids || [],
    };
    return ApiClient.post<CaseDocket>('/cases', backendPayload);
  },

  async createCaseFromAlert(payload: CreateCaseFromAlertPayload): Promise<CaseDocket> {
    return ApiClient.post<CaseDocket>('/cases/from-alert', payload);
  },

  async updateCase(caseId: string, payload: UpdateCasePayload): Promise<CaseDocket> {
    const backendPayload: Record<string, any> = {};
    if (payload.title) backendPayload.title = payload.title;
    if (payload.description) backendPayload.description = payload.description;
    if (payload.status) backendPayload.status = payload.status;
    if (payload.priority) backendPayload.priority = payload.priority;
    if (payload.recovered_amount_inr !== undefined) {
      backendPayload.recovered_amount_inr = payload.recovered_amount_inr;
    }
    if (payload.assigned_investigator_name || payload.assigned_investigator_id) {
      backendPayload.assigned_to = payload.assigned_investigator_name || payload.assigned_investigator_id;
    }
    if (payload.additional_notes) {
      backendPayload.investigation_notes = payload.additional_notes;
    }
    return ApiClient.patch<CaseDocket>(`/cases/${encodeURIComponent(caseId)}`, backendPayload);
  },

  async assignCase(caseId: string, payload: { assigned_investigator: string; notes?: string }): Promise<CaseDocket> {
    return ApiClient.post<CaseDocket>(`/cases/${encodeURIComponent(caseId)}/assign`, payload);
  },

  async getNotes(caseId: string): Promise<CaseNoteItem[]> {
    return ApiClient.get<CaseNoteItem[]>(`/cases/${encodeURIComponent(caseId)}/notes`);
  },

  async addNote(caseId: string, payload: { content: string; is_internal?: boolean }): Promise<CaseNoteItem> {
    return ApiClient.post<CaseNoteItem>(`/cases/${encodeURIComponent(caseId)}/notes`, payload);
  },

  async getEvidence(caseId: string): Promise<CaseEvidenceItem[]> {
    return ApiClient.get<CaseEvidenceItem[]>(`/cases/${encodeURIComponent(caseId)}/evidence`);
  },

  async addEvidence(
    caseId: string,
    payload: {
      evidence_type: string;
      evidence_reference_id: string;
      title: string;
      description?: string;
      metadata_json?: Record<string, any>;
    }
  ): Promise<CaseEvidenceItem> {
    return ApiClient.post<CaseEvidenceItem>(`/cases/${encodeURIComponent(caseId)}/evidence`, payload);
  },

  async getTimeline(caseId: string): Promise<CaseTimelineEventItem[]> {
    return ApiClient.get<CaseTimelineEventItem[]>(`/cases/${encodeURIComponent(caseId)}/timeline`);
  },

  async resolveCase(
    caseId: string,
    payload: {
      resolution_category: string;
      resolution_reason?: string;
      resolution_notes: string;
    }
  ): Promise<CaseDocket> {
    return ApiClient.post<CaseDocket>(`/cases/${encodeURIComponent(caseId)}/resolve`, payload);
  },

  async closeCase(
    caseId: string,
    payload: {
      closure_reason?: string;
      closure_notes?: string;
    }
  ): Promise<CaseDocket> {
    return ApiClient.post<CaseDocket>(`/cases/${encodeURIComponent(caseId)}/close`, payload);
  },

  async exportDossier(caseId: string): Promise<any> {
    return ApiClient.get<any>(`/cases/${encodeURIComponent(caseId)}/export`);
  },
};
