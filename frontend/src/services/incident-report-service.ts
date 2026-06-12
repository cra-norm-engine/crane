// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type {
  IncidentEnisaMarkSentRequest,
  IncidentReportCreate,
  IncidentReportRead,
  IncidentReportUpdate,
} from "@/types/product";

export const incidentReportService = {
  async list(opts?: { productReleaseId?: string; productId?: string }): Promise<IncidentReportRead[]> {
    const params: Record<string, string> = {};
    if (opts?.productReleaseId) params.product_release_id = opts.productReleaseId;
    else if (opts?.productId)   params.product_id = opts.productId;
    const { data } = await apiClient.get<IncidentReportRead[]>("/incident-reports/", {
      params: Object.keys(params).length ? params : undefined,
    });
    return data;
  },

  async get(reportId: string): Promise<IncidentReportRead> {
    const { data } = await apiClient.get<IncidentReportRead>(`/incident-reports/${reportId}`);
    return data;
  },

  async create(payload: IncidentReportCreate): Promise<IncidentReportRead> {
    const { data } = await apiClient.post<IncidentReportRead>("/incident-reports/", payload);
    return data;
  },

  async update(reportId: string, payload: IncidentReportUpdate): Promise<IncidentReportRead> {
    const { data } = await apiClient.put<IncidentReportRead>(`/incident-reports/${reportId}`, payload);
    return data;
  },

  async remove(reportId: string): Promise<void> {
    await apiClient.delete(`/incident-reports/${reportId}`);
  },

  /** CRA Art. 14 — record that the 24h early-warning notification was submitted to the ENISA SRP. */
  async markEnisaEarlyWarningSent(
    reportId: string,
    payload: IncidentEnisaMarkSentRequest = {},
  ): Promise<IncidentReportRead> {
    const { data } = await apiClient.post<IncidentReportRead>(
      `/incident-reports/${reportId}/enisa/mark-early-warning-sent`,
      payload,
    );
    return data;
  },

  /** CRA Art. 14 — record that the 72h incident notification was submitted to the ENISA SRP. */
  async markEnisaInitialReportSent(
    reportId: string,
    payload: IncidentEnisaMarkSentRequest = {},
  ): Promise<IncidentReportRead> {
    const { data } = await apiClient.post<IncidentReportRead>(
      `/incident-reports/${reportId}/enisa/mark-initial-report-sent`,
      payload,
    );
    return data;
  },

  /**
   * CRA Art. 14 — record that the final report was submitted.
   * Note: for incidents the final report is due 1 month after the 72h notification,
   * NOT 14 days after a fix (that rule applies only to vulnerability reports).
   */
  async markEnisaFinalReportSent(
    reportId: string,
    payload: IncidentEnisaMarkSentRequest = {},
  ): Promise<IncidentReportRead> {
    const { data } = await apiClient.post<IncidentReportRead>(
      `/incident-reports/${reportId}/enisa/mark-final-report-sent`,
      payload,
    );
    return data;
  },
};
