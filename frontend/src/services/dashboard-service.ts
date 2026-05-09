import { apiClient } from "@/services/api";
import type { DashboardRead } from "@/types/dashboard";

export const dashboardService = {
  async get(): Promise<DashboardRead> {
    const { data } = await apiClient.get<DashboardRead>("/dashboard");
    return data;
  },
};
