// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type {
  DeclarationData,
  DeclarationEditFields,
  DeclarationSummary,
} from "@/types/declaration";
import type { ProductReleaseRead } from "@/types/release-gate";

// Client for the EU Declaration of Conformity endpoints (CRA Art. 28 / Annex V):
// listing, structured preview data, PDF download, and the draft/approved/signed
// workflow. Mirrors the blob-download pattern used by releaseGateService.
export const euDeclarationService = {
  // All releases with their DoC status, for the top-level Declarations page.
  async list(productId?: string): Promise<DeclarationSummary[]> {
    const { data } = await apiClient.get<DeclarationSummary[]>(
      "/product-releases/declarations",
      { params: productId ? { product_id: productId } : undefined },
    );
    return data;
  },

  // Structured Annex V content for the in-app preview (same builder backs the PDF).
  async getData(productReleaseId: string): Promise<DeclarationData> {
    const { data } = await apiClient.get<DeclarationData>(
      `/product-releases/${productReleaseId}/declaration/data`,
    );
    return data;
  },

  // Generate and download the DoC PDF. Extended timeout: WeasyPrint rendering on
  // low-resource hosts can take 60–90 s.
  async downloadPdf(productReleaseId: string): Promise<void> {
    const response = await apiClient.get(
      `/product-releases/${productReleaseId}/declaration`,
      { responseType: "blob", timeout: 120_000 },
    );
    const contentDisposition: string = response.headers["content-disposition"] ?? "";
    const match = contentDisposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : "eu-declaration-of-conformity.pdf";
    const url = URL.createObjectURL(response.data as Blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  },

  // Update editable DoC fields (Annex V). Only permitted while in draft.
  async update(
    productReleaseId: string,
    changes: Partial<DeclarationEditFields>,
  ): Promise<ProductReleaseRead> {
    const { data } = await apiClient.patch<ProductReleaseRead>(
      `/product-releases/${productReleaseId}/declaration`,
      changes,
    );
    return data;
  },

  // Return an approved DoC to draft so it can be edited again.
  async submit(productReleaseId: string): Promise<ProductReleaseRead> {
    const { data } = await apiClient.post<ProductReleaseRead>(
      `/product-releases/${productReleaseId}/declaration/submit`,
    );
    return data;
  },

  // Approve a draft DoC and capture its signature (approver + signatory).
  async approve(productReleaseId: string, signatory?: string): Promise<ProductReleaseRead> {
    const { data } = await apiClient.post<ProductReleaseRead>(
      `/product-releases/${productReleaseId}/declaration/approve`,
      { signatory: signatory ?? null },
    );
    return data;
  },

  // Formally sign (draw up) an approved DoC. Locks it from further edits.
  async sign(productReleaseId: string, signatory?: string): Promise<ProductReleaseRead> {
    const { data } = await apiClient.post<ProductReleaseRead>(
      `/product-releases/${productReleaseId}/declaration/sign`,
      { signatory: signatory ?? null },
    );
    return data;
  },
};
