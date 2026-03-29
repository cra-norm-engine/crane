import { apiClient } from "@/services/api";
import type {
  SecurityUpdateCreate,
  SecurityUpdateRead,
  SecurityUpdateUpdate,
} from "@/types/product";

export const securityUpdateService = {
  async list(productReleaseId?: string): Promise<SecurityUpdateRead[]> {
    const { data } = await apiClient.get<SecurityUpdateRead[]>("/security-updates/", {
      params: productReleaseId ? { product_release_id: productReleaseId } : undefined,
    });
    return data;
  },

  async get(securityUpdateId: string): Promise<SecurityUpdateRead> {
    const { data } = await apiClient.get<SecurityUpdateRead>(
      `/security-updates/${securityUpdateId}`,
    );
    return data;
  },

  async create(payload: SecurityUpdateCreate): Promise<SecurityUpdateRead> {
    const { data } = await apiClient.post<SecurityUpdateRead>("/security-updates/", payload);
    return data;
  },

  async update(
    securityUpdateId: string,
    payload: SecurityUpdateUpdate,
  ): Promise<SecurityUpdateRead> {
    const { data } = await apiClient.put<SecurityUpdateRead>(
      `/security-updates/${securityUpdateId}`,
      payload,
    );
    return data;
  },

  async remove(securityUpdateId: string): Promise<void> {
    await apiClient.delete(`/security-updates/${securityUpdateId}`);
  },
};