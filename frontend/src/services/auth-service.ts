// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type { LoginPayload, TokenResponse, UserRead } from "@/types/auth";

export async function loginRequest(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", payload);
  return data;
}

export async function fetchCurrentUser(accessToken: string): Promise<UserRead> {
  const { data } = await apiClient.get<UserRead>("/auth/me", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  return data;
}

export async function changePasswordRequest(payload: {
  current_password: string;
  new_password: string;
}): Promise<void> {
  await apiClient.post("/auth/change-password", payload);
}

export const authService = {
  login: loginRequest,
  fetchCurrentUser,
  changePassword: changePasswordRequest,
};