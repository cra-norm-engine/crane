export type CertificationScheme =
  | "eu_cybersecurity_act"
  | "iec_62443"
  | "common_criteria"
  | "etsi_en_303_645"
  | "iso_iec_27001"
  | "soc2"
  | "other";

export type CertificationStatus =
  | "pending"
  | "active"
  | "expired"
  | "suspended"
  | "withdrawn";

export interface CertificationRecord {
  id: string;
  product_id: string;
  certification_scheme: CertificationScheme;
  certification_scheme_label: string | null;
  certification_body_name: string;
  certificate_number: string | null;
  scope_description: string;
  issued_date: string | null;
  valid_until_date: string | null;
  status: CertificationStatus;
  notes: string | null;
  recertification_required_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface CertificationRecordCreate {
  product_id: string;
  certification_scheme: CertificationScheme;
  certification_scheme_label?: string | null;
  certification_body_name: string;
  certificate_number?: string | null;
  scope_description: string;
  issued_date?: string | null;
  valid_until_date?: string | null;
  status?: CertificationStatus;
  notes?: string | null;
  recertification_required_by?: string | null;
}

export interface CertificationRecordUpdate {
  certification_scheme?: CertificationScheme;
  certification_scheme_label?: string | null;
  certification_body_name?: string;
  certificate_number?: string | null;
  scope_description?: string;
  issued_date?: string | null;
  valid_until_date?: string | null;
  status?: CertificationStatus;
  notes?: string | null;
  recertification_required_by?: string | null;
}

export const SCHEME_LABELS: Record<CertificationScheme, string> = {
  eu_cybersecurity_act: "EU Cybersecurity Act (EUCC)",
  iec_62443: "IEC 62443",
  common_criteria: "Common Criteria (ISO 15408)",
  etsi_en_303_645: "ETSI EN 303 645",
  iso_iec_27001: "ISO/IEC 27001",
  soc2: "SOC 2",
  other: "Other",
};

export const STATUS_LABELS: Record<CertificationStatus, string> = {
  pending: "Pending",
  active: "Active",
  expired: "Expired",
  suspended: "Suspended",
  withdrawn: "Withdrawn",
};
