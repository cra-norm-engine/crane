import { apiClient } from "@/services/api";
import type { TaskItem } from "@/types/task";

export const taskService = {
  /**
   * Fetch all open tasks assigned to the current user, sorted by urgency.
   */
  async listMyTasks(): Promise<TaskItem[]> {
    const { data } = await apiClient.get<TaskItem[]>("/my-tasks/");
    return data;
  },
};
