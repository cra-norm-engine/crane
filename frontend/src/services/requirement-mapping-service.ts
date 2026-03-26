import { apiClient } from "@/services/api";
import type {
  RequirementMappingCreate,
  RequirementMappingRead,
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
};