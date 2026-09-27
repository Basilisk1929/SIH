/**
 * NCRP Citizen Complaints and NLP Extraction API service.
 */

import { Complaint, PaginatedResponse } from '../types';
import { ApiClient } from './api';

export interface ComplaintCreateInput {
  narrative?: string;
  category?: string;
  subcategory?: string;
  reported_loss_inr?: number;
  victim_state?: string;
  victim_district?: string;
  suspect_upi?: string;
  suspect_account_number?: string;
  suspect_ifsc?: string;
  suspect_phone?: string;
  acknowledgement_no?: string;
}

export const ComplaintsService = {
  async getComplaints(limit = 25, offset = 0): Promise<PaginatedResponse<Complaint>> {
    return ApiClient.get<PaginatedResponse<Complaint>>(`/complaints?limit=${limit}&offset=${offset}`);
  },

  async processComplaintPipeline(payload: ComplaintCreateInput): Promise<any> {
    return ApiClient.post<any>('/complaints/pipeline', payload);
  },

  async extractNlpEntities(text: string): Promise<any> {
    return ApiClient.post<any>('/nlp/extract', { text });
  },
};
