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

  async detachEvidence(linkId: string): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.delete<ReleaseGateDetailRead>(
      `/release-gate-evidence/${linkId}`,
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

  async addChecklistItem(
    productReleaseId: string,
    title: string,
    description?: string,
  ): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.post<ReleaseGateDetailRead>(
      `/product-releases/${productReleaseId}/gate/items`,
      { title, description: description || null },
    );
    return data;
  },

  async removeChecklistItem(
    productReleaseId: string,
    gateItemId: string,
  ): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.delete<ReleaseGateDetailRead>(
      `/product-releases/${productReleaseId}/gate/items/${gateItemId}`,
    );
    return data;
  },

  async downloadBundle(productReleaseId: string): Promise<void> {
    const response = await apiClient.get(
      `/product-releases/${productReleaseId}/gate/bundle`,
      { responseType: "blob" },
    );
    const contentDisposition: string = response.headers["content-disposition"] ?? "";
    const match = contentDisposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : "technical-documentation.zip";
    const url = URL.createObjectURL(response.data as Blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  },

  async downloadReport(productReleaseId: string): Promise<void> {
    /* Generate and download the PDF compliance report for this release. */
    const response = await apiClient.get(
      `/product-releases/${productReleaseId}/report`,
      { responseType: "blob" },
    );
    const contentDisposition: string = response.headers["content-disposition"] ?? "";
    const match = contentDisposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : "cra-compliance-report.pdf";
    const url = URL.createObjectURL(response.data as Blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  },
};
