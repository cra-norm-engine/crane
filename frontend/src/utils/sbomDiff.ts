/**
 * Utility functions for SBOM differential analysis display.
 * Extracts and normalizes diff data from analysis findings.
 */

export interface SbomDiffData {
  added: unknown[];
  removed: unknown[];
  changed: unknown[];
}

/**
 * Format a component object as a human-readable string (name@version).
 * Handles various component object shapes and string inputs.
 */
export function formatComponent(c: unknown): string {
  if (typeof c === "string") return c;
  if (c && typeof c === "object") {
    const obj = c as Record<string, unknown>;
    const name = obj.name ?? obj.component ?? "";
    const version = obj.version ? `@${obj.version}` : "";
    return `${name}${version}`;
  }
  return JSON.stringify(c);
}

/**
 * Extract and normalize diff data from sbom-tools analysis findings.
 * Handles multiple key names for each section (added, removed, changed)
 * as the diff format may vary depending on the analysis tool version.
 */
export function extractDiffData(findings: unknown): SbomDiffData {
  const diff: SbomDiffData = {
    added: [],
    removed: [],
    changed: [],
  };

  if (!findings || typeof findings !== "object") {
    return diff;
  }

  const d = findings as Record<string, unknown>;

  for (const key of ["added", "new_components", "additions"]) {
    const val = d[key];
    if (Array.isArray(val)) {
      diff.added = val;
      break;
    }
  }

  for (const key of ["removed", "deleted_components", "removals"]) {
    const val = d[key];
    if (Array.isArray(val)) {
      diff.removed = val;
      break;
    }
  }

  for (const key of ["changed", "modified_components", "modifications", "updated"]) {
    const val = d[key];
    if (Array.isArray(val)) {
      diff.changed = val;
      break;
    }
  }

  return diff;
}
