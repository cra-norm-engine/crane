// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type { CvdPolicyCreate, CvdPolicyRead, CvdPolicyUpdate } from "@/types/product";

export const cvdPolicyService = {
  async list(productId?: string): Promise<CvdPolicyRead[]> {
    const { data } = await apiClient.get<CvdPolicyRead[]>("/cvd-policies/", {
      params: productId ? { product_id: productId } : undefined,
    });
    return data;
  },

  async get(policyId: string): Promise<CvdPolicyRead> {
    const { data } = await apiClient.get<CvdPolicyRead>(`/cvd-policies/${policyId}`);
    return data;
  },

  async create(payload: CvdPolicyCreate): Promise<CvdPolicyRead> {
    const { data } = await apiClient.post<CvdPolicyRead>("/cvd-policies/", payload);
    return data;
  },

  async update(policyId: string, payload: CvdPolicyUpdate): Promise<CvdPolicyRead> {
    const { data } = await apiClient.put<CvdPolicyRead>(`/cvd-policies/${policyId}`, payload);
    return data;
  },

  async remove(policyId: string): Promise<void> {
    await apiClient.delete(`/cvd-policies/${policyId}`);
  },
};
