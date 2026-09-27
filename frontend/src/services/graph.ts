/**
 * Graph Intelligence and Mule Link Analysis API service.
 */

import { SubgraphData } from '../types';
import { ApiClient } from './api';

export const GraphService = {
  async getNetworkGraph(accountNumber = 'SYN1122334455', maxHops = 2): Promise<SubgraphData> {
    return ApiClient.get<SubgraphData>(`/graph/subgraph/${encodeURIComponent(accountNumber)}?depth=${maxHops}`);
  },

  async getConnectedAccounts(accountNumber: string, limit = 50): Promise<any> {
    return ApiClient.get<any>(`/graph/connected-accounts/${encodeURIComponent(accountNumber)}?limit=${limit}`);
  },

  async getCashoutPaths(accountNumber: string, maxHops = 4): Promise<any> {
    return ApiClient.get<any>(`/graph/cashout-paths/${encodeURIComponent(accountNumber)}?max_hops=${maxHops}`);
  },

  async traceMuleChain(complaintAck: string): Promise<any> {
    return ApiClient.get<any>(`/graph/mule-chain/${encodeURIComponent(complaintAck)}`);
  },
};
