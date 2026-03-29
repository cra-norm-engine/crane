import { apiClient } from "@/services/api";
import type {
  LifecycleNotificationDismissRequest,
  LifecycleNotificationRead,
} from "@/types/product";

export const lifecycleNotificationService = {
  async list(params?: {
    status?: "pending" | "sent" | "dismissed";
    support_period_record_id?: string;
  }): Promise<LifecycleNotificationRead[]> {
    const { data } = await apiClient.get<LifecycleNotificationRead[]>(
      "/lifecycle-notifications/",
      { params },
    );
    return data;
  },

  async get(notificationId: string): Promise<LifecycleNotificationRead> {
    const { data } = await apiClient.get<LifecycleNotificationRead>(
      `/lifecycle-notifications/${notificationId}`,
    );
    return data;
  },

  async scheduleEosCheck(): Promise<LifecycleNotificationRead[]> {
    const { data } = await apiClient.post<LifecycleNotificationRead[]>(
      "/lifecycle-notifications/schedule-eos-check",
    );
    return data;
  },

  async markSent(notificationId: string, sent_at?: string | null): Promise<LifecycleNotificationRead> {
    const { data } = await apiClient.post<LifecycleNotificationRead>(
      `/lifecycle-notifications/${notificationId}/mark-sent`,
      { sent_at: sent_at ?? null },
    );
    return data;
  },

  async dismiss(
    notificationId: string,
    payload?: LifecycleNotificationDismissRequest,
  ): Promise<LifecycleNotificationRead> {
    const { data } = await apiClient.post<LifecycleNotificationRead>(
      `/lifecycle-notifications/${notificationId}/dismiss`,
      payload ?? {},
    );
    return data;
  },
};