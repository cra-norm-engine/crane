// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type {
  AnnexRequirementCreate,
  AnnexRequirementRead,
  AnnexRequirementUpdate,
} from "@/types/annex-requirement";

export const annexRequirementService = {
  async list(params?: {
    annex_part?: string;
    is_active?: boolean;
  }): Promise<AnnexRequirementRead[]> {
    const { data } = await apiClient.get<AnnexRequirementRead[]>("/annex-requirements", {
      params,
    });
    return data;
  },

  async get(annexRequirementId: string): Promise<AnnexRequirementRead> {
    const { data } = await apiClient.get<AnnexRequirementRead>(
      `/annex-requirements/${annexRequirementId}`,
    );
    return data;
  },

  async create(payload: AnnexRequirementCreate): Promise<AnnexRequirementRead> {
    const { data } = await apiClient.post<AnnexRequirementRead>("/annex-requirements", payload);
    return data;
  },

  async update(
    annexRequirementId: string,
    payload: AnnexRequirementUpdate,
  ): Promise<AnnexRequirementRead> {
    const { data } = await apiClient.patch<AnnexRequirementRead>(
      `/annex-requirements/${annexRequirementId}`,
      payload,
    );
    return data;
  },

  async remove(annexRequirementId: string): Promise<void> {
    await apiClient.delete(`/annex-requirements/${annexRequirementId}`);
  },
};