import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

/**
 * Three independent sidebars are defined — one per top-level navigation section.
 * Each maps to a navbar item via the sidebarId key in docusaurus.config.ts.
 */
const sidebars: SidebarsConfig = {
  // ── User Guide ────────────────────────────────────────────────────────────
  userGuideSidebar: [
    {
      type: "doc",
      id: "introduction",
      label: "Introduction",
    },
    {
      type: "category",
      label: "Getting Started",
      collapsed: false,
      items: [
        "getting-started/prerequisites",
        "getting-started/installation",
        "getting-started/first-login",
      ],
    },
    {
      type: "category",
      label: "User Guide",
      collapsed: false,
      items: [
        "user-guide/product-registry",
        "user-guide/scope-evaluation",
        "user-guide/risk-assessments",
        "user-guide/release-management",
        "user-guide/release-gate",
        "user-guide/substantial-changes",
        "user-guide/support-period",
        "user-guide/certification-tracking",
        "user-guide/security-updates",
        "user-guide/user-management",
      ],
    },
  ],

  // ── CRA Reference ─────────────────────────────────────────────────────────
  craReferenceSidebar: [
    {
      type: "category",
      label: "CRA Reference",
      collapsed: false,
      items: [
        "cra-reference/overview",
        "cra-reference/scope-and-exclusions",
        "cra-reference/classification",
        "cra-reference/substantial-modifications",
      ],
    },
  ],

  // ── Developer Guide ───────────────────────────────────────────────────────
  developerGuideSidebar: [
    {
      type: "category",
      label: "Developer Guide",
      collapsed: false,
      items: [
        "developer-guide/architecture",
        "developer-guide/local-development",
        "developer-guide/database-migrations",
        "developer-guide/contributing",
      ],
    },
  ],
};

export default sidebars;
