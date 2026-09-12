import { apiClient } from "@/services/api";

export interface DependencyTrackProject { uuid: string; name: string; version: string | null }
export interface DependencyTrackSbom { id: string; label: string }
export interface DependencyTrackConnection {
  id: string; server_url: string; project_id: string; project_name: string;
  sbom_record_id: string; automatic_sync: boolean; last_attempt_at: string | null;
  last_synced_at: string | null; last_error: string | null;
  last_result: { created: number; updated: number; unchanged: number; stale: number; assessment_conflicts: string[] } | null;
}
export interface DependencyTrackCredentials { server_url: string; api_key: string }
const path = "/admin/dependency-track";
const requestOptions = { timeout: 120000 };
export const dependencyTrackService = {
  async list(): Promise<DependencyTrackConnection[]> { return (await apiClient.get(path)).data; },
  async sboms(): Promise<DependencyTrackSbom[]> { return (await apiClient.get(`${path}/sboms`)).data; },
  async test(payload: DependencyTrackCredentials): Promise<DependencyTrackProject[]> {
    return (await apiClient.post(`${path}/test`, payload, requestOptions)).data;
  },
  async connect(payload: DependencyTrackCredentials & { project_id: string; sbom_record_id: string; automatic_sync: boolean }): Promise<DependencyTrackConnection> {
    return (await apiClient.post(path, payload, requestOptions)).data;
  },
  async sync(id: string): Promise<DependencyTrackConnection> { return (await apiClient.post(`${path}/${id}/sync`, {}, requestOptions)).data; },
  async schedule(id: string, automatic_sync: boolean): Promise<DependencyTrackConnection> { return (await apiClient.patch(`${path}/${id}`, { automatic_sync })).data; },
  async disconnect(id: string): Promise<void> { await apiClient.delete(`${path}/${id}`); },
};
