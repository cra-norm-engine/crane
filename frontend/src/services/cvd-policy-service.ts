import { apiClient } from "@/services/api";
import type { CvdPolicyCreate, CvdPolicyRead, CvdPolicyUpdate } from "@/types/product";

export const cvdPolicyService = {
  async list(productId?: string): Promise<CvdPolicyRead[]> {
    const { data } = await apiClient.get<CvdPolicyRead[]>("/cvd-policies/", {
      params: productId ? { product_id: productId } : undefined,
    });
    return data;
  },

  async get(policyId: string): Promise<CvdPolicyRead> {
    const { data } = await apiClient.get<CvdPolicyRead>(`/cvd-policies/${policyId}`);
    return data;
  },

  async create(payload: CvdPolicyCreate): Promise<CvdPolicyRead> {
    const { data } = await apiClient.post<CvdPolicyRead>("/cvd-policies/", payload);
    return data;
  },

  async update(policyId: string, payload: CvdPolicyUpdate): Promise<CvdPolicyRead> {
    const { data } = await apiClient.put<CvdPolicyRead>(`/cvd-policies/${policyId}`, payload);
    return data;
  },

  async remove(policyId: string): Promise<void> {
    await apiClient.delete(`/cvd-policies/${policyId}`);
  },
};
