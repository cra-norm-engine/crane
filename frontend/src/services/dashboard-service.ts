// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type {
  ConformanceSummary,
  DashboardRead,
  ProductReadinessRead,
  ReleaseJourney,
} from "@/types/dashboard";

export const dashboardService = {
  async get(): Promise<DashboardRead> {
    const { data } = await apiClient.get<DashboardRead>("/dashboard");
    return data;
  },

  /** Per-product compliance readiness (Annex I Part I coverage), sorted worst-first. */
  async getProductReadiness(): Promise<ProductReadinessRead[]> {
    const { data } = await apiClient.get<ProductReadinessRead[]>("/dashboard/product-readiness");
    return data;
  },

  /** High-level portfolio conformance (% of in-scope products with an approved assessment). */
  async getConformance(): Promise<ConformanceSummary> {
    const { data } = await apiClient.get<ConformanceSummary>("/dashboard/conformance");
    return data;
  },

  // Fetch compliance journeys, optionally filtered by product and/or release.
  // No filter → active overview; product_id → that product's releases;
  // release_id → just that release.
  async getReleaseJourneys(filters?: {
    productId?: string;
    releaseId?: string;
  }): Promise<ReleaseJourney[]> {
    const params: Record<string, string> = {};
    if (filters?.productId) params.product_id = filters.productId;
    if (filters?.releaseId) params.release_id = filters.releaseId;
    const { data } = await apiClient.get<ReleaseJourney[]>("/dashboard/journeys", {
      params,
    });
    return data;
  },
};
