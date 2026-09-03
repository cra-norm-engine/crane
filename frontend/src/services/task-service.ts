// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type { ManualTaskCreate, TaskActivity, TaskItem, TaskNotification } from "@/types/task";

export interface TaskListOptions {
  scope?: "my_work" | "assigned_by_me" | "all";
  state?: "open" | "completed" | "archived" | "all";
  priority?: "low" | "medium" | "high";
  product_id?: string;
  product_release_id?: string;
  search?: string;
}

export const taskService = {
  /**
   * Fetch all open tasks assigned to the current user, sorted by urgency.
   */
  async listMyTasks(includeCompleted = false, options?: TaskListOptions): Promise<TaskItem[]> {
    const { data } = await apiClient.get<TaskItem[]>("/my-tasks/", {
      params: { ...(includeCompleted ? { include_completed: true } : {}), ...options },
    });
    return data;
  },
  async create(payload: ManualTaskCreate): Promise<TaskItem> {
    const { data } = await apiClient.post<TaskItem>("/my-tasks/", payload);
    return data;
  },
  async update(id: string, payload: ManualTaskCreate): Promise<TaskItem> {
    const { data } = await apiClient.patch<TaskItem>(`/my-tasks/${id}`, payload);
    return data;
  },
  async updateStatus(id: string, status: string): Promise<TaskItem> {
    const { data } = await apiClient.patch<TaskItem>(`/my-tasks/${id}/status`, { status });
    return data;
  },
  async complete(id: string, completionNote: string | null): Promise<TaskItem> {
    const { data } = await apiClient.post<TaskItem>(`/my-tasks/${id}/complete`, { completion_note: completionNote });
    return data;
  },
  async reopen(id: string, reason: string): Promise<TaskItem> {
    const { data } = await apiClient.post<TaskItem>(`/my-tasks/${id}/reopen`, { reason });
    return data;
  },
  async archive(id: string, reason: string): Promise<TaskItem> {
    const { data } = await apiClient.post<TaskItem>(`/my-tasks/${id}/archive`, { reason });
    return data;
  },
  async restore(id: string): Promise<TaskItem> {
    const { data } = await apiClient.post<TaskItem>(`/my-tasks/${id}/restore`);
    return data;
  },
  async activity(id: string): Promise<TaskActivity[]> {
    const { data } = await apiClient.get<TaskActivity[]>(`/my-tasks/${id}/activity`);
    return data;
  },
  async attachArtifact(id: string, revisionId: string): Promise<TaskItem> {
    const { data } = await apiClient.post<TaskItem>(`/my-tasks/${id}/artifacts/${revisionId}`);
    return data;
  },
  async detachArtifact(id: string, revisionId: string): Promise<TaskItem> {
    const { data } = await apiClient.delete<TaskItem>(`/my-tasks/${id}/artifacts/${revisionId}`);
    return data;
  },
  async notifications(unreadOnly = false): Promise<TaskNotification[]> {
    const { data } = await apiClient.get<TaskNotification[]>("/my-tasks/notifications/list", { params: { unread_only: unreadOnly } });
    return data;
  },
  async markNotificationRead(id: string): Promise<void> {
    await apiClient.post(`/my-tasks/notifications/${id}/read`);
  },
};
