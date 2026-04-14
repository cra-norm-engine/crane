import { apiClient } from "@/services/api";
import type { AuditEventListParams, AuditEventListRead, AuditIntegrityRead } from "@/types/audit";

export const auditService = {
  async listEvents(params?: AuditEventListParams): Promise<AuditEventListRead> {
    const { data } = await apiClient.get<AuditEventListRead>("/audit/events", {
      params,
    });
    return data;
  },

  async getIntegrity(): Promise<AuditIntegrityRead> {
    const { data } = await apiClient.get<AuditIntegrityRead>("/audit/integrity");
    return data;
  },
};
