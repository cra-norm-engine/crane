from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

EXPORT_SCHEMA_VERSION = "2.0"
SUPPORTED_SCHEMA_VERSIONS = {"1.0", EXPORT_SCHEMA_VERSION}
MAX_IMPORT_BYTES = 50 * 1024 * 1024


class ProductDataMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: str
    exported_at: datetime
    exported_by: str | None = None
    tool: str
    crane_version: str | None = None
    bundle_id: UUID | None = None
    sensitivity: Literal["internal", "confidential", "restricted"] = "confidential"


class ProductDataIntegrity(BaseModel):
    algorithm: Literal["sha256"] = "sha256"
    digest_scope: Literal["bundle_without_integrity"] = "bundle_without_integrity"
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    hmac_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class ProductDataBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meta: ProductDataMeta = Field(alias="_meta")
    manifest: dict[str, Any] = Field(default_factory=dict)
    integrity: ProductDataIntegrity | None = None
    product: dict[str, Any]
    releases: list[dict[str, Any]] = Field(default_factory=list)
    risk_assessments: list[dict[str, Any]] = Field(default_factory=list)
    security_advisories: list[dict[str, Any]] = Field(default_factory=list)
    cvd_policies: list[dict[str, Any]] = Field(default_factory=list)
    support_periods: list[dict[str, Any]] = Field(default_factory=list)
    certification_records: list[dict[str, Any]] = Field(default_factory=list)
    changes: list[dict[str, Any]] = Field(default_factory=list)


class ProductDataIssue(BaseModel):
    level: Literal["must_fix", "will_adjust", "will_skip", "ready"]
    path: str
    message: str


class ProductDataValidationRead(BaseModel):
    valid: bool
    bundle_id: UUID
    schema_version: str
    source_product_name: str
    source_product_code: str
    suggested_product_code: str
    digest: str
    signature_status: Literal["verified", "unsigned", "unverified", "invalid"]
    counts: dict[str, int]
    included: list[str]
    excluded: list[str]
    issues: list[ProductDataIssue]


class ProductDataImportRead(BaseModel):
    product_id: UUID
    bundle_id: UUID
    digest: str
    counts: dict[str, int]
    adjusted: int
    skipped: int


class ProductDataHistoryItem(BaseModel):
    occurred_at: datetime
    action: str
    status: str
    product_id: UUID | None
    product_name: str | None
    bundle_id: UUID | None
    digest: str | None
    counts: dict[str, int] = Field(default_factory=dict)
