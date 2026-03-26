import { apiClient } from "@/services/api";
import type {
  AnnexPart,
  AnnexRequirementCreate,
  AnnexRequirementRead,
  AnnexRequirementUpdate,
  EvidenceItemCreate,
  EvidenceItemRead,
  EvidenceItemUpdate,
  RequirementMappingCreate,
  RequirementMappingRead,
  RequirementMappingUpdate,
  RiskAssessmentCreate,
  RiskAssessmentDuplicateRequest,
  RiskAssessmentRead,
  RiskAssessmentUpdate,
  RiskItemCreate,
  RiskItemRead,
  RiskItemUpdate,
} from "@/types/risk";

export interface RiskAssessmentListParams {
  product_id?: string;
  product_release_id?: string;
}

export interface AnnexRequirementListParams {
  is_active?: boolean;
  annex_part?: AnnexPart;
}

export interface RequirementMappingListParams {
  risk_item_id?: string;
  annex_requirement_id?: string;
  matrix?: boolean;
}

export interface EvidenceItemListParams {
  product_release_id?: string;
  risk_assessment_id?: string;
  requirement_mapping_id?: string;
}

class RiskService {
  async listRiskAssessments(params: RiskAssessmentListParams): Promise<RiskAssessmentRead[]> {
    const response = await apiClient.get<RiskAssessmentRead[]>("/risk-assessments", { params });
    return response.data;
  }

  async getRiskAssessment(assessmentId: string): Promise<RiskAssessmentRead> {
    const response = await apiClient.get<RiskAssessmentRead>(`/risk-assessments/${assessmentId}`);
    return response.data;
  }

  async createRiskAssessment(payload: RiskAssessmentCreate): Promise<RiskAssessmentRead> {
    const response = await apiClient.post<RiskAssessmentRead>("/risk-assessments", payload);
    return response.data;
  }

  async updateRiskAssessment(
    assessmentId: string,
    payload: RiskAssessmentUpdate,
  ): Promise<RiskAssessmentRead> {
    const response = await apiClient.patch<RiskAssessmentRead>(
      `/risk-assessments/${assessmentId}`,
      payload,
    );
    return response.data;
  }

  async approveRiskAssessment(assessmentId: string): Promise<RiskAssessmentRead> {
    const response = await apiClient.post<RiskAssessmentRead>(
      `/risk-assessments/${assessmentId}/approve`,
      {},
    );
    return response.data;
  }

  async duplicateRiskAssessmentVersion(
    assessmentId: string,
    payload: RiskAssessmentDuplicateRequest,
  ): Promise<RiskAssessmentRead> {
    const response = await apiClient.post<RiskAssessmentRead>(
      `/risk-assessments/${assessmentId}/duplicate-version`,
      payload,
    );
    return response.data;
  }

  async listRiskItems(riskAssessmentId: string): Promise<RiskItemRead[]> {
    const response = await apiClient.get<RiskItemRead[]>("/risk-items", {
      params: { risk_assessment_id: riskAssessmentId },
    });
    return response.data;
  }

  async getRiskItem(riskItemId: string): Promise<RiskItemRead> {
    const response = await apiClient.get<RiskItemRead>(`/risk-items/${riskItemId}`);
    return response.data;
  }

  async createRiskItem(payload: RiskItemCreate): Promise<RiskItemRead> {
    const response = await apiClient.post<RiskItemRead>("/risk-items", payload);
    return response.data;
  }

  async updateRiskItem(riskItemId: string, payload: RiskItemUpdate): Promise<RiskItemRead> {
    const response = await apiClient.patch<RiskItemRead>(`/risk-items/${riskItemId}`, payload);
    return response.data;
  }

  async deleteRiskItem(riskItemId: string): Promise<void> {
    await apiClient.delete(`/risk-items/${riskItemId}`);
  }

  async listAnnexRequirements(
    params?: AnnexRequirementListParams,
  ): Promise<AnnexRequirementRead[]> {
    const response = await apiClient.get<AnnexRequirementRead[]>("/annex-requirements", { params });
    return response.data;
  }

  async getAnnexRequirement(requirementId: string): Promise<AnnexRequirementRead> {
    const response = await apiClient.get<AnnexRequirementRead>(
      `/annex-requirements/${requirementId}`,
    );
    return response.data;
  }

  async createAnnexRequirement(
    payload: AnnexRequirementCreate,
  ): Promise<AnnexRequirementRead> {
    const response = await apiClient.post<AnnexRequirementRead>(
      "/annex-requirements",
      payload,
    );
    return response.data;
  }

  async updateAnnexRequirement(
    requirementId: string,
    payload: AnnexRequirementUpdate,
  ): Promise<AnnexRequirementRead> {
    const response = await apiClient.patch<AnnexRequirementRead>(
      `/annex-requirements/${requirementId}`,
      payload,
    );
    return response.data;
  }

  async listRequirementMappings(
    params?: RequirementMappingListParams,
  ): Promise<RequirementMappingRead[]> {
    const response = await apiClient.get<RequirementMappingRead[]>("/requirement-mappings", {
      params,
    });
    return response.data;
  }

  async getRequirementMapping(mappingId: string): Promise<RequirementMappingRead> {
    const response = await apiClient.get<RequirementMappingRead>(
      `/requirement-mappings/${mappingId}`,
    );
    return response.data;
  }

  async createRequirementMapping(
    payload: RequirementMappingCreate,
  ): Promise<RequirementMappingRead> {
    const response = await apiClient.post<RequirementMappingRead>(
      "/requirement-mappings",
      payload,
    );
    return response.data;
  }

  async updateRequirementMapping(
    mappingId: string,
    payload: RequirementMappingUpdate,
  ): Promise<RequirementMappingRead> {
    const response = await apiClient.patch<RequirementMappingRead>(
      `/requirement-mappings/${mappingId}`,
      payload,
    );
    return response.data;
  }

  async deleteRequirementMapping(mappingId: string): Promise<void> {
    await apiClient.delete(`/requirement-mappings/${mappingId}`);
  }

  async listEvidenceItems(params: EvidenceItemListParams): Promise<EvidenceItemRead[]> {
    const response = await apiClient.get<EvidenceItemRead[]>("/evidence-items", { params });
    return response.data;
  }

  async getEvidenceItem(evidenceItemId: string): Promise<EvidenceItemRead> {
    const response = await apiClient.get<EvidenceItemRead>(
      `/evidence-items/${evidenceItemId}`,
    );
    return response.data;
  }

  async createEvidenceItem(payload: EvidenceItemCreate): Promise<EvidenceItemRead> {
    const response = await apiClient.post<EvidenceItemRead>("/evidence-items", payload);
    return response.data;
  }

  async updateEvidenceItem(
    evidenceItemId: string,
    payload: EvidenceItemUpdate,
  ): Promise<EvidenceItemRead> {
    const response = await apiClient.patch<EvidenceItemRead>(
      `/evidence-items/${evidenceItemId}`,
      payload,
    );
    return response.data;
  }

  async deleteEvidenceItem(evidenceItemId: string): Promise<void> {
    await apiClient.delete(`/evidence-items/${evidenceItemId}`);
  }
}

export const riskService = new RiskService();
export default riskService;