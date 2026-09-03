# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from app.models.annex_requirement import AnnexRequirement
from app.models.comment import Comment
from app.models.change import Change, ChangeComplianceAction, SubstantialModificationAssessment
from app.models.artifact import Artifact, ArtifactProductLink, ArtifactRevision
from app.models.audit_log_event import AuditLogEvent
from app.models.certification_record import CertificationRecord
from app.models.cvd_policy import CvdPolicy
from app.models.evidence_item import EvidenceItem
from app.models.lifecycle_notification import LifecycleNotification
from app.models.market_action import MarketAction
from app.models.manual_task import ManualTask, ManualTaskArtifactLink, TaskNotification
from app.models.maturity import MaturityAssessment, MaturityEvidenceLink, MaturityImprovementAction, MaturityModelVersion, MaturityResponse
from app.models.permission import Permission
from app.models.placeholders import DomainPlaceholder
from app.models.product import (
    Product,
    ProductRelease,
    ProductScopeEvaluation,
    RemoteProcessingElement,
)
from app.models.requirement_assessment import (
    ReleaseRequirementAssessment,
    ReleaseRequirementAssessmentSnapshot,
)
from app.models.requirement_mapping import (
    ProductRequirementDecision,
    RequirementMapping,
    RequirementMappingArtifactLink,
)
from app.models.release_gate import ReleaseGate, ReleaseGateEvidenceLink, ReleaseGateItem
from app.models.revoked_token import RevokedToken
from app.models.risk_assessment import RiskAssessment
from app.models.risk_item import RiskItem
from app.models.role_permission import RolePermission
from app.models.sbom_record import SbomRecord
from app.models.security_advisory import SecurityAdvisory
from app.models.security_update import SecurityUpdate
from app.models.support_period_record import SupportPeriodNotificationRecipient, SupportPeriodRecord
from app.models.user import Role, User, UserRole
from app.models.user_preference import UserPreference
from app.models.vulnerability_report import VulnerabilityReport
from app.models.vulnerability_priority_policy import VulnerabilityPriorityPolicy
from app.models.vulnerability_priority_evaluation import VulnerabilityPriorityEvaluation
from app.models.incident_report import IncidentReport
from app.models.sbom_vulnerability_finding import SbomVulnerabilityFinding
from app.models.sbom_scan_run import SbomScanRun
from app.models.advisory_release import AdvisoryRelease
from app.models.supplier_assessment import (AssessmentEvidenceLink, AssessmentResponse, ComponentMaintainerNotification, ProductComponentLink, Supplier, SupplierAssessment, SupplierFinding, ThirdPartyComponent)

__all__ = [
    "AnnexRequirement",
    "Comment",
    "Change",
    "ChangeComplianceAction",
    "SubstantialModificationAssessment",
    "Artifact",
    "ArtifactProductLink",
    "ArtifactRevision",
    "AuditLogEvent",
    "CertificationRecord",
    "CvdPolicy",
    "EvidenceItem",
    "LifecycleNotification",
    "MarketAction",
    "ManualTask",
    "ManualTaskArtifactLink",
    "TaskNotification",
    "MaturityAssessment",
    "MaturityEvidenceLink",
    "MaturityImprovementAction",
    "MaturityModelVersion",
    "MaturityResponse",
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
    "ReleaseRequirementAssessment",
    "ReleaseRequirementAssessmentSnapshot",
    "RequirementMapping",
    "RequirementMappingArtifactLink",
    "RevokedToken",
    "RiskAssessment",
    "RiskItem",
    "RolePermission",
    "SbomRecord",
    "SecurityAdvisory",
    "SecurityUpdate",
    "SupportPeriodRecord",
    "SupportPeriodNotificationRecipient",
    "Role",
    "User",
    "UserRole",
    "UserPreference",
    "VulnerabilityReport",
    "VulnerabilityPriorityPolicy",
    "VulnerabilityPriorityEvaluation",
    "IncidentReport",
    "SbomVulnerabilityFinding",
    "SbomScanRun",
    "AdvisoryRelease",
    "Supplier", "ThirdPartyComponent", "ProductComponentLink", "SupplierAssessment",
    "AssessmentResponse", "AssessmentEvidenceLink", "SupplierFinding",
    "ComponentMaintainerNotification",
]
