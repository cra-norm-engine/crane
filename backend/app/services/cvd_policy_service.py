# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException, ValidationException
from app.models.cvd_policy import CvdPolicy, CvdPolicyProduct
from app.models.enums import AuditStatus, EntityType
from app.repositories.cvd_policy_repository import CvdPolicyRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cvd_policy import CvdPolicyCreate, CvdPolicyRead, CvdPolicyUpdate


class CvdPolicyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CvdPolicyRepository(db)
        self.product_repository = ProductRepository(db)

    def list_cvd_policies(self, *, product_id: UUID | None = None) -> list[CvdPolicyRead]:
        policies = self.repository.list_all(product_id=product_id)
        return [CvdPolicyRead.model_validate(p) for p in policies]

    def get_cvd_policy(self, policy_id: UUID) -> CvdPolicyRead:
        return CvdPolicyRead.model_validate(self.repository.get_or_404(policy_id))

    def create_cvd_policy(self, payload: CvdPolicyCreate, actor: object) -> CvdPolicyRead:
        self._validate_products(payload.product_ids)
        policy = CvdPolicy(**payload.model_dump(exclude={"product_ids"}))
        policy.product_links = [
            CvdPolicyProduct(product_id=product_id) for product_id in payload.product_ids
        ]
        try:
            self.repository.add(policy)
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="cvd_policy.created",
                entity_type=EntityType.cvd_policy,
                entity_id=policy.id,
                status=AuditStatus.success,
                details_json={
                    "organization_wide": policy.organization_wide,
                    "product_ids": [str(product_id) for product_id in policy.product_ids],
                    "status": policy.status,
                },
            )
            self.db.commit()
            self.db.refresh(policy)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create CVD policy") from exc
        return CvdPolicyRead.model_validate(policy)

    def update_cvd_policy(
        self, policy_id: UUID, payload: CvdPolicyUpdate, actor: object
    ) -> CvdPolicyRead:
        policy = self.repository.get_or_404(policy_id)
        updates = payload.model_dump(exclude_unset=True)
        product_ids = updates.pop("product_ids", None)
        organization_wide = updates.get("organization_wide", policy.organization_wide)
        effective_product_ids = product_ids if product_ids is not None else policy.product_ids
        if organization_wide == bool(effective_product_ids):
            raise ValidationException("Choose organization-wide scope or at least one product")
        if product_ids is not None:
            product_ids = list(dict.fromkeys(product_ids))
            self._validate_products(product_ids)
            policy.product_links = [
                CvdPolicyProduct(product_id=product_id) for product_id in product_ids
            ]
        for field, value in updates.items():
            setattr(policy, field, value)
        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="cvd_policy.updated",
                entity_type=EntityType.cvd_policy,
                entity_id=policy.id,
                status=AuditStatus.success,
                details_json={
                    "organization_wide": policy.organization_wide,
                    "product_ids": [str(product_id) for product_id in policy.product_ids],
                    "updated_fields": sorted(
                        [*updates.keys(), *(["product_ids"] if product_ids is not None else [])]
                    ),
                },
            )
            self.db.commit()
            self.db.refresh(policy)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to update CVD policy") from exc
        return CvdPolicyRead.model_validate(policy)

    def delete_cvd_policy(self, policy_id: UUID, actor: object) -> None:
        policy = self.repository.get_or_404(policy_id)
        self.repository.delete(policy)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="cvd_policy.deleted",
            entity_type=EntityType.cvd_policy,
            entity_id=policy_id,
            status=AuditStatus.success,
            details_json={
                "organization_wide": policy.organization_wide,
                "product_ids": [str(product_id) for product_id in policy.product_ids],
            },
        )
        self.db.commit()

    def _validate_products(self, product_ids: list[UUID]) -> None:
        for product_id in product_ids:
            self.product_repository.get_or_404(product_id)
