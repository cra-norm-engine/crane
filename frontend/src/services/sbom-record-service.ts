import { apiClient } from "@/services/api";
import type { SbomRecordCreate, SbomRecordRead, SbomRecordUpdate } from "@/types/product";

export const sbomRecordService = {
  async list(productReleaseId?: string): Promise<SbomRecordRead[]> {
    const { data } = await apiClient.get<SbomRecordRead[]>("/sbom-records/", {
      params: productReleaseId ? { product_release_id: productReleaseId } : undefined,
    });
    return data;
  },

  async get(sbomId: string): Promise<SbomRecordRead> {
    const { data } = await apiClient.get<SbomRecordRead>(`/sbom-records/${sbomId}`);
    return data;
  },

  async create(payload: SbomRecordCreate): Promise<SbomRecordRead> {
    const { data } = await apiClient.post<SbomRecordRead>("/sbom-records/", payload);
    return data;
  },

  async update(sbomId: string, payload: SbomRecordUpdate): Promise<SbomRecordRead> {
    const { data } = await apiClient.put<SbomRecordRead>(`/sbom-records/${sbomId}`, payload);
    return data;
  },

  async remove(sbomId: string): Promise<void> {
    await apiClient.delete(`/sbom-records/${sbomId}`);
  },
};
