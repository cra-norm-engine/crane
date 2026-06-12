# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ConformityRoute, ProductClassification


class ProductScopeEvaluationRequest(BaseModel):
    is_digital_product: bool
    has_network_connectivity: bool
    performs_remote_data_processing: bool
    safety_component: bool
    used_in_critical_sector: bool
    handles_sensitive_functions: bool
    excluded_category: bool
    notes: str | None = None


class ProductScopeEvaluationResult(BaseModel):
    in_scope: bool
    rationale: str
    recommended_classification: ProductClassification
    suggested_conformity_route: ConformityRoute


class ProductScopeEvaluationRead(ProductScopeEvaluationRequest, ProductScopeEvaluationResult):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: datetime