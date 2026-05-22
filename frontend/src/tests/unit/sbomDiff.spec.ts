import { describe, it, expect } from "vitest"
import { formatComponent, extractDiffData } from "@/utils/sbomDiff"

describe("sbomDiff utilities", () => {
  describe("formatComponent", () => {
    it("formats string component as-is", () => {
      expect(formatComponent("lodash@4.17.20")).toBe("lodash@4.17.20")
    })

    it("formats object with name and version", () => {
      const component = { name: "express", version: "4.18.0" }
      expect(formatComponent(component)).toBe("express@4.18.0")
    })

    it("formats object with component key instead of name", () => {
      const component = { component: "react", version: "18.2.0" }
      expect(formatComponent(component)).toBe("react@18.2.0")
    })

    it("formats component without version", () => {
      const component = { name: "typescript" }
      expect(formatComponent(component)).toBe("typescript")
    })

    it("handles null and undefined in object", () => {
      const component = { name: "npm", version: null }
      expect(formatComponent(component)).toBe("npm")
    })

    it("returns JSON stringified for unknown types", () => {
      expect(formatComponent(123)).toBe("123")
      expect(formatComponent(true)).toBe("true")
      expect(formatComponent(null)).toBe("null")
    })
  })

  describe("extractDiffData", () => {
    it("extracts added components from 'added' key", () => {
      const findings = {
        added: [{ name: "express", version: "4.18.0" }],
        removed: [],
        changed: [],
      }
      const diff = extractDiffData(findings)
      expect(diff.added).toHaveLength(1)
      expect(diff.added[0]).toEqual({ name: "express", version: "4.18.0" })
      expect(diff.removed).toEqual([])
      expect(diff.changed).toEqual([])
    })

    it("extracts added components from 'new_components' key", () => {
      const findings = {
        new_components: [{ name: "axios", version: "1.0.0" }],
      }
      const diff = extractDiffData(findings)
      expect(diff.added).toHaveLength(1)
      expect(diff.added[0].name).toBe("axios")
    })

    it("extracts added components from 'additions' key", () => {
      const findings = {
        additions: [{ name: "typescript", version: "5.0.0" }],
      }
      const diff = extractDiffData(findings)
      expect(diff.added).toHaveLength(1)
      expect(diff.added[0].name).toBe("typescript")
    })

    it("extracts removed components from 'removed' key", () => {
      const findings = {
        removed: [{ name: "old-lib", version: "1.0.0" }],
      }
      const diff = extractDiffData(findings)
      expect(diff.removed).toHaveLength(1)
      expect(diff.removed[0].name).toBe("old-lib")
    })

    it("extracts removed components from 'deleted_components' key", () => {
      const findings = {
        deleted_components: [{ name: "deprecated", version: "2.0.0" }],
      }
      const diff = extractDiffData(findings)
      expect(diff.removed).toHaveLength(1)
    })

    it("extracts changed components from 'changed' key", () => {
      const findings = {
        changed: [{ name: "react", from: "16.0.0", to: "18.0.0" }],
      }
      const diff = extractDiffData(findings)
      expect(diff.changed).toHaveLength(1)
    })

    it("extracts changed components from 'modified_components' key", () => {
      const findings = {
        modified_components: [{ name: "vue", from: "2.0.0", to: "3.0.0" }],
      }
      const diff = extractDiffData(findings)
      expect(diff.changed).toHaveLength(1)
    })

    it("extracts changed components from 'modifications' key", () => {
      const findings = {
        modifications: [{ name: "angular", from: "12.0.0", to: "14.0.0" }],
      }
      const diff = extractDiffData(findings)
      expect(diff.changed).toHaveLength(1)
    })

    it("extracts changed components from 'updated' key", () => {
      const findings = {
        updated: [{ name: "svelte", from: "3.0.0", to: "4.0.0" }],
      }
      const diff = extractDiffData(findings)
      expect(diff.changed).toHaveLength(1)
    })

    it("returns empty arrays for null findings", () => {
      const diff = extractDiffData(null)
      expect(diff.added).toEqual([])
      expect(diff.removed).toEqual([])
      expect(diff.changed).toEqual([])
    })

    it("returns empty arrays for undefined findings", () => {
      const diff = extractDiffData(undefined)
      expect(diff.added).toEqual([])
      expect(diff.removed).toEqual([])
      expect(diff.changed).toEqual([])
    })

    it("returns empty arrays for non-object findings", () => {
      expect(extractDiffData("invalid").added).toEqual([])
      expect(extractDiffData(123).added).toEqual([])
      expect(extractDiffData(true).added).toEqual([])
    })

    it("handles complete diff with all three sections", () => {
      const findings = {
        added: [{ name: "new-lib" }],
        removed: [{ name: "old-lib" }],
        changed: [{ name: "updated-lib" }],
      }
      const diff = extractDiffData(findings)
      expect(diff.added).toHaveLength(1)
      expect(diff.removed).toHaveLength(1)
      expect(diff.changed).toHaveLength(1)
    })

    it("ignores non-array values for diff sections", () => {
      const findings = {
        added: "not-an-array",
        removed: null,
        changed: 123,
      }
      const diff = extractDiffData(findings)
      expect(diff.added).toEqual([])
      expect(diff.removed).toEqual([])
      expect(diff.changed).toEqual([])
    })

    it("uses first matching key when multiple formats present", () => {
      const findings = {
        added: [{ name: "preferred" }],
        new_components: [{ name: "should-be-ignored" }],
      }
      const diff = extractDiffData(findings)
      expect(diff.added).toHaveLength(1)
      expect(diff.added[0].name).toBe("preferred")
    })
  })
})
