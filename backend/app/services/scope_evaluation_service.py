# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.models.enums import AuditActionType, AuditStatus, ConformityRoute, EntityType
from app.models.product import ProductScopeEvaluation
from app.repositories.product_repository import ProductRepository
from app.repositories.product_scope_evaluation_repository import ProductScopeEvaluationRepository
from app.schemas.scope_evaluation import ProductScopeEvaluationRead, ProductScopeEvaluationRequest
from app.services.cra_rule_service import CRARuleService


class ScopeEvaluationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.product_repository = ProductRepository(db)
        self.repository = ProductScopeEvaluationRepository(db)
        self.rule_service = CRARuleService()

    def evaluate_product_scope(
        self,
        *,
        product_id: UUID,
        payload: ProductScopeEvaluationRequest,
        actor: object,
    ) -> ProductScopeEvaluationRead:
        product = self.product_repository.get_or_404(product_id)
        result = self.rule_service.evaluate(payload)

        evaluation = ProductScopeEvaluation(
            product_id=product.id,
            **payload.model_dump(),
            in_scope=result.in_scope,
            rationale=result.rationale,
            recommended_classification=result.recommended_classification,
            suggested_conformity_route=result.suggested_conformity_route,
        )
        self.repository.add(evaluation)

        product.scope_status = "in_scope" if result.in_scope else "out_of_scope"
        product.current_classification = result.recommended_classification

        # Phase 2 — stamp the decision provenance so the inventory record is
        # audit-ready. Records who decided and when for every evaluation; for
        # out-of-scope results also seed the justification from the rule rationale
        # (the user can later refine the justification/signature via the edit form).
        actor_id = getattr(actor, "id", None)
        product.scope_decided_by_user_id = actor_id
        product.scope_decided_at = datetime.now(UTC)
        if not result.in_scope and not product.out_of_scope_justification:
            product.out_of_scope_justification = result.rationale

        # Phase 3 — seed the product-level conformity route from the wizard's
        # suggestion while it is still undecided, so the inventory shows a route
        # without overwriting a route the team has already chosen.
        if product.conformity_route == ConformityRoute.undecided:
            product.conformity_route = result.suggested_conformity_route

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.create,
            entity_type=EntityType.product_scope_evaluation,
            entity_id=evaluation.id,
            status=AuditStatus.success,
            details_json={
                "product_id": str(product.id),
                "in_scope": result.in_scope,
                "recommended_classification": result.recommended_classification.value,
                "suggested_conformity_route": result.suggested_conformity_route.value,
            },
        )
        self.db.commit()
        self.db.refresh(evaluation)

        return ProductScopeEvaluationRead.model_validate(evaluation)