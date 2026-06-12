// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type { ArtifactListRead, ArtifactRead } from "@/types/artifact";

export const artifactService = {
  async list(params?: { product_id?: string; query?: string }): Promise<ArtifactListRead[]> {
    const { data } = await apiClient.get<ArtifactListRead[]>("/artifacts", { params });
    return data;
  },

  async getById(artifactId: string): Promise<ArtifactRead> {
    const { data } = await apiClient.get<ArtifactRead>(`/artifacts/${artifactId}`);
    return data;
  },

  async createUpload(formData: FormData): Promise<ArtifactRead> {
    const { data } = await apiClient.post<ArtifactRead>("/artifacts/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async createExternalLink(formData: FormData): Promise<ArtifactRead> {
    const { data } = await apiClient.post<ArtifactRead>("/artifacts/external-link", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async downloadRevision(revisionId: string, fallbackFilename: string): Promise<void> {
    const response = await apiClient.get<Blob>(`/artifacts/revisions/${revisionId}/download`, {
      responseType: "blob",
    });
    const blobUrl = window.URL.createObjectURL(response.data);
    const anchor = document.createElement("a");
    anchor.href = blobUrl;
    anchor.download = fallbackFilename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(blobUrl);
  },
};
