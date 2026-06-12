// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

export type AnnexPart = "part_i" | "part_ii";

export interface AnnexRequirementRead {
  id: string;
  code: string;
  title: string;
  description: string;
  annex_part: AnnexPart;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnnexRequirementSummaryRead {
  id: string;
  code: string;
  title: string;
  annex_part: AnnexPart;
  is_active: boolean;
}

export interface AnnexRequirementCreate {
  code: string;
  title: string;
  description: string;
  annex_part: AnnexPart;
  is_active?: boolean;
}

export interface AnnexRequirementUpdate {
  title?: string;
  description?: string;
  annex_part?: AnnexPart;
  is_active?: boolean;
}

export type AnnexRequirement = AnnexRequirementRead;