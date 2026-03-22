import { apiClient } from "@/services/api";
import type { ProductCreate, ProductRead, ProductUpdate } from "@/types/product";

export const productService = {
  async list(): Promise<ProductRead[]> {
    const { data } = await apiClient.get<ProductRead[]>("/products");
    return data;
  },
  async get(productId: string): Promise<ProductRead> {
    const { data } = await apiClient.get<ProductRead>(`/products/${productId}`);
    return data;
  },
  async create(payload: ProductCreate): Promise<ProductRead> {
    const { data } = await apiClient.post<ProductRead>("/products", payload);
    return data;
  },
  async update(productId: string, payload: ProductUpdate): Promise<ProductRead> {
    const { data } = await apiClient.put<ProductRead>(`/products/${productId}`, payload);
    return data;
  },
  async remove(productId: string): Promise<void> {
    await apiClient.delete(`/products/${productId}`);
  },
};