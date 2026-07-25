import { apiClient } from "@/services/api"
import type { MaturityDetail, MaturitySummary } from "@/types/maturity"

export const maturityService = {
  async list() { return (await apiClient.get<MaturitySummary[]>("/maturity-assessments")).data },
  async create(payload: { title: string; scope: string }) { return (await apiClient.post<MaturitySummary>("/maturity-assessments", payload)).data },
  async get(id: string) { return (await apiClient.get<MaturityDetail>(`/maturity-assessments/${id}`)).data },
  async answer(id: string, code: string, payload: { score: number | null; rationale?: string; confidence?: string }) { return (await apiClient.put<MaturityDetail>(`/maturity-assessments/${id}/responses/${code}`, payload)).data },
  async transition(id: string, action: "submit" | "approve", justification?: string) { return (await apiClient.post<MaturityDetail>(`/maturity-assessments/${id}/workflow/${action}`, undefined, { params: { justification } })).data },
  async linkEvidence(id: string, code: string, evidence: { entity_type: string; entity_id: string; label: string }) { return (await apiClient.post<MaturityDetail>(`/maturity-assessments/${id}/evidence/${code}`, evidence)).data },
  async updateAction(id: string, actionId: string, payload: Record<string, string | null>) { return (await apiClient.patch<MaturityDetail>(`/maturity-assessments/${id}/actions/${actionId}`, payload)).data },
  async export(id: string, format: "json" | "pdf") { return (await apiClient.get(`/maturity-assessments/${id}/export.${format}`, { responseType: "blob" })).data as Blob },
}
