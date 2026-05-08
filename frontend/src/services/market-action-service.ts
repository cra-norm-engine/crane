import { apiClient } from "@/services/api";
import type {
  AuthorityNotifiedRequest,
  MarketActionCreate,
  MarketActionRead,
  MarketActionStatus,
  MarketActionType,
  MarketActionUpdate,
} from "@/types/market-action";

export const marketActionService = {
  async list(params?: {
    product_release_id?: string;
    action_type?: MarketActionType;
    status?: MarketActionStatus;
  }): Promise<MarketActionRead[]> {
    const { data } = await apiClient.get<MarketActionRead[]>("/market-actions/", { params });
    return data;
  },

  async get(actionId: string): Promise<MarketActionRead> {
    const { data } = await apiClient.get<MarketActionRead>(`/market-actions/${actionId}`);
    return data;
  },

  async create(payload: MarketActionCreate): Promise<MarketActionRead> {
    const { data } = await apiClient.post<MarketActionRead>("/market-actions/", payload);
    return data;
  },

  async update(actionId: string, payload: MarketActionUpdate): Promise<MarketActionRead> {
    const { data } = await apiClient.put<MarketActionRead>(`/market-actions/${actionId}`, payload);
    return data;
  },

  async markAuthorityNotified(
    actionId: string,
    payload: AuthorityNotifiedRequest = {},
  ): Promise<MarketActionRead> {
    const { data } = await apiClient.post<MarketActionRead>(
      `/market-actions/${actionId}/mark-authority-notified`,
      payload,
    );
    return data;
  },

  async close(actionId: string): Promise<MarketActionRead> {
    const { data } = await apiClient.post<MarketActionRead>(`/market-actions/${actionId}/close`);
    return data;
  },

  async remove(actionId: string): Promise<void> {
    await apiClient.delete(`/market-actions/${actionId}`);
  },
};
