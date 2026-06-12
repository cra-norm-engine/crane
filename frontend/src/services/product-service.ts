// CRANE — CRA Norm Engine
// Copyright (C) 2026 Ali Mohammad Hosseini
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
// See <https://www.gnu.org/licenses/>.

import { apiClient } from "@/services/api";
import type {
  ProductCreate,
  ProductDetailRead,
  ProductRead,
  ProductScopeEvaluationRead,
  ProductScopeEvaluationRequest,
  ProductSummaryRead,
  ProductUpdate,
} from "@/types/product";

export const productService = {
  async list(search?: string): Promise<ProductSummaryRead[]> {
    const { data } = await apiClient.get<ProductSummaryRead[]>("/products/", {
      params: search ? { search } : undefined,
    });
    return data;
  },

  async get(productId: string): Promise<ProductDetailRead> {
    const { data } = await apiClient.get<ProductDetailRead>(`/products/${productId}`);
    return data;
  },

  async create(payload: ProductCreate): Promise<ProductRead> {
    const { data } = await apiClient.post<ProductRead>("/products/", payload);
    return data;
  },

  async update(productId: string, payload: ProductUpdate): Promise<ProductRead> {
    const { data } = await apiClient.put<ProductRead>(`/products/${productId}`, payload);
    return data;
  },

  async remove(productId: string): Promise<void> {
    await apiClient.delete(`/products/${productId}`);
  },

  async evaluateScope(
    productId: string,
    payload: ProductScopeEvaluationRequest,
  ): Promise<ProductScopeEvaluationRead> {
    const { data } = await apiClient.post<ProductScopeEvaluationRead>(
      `/products/${productId}/scope-evaluation`,
      payload,
    );
    return data;
  },
};