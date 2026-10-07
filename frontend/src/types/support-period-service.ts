// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type {
  SupportPeriodRecordCreate,
  SupportPeriodRecordHistoryRead,
  SupportPeriodRecordRead,
  SupportPeriodRecordUpdate,
  SupportPeriodSnippetGenerateRequest,
  SupportPeriodSnippetRead,
} from "@/types/product";

export const supportPeriodService = {
  async list(params?: {
    product_id?: string;
    active_only?: boolean;
  }): Promise<SupportPeriodRecordRead[]> {
    const { data } = await apiClient.get<SupportPeriodRecordRead[]>("/support-periods/", {
      params,
    });
    return data;
  },

  async get(recordId: string): Promise<SupportPeriodRecordRead> {
    const { data } = await apiClient.get<SupportPeriodRecordRead>(`/support-periods/${recordId}`);
    return data;
  },

  async create(payload: SupportPeriodRecordCreate): Promise<SupportPeriodRecordRead> {
    const { data } = await apiClient.post<SupportPeriodRecordRead>("/support-periods/", payload);
    return data;
  },

  async update(recordId: string, payload: SupportPeriodRecordUpdate): Promise<SupportPeriodRecordRead> {
    const { data } = await apiClient.put<SupportPeriodRecordRead>(
      `/support-periods/${recordId}`,
      payload,
    );
    return data;
  },

  async getActiveForProduct(productId: string): Promise<SupportPeriodRecordRead> {
    const { data } = await apiClient.get<SupportPeriodRecordRead>(
      `/support-periods/product/${productId}/active`,
    );
    return data;
  },

  async getHistoryForProduct(productId: string): Promise<SupportPeriodRecordHistoryRead> {
    const { data } = await apiClient.get<SupportPeriodRecordHistoryRead>(
      `/support-periods/product/${productId}/history`,
    );
    return data;
  },

  async generateSnippets(
    payload: SupportPeriodSnippetGenerateRequest,
  ): Promise<SupportPeriodSnippetRead> {
    const { data } = await apiClient.post<SupportPeriodSnippetRead>(
      "/support-periods/generate-snippets",
      payload,
    );
    return data;
  },
};