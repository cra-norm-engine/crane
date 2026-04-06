import { apiClient } from "@/services/api";
import type { ProductReleaseRead } from "@/types/release-gate";
import type { ProductReleaseCreate } from "@/types/product";

export const productReleaseService = {
  async list(productId?: string): Promise<ProductReleaseRead[]> {
    const { data } = await apiClient.get<ProductReleaseRead[]>("/product-releases/", {
      params: productId ? { product_id: productId } : undefined,
    });
    return data;
  },

  async get(releaseId: string): Promise<ProductReleaseRead> {
    const { data } = await apiClient.get<ProductReleaseRead>(`/product-releases/${releaseId}`);
    return data;
  },

  async create(payload: ProductReleaseCreate): Promise<ProductReleaseRead> {
    const { data } = await apiClient.post<ProductReleaseRead>("/product-releases/", payload);
    return data;
  },
};
