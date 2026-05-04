import { apiClient } from "@/services/api";
import type {
  SecurityAdvisoryCreate,
  SecurityAdvisoryRead,
  SecurityAdvisoryUpdate,
} from "@/types/product";

export const securityAdvisoryService = {
  async list(productReleaseId?: string): Promise<SecurityAdvisoryRead[]> {
    const { data } = await apiClient.get<SecurityAdvisoryRead[]>("/security-advisories/", {
      params: productReleaseId ? { product_release_id: productReleaseId } : undefined,
    });
    return data;
  },

  async get(advisoryId: string): Promise<SecurityAdvisoryRead> {
    const { data } = await apiClient.get<SecurityAdvisoryRead>(
      `/security-advisories/${advisoryId}`,
    );
    return data;
  },

  async create(payload: SecurityAdvisoryCreate): Promise<SecurityAdvisoryRead> {
    const { data } = await apiClient.post<SecurityAdvisoryRead>("/security-advisories/", payload);
    return data;
  },

  async update(
    advisoryId: string,
    payload: SecurityAdvisoryUpdate,
  ): Promise<SecurityAdvisoryRead> {
    const { data } = await apiClient.put<SecurityAdvisoryRead>(
      `/security-advisories/${advisoryId}`,
      payload,
    );
    return data;
  },

  async remove(advisoryId: string): Promise<void> {
    await apiClient.delete(`/security-advisories/${advisoryId}`);
  },
};
