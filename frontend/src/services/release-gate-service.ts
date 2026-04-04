import { apiClient } from "@/services/api";
import type { ReleaseGateDetailRead, GateDecision } from "@/types/release-gate";
import type { ArtifactType } from "@/types/artifact";

export const releaseGateService = {
  async getByRelease(productReleaseId: string): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.get<ReleaseGateDetailRead>(
      `/product-releases/${productReleaseId}/gate`,
    );
    return data;
  },

  async submit(productReleaseId: string): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.post<ReleaseGateDetailRead>(
      `/product-releases/${productReleaseId}/gate/submit`,
    );
    return data;
  },

  async approve(productReleaseId: string): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.post<ReleaseGateDetailRead>(
      `/product-releases/${productReleaseId}/gate/approve`,
    );
    return data;
  },

  async attachEvidence(
    productReleaseId: string,
    gateItemId: string,
    artifactRevisionId: string,
  ): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.post<ReleaseGateDetailRead>(
      `/product-releases/${productReleaseId}/gate/items/${gateItemId}/evidence`,
      { artifact_revision_id: artifactRevisionId },
    );
    return data;
  },

  async reviewEvidence(
    linkId: string,
    decision: GateDecision,
    rationale?: string,
  ): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.post<ReleaseGateDetailRead>(
      `/release-gate-evidence/${linkId}/review`,
      { decision, rationale: rationale || null },
    );
    return data;
  },

  async uploadEvidence(
    productReleaseId: string,
    gateItemId: string,
    formData: FormData,
  ): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.post<ReleaseGateDetailRead>(
      `/product-releases/${productReleaseId}/gate/items/${gateItemId}/upload`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return data;
  },

  async addEvidenceLink(
    productReleaseId: string,
    gateItemId: string,
    formData: FormData,
  ): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.post<ReleaseGateDetailRead>(
      `/product-releases/${productReleaseId}/gate/items/${gateItemId}/link`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return data;
  },
};
