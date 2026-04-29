import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

const config: Config = {
  title: "CRA Conformity Management",
  tagline:
    "Self-hosted compliance management for manufacturers of products with digital elements under the EU Cyber Resilience Act",
  favicon: "img/favicon.ico",

  // Set to your Cloudflare Pages domain once deployed.
  // Example: https://cra-conformity-management.pages.dev
  url: "https://cra-conformity-management.pages.dev",
  baseUrl: "/",

  // GitHub repository details — used by the "Edit this page" links.
  organizationName: "amh1036",
  projectName: "CRA-Compliance-Tool",

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  presets: [
    [
      "classic",
      {
        docs: {
          // Documentation lives at /docs in the sidebar; served at /docs on the site.
          routeBasePath: "/",
          sidebarPath: "./sidebars.ts",
          // Allow readers to open a pull request to improve documentation.
          editUrl:
            "https://github.com/amh1036/CRA-Compliance-Tool/edit/main/docs/",
        },
        // Blog is not required for compliance documentation.
        blog: false,
        theme: {
          customCss: "./src/css/custom.css",
        },
        sitemap: {
          changefreq: "weekly",
          priority: 0.5,
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Social card image shown when the URL is shared.
    image: "img/social-card.png",

    navbar: {
      title: "CRA Conformity Management",
      logo: {
        alt: "CRA Conformity Management Logo",
        src: "img/logo.svg",
      },
      items: [
        {
          type: "docSidebar",
          sidebarId: "userGuideSidebar",
          position: "left",
          label: "User Guide",
        },
        {
          type: "docSidebar",
          sidebarId: "craReferenceSidebar",
          position: "left",
          label: "CRA Reference",
        },
        {
          type: "docSidebar",
          sidebarId: "developerGuideSidebar",
          position: "left",
          label: "Developer Guide",
        },
        {
          href: "https://github.com/amh1036/CRA-Compliance-Tool",
          label: "GitHub",
          position: "right",
        },
      ],
    },

    footer: {
      style: "dark",
      links: [
        {
          title: "Documentation",
          items: [
            { label: "Introduction", to: "/" },
            { label: "Getting Started", to: "/getting-started/prerequisites" },
            { label: "User Guide", to: "/user-guide/product-registry" },
          ],
        },
        {
          title: "Reference",
          items: [
            { label: "CRA Overview", to: "/cra-reference/overview" },
            {
              label: "Substantial Modifications",
              to: "/cra-reference/substantial-modifications",
            },
            {
              label: "Developer Guide",
              to: "/developer-guide/architecture",
            },
          ],
        },
        {
          title: "External Resources",
          items: [
            {
              label: "EU Cyber Resilience Act (Official Text)",
              href: "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R2847",
            },
            {
              label: "ENISA CRA Guidance",
              href: "https://www.enisa.europa.eu",
            },
            {
              label: "GitHub Repository",
              href: "https://github.com/amh1036/CRA-Compliance-Tool",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} CRA Conformity Management. Built with Docusaurus.`,
    },

    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      // Additional languages used in code blocks throughout the documentation.
      additionalLanguages: ["bash", "python", "typescript", "yaml", "sql"],
    },

    // Table of contents depth on the right sidebar.
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 4,
    },

    colorMode: {
      defaultMode: "light",
      // Compliance documentation is typically reviewed in light mode environments.
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
