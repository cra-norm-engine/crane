// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

/**
 * Lightweight user service for populating assignee pickers.
 * Uses the /admin/users/summary endpoint which is accessible to all authenticated users.
 */

import { apiClient } from "@/services/api";

export interface UserSummary {
  id: string;
  full_name: string | null;
  email: string;
}

export const userService = {
  /** Return id + name for all active users. No admin permission required. */
  async listSummary(): Promise<UserSummary[]> {
    const { data } = await apiClient.get<UserSummary[]>("/admin/users/summary");
    return data;
  },

  /** Helper: pick display name (full_name falls back to email). */
  displayName(user: UserSummary): string {
    return user.full_name?.trim() || user.email;
  },
};
