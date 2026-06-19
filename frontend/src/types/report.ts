// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

// Structured compliance-report data returned by GET /product-releases/{id}/report/data.
// Mirrors build_report_data() in backend/app/services/release_report_service.py.
// A field may carry the placeholder sentinel below when CRANE has no data model
// for it yet — render those as "Not recorded in CRANE".

// Sentinel emitted by the backend for not-yet-modelled fields.
export const REPORT_PLACEHOLDER = "__placeholder__";

// A value that may be a real string, null, or the placeholder sentinel.
export type Maybe = string | null;

export interface AnnexRow {
  code: string;
  title: string;
  status: string;
  bucket: "compliant" | "partial" | "gap" | "na";
  evidence: string;
  applicability: Maybe;
  rationale: Maybe;
  linked_artifacts: string[];
}

export interface VulnRow {
  cve: string;
  title: string;
  severity: string;
  vex: string;
}

export interface CertRow {
  scheme: Maybe;
  body: Maybe;
  number: Maybe;
  status: Maybe;
  valid_until: string;
}

export interface ReleaseReport {
  meta: {
    report_id: string;
    version: Maybe;
    generated_at: string;
    generated_by: Maybe;
    data_snapshot_at: string;
    tool_name: string;
    status: string;
    confidentiality: string;
  };
  product: {
    name: Maybe;
    model: Maybe;
    hardware_version: Maybe;
    firmware_version: Maybe;
    product_type: Maybe;
    intended_use: Maybe;
    is_embedded: string;
    is_pre_cra: string;
    remote_processing_in_scope: string;
  };
  remote_processing: {
    available: boolean;
    items: {
      name: string;
      provider: string;
      data_processed: string;
      location: string;
      criticality: string;
      classification: string;
      classification_bucket: string;
      rationale: string;
      necessary: string;
      bidirectional: string;
    }[];
  };
  operators: {
    manufacturer: { name: Maybe; contact_email: Maybe; contact_url: Maybe };
    authorised_rep: Maybe;
    importers: Maybe;
    distributors: Maybe;
    spoc: Maybe;
  };
  classification: {
    classification: Maybe;
    is_critical: string;
    scope_status: Maybe;
    annex_item: Maybe;
    rationale: Maybe;
    conformity_route: Maybe;
  };
  risk: {
    available: boolean;
    methodology?: Maybe;
    summary?: Maybe;
    status?: Maybe;
    approved_by?: Maybe;
    approved_at?: string;
    item_count?: number;
    title?: Maybe;
    count?: number;
    items?: {
      title: string;
      threat: string;
      asset: string;
      likelihood: string;
      impact: string;
      risk_level: string;
      risk_bucket: string;
      residual: string;
      residual_bucket: string;
      mitigation: string;
      status: string;
    }[];
  };
  annex_part1: AnnexRow[];
  annex_part2: AnnexRow[];
  coverage: {
    total: number;
    counts: Record<string, number>;
    pct: Record<string, number>;
    available: boolean;
  };
  sbom: {
    available: boolean;
    id?: Maybe;
    format?: Maybe;
    component_count?: number | null;
    quality_score?: number | null;
    ntia_compliant?: string;
    direct_transitive?: Maybe;
    findings?: {
      component: string;
      version: string;
      vuln_id: string;
      severity: string;
      severity_bucket: string;
      cvss_score: number | null;
      summary: string;
      fix_status: string;
    }[];
  };
  vuln: {
    available: boolean;
    total: number;
    open_critical: number;
    open_high: number;
    resolved_count: number;
    mttr: string;
    vex_breakdown: Record<string, number>;
    kev_flag: boolean;
    kev_notes: Maybe;
    top: VulnRow[];
  };
  conformity: {
    route: Maybe;
    module: Maybe;
    notified_body: Maybe;
    nb_number: Maybe;
    standards: Maybe;
    certifications: CertRow[];
  };
  doc: {
    reference_no: Maybe;
    date: string;
    notified_body: Maybe;
    signatory: Maybe;
    simplified_url: Maybe;
    status: Maybe;
    ce_marking: Maybe;
  };
  techdoc: { n: number; name: string; status: string }[];
  evidence: {
    available: boolean;
    total?: number;
    retained?: number;
    external?: number;
    verified?: number;
    failed?: number;
    legal_holds?: number;
    earliest_retention?: string;
  };
  user_info: {
    available: boolean;
    items: { ref: string; content: string; status: string; location: string }[];
  };
  support: {
    available: boolean;
    start?: string;
    end?: string;
    type?: Maybe;
    notify_before_days?: number | null;
    justification?: Maybe;
  };
  mods: { date: string; description: string; type: string; outcome: string; substantial: boolean }[];
  cvd: {
    available: boolean;
    policy_status: Maybe;
    policy_url: Maybe;
    contact: Maybe;
    csirt_coordinator: Maybe;
    playbook_ready: boolean;
    last_notification: Maybe;
    incident_count: number;
    safe_harbor: Maybe;
    acknowledgement_offered: Maybe;
    disclosure_window_days: number | null;
    response_sla_hours: number | null;
    scope_description: Maybe;
    out_of_scope_description: Maybe;
    supported_versions: Maybe;
    security_txt_url: Maybe;
    pgp_key_url: Maybe;
    bug_bounty_url: Maybe;
  };
  audit: { at: string; actor: string; action: string }[];
  signoff: {
    gate_approver: { email: Maybe; at: string } | null;
    compliance_lead: Maybe;
    notified_body_reviewer: Maybe;
    executive: Maybe;
  };
}
