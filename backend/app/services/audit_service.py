from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.audit_log_event import AuditLogEvent
from app.models.user import User
from app.schemas.audit import (
    AuditActorRead,
    AuditEventListRead,
    AuditEventRead,
    AuditIntegrityIssueRead,
    AuditIntegrityRead,
)


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_events(
        self,
        *,
        entity_id: UUID | None = None,
        product_id: UUID | None = None,
        product_release_id: UUID | None = None,
        actor_user_id: UUID | None = None,
        action_type: str | None = None,
        action_prefix: str | None = None,
        entity_type: str | None = None,
        limit: int = 100,
    ) -> AuditEventListRead:
        limit = max(1, min(limit, 250))
        statement = select(AuditLogEvent)
        statement = self._apply_filters(
            statement,
            entity_id=entity_id,
            product_id=product_id,
            product_release_id=product_release_id,
            actor_user_id=actor_user_id,
            action_type=action_type,
            action_prefix=action_prefix,
            entity_type=entity_type,
        )

        total = self.db.scalar(select(func.count()).select_from(statement.subquery())) or 0
        events = list(
            self.db.scalars(
                statement.order_by(AuditLogEvent.occurred_at.desc()).limit(limit)
            ).all()
        )
        actors = self._load_actors(event.actor_user_id for event in events)

        return AuditEventListRead(
            items=[self._serialize_event(event, actors) for event in events],
            total=total,
        )

    def verify_integrity(self, *, limit_issues: int = 25) -> AuditIntegrityRead:
        events = list(
            self.db.scalars(
                select(AuditLogEvent).order_by(AuditLogEvent.sequence_number.asc())
            ).all()
        )

        issues: list[AuditIntegrityIssueRead] = []
        previous_event: AuditLogEvent | None = None
        verified_events = 0

        for index, event in enumerate(events, start=1):
            event_is_valid = True

            if event.sequence_number != index:
                issues.append(
                    AuditIntegrityIssueRead(
                        sequence_number=event.sequence_number,
                        event_id=event.id,
                        reason=f"Expected sequence {index} but found {event.sequence_number}.",
                    )
                )
                event_is_valid = False

            if previous_event is None:
                if event.previous_event_id is not None or event.previous_checksum is not None:
                    issues.append(
                        AuditIntegrityIssueRead(
                            sequence_number=event.sequence_number,
                            event_id=event.id,
                            reason="Genesis audit event must not reference a previous event.",
                        )
                    )
                    event_is_valid = False
            else:
                if event.previous_event_id != previous_event.id:
                    issues.append(
                        AuditIntegrityIssueRead(
                            sequence_number=event.sequence_number,
                            event_id=event.id,
                            reason="Previous event pointer does not match the preceding audit event.",
                        )
                    )
                    event_is_valid = False
                if event.previous_checksum != previous_event.checksum:
                    issues.append(
                        AuditIntegrityIssueRead(
                            sequence_number=event.sequence_number,
                            event_id=event.id,
                            reason="Previous checksum does not match the preceding audit event checksum.",
                        )
                    )
                    event_is_valid = False

            expected_checksum = AuditLogEvent.compute_checksum(
                occurred_at=event.occurred_at,
                actor_user_id=event.actor_user_id,
                action_type=event.action_type,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                sequence_number=event.sequence_number,
                previous_event_id=event.previous_event_id,
                previous_checksum=event.previous_checksum,
                status=event.status,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                details_json=event.details_json,
            )
            if expected_checksum != event.checksum:
                issues.append(
                    AuditIntegrityIssueRead(
                        sequence_number=event.sequence_number,
                        event_id=event.id,
                        reason="Stored checksum does not match the recomputed checksum.",
                    )
                )
                event_is_valid = False

            if event_is_valid:
                verified_events += 1

            previous_event = event

            if len(issues) >= limit_issues:
                break

        latest_sequence_number = events[-1].sequence_number if events else None
        return AuditIntegrityRead(
            verified=len(issues) == 0,
            total_events=len(events),
            verified_events=verified_events,
            latest_sequence_number=latest_sequence_number,
            issues=issues[:limit_issues],
        )

    def _apply_filters(
        self,
        statement: Select[tuple[AuditLogEvent]],
        *,
        entity_id: UUID | None,
        product_id: UUID | None,
        product_release_id: UUID | None,
        actor_user_id: UUID | None,
        action_type: str | None,
        action_prefix: str | None,
        entity_type: str | None,
    ) -> Select[tuple[AuditLogEvent]]:
        if entity_id is not None:
            statement = statement.where(AuditLogEvent.entity_id == entity_id)

        if product_id is not None:
            product_id_text = str(product_id)
            statement = statement.where(
                or_(
                    AuditLogEvent.entity_id == product_id,
                    AuditLogEvent.details_json["product_id"].astext == product_id_text,
                )
            )

        if product_release_id is not None:
            release_id_text = str(product_release_id)
            statement = statement.where(
                or_(
                    AuditLogEvent.entity_id == product_release_id,
                    AuditLogEvent.details_json["product_release_id"].astext == release_id_text,
                )
            )

        if actor_user_id is not None:
            statement = statement.where(AuditLogEvent.actor_user_id == actor_user_id)

        if action_type:
            statement = statement.where(AuditLogEvent.action_type == action_type)

        if action_prefix:
            statement = statement.where(AuditLogEvent.action_type.like(f"{action_prefix}%"))

        if entity_type:
            statement = statement.where(AuditLogEvent.entity_type == entity_type)

        return statement

    def _load_actors(self, actor_ids: Iterable[UUID | None]) -> dict[UUID, User]:
        ids = sorted({actor_id for actor_id in actor_ids if actor_id is not None}, key=str)
        if not ids:
            return {}

        statement = select(User).where(User.id.in_(ids))
        return {user.id: user for user in self.db.scalars(statement).all()}

    def _serialize_event(self, event: AuditLogEvent, actors: dict[UUID, User]) -> AuditEventRead:
        actor = actors.get(event.actor_user_id) if event.actor_user_id is not None else None
        details = event.details_json or {}

        return AuditEventRead(
            id=event.id,
            occurred_at=event.occurred_at,
            actor=AuditActorRead(
                id=actor.id if actor else event.actor_user_id,
                full_name=actor.full_name if actor else None,
                email=actor.email if actor else None,
            ),
            action_type=event.action_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            status=event.status,
            summary=self._build_summary(event.action_type, details, event.entity_type),
            entity_label=self._build_entity_label(details),
            product_id=self._uuid_from_details(details.get("product_id")),
            product_release_id=self._uuid_from_details(details.get("product_release_id")),
            details_json=details,
        )

    def _build_entity_label(self, details: dict) -> str | None:
        for key in (
            "name",
            "title",
            "product_code",
            "version",
            "release_version",
            "artifact_title",
            "target_user_email",
            "email",
        ):
            value = details.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _build_summary(self, action_type: str, details: dict, entity_type: str) -> str:
        product_name = details.get("product_name") or details.get("name")
        product_code = details.get("product_code")
        release_version = details.get("release_version") or details.get("version")
        artifact_title = details.get("artifact_title") or details.get("title")
        target_user_email = details.get("target_user_email") or details.get("email")
        decision = details.get("decision")

        summaries = {
            "product.created": f"Created product {self._label(product_name, product_code, fallback='record')}",
            "product.updated": f"Updated product {self._label(product_name, product_code, fallback='record')}",
            "product.deleted": f"Deleted product {self._label(product_name, product_code, fallback='record')}",
            "support_period.set": (
                f"Set support period {details.get('support_start_date')} to {details.get('support_end_date')}"
            ),
            "support_period.versioned": (
                f"Updated support period to {details.get('support_start_date')} through {details.get('support_end_date')}"
            ),
            "release.created": f"Created release {release_version or 'record'}",
            "release.updated": f"Updated release {release_version or 'record'}",
            "release.published": f"Marked release {release_version or 'record'} as released",
            "release.deleted": f"Deleted release {release_version or 'record'}",
            "release_gate.submitted": f"Submitted release {release_version or 'record'} for review",
            "release_gate.approved": f"Approved release gate for {release_version or 'record'}",
            "artifact.uploaded": f"Uploaded artifact {artifact_title or 'file'}",
            "artifact.linked": f"Added linked artifact {artifact_title or 'evidence'}",
            "artifact.revision_uploaded": f"Uploaded a new revision for {artifact_title or 'artifact'}",
            "artifact.attached_to_gate": f"Attached {artifact_title or 'artifact'} to release evidence",
            "artifact.reviewed": f"Reviewed release evidence as {decision or 'updated'}",
            "risk_assessment.created": f"Created risk assessment {details.get('title') or 'record'}",
            "risk_assessment.updated": f"Updated risk assessment {details.get('title') or 'record'}",
            "risk_assessment.approved": f"Approved risk assessment {details.get('title') or 'record'}",
            "risk_assessment.duplicated": f"Duplicated risk assessment to {details.get('system_version_label') or 'new version'}",
            "risk_assessment.deleted": f"Deleted risk assessment {details.get('title') or 'record'}",
            "security_update.created": f"Created security update {details.get('title') or 'record'}",
            "security_update.updated": f"Updated security update {details.get('title') or 'record'}",
            "security_update.deleted": f"Deleted security update {details.get('title') or 'record'}",
            "admin.user.created": f"Created user {target_user_email or 'account'}",
            "admin.user.roles_updated": f"Updated roles for {target_user_email or 'user'}",
            "admin.user.activated": f"Activated user {target_user_email or 'account'}",
            "admin.user.deactivated": f"Deactivated user {target_user_email or 'account'}",
        }

        if action_type in summaries:
            return summaries[action_type]

        return f"{action_type.replace('.', ' ').replace('_', ' ')} on {entity_type.replace('_', ' ')}"

    def _label(self, primary: object, secondary: object, *, fallback: str) -> str:
        if isinstance(primary, str) and primary.strip() and isinstance(secondary, str) and secondary.strip():
            return f"{primary.strip()} ({secondary.strip()})"
        if isinstance(primary, str) and primary.strip():
            return primary.strip()
        if isinstance(secondary, str) and secondary.strip():
            return secondary.strip()
        return fallback

    def _uuid_from_details(self, value: object) -> UUID | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            return UUID(value)
        except ValueError:
            return None
