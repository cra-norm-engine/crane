import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount, type VueWrapper } from "@vue/test-utils";
import AnnexMatrixView from "@/views/AnnexMatrixView.vue";
import RequirementLibraryView from "@/views/RequirementLibraryView.vue";
import { apiClient } from "@/services/api";
import type { AnnexRequirementRead } from "@/types/annex-requirement";
import type { ProductRequirementMatrixRowRead } from "@/types/requirement-mapping";

vi.mock("vue-router", () => ({ useRoute: () => ({ query: { product_id: "P", release_id: "R" } }) }));
vi.mock("@/stores/auth", () => ({ useAuthStore: () => ({ hasPermission: () => true }) }));
vi.mock("@/services/api", () => ({ apiClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() } }));

function requirement(id: string, kind: "essential" | "technical"): AnnexRequirementRead {
  return {
    id, kind, code: id, title: kind === "essential" ? "Protect against unauthorized access" : `Technical control ${id}`,
    description: "Objective for the assessed product.", annex_part: "part_i", is_active: true,
    source_id: kind === "essential" ? "CRA" : "SOURCE", source_identifier: kind === "essential" ? "CRA-ANNEX-I" : "TEST-STANDARD",
    source_title: "Source title", source_edition: "2026", clause_reference: "5.1", applicability_guidance: null,
    verification_guidance: "Inspect and test the implemented control.", expected_evidence: "Test report", acceptance_criteria: "Reject unauthorized operations.",
    contributions: kind === "technical" ? [{ essential_requirement_id: "E", contribution: "Protects the administrative interface; other interfaces require separate review." }] : [],
    revision: 1, status: "published", is_mandatory: false, created_at: "2026-10-09T12:00:00Z", updated_at: "2026-10-09T12:00:00Z",
  };
}
function row(id: string, kind: "essential" | "technical"): ProductRequirementMatrixRowRead {
  return {
    annex_requirement: requirement(id, kind), artifact_traceability_available: true, applicability_decision: "applicable",
    applicability_rationale: "The product exposes an administrative interface.", mapping_ids: [], trace_records: [],
    risk_items: [], artifacts: [], engineering_requirement_refs: [], sdl_activities: [], notes: [], overall_status: "planned",
    applicability: "applicable", traceability_strength: "missing", implementation_status: "implemented", finalized: false,
    validation_notes: null, verification_result: null, validated_by_user_id: null, validated_at: null,
    supporting_requirements: [], supporting_artifacts: [], blockers: ["Record a validation conclusion after reviewing scope, criteria and evidence."],
  };
}
let rows: ProductRequirementMatrixRowRead[];
let locked: boolean;
let wrapper: VueWrapper | undefined;
const sources = [
  { id: "CRA", identifier: "CRA-ANNEX-I", title: "CRA essential requirements", source_type: "regulation", edition: "2024", status: "published", organization_wide: true, is_system_managed: true, product_ids: [], requirement_count: 1 },
  { id: "SOURCE", identifier: "TEST-STANDARD", title: "Technical standard", source_type: "standard", edition: "2026", status: "published", organization_wide: true, is_system_managed: false, product_ids: [], requirement_count: 2 },
];

async function renderMatrix() {
  wrapper = mount(AnnexMatrixView, { attachTo: document.body });
  await flushPromises();
  return wrapper;
}
async function clickText(text: string) {
  const button = wrapper!.findAll("button").find((b) => b.text() === text);
  expect(button, `Button '${text}'`).toBeDefined();
  await button!.trigger("click");
  await flushPromises();
}

beforeEach(() => {
  vi.clearAllMocks();
  locked = false;
  rows = [row("E", "essential"), row("T", "technical")];
  rows[0].supporting_requirements = [{ requirement: rows[1].annex_requirement, contribution: rows[1].annex_requirement.contributions[0].contribution, applicability_decision: "applicable", implementation_status: "implemented", finalized: false }];
  vi.mocked(apiClient.get).mockImplementation(async (url) => {
    if (url === "/products/") return { data: [{ id: "P", name: "Product", product_code: "TEST" }] };
    if (url === "/product-releases/") return { data: [{ id: "R", product_id: "P", display_version: "1.0", release_status: "draft" }] };
    if (url === "/product-releases/R/requirement-matrix") return { data: structuredClone(rows) };
    if (url === "/product-releases/R/requirement-assessment") return { data: { product_release_id: "R", is_locked: locked, status: locked ? "approved" : "draft", version: locked ? 1 : 0, can_approve: false, unfinalized_codes: ["E", "T"] } };
    if (url === "/requirement-sources") return { data: structuredClone(sources) };
    if (url === "/requirement-sources/CRA/requirements") return { data: [requirement("E", "essential")] };
    if (url === "/requirement-sources/SOURCE/requirements") return { data: [requirement("T", "technical"), requirement("NEW", "technical"), { ...requirement("OTHER", "technical"), contributions: [] }] };
    return { data: [] };
  });
  vi.mocked(apiClient.post).mockResolvedValue({ data: [] });
  vi.mocked(apiClient.patch).mockImplementation(async (_url, payload) => {
    rows[0] = { ...rows[0], ...(payload as Record<string, unknown>) };
    return { data: structuredClone(rows[0]) };
  });
});
afterEach(() => { wrapper?.unmount(); wrapper = undefined; document.body.innerHTML = ""; });

describe("Release requirement traceability", () => {
  it("starts with CRA essentials and lets users follow technical work and return to the objective", async () => {
    await renderMatrix();
    expect(wrapper!.findAll(".matrix-row")).toHaveLength(1);
    expect(wrapper!.get(".matrix-row").text()).toContain("Protect against unauthorized access");
    await wrapper!.get(".matrix-row").trigger("click");
    await clickText("2 · Technical approach");
    expect(wrapper!.get(".supporting-requirement-card").text()).toContain("administrative interface");
    await clickText("Assess requirement");
    expect(wrapper!.get(".drawer-header h2").text()).toContain("Technical control T");
    await clickText("← Back to CRA objective");
    expect(wrapper!.get(".drawer-header h2").text()).toContain("Protect against unauthorized access");
    expect(wrapper!.find(".drawer-step-nav button.active").text()).toContain("Technical approach");
  });

  it("suggests relevant published requirements and adopts only the selected ones", async () => {
    await renderMatrix();
    await wrapper!.get(".matrix-row").trigger("click");
    await clickText("2 · Technical approach");
    await clickText("Choose requirements");
    expect(wrapper!.findAll(".picker-requirement")).toHaveLength(3);
    expect(wrapper!.findAll(".picker-requirement")[2].text()).toContain("Technical control OTHER");
    await wrapper!.get(".picker-toggle input").setValue(true);
    expect(wrapper!.findAll(".picker-requirement")).toHaveLength(2);
    expect(wrapper!.find(".picker-requirement input:disabled").exists()).toBe(true);
    const newRequirement = wrapper!.findAll(".picker-requirement").find((item) => item.text().includes("Technical control NEW"))!;
    await newRequirement.get("input").setValue(true);
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: rows });
    await clickText("Add to CRA essential");
    expect(apiClient.post).toHaveBeenCalledWith("/product-releases/R/requirement-baseline", { requirement_ids: ["NEW"], essential_requirement_id: "E", contribution_notes: {} });
    expect(wrapper!.find(".requirement-picker").exists()).toBe(false);
  });

  it("shows existing unmapped requirements and requires an explanation before linking", async () => {
    rows[1].annex_requirement.contributions = [];
    rows[0].supporting_requirements = [];
    await renderMatrix();
    await wrapper!.get(".matrix-row").trigger("click");
    await clickText("2 · Technical approach");
    await clickText("Choose requirements");
    const existing = wrapper!.findAll(".picker-requirement").find((item) => item.text().includes("Technical control T"))!;
    expect(existing.get("input").attributes("disabled")).toBeUndefined();
    await existing.get("input").setValue(true);
    const add = wrapper!.findAll("button").find((button) => button.text() === "Add to CRA essential")!;
    expect(add.attributes("disabled")).toBeDefined();
    await existing.get("textarea").setValue("Rejects unauthorized administration of this release.");
    expect(add.attributes("disabled")).toBeUndefined();
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: rows });
    await clickText("Add to CRA essential");
    expect(apiClient.post).toHaveBeenCalledWith("/product-releases/R/requirement-baseline", {
      requirement_ids: ["T"], essential_requirement_id: "E", contribution_notes: { T: "Rejects unauthorized administration of this release." },
    });
  });

  it("records failure with a conclusion rather than declaring fulfillment", async () => {
    await renderMatrix();
    await wrapper!.get(".matrix-row").trigger("click");
    await clickText("5 · Review");
    const form = wrapper!.get(".validation-review");
    expect(form.get("button").attributes("disabled")).toBeDefined();
    await form.get("select").setValue("fail");
    await form.get("textarea").setValue("The privileged endpoint accepted an unauthorized request.");
    await clickText("Save fulfillment review");
    expect(apiClient.patch).toHaveBeenCalledWith("/product-releases/R/requirement-matrix/E/status", {
      implementation_status: "implemented", verification_result: "fail", validation_notes: "The privileged endpoint accepted an unauthorized request.",
    });
    expect(wrapper!.get(".finalize-banner").text()).toContain("Action required");
  });

  it("keeps approved assessments read-only while allowing inspection", async () => {
    locked = true;
    await renderMatrix();
    expect(wrapper!.text()).not.toContain("Choose technical requirements");
    await wrapper!.get(".matrix-row").trigger("click");
    await clickText("5 · Review");
    expect(wrapper!.get(".validation-review textarea").attributes("disabled")).toBeDefined();
    expect(wrapper!.findAll("button").some((button) => button.text() === "Save fulfillment review")).toBe(false);
  });
});

describe("Requirement library authoring", () => {
  it("saves an explicit contribution and acceptance criteria for a draft technical requirement", async () => {
    const original = sources[1].status;
    sources[1].status = "draft";
    try {
      wrapper = mount(RequirementLibraryView);
      await flushPromises();
      await wrapper.findAll(".source-card")[1].get("button").trigger("click");
      await flushPromises();
      await clickText("Add requirement");
      const form = wrapper.get(".requirement-form");
      await form.findAll("input")[0].setValue("SEC-002");
      await form.findAll("input")[2].setValue("Limit failed authentication attempts");
      await form.findAll("textarea")[0].setValue("Apply a bounded retry policy.");
      await form.findAll("textarea")[2].setValue("A sixth consecutive failed attempt is rejected.");
      await form.get(".essential-option input").setValue(true);
      await form.get(".contribution-rationale textarea").setValue("Limits password guessing at the administrative interface.");
      vi.mocked(apiClient.post).mockResolvedValueOnce({ data: requirement("CREATED", "technical") });
      await form.trigger("submit");
      await flushPromises();
      expect(apiClient.post).toHaveBeenCalledWith("/requirement-sources/SOURCE/requirements", expect.objectContaining({
        code: "SEC-002", acceptance_criteria: "A sixth consecutive failed attempt is rejected.",
        contributions: [{ essential_requirement_id: "E", contribution: "Limits password guessing at the administrative interface." }],
      }));
    } finally { sources[1].status = original; }
  });
});
