// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type {
  SecurityAdvisoryCreate,
  SecurityAdvisoryRead,
  SecurityAdvisoryUpdate,
} from "@/types/product";

export const securityAdvisoryService = {
  async list(opts?: { productId?: string; releaseId?: string }): Promise<SecurityAdvisoryRead[]> {
    const params: Record<string, string> = {};
    if (opts?.productId) params.product_id = opts.productId;
    if (opts?.releaseId) params.release_id = opts.releaseId;
    const { data } = await apiClient.get<SecurityAdvisoryRead[]>("/security-advisories/", {
      params: Object.keys(params).length ? params : undefined,
    });
    return data;
  },

  async get(advisoryId: string): Promise<SecurityAdvisoryRead> {
    const { data } = await apiClient.get<SecurityAdvisoryRead>(
      `/security-advisories/${advisoryId}`,
    );
    return data;
  },

  async create(payload: SecurityAdvisoryCreate): Promise<SecurityAdvisoryRead> {
    const { data } = await apiClient.post<SecurityAdvisoryRead>("/security-advisories/", payload);
    return data;
  },

  async update(
    advisoryId: string,
    payload: SecurityAdvisoryUpdate,
  ): Promise<SecurityAdvisoryRead> {
    const { data } = await apiClient.put<SecurityAdvisoryRead>(
      `/security-advisories/${advisoryId}`,
      payload,
    );
    return data;
  },

  async remove(advisoryId: string): Promise<void> {
    await apiClient.delete(`/security-advisories/${advisoryId}`);
  },
};
