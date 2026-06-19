// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type { ReleaseGateDetailRead, GateDecision } from "@/types/release-gate";
import type { ArtifactType } from "@/types/artifact";
import type { ReleaseReport } from "@/types/report";

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

  // Make `dependentItemId` require `prerequisiteItemId` to be accepted first.
  async addPrerequisite(
    productReleaseId: string,
    dependentItemId: string,
    prerequisiteItemId: string,
  ): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.post<ReleaseGateDetailRead>(
      `/product-releases/${productReleaseId}/gate/prerequisites`,
      null,
      { params: { dependent_item_id: dependentItemId, prerequisite_item_id: prerequisiteItemId } },
    );
    return data;
  },

  async removePrerequisite(
    productReleaseId: string,
    dependentItemId: string,
    prerequisiteItemId: string,
  ): Promise<ReleaseGateDetailRead> {
    const { data } = await apiClient.delete<ReleaseGateDetailRead>(
      `/product-releases/${productReleaseId}/gate/prerequisites`,
      { params: { dependent_item_id: dependentItemId, prerequisite_item_id: prerequisiteItemId } },
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
    /* Generate and download the PDF compliance report for this release.
       Extended timeout: WeasyPrint rendering on low-resource hosts can take 60–90 s. */
    const response = await apiClient.get(
      `/product-releases/${productReleaseId}/report`,
      { responseType: "blob", timeout: 120_000 },
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

  // Fetch the structured compliance-report data (all 17 sections) for the
  // in-app HTML report view. Same builder backs the PDF export.
  async getReportData(productReleaseId: string): Promise<ReleaseReport> {
    const { data } = await apiClient.get<ReleaseReport>(
      `/product-releases/${productReleaseId}/report/data`,
    );
    return data;
  },
};
