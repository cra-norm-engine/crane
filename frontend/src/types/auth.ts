// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

export interface LoginPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserPreferences {
  theme: string;
  timezone: string;
  date_format: string;
  default_landing_page: string;
}

export type UserPreferencesUpdate = Partial<UserPreferences>;

export interface UserRead {
  id: string;
  email: string;
  full_name: string;
  avatar_data: string | null;
  is_active: boolean;
  roles: string[];
  permissions: string[];
  auth_provider: string;
  must_change_password: boolean;
  preferences: UserPreferences;
}
