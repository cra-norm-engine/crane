import { apiClient } from "@/services/api";
import type {
  RiskAssessmentApproveRequest,
  RiskAssessmentDetailRead,
  RiskAssessmentDuplicateRequest,
  RiskAssessmentRead,
  RiskAssessmentCreate,
  RiskAssessmentUpdate,
} from "@/types/risk-assessment";

export const riskAssessmentService = {
  async list(params?: {
    product_id?: string;
    product_release_id?: string;
  }): Promise<RiskAssessmentRead[]> {
    const { data } = await apiClient.get<RiskAssessmentRead[]>("/risk-assessments", {
      params,
    });
    return data;
  },

  async get(assessmentId: string): Promise<RiskAssessmentDetailRead> {
    const { data } = await apiClient.get<RiskAssessmentDetailRead>(
      `/risk-assessments/${assessmentId}`,
    );
    return data;
  },

  async create(payload: RiskAssessmentCreate): Promise<RiskAssessmentRead> {
    const { data } = await apiClient.post<RiskAssessmentRead>("/risk-assessments", payload);
    return data;
  },

  async update(
    assessmentId: string,
    payload: RiskAssessmentUpdate,
  ): Promise<RiskAssessmentRead> {
    const { data } = await apiClient.patch<RiskAssessmentRead>(
      `/risk-assessments/${assessmentId}`,
      payload,
    );
    return data;
  },

  async approve(
    assessmentId: string,
    payload: RiskAssessmentApproveRequest = {},
  ): Promise<RiskAssessmentRead> {
    const { data } = await apiClient.post<RiskAssessmentRead>(
      `/risk-assessments/${assessmentId}/approve`,
      payload,
    );
    return data;
  },

  async duplicateVersion(
    assessmentId: string,
    payload: RiskAssessmentDuplicateRequest,
  ): Promise<RiskAssessmentRead> {
    const { data } = await apiClient.post<RiskAssessmentRead>(
      `/risk-assessments/${assessmentId}/duplicate-version`,
      payload,
    );
    return data;
  },

  async remove(assessmentId: string): Promise<void> {
    await apiClient.delete(`/risk-assessments/${assessmentId}`);
  },
};
