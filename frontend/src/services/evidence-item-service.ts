// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type {
  EvidenceItemCreate,
  EvidenceItemRead,
  EvidenceItemUpdate,
} from "@/types/evidence-item";

export const evidenceItemService = {
  async list(params: {
    product_release_id?: string;
    risk_assessment_id?: string;
    requirement_mapping_id?: string;
  }): Promise<EvidenceItemRead[]> {
    const { data } = await apiClient.get<EvidenceItemRead[]>("/evidence-items", {
      params,
    });
    return data;
  },

  async get(evidenceItemId: string): Promise<EvidenceItemRead> {
    const { data } = await apiClient.get<EvidenceItemRead>(
      `/evidence-items/${evidenceItemId}`,
    );
    return data;
  },

  async create(payload: EvidenceItemCreate): Promise<EvidenceItemRead> {
    const { data } = await apiClient.post<EvidenceItemRead>("/evidence-items", payload);
    return data;
  },

  async update(
    evidenceItemId: string,
    payload: EvidenceItemUpdate,
  ): Promise<EvidenceItemRead> {
    const { data } = await apiClient.patch<EvidenceItemRead>(
      `/evidence-items/${evidenceItemId}`,
      payload,
    );
    return data;
  },

  async remove(evidenceItemId: string): Promise<void> {
    await apiClient.delete(`/evidence-items/${evidenceItemId}`);
  },
};