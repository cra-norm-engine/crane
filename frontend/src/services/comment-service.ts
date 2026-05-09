import { apiClient } from "@/services/api";
import type { CommentCreate, CommentRead, CommentUpdate } from "@/types/comment";

export const commentService = {
  /**
   * Fetch all comments for a specific entity, ordered oldest-first.
   */
  async list(entityType: string, entityId: string): Promise<CommentRead[]> {
    const { data } = await apiClient.get<CommentRead[]>("/comments/", {
      params: { entity_type: entityType, entity_id: entityId },
    });
    return data;
  },

  async create(payload: CommentCreate): Promise<CommentRead> {
    const { data } = await apiClient.post<CommentRead>("/comments/", payload);
    return data;
  },

  async update(commentId: string, payload: CommentUpdate): Promise<CommentRead> {
    const { data } = await apiClient.put<CommentRead>(`/comments/${commentId}`, payload);
    return data;
  },

  async remove(commentId: string): Promise<void> {
    await apiClient.delete(`/comments/${commentId}`);
  },
};
