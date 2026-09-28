from __future__ import annotations

import hashlib
import hmac
import io
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from json import JSONEncoder
from typing import Any
from uuid import UUID, uuid4

from fastapi import UploadFile
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event, snapshot_model
from app.core.config import settings
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.advisory_release import AdvisoryRelease
from app.models.audit_log_event import AuditLogEvent
from app.models.certification_record import CertificationRecord
from app.models.change import Change
from app.models.cvd_policy import CvdPolicy
from app.models.enums import (
    AdvisoryStatus,
    AuditStatus,
    CertificationStatus,
    ChangeStatus,
    CvdPolicyStatus,
    EntityType,
    ReleaseStatus,
    RiskAssessmentStatus,
    RiskItemStatus,
    VulnerabilityLifecycleStatus,
)
from app.models.product import Product, ProductRelease
from app.models.risk_assessment import RiskAssessment
from app.models.risk_item import RiskItem
from app.models.sbom_record import SbomRecord
from app.models.security_advisory import SecurityAdvisory
from app.models.security_update import SecurityUpdate
from app.models.support_period_record import SupportPeriodRecord
from app.models.vulnerability_report import VulnerabilityReport
from app.schemas.certification_record import CertificationRecordCreate
from app.schemas.change import ChangeCreate
from app.schemas.cvd_policy import CvdPolicyCreate
from app.schemas.product import ProductCreate
from app.schemas.product_data import (
    EXPORT_SCHEMA_VERSION,
    MAX_IMPORT_BYTES,
    SUPPORTED_SCHEMA_VERSIONS,
    ProductDataBundle,
    ProductDataHistoryItem,
    ProductDataImportRead,
    ProductDataIssue,
    ProductDataValidationRead,
)
from app.schemas.product_release import ProductReleaseCreate
from app.schemas.risk_assessment import RiskAssessmentCreate
from app.schemas.risk_item import RiskItemCreate
from app.schemas.sbom_record import SbomRecordCreate
from app.schemas.security_advisory import SecurityAdvisoryCreate
from app.schemas.security_update import SecurityUpdateCreate
from app.schemas.support_period_record import SupportPeriodRecordCreate
from app.schemas.vulnerability_report import VulnerabilityReportCreate

ARRAY_LIMITS = {
    "releases": 200,
    "risk_assessments": 500,
    "risk_items": 2_000,
    "vulnerability_reports": 500,
    "security_advisories": 500,
    "security_updates": 500,
    "sbom_records": 200,
    "cvd_policies": 100,
    "support_periods": 200,
    "certification_records": 200,
    "changes": 500,
}
EXCLUDED_DATA = [
    "File attachments and artifact binaries",
    "User accounts, roles, assignments and approvals",
    "Audit ledger entries",
    "Authentication, integration and system settings",
    "Release-gate approvals and electronic signatures",
]
INCLUDED_DATA = [
    "Product record",
    "Selected releases",
    "Risk assessments and risk items",
    "Vulnerability reports, advisories and security updates",
    "SBOM records",
    "CVD policies and support periods",
    "Certification records and product changes",
]
_DANGEROUS_KEYS = {"__proto__", "constructor", "prototype"}


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def _digest(bundle: dict[str, Any]) -> tuple[str, str | None]:
    payload = {key: value for key, value in bundle.items() if key != "integrity"}
    sha = hashlib.sha256()
    signer = hmac.new(settings.product_data_hmac_key.encode(), digestmod=hashlib.sha256) if settings.product_data_hmac_key else None
    for chunk in JSONEncoder(sort_keys=True, separators=(",", ":"), default=_json_default).iterencode(payload):
        encoded = chunk.encode()
        sha.update(encoded)
        if signer:
            signer.update(encoded)
    return sha.hexdigest(), signer.hexdigest() if signer else None


def _walk_json(value: Any, *, depth: int = 0, nodes: list[int] | None = None) -> None:
    if depth > 40:
        raise ValidationException("Import rejected: JSON nesting exceeds 40 levels")
    counter = nodes if nodes is not None else [0]
    counter[0] += 1
    if counter[0] > 2_000_000:
        raise ValidationException("Import rejected: JSON document is too complex")
    if isinstance(value, dict):
        for key, child in value.items():
            if key in _DANGEROUS_KEYS:
                raise ValidationException(f'Import rejected: dangerous key "{key}"')
            _walk_json(child, depth=depth + 1, nodes=counter)
    elif isinstance(value, list):
        for child in value:
            _walk_json(child, depth=depth + 1, nodes=counter)


def load_bundle(upload: UploadFile) -> tuple[ProductDataBundle, dict[str, Any]]:
    upload.file.seek(0, 2)
    size = upload.file.tell()
    upload.file.seek(0)
    if size > MAX_IMPORT_BYTES:
        raise ValidationException(f"Import is limited to {MAX_IMPORT_BYTES // 1024 // 1024} MB")
    if size == 0:
        raise ValidationException("The selected import file is empty")
    wrapper = io.TextIOWrapper(upload.file, encoding="utf-8")
    try:
        raw = json.load(wrapper)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationException("File is not valid UTF-8 JSON") from exc
    finally:
        wrapper.detach()
    if not isinstance(raw, dict):
        raise ValidationException("The import root must be a JSON object")
    _walk_json(raw)
    try:
        bundle = ProductDataBundle.model_validate(raw)
    except ValidationError as exc:
        raise ValidationException(f"Invalid CRANE bundle: {exc.errors()[0]['msg']}") from exc
    if bundle.meta.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValidationException(
            f'Unsupported schema version "{bundle.meta.schema_version}"; supported versions: {", ".join(sorted(SUPPORTED_SCHEMA_VERSIONS))}'
        )
    return bundle, raw


@dataclass
class PreparedBundle:
    product: dict[str, Any] | None = None
    releases: list[tuple[str, dict[str, Any], dict[str, Any]]] = field(default_factory=list)
    assessments: list[tuple[str, dict[str, Any], list[dict[str, Any]]]] = field(default_factory=list)
    advisories: list[tuple[dict[str, Any], list[str]]] = field(default_factory=list)
    policies: list[dict[str, Any]] = field(default_factory=list)
    support_periods: list[tuple[dict[str, Any], str | None]] = field(default_factory=list)
    certifications: list[dict[str, Any]] = field(default_factory=list)
    changes: list[tuple[dict[str, Any], str]] = field(default_factory=list)
    issues: list[ProductDataIssue] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))


class ProductDataService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def _validated(schema: type[BaseModel], data: dict[str, Any], path: str, prepared: PreparedBundle) -> dict[str, Any] | None:
        try:
            return schema.model_validate(data).model_dump()
        except ValidationError as exc:
            for error in exc.errors()[:10]:
                location = ".".join(str(part) for part in error["loc"])
                prepared.issues.append(ProductDataIssue(
                    level="must_fix",
                    path=f"{path}.{location}" if location else path,
                    message=error["msg"],
                ))
            return None

    @staticmethod
    def _source_id(record: dict[str, Any], path: str, prepared: PreparedBundle) -> str | None:
        try:
            return str(UUID(str(record.get("id", ""))))
        except ValueError:
            prepared.issues.append(ProductDataIssue(level="must_fix", path=f"{path}.id", message="A valid source UUID is required"))
            return None

    def _prepare(
        self,
        bundle: ProductDataBundle,
        *,
        actor_id: UUID,
        product_name: str | None,
        product_code: str | None,
    ) -> PreparedBundle:
        result = PreparedBundle()
        source_product = dict(bundle.product)
        source_product.update({
            "name": (product_name or str(source_product.get("name", ""))).strip(),
            "product_code": (product_code or str(source_product.get("product_code", ""))).strip(),
            "parent_product_id": None,
        })
        result.product = self._validated(ProductCreate, source_product, "product", result)

        release_ids: set[str] = set()
        assessment_ids: set[str] = set()
        for index, release in enumerate(bundle.releases):
            path = f"releases[{index}]"
            source_id = self._source_id(release, path, result)
            if source_id and source_id in release_ids:
                result.issues.append(ProductDataIssue(level="must_fix", path=f"{path}.id", message="Duplicate release ID"))
                continue
            if source_id:
                release_ids.add(source_id)
            payload = dict(release)
            payload.update({
                "product_id": UUID(int=0),
                "release_status": ReleaseStatus.draft,
                "parent_release_id": None,
                "substantiality_analysis_id": None,
                "caused_by_change_id": None,
                "remote_processing_element_ids": [],
            })
            valid = self._validated(ProductReleaseCreate, payload, path, result)
            if source_id and valid:
                children = {
                    "vulnerability_reports": list(release.get("vulnerability_reports") or []),
                    "security_updates": list(release.get("security_updates") or []),
                    "sbom_records": list(release.get("sbom_records") or []),
                }
                result.releases.append((source_id, valid, children))
                result.counts["releases"] += 1

        for index, assessment in enumerate(bundle.risk_assessments):
            path = f"risk_assessments[{index}]"
            source_id = self._source_id(assessment, path, result)
            if source_id and source_id in assessment_ids:
                result.issues.append(ProductDataIssue(level="must_fix", path=f"{path}.id", message="Duplicate risk-assessment ID"))
                continue
            if source_id:
                assessment_ids.add(source_id)
            release_id = str(assessment.get("product_release_id") or "") or None
            if release_id and release_id not in release_ids:
                result.issues.append(ProductDataIssue(level="will_skip", path=f"{path}.product_release_id", message="Unknown release link will be removed"))
                release_id = None
            payload = dict(assessment)
            payload.update({
                "product_id": UUID(int=0),
                "product_release_id": UUID(release_id) if release_id else None,
                "owner_user_id": actor_id,
                "status": RiskAssessmentStatus.draft,
            })
            valid = self._validated(RiskAssessmentCreate, payload, path, result)
            risk_items: list[dict[str, Any]] = []
            source_risk_items = assessment.get("risk_items") or []
            if len(source_risk_items) > ARRAY_LIMITS["risk_items"]:
                result.issues.append(ProductDataIssue(level="must_fix", path=f"{path}.risk_items", message=f"Limit is {ARRAY_LIMITS['risk_items']} risk items per assessment"))
                source_risk_items = []
            for item_index, item in enumerate(source_risk_items):
                item_payload = dict(item)
                item_payload.update({"risk_assessment_id": UUID(int=0), "owner_user_id": None, "status": RiskItemStatus.open})
                valid_item = self._validated(RiskItemCreate, item_payload, f"{path}.risk_items[{item_index}]", result)
                if valid_item:
                    risk_items.append(valid_item)
                    result.counts["risk_items"] += 1
            if source_id and valid:
                valid["_source_release_id"] = release_id
                result.assessments.append((source_id, valid, risk_items))
                result.counts["risk_assessments"] += 1

        advisory_ids_in_bundle: set[str] = set()
        for index, advisory in enumerate(bundle.security_advisories):
            path = f"security_advisories[{index}]"
            source_advisory_id = str(advisory.get("advisory_id", ""))
            if source_advisory_id in advisory_ids_in_bundle:
                result.issues.append(ProductDataIssue(level="must_fix", path=f"{path}.advisory_id", message="Duplicate advisory identifier"))
                continue
            advisory_ids_in_bundle.add(source_advisory_id)
            release_refs = advisory.get("releases") or []
            mapped_ids = [str(ref.get("id")) for ref in release_refs if isinstance(ref, dict) and str(ref.get("id")) in release_ids]
            payload = dict(advisory)
            payload.update({"product_id": UUID(int=0), "release_ids": [], "status": AdvisoryStatus.draft, "published_at": None})
            advisory_id = str(payload.get("advisory_id", ""))
            if advisory_id and self.db.scalar(select(SecurityAdvisory.id).where(SecurityAdvisory.advisory_id == advisory_id)):
                suffix_source = bundle.meta.bundle_id or advisory.get("id") or bundle.product.get("id") or advisory_id
                adjusted = f"{advisory_id}-import-{str(suffix_source)[:8]}"[:100]
                payload["advisory_id"] = adjusted
                result.issues.append(ProductDataIssue(level="will_adjust", path=f"{path}.advisory_id", message=f'Identifier will be changed to "{adjusted}"'))
            valid = self._validated(SecurityAdvisoryCreate, payload, path, result)
            if valid:
                valid.pop("release_ids", None)
                valid.pop("all_releases", None)
                result.advisories.append((valid, mapped_ids))
                result.counts["security_advisories"] += 1

        for index, policy in enumerate(bundle.cvd_policies):
            payload = dict(policy)
            payload.update({"product_id": UUID(int=0), "status": CvdPolicyStatus.draft})
            valid = self._validated(CvdPolicyCreate, payload, f"cvd_policies[{index}]", result)
            if valid:
                result.policies.append(valid)
                result.counts["cvd_policies"] += 1

        for index, period in enumerate(bundle.support_periods):
            source_release_id = str(period.get("product_release_id") or "") or None
            if source_release_id and source_release_id not in release_ids:
                result.issues.append(ProductDataIssue(level="will_skip", path=f"support_periods[{index}].product_release_id", message="Unknown release link will be removed"))
                source_release_id = None
            payload = dict(period)
            payload.update({"product_id": UUID(int=0), "product_release_id": None, "recipient_user_ids": []})
            valid = self._validated(SupportPeriodRecordCreate, payload, f"support_periods[{index}]", result)
            if valid:
                result.support_periods.append((valid, source_release_id))
                result.counts["support_periods"] += 1

        for index, certification in enumerate(bundle.certification_records):
            payload = dict(certification)
            payload.update({"product_id": UUID(int=0), "status": CertificationStatus.pending})
            valid = self._validated(CertificationRecordCreate, payload, f"certification_records[{index}]", result)
            if valid:
                result.certifications.append(valid)
                result.counts["certification_records"] += 1

        for index, change in enumerate(bundle.changes):
            release_id = str(change.get("product_version_id") or "")
            if release_id not in release_ids:
                result.issues.append(ProductDataIssue(level="will_skip", path=f"changes[{index}]", message="Change references a release outside this bundle"))
                continue
            payload = dict(change)
            payload["product_version_id"] = UUID(int=0)
            valid = self._validated(ChangeCreate, payload, f"changes[{index}]", result)
            if valid:
                result.changes.append((valid, release_id))
                result.counts["changes"] += 1

        for source_id, _, children in result.releases:
            for kind, schema in (
                ("vulnerability_reports", VulnerabilityReportCreate),
                ("security_updates", SecurityUpdateCreate),
                ("sbom_records", SbomRecordCreate),
            ):
                records = children[kind]
                if len(records) > ARRAY_LIMITS[kind]:
                    result.issues.append(ProductDataIssue(level="must_fix", path=f"releases[{source_id}].{kind}", message=f"Limit is {ARRAY_LIMITS[kind]} records per release"))
                    continue
                normalized: list[dict[str, Any]] = []
                for child_index, record in enumerate(records):
                    payload = dict(record)
                    payload["product_release_id"] = UUID(int=0)
                    if kind == "vulnerability_reports":
                        payload.update({
                            "status": VulnerabilityLifecycleStatus.reported,
                            "assigned_to_user_id": None,
                            "linked_security_update_id": None,
                            "linked_advisory_id": None,
                        })
                    valid = self._validated(schema, payload, f"releases[{source_id}].{kind}[{child_index}]", result)
                    if valid:
                        normalized.append(valid)
                        result.counts[kind] += 1
                children[kind] = normalized

        if any(str(bundle.product.get(field) or "") for field in ("scope_decided_by_user_id",)) or any(
            assessment.get("owner_user_id") or assessment.get("reviewer_user_id") for assessment in bundle.risk_assessments
        ):
            result.issues.append(ProductDataIssue(level="will_adjust", path="user_assignments", message="Source users, reviewers and approvals will not be transferred"))
        result.issues.append(ProductDataIssue(level="ready", path="transaction", message="All writes will use one database transaction and roll back together on failure"))
        return result

    def validate(
        self,
        bundle: ProductDataBundle,
        raw: dict[str, Any],
        *,
        actor_id: UUID,
        product_name: str | None = None,
        product_code: str | None = None,
    ) -> tuple[ProductDataValidationRead, PreparedBundle]:
        for section in ("releases", "risk_assessments", "security_advisories", "cvd_policies", "support_periods", "certification_records", "changes"):
            records = getattr(bundle, section)
            if len(records) > ARRAY_LIMITS[section]:
                raise ValidationException(f"Import has too many {section.replace('_', ' ')}; limit is {ARRAY_LIMITS[section]}")
        source_code = str(bundle.product.get("product_code", "")).strip()
        requested_code = product_code.strip() if product_code is not None else None
        desired_code = requested_code or source_code
        code_exists = bool(desired_code and self.db.scalar(select(Product.id).where(Product.product_code == desired_code)))
        effective_code = self._suggest_code(desired_code) if code_exists and requested_code is None else desired_code
        prepared = self._prepare(bundle, actor_id=actor_id, product_name=product_name, product_code=effective_code)
        if code_exists:
            if requested_code is None:
                prepared.issues.append(ProductDataIssue(
                    level="will_adjust",
                    path="product.product_code",
                    message=f'Product code already exists; import will use "{effective_code}"',
                ))
            else:
                prepared.issues.append(ProductDataIssue(level="must_fix", path="product.product_code", message="Product code already exists"))
        desired_name = (product_name or str(bundle.product.get("name", ""))).strip()
        if desired_name and self.db.scalar(select(Product.id).where(Product.name == desired_name)):
            prepared.issues.append(ProductDataIssue(level="will_adjust", path="product.name", message="A product with this name already exists; the code must remain unique"))

        actual_digest, actual_hmac = _digest(raw)
        signature_status = "unsigned"
        if bundle.integrity:
            if not hmac.compare_digest(bundle.integrity.sha256, actual_digest):
                signature_status = "invalid"
                prepared.issues.append(ProductDataIssue(level="must_fix", path="integrity.sha256", message="Bundle digest does not match its contents"))
            elif bundle.integrity.hmac_sha256:
                if not settings.product_data_hmac_key:
                    signature_status = "unverified"
                    prepared.issues.append(ProductDataIssue(level="will_adjust", path="integrity.hmac_sha256", message="Signature cannot be verified because this CRANE instance has no transfer key"))
                elif actual_hmac and hmac.compare_digest(bundle.integrity.hmac_sha256, actual_hmac):
                    signature_status = "verified"
                else:
                    signature_status = "invalid"
                    prepared.issues.append(ProductDataIssue(level="must_fix", path="integrity.hmac_sha256", message="Bundle authentication failed"))
        else:
            prepared.issues.append(ProductDataIssue(level="will_adjust", path="integrity", message="Unsigned legacy bundle; integrity cannot be authenticated"))

        counts = {key: int(value) for key, value in prepared.counts.items()}
        bundle_id = bundle.meta.bundle_id or UUID(actual_digest[:32])
        result = ProductDataValidationRead(
            valid=not any(issue.level == "must_fix" for issue in prepared.issues),
            bundle_id=bundle_id,
            schema_version=bundle.meta.schema_version,
            source_product_name=str(bundle.product.get("name", "")),
            source_product_code=str(bundle.product.get("product_code", "")),
            suggested_product_code=effective_code if requested_code is None else self._suggest_code(desired_code),
            digest=actual_digest,
            signature_status=signature_status,
            counts=counts,
            included=list(bundle.manifest.get("included") or INCLUDED_DATA),
            excluded=list(bundle.manifest.get("excluded") or EXCLUDED_DATA),
            issues=prepared.issues,
        )
        return result, prepared

    def _suggest_code(self, code: str) -> str:
        base = re.sub(r"[^A-Za-z0-9._-]", "-", code).strip("-")[:90] or "imported-product"
        candidate = base
        suffix = 2
        while self.db.scalar(select(Product.id).where(Product.product_code == candidate)):
            candidate = f"{base[:95-len(str(suffix))]}-{suffix}"
            suffix += 1
        return candidate

    def import_bundle(
        self,
        bundle: ProductDataBundle,
        raw: dict[str, Any],
        *,
        actor_id: UUID,
        product_name: str | None,
        product_code: str | None,
    ) -> ProductDataImportRead:
        validation, prepared = self.validate(
            bundle, raw, actor_id=actor_id, product_name=product_name, product_code=product_code
        )
        if not validation.valid or not prepared.product:
            first = next((issue for issue in validation.issues if issue.level == "must_fix"), None)
            raise ValidationException(first.message if first else "Bundle validation failed")
        try:
            product = Product(**prepared.product)
            self.db.add(product)
            self.db.flush()
            release_map: dict[str, UUID] = {}
            for system_version, (source_id, payload, _) in enumerate(prepared.releases, start=1):
                payload = dict(payload)
                payload.pop("remote_processing_element_ids", None)
                payload.update({"product_id": product.id, "system_version": system_version})
                release = ProductRelease(**payload)
                self.db.add(release)
                self.db.flush()
                release_map[source_id] = release.id

            for source_id, _, children in prepared.releases:
                release_id = release_map[source_id]
                for model, key in (
                    (VulnerabilityReport, "vulnerability_reports"),
                    (SecurityUpdate, "security_updates"),
                    (SbomRecord, "sbom_records"),
                ):
                    for child in children[key]:
                        data = dict(child)
                        data["product_release_id"] = release_id
                        self.db.add(model(**data))

            for payload, source_release_ids in prepared.advisories:
                data = dict(payload)
                data["product_id"] = product.id
                advisory = SecurityAdvisory(**data)
                self.db.add(advisory)
                self.db.flush()
                for source_release_id in source_release_ids:
                    if source_release_id in release_map:
                        self.db.add(AdvisoryRelease(security_advisory_id=advisory.id, product_release_id=release_map[source_release_id]))

            for system_version, (_, payload, items) in enumerate(prepared.assessments, start=1):
                data = dict(payload)
                source_release_id = data.pop("_source_release_id", None)
                data.update({
                    "product_id": product.id,
                    "product_release_id": release_map.get(source_release_id),
                    "system_version": system_version,
                })
                assessment = RiskAssessment(**data)
                self.db.add(assessment)
                self.db.flush()
                for item in items:
                    item_data = dict(item)
                    item_data["risk_assessment_id"] = assessment.id
                    self.db.add(RiskItem(**item_data))

            for payload in prepared.policies:
                self.db.add(CvdPolicy(**{**payload, "product_id": product.id}))
            for payload, source_release_id in prepared.support_periods:
                data = dict(payload)
                data.pop("recipient_user_ids", None)
                data.update({
                    "product_id": product.id,
                    "product_release_id": release_map.get(source_release_id),
                    "created_by_user_id": actor_id,
                    "change_reason": "Imported from a CRANE product-data bundle",
                })
                self.db.add(SupportPeriodRecord(**data))
            for payload in prepared.certifications:
                self.db.add(CertificationRecord(**{**payload, "product_id": product.id}))
            for payload, source_release_id in prepared.changes:
                self.db.add(Change(**{
                    **payload,
                    "product_version_id": release_map[source_release_id],
                    "initiator_user_id": actor_id,
                    "status": ChangeStatus.draft,
                }))

            create_audit_event(
                self.db,
                actor_user_id=actor_id,
                action_type="product_data.imported",
                entity_type=EntityType.product,
                entity_id=product.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "bundle_id": str(validation.bundle_id),
                    "digest": validation.digest,
                    "counts": validation.counts,
                    "adjusted": sum(issue.level == "will_adjust" for issue in validation.issues),
                    "skipped": sum(issue.level == "will_skip" for issue in validation.issues),
                },
            )
            self.db.commit()
            return ProductDataImportRead(
                product_id=product.id,
                bundle_id=validation.bundle_id,
                digest=validation.digest,
                counts=validation.counts,
                adjusted=sum(issue.level == "will_adjust" for issue in validation.issues),
                skipped=sum(issue.level == "will_skip" for issue in validation.issues),
            )
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Import conflicted with data created after validation; no records were imported") from exc
        except Exception:
            self.db.rollback()
            raise

    def export_bundle(
        self,
        product_id: UUID,
        *,
        actor_id: UUID,
        actor_email: str,
        release_ids: list[UUID] | None,
        redact_personal_data: bool,
        include_embargoed: bool,
        sensitivity: str,
    ) -> tuple[dict[str, Any], str, str]:
        product = self.db.get(Product, product_id)
        if not product:
            raise NotFoundException("Product not found")
        releases = list(self.db.scalars(select(ProductRelease).where(ProductRelease.product_id == product_id).order_by(ProductRelease.system_version)))
        if release_ids:
            requested = set(release_ids)
            releases = [release for release in releases if release.id in requested]
            if len(releases) != len(requested):
                raise ValidationException("One or more selected releases do not belong to this product")
        selected_ids = {release.id for release in releases}

        vulnerabilities = self._group_by_release(VulnerabilityReport, selected_ids)
        updates = self._group_by_release(SecurityUpdate, selected_ids)
        sboms = self._group_by_release(SbomRecord, selected_ids)
        exported_releases: list[dict[str, Any]] = []
        for release in releases:
            item = snapshot_model(release)
            item["display_version"] = release.user_version or f"v{release.system_version}"
            item["vulnerability_reports"] = []
            for report in vulnerabilities[release.id]:
                report_data = snapshot_model(report)
                if redact_personal_data:
                    report_data["reporter_name"] = None
                    report_data["reporter_email"] = None
                item["vulnerability_reports"].append(report_data)
            item["security_updates"] = [snapshot_model(record) for record in updates[release.id]]
            item["sbom_records"] = [snapshot_model(record) for record in sboms[release.id]]
            exported_releases.append(item)

        assessment_query = select(RiskAssessment).where(RiskAssessment.product_id == product_id)
        assessments = list(self.db.scalars(assessment_query.order_by(RiskAssessment.system_version)))
        if release_ids:
            assessments = [a for a in assessments if a.product_release_id is None or a.product_release_id in selected_ids]
        assessment_ids = {assessment.id for assessment in assessments}
        risk_items: dict[UUID, list[RiskItem]] = defaultdict(list)
        if assessment_ids:
            for item in self.db.scalars(select(RiskItem).where(RiskItem.risk_assessment_id.in_(assessment_ids))):
                risk_items[item.risk_assessment_id].append(item)
        exported_assessments = []
        for assessment in assessments:
            item = snapshot_model(assessment)
            item["display_version"] = assessment.user_version or f"v{assessment.system_version}"
            item["risk_items"] = [snapshot_model(risk_item) for risk_item in risk_items[assessment.id]]
            exported_assessments.append(item)

        advisories = list(self.db.scalars(select(SecurityAdvisory).where(SecurityAdvisory.product_id == product_id)))
        now = datetime.now(UTC)
        excluded_embargoed = 0
        if not include_embargoed:
            kept = []
            for advisory in advisories:
                if advisory.status == AdvisoryStatus.embargo or (advisory.embargo_until and advisory.embargo_until > now):
                    excluded_embargoed += 1
                else:
                    kept.append(advisory)
            advisories = kept
        advisory_ids = {advisory.id for advisory in advisories}
        links: dict[UUID, list[UUID]] = defaultdict(list)
        if advisory_ids:
            for link in self.db.scalars(select(AdvisoryRelease).where(AdvisoryRelease.security_advisory_id.in_(advisory_ids))):
                if link.product_release_id in selected_ids:
                    links[link.security_advisory_id].append(link.product_release_id)
        release_by_id = {release.id: release for release in releases}
        exported_advisories = []
        for advisory in advisories:
            item = snapshot_model(advisory)
            item["releases"] = [
                {
                    "id": str(release_id),
                    "display_version": release_by_id[release_id].user_version or f"v{release_by_id[release_id].system_version}",
                    "release_status": release_by_id[release_id].release_status.value,
                }
                for release_id in links[advisory.id]
            ]
            exported_advisories.append(item)

        policies = self._snapshots(select(CvdPolicy).where(CvdPolicy.product_id == product_id))
        periods_models = list(self.db.scalars(select(SupportPeriodRecord).where(SupportPeriodRecord.product_id == product_id)))
        if release_ids:
            periods_models = [p for p in periods_models if p.product_release_id is None or p.product_release_id in selected_ids]
        certifications = self._snapshots(select(CertificationRecord).where(CertificationRecord.product_id == product_id))
        changes = self._snapshots(select(Change).where(Change.product_version_id.in_(selected_ids))) if selected_ids else []

        bundle_id = uuid4()
        counts = {
            "releases": len(exported_releases),
            "risk_assessments": len(exported_assessments),
            "risk_items": sum(len(item["risk_items"]) for item in exported_assessments),
            "vulnerability_reports": sum(len(item["vulnerability_reports"]) for item in exported_releases),
            "security_advisories": len(exported_advisories),
            "security_updates": sum(len(item["security_updates"]) for item in exported_releases),
            "sbom_records": sum(len(item["sbom_records"]) for item in exported_releases),
            "cvd_policies": len(policies),
            "support_periods": len(periods_models),
            "certification_records": len(certifications),
            "changes": len(changes),
        }
        bundle: dict[str, Any] = {
            "_meta": {
                "schema_version": EXPORT_SCHEMA_VERSION,
                "exported_at": datetime.now(UTC).isoformat(),
                "exported_by": None if redact_personal_data else actor_email,
                "tool": "CRANE CRA Compliance Tool",
                "crane_version": settings.app_version,
                "bundle_id": str(bundle_id),
                "sensitivity": sensitivity,
            },
            "manifest": {
                "included": INCLUDED_DATA,
                "excluded": EXCLUDED_DATA,
                "counts": counts,
                "release_scope": "selected" if release_ids else "all",
                "personal_data_redacted": redact_personal_data,
                "embargoed_advisories_excluded": excluded_embargoed,
            },
            "product": snapshot_model(product),
            "releases": exported_releases,
            "risk_assessments": exported_assessments,
            "security_advisories": exported_advisories,
            "cvd_policies": policies,
            "support_periods": [snapshot_model(period) for period in periods_models],
            "certification_records": certifications,
            "changes": changes,
        }
        digest, signature = _digest(bundle)
        bundle["integrity"] = {
            "algorithm": "sha256",
            "digest_scope": "bundle_without_integrity",
            "sha256": digest,
            "hmac_sha256": signature,
        }
        create_audit_event(
            self.db,
            actor_user_id=actor_id,
            action_type="product_data.exported",
            entity_type=EntityType.product,
            entity_id=product.id,
            status=AuditStatus.success,
            details_json={
                "product_id": str(product.id),
                "product_name": product.name,
                "bundle_id": str(bundle_id),
                "digest": digest,
                "counts": counts,
                "redacted": redact_personal_data,
            },
        )
        self.db.commit()
        safe_name = re.sub(r"[^a-z0-9]+", "-", product.name.lower()).strip("-") or "product"
        filename = f"crane-export_{safe_name}_{datetime.now(UTC).date().isoformat()}.json"
        return bundle, digest, filename

    def _group_by_release(self, model: type[Any], release_ids: set[UUID]) -> dict[UUID, list[Any]]:
        grouped: dict[UUID, list[Any]] = defaultdict(list)
        if release_ids:
            for record in self.db.scalars(select(model).where(model.product_release_id.in_(release_ids))):
                grouped[record.product_release_id].append(record)
        return grouped

    def _snapshots(self, statement: Any) -> list[dict[str, Any]]:
        return [snapshot_model(record) for record in self.db.scalars(statement)]

    def history(self, limit: int = 20) -> list[ProductDataHistoryItem]:
        events = list(self.db.scalars(
            select(AuditLogEvent)
            .where(AuditLogEvent.action_type.in_(["product_data.exported", "product_data.imported"]))
            .order_by(AuditLogEvent.occurred_at.desc())
            .limit(limit)
        ))
        return [ProductDataHistoryItem(
            occurred_at=event.occurred_at,
            action=event.action_type.rsplit(".", 1)[-1],
            status=event.status,
            product_id=event.entity_id,
            product_name=event.details_json.get("product_name"),
            bundle_id=event.details_json.get("bundle_id"),
            digest=event.details_json.get("digest"),
            counts=event.details_json.get("counts") or {},
        ) for event in events]
