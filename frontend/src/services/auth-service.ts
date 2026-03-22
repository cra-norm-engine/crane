import { apiClient } from "@/services/api";
import type { LoginPayload, TokenResponse } from "@/types/auth";

export const authService = {
  async login(payload: LoginPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>("/auth/login", payload);
    return data;
  },
};