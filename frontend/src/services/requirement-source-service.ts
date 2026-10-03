import { apiClient } from "@/services/api";
import type { LibraryRequirement, RequirementSourceCreate, RequirementSourceRead } from "@/types/requirement-source";

export interface LibraryRequirementCreate {
  code: string;
  title: string;
  description: string;
  source_id: string;
  clause_reference?: string | null;
  applicability_guidance?: string | null;
  verification_guidance?: string | null;
  expected_evidence?: string | null;
  is_mandatory: boolean;
}

export const requirementSourceService = {
  async list(): Promise<RequirementSourceRead[]> {
    const { data } = await apiClient.get<RequirementSourceRead[]>("/requirement-sources");
    return data;
  },
  async create(payload: RequirementSourceCreate): Promise<RequirementSourceRead> {
    const { data } = await apiClient.post<RequirementSourceRead>("/requirement-sources", payload);
    return data;
  },
  async update(id: string, payload: Partial<RequirementSourceCreate>): Promise<RequirementSourceRead> {
    const { data } = await apiClient.patch<RequirementSourceRead>(`/requirement-sources/${id}`, payload);
    return data;
  },
  async setStatus(id: string, status: "published" | "retired"): Promise<RequirementSourceRead> {
    const { data } = await apiClient.post<RequirementSourceRead>(`/requirement-sources/${id}/status`, { status });
    return data;
  },
  async requirements(id: string): Promise<LibraryRequirement[]> {
    const { data } = await apiClient.get<LibraryRequirement[]>(`/requirement-sources/${id}/requirements`);
    return data;
  },
  async createRequirement(id: string, payload: LibraryRequirementCreate): Promise<LibraryRequirement> {
    const { data } = await apiClient.post<LibraryRequirement>(`/requirement-sources/${id}/requirements`, payload);
    return data;
  },
};
