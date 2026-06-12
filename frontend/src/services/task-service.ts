// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type { TaskItem } from "@/types/task";

export const taskService = {
  /**
   * Fetch all open tasks assigned to the current user, sorted by urgency.
   */
  async listMyTasks(): Promise<TaskItem[]> {
    const { data } = await apiClient.get<TaskItem[]>("/my-tasks/");
    return data;
  },
};
