import { apiClient } from "@/services/api";
import type {
  ProductRequirementMatrixRowRead,
  ProductRequirementDecisionUpdate,
  RequirementMappingArtifactLinkRequest,
  RequirementMappingCreate,
  RequirementMappingRead,
  RequirementMappingMatrixRead,
  RequirementMappingUpdate,
} from "@/types/requirement-mapping";

export const requirementMappingService = {
  async list(params?: {
    risk_item_id?: string;
    annex_requirement_id?: string;
    matrix?: boolean;
  }): Promise<RequirementMappingRead[]> {
    const { data } = await apiClient.get<RequirementMappingRead[]>("/requirement-mappings", {
      params,
    });
    return data;
  },

  async get(mappingId: string): Promise<RequirementMappingRead> {
    const { data } = await apiClient.get<RequirementMappingRead>(
      `/requirement-mappings/${mappingId}`,
    );
    return data;
  },

  async create(payload: RequirementMappingCreate): Promise<RequirementMappingRead> {
    const { data } = await apiClient.post<RequirementMappingRead>(
      "/requirement-mappings",
      payload,
    );
    return data;
  },

  async update(
    mappingId: string,
    payload: RequirementMappingUpdate,
  ): Promise<RequirementMappingRead> {
    const { data } = await apiClient.patch<RequirementMappingRead>(
      `/requirement-mappings/${mappingId}`,
      payload,
    );
    return data;
  },

  async remove(mappingId: string): Promise<void> {
    await apiClient.delete(`/requirement-mappings/${mappingId}`);
  },

  async productMatrix(productId: string): Promise<ProductRequirementMatrixRowRead[]> {
    const { data } = await apiClient.get<ProductRequirementMatrixRowRead[]>(
      "/requirement-mappings/product-matrix",
      {
        params: { product_id: productId },
      },
    );
    return data;
  },

  async attachArtifact(
    mappingId: string,
    payload: RequirementMappingArtifactLinkRequest,
  ): Promise<RequirementMappingMatrixRead> {
    const { data } = await apiClient.post<RequirementMappingMatrixRead>(
      `/requirement-mappings/${mappingId}/artifacts`,
      payload,
    );
    return data;
  },

  async detachArtifact(
    mappingId: string,
    artifactId: string,
  ): Promise<RequirementMappingMatrixRead> {
    const { data } = await apiClient.delete<RequirementMappingMatrixRead>(
      `/requirement-mappings/${mappingId}/artifacts/${artifactId}`,
    );
    return data;
  },

  async updateProductRequirementDecision(
    productId: string,
    annexRequirementId: string,
    payload: ProductRequirementDecisionUpdate,
  ): Promise<void> {
    await apiClient.patch(
      `/requirement-mappings/product-matrix/${annexRequirementId}/decision`,
      payload,
      { params: { product_id: productId } },
    );
  },
};
