// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type { LabelData } from "@/types/declaration";

// Client for the package-label endpoints: structured preview data and PDF
// download. Mirrors the blob-download pattern used by releaseGateService.
export const packageLabelService = {
  // Structured label content for the in-app preview (same builder backs the PDF).
  async getData(productReleaseId: string): Promise<LabelData> {
    const { data } = await apiClient.get<LabelData>(
      `/product-releases/${productReleaseId}/label/data`,
    );
    return data;
  },

  // Generate and download the printable package-label PDF.
  async downloadPdf(productReleaseId: string): Promise<void> {
    const response = await apiClient.get(
      `/product-releases/${productReleaseId}/label`,
      { responseType: "blob", timeout: 120_000 },
    );
    const contentDisposition: string = response.headers["content-disposition"] ?? "";
    const match = contentDisposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : "package-label.pdf";
    const url = URL.createObjectURL(response.data as Blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  },
};
