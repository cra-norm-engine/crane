// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { computed } from "vue";

import { useAuthStore } from "@/stores/auth";

/**
 * Date formatting that honours the signed-in user's preferences (timezone +
 * date format). Centralised so existing ad-hoc `toLocaleDateString` calls can be
 * migrated to it incrementally.
 *
 * Supported date_format tokens: "YYYY-MM-DD" (ISO), "DD/MM/YYYY", "MM/DD/YYYY".
 */

const DEFAULT_TIMEZONE = "UTC";
const DEFAULT_FORMAT = "YYYY-MM-DD";

export const DATE_FORMAT_OPTIONS = ["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"] as const;

function partsFor(date: Date, timeZone: string): Record<string, string> {
  // en-CA with explicit parts gives stable zero-padded numeric values per timezone.
  const fmt = new Intl.DateTimeFormat("en-CA", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  const parts: Record<string, string> = {};
  for (const p of fmt.formatToParts(date)) {
    if (p.type !== "literal") parts[p.type] = p.value;
  }
  return parts;
}

function safeTimeZone(timeZone: string): string {
  try {
    new Intl.DateTimeFormat("en-CA", { timeZone });
    return timeZone;
  } catch {
    return DEFAULT_TIMEZONE;
  }
}

export function formatDate(
  value: string | number | Date | null | undefined,
  options?: { timezone?: string; format?: string },
): string {
  if (value === null || value === undefined || value === "") return "—";

  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";

  const timeZone = safeTimeZone(options?.timezone || DEFAULT_TIMEZONE);
  const format = options?.format || DEFAULT_FORMAT;
  const { year, month, day } = partsFor(date, timeZone);

  switch (format) {
    case "DD/MM/YYYY":
      return `${day}/${month}/${year}`;
    case "MM/DD/YYYY":
      return `${month}/${day}/${year}`;
    case "YYYY-MM-DD":
    default:
      return `${year}-${month}-${day}`;
  }
}

/** Reactive helper bound to the current user's stored preferences. */
export function useDateFormat() {
  const authStore = useAuthStore();

  const timezone = computed(() => authStore.preferences?.timezone || DEFAULT_TIMEZONE);
  const dateFormat = computed(() => authStore.preferences?.date_format || DEFAULT_FORMAT);

  function format(value: string | number | Date | null | undefined): string {
    return formatDate(value, { timezone: timezone.value, format: dateFormat.value });
  }

  return { format, timezone, dateFormat };
}
