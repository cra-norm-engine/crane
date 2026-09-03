import { apiClient } from "@/services/api";

export interface JiraConnection {
  id: string;
  cloud_id: string;
  site_url: string;
  site_name: string;
  project_key: string | null;
  issue_type: string;
  status_mapping_json: Record<string, string>;
  priority_mapping_json: Record<string, string>;
  is_active: boolean;
  last_error: string | null;
}

export interface JiraTaskLink {
  id: string;
  manual_task_id: string;
  issue_id: string;
  issue_key: string;
  issue_url: string;
  sync_status: string;
  last_synced_at: string | null;
  last_error: string | null;
}

export interface JiraUserMapping {
  id: string;
  crane_user_id: string;
  jira_account_id: string;
  jira_display_name: string | null;
}

export const jiraService = {
  async authorizationUrl(): Promise<string> {
    const { data } = await apiClient.get<{ authorization_url: string }>("/jira/oauth/start");
    return data.authorization_url;
  },
  async connections(): Promise<JiraConnection[]> {
    const { data } = await apiClient.get<JiraConnection[]>("/jira/connections");
    return data;
  },
  async configure(id: string, payload: { project_key: string; issue_type: string; status_mapping_json: Record<string, string>; priority_mapping_json: Record<string, string> }): Promise<JiraConnection> {
    const { data } = await apiClient.patch<JiraConnection>(`/jira/connections/${id}`, payload);
    return data;
  },
  async disconnect(id: string): Promise<void> {
    await apiClient.delete(`/jira/connections/${id}`);
  },
  async userMappings(id: string): Promise<JiraUserMapping[]> {
    const { data } = await apiClient.get<JiraUserMapping[]>(`/jira/connections/${id}/users`);
    return data;
  },
  async setUserMapping(id: string, craneUserId: string, jiraAccountId: string): Promise<JiraUserMapping> {
    const { data } = await apiClient.put<JiraUserMapping>(`/jira/connections/${id}/users`, {
      crane_user_id: craneUserId, jira_account_id: jiraAccountId,
    });
    return data;
  },
  async taskLink(taskId: string): Promise<JiraTaskLink | null> {
    const { data } = await apiClient.get<JiraTaskLink | null>(`/jira/tasks/${taskId}`);
    return data;
  },
  async exportTask(taskId: string, connectionId: string): Promise<JiraTaskLink> {
    const { data } = await apiClient.post<JiraTaskLink>(`/jira/tasks/${taskId}/export`, null, { params: { connection_id: connectionId } });
    return data;
  },
  async syncTask(taskId: string, direction: "push" | "pull"): Promise<JiraTaskLink> {
    const { data } = await apiClient.post<JiraTaskLink>(`/jira/tasks/${taskId}/sync`, { direction });
    return data;
  },
};
