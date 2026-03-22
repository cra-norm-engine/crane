from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import EvidenceType

DOMAIN_ENTITY_NAMES: tuple[str, ...] = (
    "Product",
    "ProductRelease",
    "RemoteProcessingElement",
    "ThirdPartyComponent",
    "SbomDocument",
    "RiskAssessment",
    "RiskItem",
    "AnnexRequirement",
    "RequirementMapping",
    "SecurityTestPlan",
    "SecurityTestReport",
    "EvidenceItem",
    "SupportPeriodRecord",
    "SecurityUpdate",
    "ReleaseGateResult",
    "SubstantialModificationAssessment",
    "TechnicalDocumentationBundle",
    "UserInformationDocument",
    "DeclarationOfConformity",
    "AuthorityResponsePackage",
    "AuditLogEvent",
    "NonConformityIncident",
    "CorrectiveAction",
    "WithdrawalRecord",
    "RecallRecord",
    "RetentionPolicy",
    "StandardLibraryEntry",
    "StandardClauseMapping",
    "StandardsProfile",
)


class DomainPlaceholder(UUIDTimestampMixin, Base):
    __tablename__ = "domain_placeholders"

    entity_name: Mapped[str] = mapped_column(String(120), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[EvidenceType | None] = mapped_column(nullable=True)