// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type {
  ProductRequirementMatrixRowRead,
  ProductRequirementDecisionUpdate,
  RequirementAssessmentRead,
  RequirementImplementationStatusUpdate,
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
    release_id?: string;
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

  /** Load the full requirement matrix for a specific release. */
  async releaseMatrix(releaseId: string): Promise<ProductRequirementMatrixRowRead[]> {
    const { data } = await apiClient.get<ProductRequirementMatrixRowRead[]>(
      `/product-releases/${releaseId}/requirement-matrix`,
    );
    return data;
  },

  /** Load a single matrix row, used to refresh just the affected requirement
   *  after a trace-record mutation instead of reloading the whole matrix. */
  async releaseRequirementRow(
    releaseId: string,
    annexRequirementId: string,
  ): Promise<ProductRequirementMatrixRowRead> {
    const { data } = await apiClient.get<ProductRequirementMatrixRowRead>(
      `/product-releases/${releaseId}/requirement-matrix/${annexRequirementId}`,
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

  /** Get the release's requirement assessment status (for the approval banner). */
  async getAssessment(releaseId: string): Promise<RequirementAssessmentRead> {
    const { data } = await apiClient.get<RequirementAssessmentRead>(
      `/product-releases/${releaseId}/requirement-assessment`,
    );
    return data;
  },

  /** Finalise (approve) the release's requirement assessment, locking the matrix. */
  async approveAssessment(releaseId: string): Promise<RequirementAssessmentRead> {
    const { data } = await apiClient.post<RequirementAssessmentRead>(
      `/product-releases/${releaseId}/requirement-assessment/approve`,
    );
    return data;
  },

  /** Reopen an approved assessment for amendment (returns it to draft). */
  async reopenAssessment(releaseId: string): Promise<RequirementAssessmentRead> {
    const { data } = await apiClient.post<RequirementAssessmentRead>(
      `/product-releases/${releaseId}/requirement-assessment/reopen`,
    );
    return data;
  },

  /** Update the applicability decision for a requirement on a specific release.
   *  Returns the rebuilt matrix row so the caller can update state in place. */
  async updateReleaseRequirementDecision(
    releaseId: string,
    annexRequirementId: string,
    payload: ProductRequirementDecisionUpdate,
  ): Promise<ProductRequirementMatrixRowRead> {
    const { data } = await apiClient.patch<ProductRequirementMatrixRowRead>(
      `/product-releases/${releaseId}/requirement-matrix/${annexRequirementId}/decision`,
      payload,
    );
    return data;
  },

  /** Update the per-requirement implementation status for a release.
   *  Returns the rebuilt matrix row for in-place state updates. */
  async updateReleaseRequirementStatus(
    releaseId: string,
    annexRequirementId: string,
    payload: RequirementImplementationStatusUpdate,
  ): Promise<ProductRequirementMatrixRowRead> {
    const { data } = await apiClient.patch<ProductRequirementMatrixRowRead>(
      `/product-releases/${releaseId}/requirement-matrix/${annexRequirementId}/status`,
      payload,
    );
    return data;
  },
};
