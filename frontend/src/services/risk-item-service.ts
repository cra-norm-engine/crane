import { apiClient } from "@/services/api";
import type { RiskItemCreate, RiskItemRead, RiskItemUpdate } from "@/types/risk-item";

export const riskItemService = {
  async listByAssessment(riskAssessmentId: string): Promise<RiskItemRead[]> {
    const { data } = await apiClient.get<RiskItemRead[]>("/risk-items", {
      params: { risk_assessment_id: riskAssessmentId },
    });
    return data;
  },

  async get(riskItemId: string): Promise<RiskItemRead> {
    const { data } = await apiClient.get<RiskItemRead>(`/risk-items/${riskItemId}`);
    return data;
  },

  async create(payload: RiskItemCreate): Promise<RiskItemRead> {
    const { data } = await apiClient.post<RiskItemRead>("/risk-items", payload);
    return data;
  },

  async update(riskItemId: string, payload: RiskItemUpdate): Promise<RiskItemRead> {
    const { data } = await apiClient.patch<RiskItemRead>(`/risk-items/${riskItemId}`, payload);
    return data;
  },

  async remove(riskItemId: string): Promise<void> {
    await apiClient.delete(`/risk-items/${riskItemId}`);
  },
};