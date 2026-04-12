from app.models.artifact import Artifact, ArtifactProductLink, ArtifactRevision
from app.models.audit_log_event import AuditLogEvent
from app.models.lifecycle_notification import LifecycleNotification
from app.models.placeholders import DomainPlaceholder
from app.models.product import (
    Product,
    ProductRelease,
    ProductScopeEvaluation,
    RemoteProcessingElement,
)
from app.models.requirement_mapping import (
    ProductRequirementDecision,
    RequirementMapping,
    RequirementMappingArtifactLink,
)
from app.models.release_gate import ReleaseGate, ReleaseGateEvidenceLink, ReleaseGateItem
from app.models.risk_assessment import RiskAssessment
from app.models.risk_item import RiskItem
from app.models.annex_requirement import AnnexRequirement
from app.models.evidence_item import EvidenceItem
from app.models.security_update import SecurityUpdate
from app.models.support_period_record import SupportPeriodNotificationRecipient, SupportPeriodRecord
from app.models.user import Role, User, UserRole
from app.models.permission import Permission
from app.models.role_permission import RolePermission

from app.models.annex_requirement import AnnexRequirement
from app.models.artifact import Artifact, ArtifactProductLink, ArtifactRevision
from app.models.audit_log_event import AuditLogEvent
from app.models.evidence_item import EvidenceItem
from app.models.lifecycle_notification import LifecycleNotification
from app.models.permission import Permission
from app.models.placeholders import DomainPlaceholder
from app.models.product import (
    Product,
    ProductRelease,
    ProductScopeEvaluation,
    RemoteProcessingElement,
)
from app.models.requirement_mapping import (
    ProductRequirementDecision,
    RequirementMapping,
    RequirementMappingArtifactLink,
)
from app.models.release_gate import ReleaseGate, ReleaseGateEvidenceLink, ReleaseGateItem
from app.models.risk_assessment import RiskAssessment
from app.models.risk_item import RiskItem
from app.models.role_permission import RolePermission
from app.models.security_update import SecurityUpdate
from app.models.support_period_record import SupportPeriodNotificationRecipient, SupportPeriodRecord
from app.models.user import Role, User, UserRole

__all__ = [
    "AnnexRequirement",
    "Artifact",
    "ArtifactProductLink",
    "ArtifactRevision",
    "AuditLogEvent",
    "EvidenceItem",
    "LifecycleNotification",
    "Permission",
    "DomainPlaceholder",
    "Product",
    "ProductRelease",
    "ProductScopeEvaluation",
    "ReleaseGate",
    "ReleaseGateEvidenceLink",
    "ReleaseGateItem",
    "RemoteProcessingElement",
    "ProductRequirementDecision",
    "RequirementMapping",
    "RequirementMappingArtifactLink",
    "RiskAssessment",
    "RiskItem",
    "RolePermission",
    "SecurityUpdate",
    "SupportPeriodRecord",
    "SupportPeriodNotificationRecipient",
    "Role",
    "User",
    "UserRole",
]
