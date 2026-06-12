// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "./api";
import type {
  RemoteProcessingAssessRequest,
  RemoteProcessingElementCreate,
  RemoteProcessingElementRead,
  RemoteProcessingElementUpdate,
} from "@/types/product";

export const remoteProcessingElementService = {
  list(params?: { product_id?: string }): Promise<RemoteProcessingElementRead[]> {
    return apiClient.get("/remote-processing-elements/", { params }).then((r) => r.data);
  },

  get(id: string): Promise<RemoteProcessingElementRead> {
    return apiClient.get(`/remote-processing-elements/${id}`).then((r) => r.data);
  },

  create(payload: RemoteProcessingElementCreate): Promise<RemoteProcessingElementRead> {
    return apiClient.post("/remote-processing-elements/", payload).then((r) => r.data);
  },

  update(id: string, payload: RemoteProcessingElementUpdate): Promise<RemoteProcessingElementRead> {
    return apiClient.put(`/remote-processing-elements/${id}`, payload).then((r) => r.data);
  },

  assess(id: string, payload: RemoteProcessingAssessRequest): Promise<RemoteProcessingElementRead> {
    return apiClient.post(`/remote-processing-elements/${id}/assess`, payload).then((r) => r.data);
  },

  delete(id: string): Promise<void> {
    return apiClient.delete(`/remote-processing-elements/${id}`).then(() => undefined);
  },
};
