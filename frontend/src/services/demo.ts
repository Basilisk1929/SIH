/**
 * Phase 11F End-to-End SIH Demo Simulator API Service.
 */

import { DemoResetResponse, DemoSimulateResponse, DemoStatusResponse } from '../types';
import { ApiClient } from './api';

export const DemoService = {
  /**
   * Trigger the real live end-to-end multi-subsystem fraud simulation.
   */
  simulateFraud: async (): Promise<DemoSimulateResponse> => {
    return ApiClient.post<DemoSimulateResponse>('/demo/simulate-fraud');
  },

  /**
   * Safely purge all synthetic demonstration entities without affecting baseline data.
   */
  resetDemoData: async (): Promise<DemoResetResponse> => {
    return ApiClient.post<DemoResetResponse>('/demo/reset');
  },

  /**
   * Check the current count of loaded demo entities in memory.
   */
  getDemoStatus: async (): Promise<DemoStatusResponse> => {
    return ApiClient.get<DemoStatusResponse>('/demo/status');
  },
};
