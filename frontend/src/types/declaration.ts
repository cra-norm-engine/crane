// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

// Types mirroring the backend EU Declaration of Conformity + package-label
// payloads. The placeholder sentinel matches the backend _PLACEHOLDER marker so
// the UI can render "not recorded" fields distinctly.
export const DOC_PLACEHOLDER = "__placeholder__";

// DoC lifecycle status (backend DocStatus enum).
export type DocStatus = "draft" | "approved" | "signed";

// One row on the top-level Declarations page.
export interface DeclarationSummary {
  release_id: string;
  product_id: string;
  product_name: string;
  product_code: string;
  system_version: number;
  version_label: string;
  doc_status: DocStatus;
  doc_number: string | null;
  doc_date: string | null;
  signatory: string | null;
  approved_by: string | null;
  approved_at: string | null;
  signed_at: string | null;
}

// Structured Annex V content returned by /declaration/data. Values may equal
// DOC_PLACEHOLDER when the underlying field is not recorded.
export interface DeclarationData {
  meta: {
    generated_at: string;
    generated_by: string;
    tool_name: string;
    is_signed: boolean;
    status: string;
  };
  reference_no: string;
  manufacturer: {
    name: string;
    address: string;
    contact_email: string;
    contact_url: string;
  };
  authorised_rep: string;
  sole_responsibility: string;
  product: {
    name: string;
    model: string;
    type: string;
    version: string;
    hardware_version: string;
    description: string;
  };
  conformity: {
    route: string;
    module: string;
    standards: string;
    notified_body: string;
    nb_number: string;
  };
  ce_marking: string;
  simplified_url: string;
  signature: {
    signatory: string;
    date: string;
    approved_by: string;
    approved_at: string;
    signed_at: string;
  };
}

// Editable EU DoC fields (Annex V), sent to PATCH /declaration while in draft.
export interface DeclarationEditFields {
  eu_doc_number: string | null;
  eu_doc_date: string | null;
  eu_doc_signatory: string | null;
  eu_doc_url: string | null;
  eu_doc_notified_body: string | null;
  notified_body_number: string | null;
  conformity_module: string | null;
  standards_applied: string | null;
  ce_marking_info: string | null;
}

// Structured package-label content returned by /label/data.
export interface LabelData {
  meta: { generated_at: string; tool_name: string };
  ce_marking: boolean;
  product: {
    name: string;
    model: string;
    version: string;
    manufacturer: string;
  };
  doc_reference: string;
  support_until: string;
  security_contact: { email: string; url: string };
  qr_target: string;
  qr_data_uri: string | null;
}
