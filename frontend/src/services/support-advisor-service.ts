import { apiClient } from '@/services/api';

export interface Component {
  id: string; link_id: string; name: string; version: string | null; supplier_name: string;
  criticality: string; is_core_function: boolean; support_start_date: string | null;
  support_end_date: string | null; support_verified_at: string | null;
  support_reference_url: string | null; support_scope: string | null;
  gap_days?: number | null; status?: string;
}
export interface Evidence { id: string; title: string; external_url: string | null }
export interface Context {
  context_version: string;
  product: { name: string }; release: { id: string; user_version: string | null };
  support: { support_start_date: string; support_end_date: string; justification_text: string | null; expected_use_time_text: string | null; comparable_products_text: string | null; third_party_support_constraints_text: string | null } | null;
  risk_assessments: { id: string; title: string }[]; vulnerabilities: { id: string; title: string }[];
  components: Component[]; evidence: Evidence[]; sboms: { id: string }[];
}
export interface Remediation {
  component_link_id: string; approach: string; rationale: string; evidence_ids: string[];
}
export interface AssessmentInput {
  context_version: string;
  product_release_id: string; support_start: string; support_end: string; expected_use_end: string;
  expected_use_basis: string; rationale: string; evidence_ids: string[]; remediations: Remediation[];
}
export interface Assessment {
  id: string; product_release_id: string; author_id: string; created_at: string; status: string;
  needs_refresh: boolean; inputs: AssessmentInput; context_snapshot: Context;
  reviewer_id: string | null; reviewed_at: string | null; review_reason: string | null;
  result: { rules_version: string; findings: { rule: string; message: string }[];
    components: Component[]; legal_admissibility: string; technical_readiness: string;
    economic_attractiveness: string; general_minimum_met: boolean; approval_blockers: string[] };
}
const base = (id: string) => `/products/${id}/support-advisor`;
export const supportAdvisorService = {
  async context(id: string, release: string) { return (await apiClient.get<Context>(`${base(id)}/context`, { params: { release_id: release } })).data; },
  async history(id: string) { return (await apiClient.get<Assessment[]>(`${base(id)}/assessments`)).data; },
  async preview(id: string, input: AssessmentInput) { return (await apiClient.post<Assessment['result']>(`${base(id)}/preview`, input)).data; },
  async create(id: string, input: AssessmentInput) { return (await apiClient.post<Assessment>(`${base(id)}/assessments`, input)).data; },
  async review(id: string, assessment: string, decision: string, reason: string) { return (await apiClient.post<Assessment>(`${base(id)}/assessments/${assessment}/review`, { decision, reason })).data; },
  async report(id: string, assessment: string) {
    const { data } = await apiClient.get(`${base(id)}/assessments/${assessment}/report`, { responseType: 'blob' });
    const url = URL.createObjectURL(data); const a = document.createElement('a');
    a.href = url; a.download = `support-assessment-${assessment}.json`; a.click(); URL.revokeObjectURL(url);
  },
};
