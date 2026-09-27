/**
 * Accounts and Mule Investigation API service.
 */

import { AccountDetail } from '../types';
import { ApiClient } from './api';

export const AccountsService = {
  async getAccountDetails(accountNumber: string): Promise<AccountDetail> {
    return ApiClient.get<AccountDetail>(`/accounts/${encodeURIComponent(accountNumber)}`);
  },

  async freezeAccount(accountNumber: string, reason: string): Promise<{ success: boolean; message: string; freeze_ref: string }> {
    return ApiClient.post<{ success: boolean; message: string; freeze_ref: string }>(
      `/accounts/${encodeURIComponent(accountNumber)}/freeze`,
      { reason }
    );
  },
};
