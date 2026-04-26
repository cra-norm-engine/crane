from __future__ import annotations

from enum import StrEnum


class ReleaseStatus(StrEnum):
    draft = "draft"
    in_review = "in_review"
    blocked = "blocked"
    approved = "approved"
    released = "released"
    withdrawn = "withdrawn"
    recalled = "recalled"
    end_of_support = "end_of_support"


class GateStatus(StrEnum):
    pass_ = "pass"
    fail = "fail"
    warning = "warning"


class RiskLevel(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AssessmentStatus(StrEnum):
    draft = "draft"
    active = "active"
    accepted = "accepted"
    archived = "archived"


class RiskAssessmentStatus(StrEnum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    archived = "archived"


class RiskItemStatus(StrEnum):
    open = "open"
    in_progress = "in_progress"
    mitigated = "mitigated"
    accepted = "accepted"
    closed = "closed"


class RequirementImplementationStatus(StrEnum):
    planned = "planned"
    in_progress = "in_progress"
    implemented = "implemented"
    verified = "verified"
    not_applicable = "not_applicable"


class AnnexPart(StrEnum):
    part_i = "part_i"
    part_ii = "part_ii"


class RequirementApplicabilityDecision(StrEnum):
    undecided = "undecided"
    applicable = "applicable"
    not_applicable = "not_applicable"


class SdlActivity(StrEnum):
    requirements = "requirements"
    design = "design"
    implementation = "implementation"
    verification = "verification"
    validation = "validation"
    vulnerability_management = "vulnerability_management"
    documentation = "documentation"
    post_market = "post_market"


class EvidenceType(StrEnum):
    document = "document"
    test_report = "test_report"
    sbom = "sbom"
    screenshot = "screenshot"
    link = "link"
    declaration = "declaration"
    annex_output = "annex_output"
    authority_package = "authority_package"


class ArtifactSourceType(StrEnum):
    upload = "upload"
    external_link = "external_link"


class ArtifactReviewDecision(StrEnum):
    pending_review = "pending_review"
    accepted = "accepted"
    rejected = "rejected"
    needs_update = "needs_update"
    waived = "waived"


class ReleaseGateWorkflowStatus(StrEnum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    blocked = "blocked"


class ReleaseGateItemCode(StrEnum):
    technical_documentation = "technical_documentation"
    risk_assessment = "risk_assessment"
    sbom = "sbom"
    test_report = "test_report"
    declaration_of_conformity = "declaration_of_conformity"
    annex_mapping = "annex_mapping"


class VulnerabilityStatus(StrEnum):
    open = "open"
    under_review = "under_review"
    remediated = "remediated"
    accepted_risk = "accepted_risk"


class ProductClassification(StrEnum):
    normal = "normal"
    important_class_1 = "important_class_1"
    important_class_2 = "important_class_2"
    critical = "critical"


class ConformityRoute(StrEnum):
    self_assessment = "self_assessment"
    third_party_assessment = "third_party_assessment"
    not_applicable = "not_applicable"
    undecided = "undecided"


class SupportType(StrEnum):
    standard = "standard"
    limited = "limited"
    extended = "extended"
    custom = "custom"


class DistributionMechanism(StrEnum):
    automatic_update = "automatic_update"
    in_app_update = "in_app_update"
    package_repository = "package_repository"
    vendor_download = "vendor_download"
    manual_install = "manual_install"
    field_service = "field_service"
    other = "other"


class SecurityUpdateSeverity(StrEnum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    informational = "informational"


class LifecycleNotificationType(StrEnum):
    end_of_support_upcoming = "end_of_support_upcoming"


class LifecycleNotificationStatus(StrEnum):
    pending = "pending"
    sent = "sent"
    dismissed = "dismissed"


class AuditActionType(StrEnum):
    login = "login"
    logout = "logout"
    failed_login = "failed_login"
    create = "create"
    update = "update"
    delete = "delete"
    export = "export"
    release_approval = "release_approval"
    release_block = "release_block"
    role_change = "role_change"
    duplicate = "duplicate"
    approve = "approve"
    notify = "notify"


class AuditStatus(StrEnum):
    success = "success"
    failure = "failure"


class AuthProvider(StrEnum):
    local = "local"
    ldap = "ldap"


class CertificationScheme(StrEnum):
    eu_cybersecurity_act = "eu_cybersecurity_act"
    iec_62443 = "iec_62443"
    common_criteria = "common_criteria"
    etsi_en_303_645 = "etsi_en_303_645"
    iso_iec_27001 = "iso_iec_27001"
    soc2 = "soc2"
    other = "other"


class CertificationStatus(StrEnum):
    pending = "pending"
    active = "active"
    expired = "expired"
    suspended = "suspended"
    withdrawn = "withdrawn"


class EntityType(StrEnum):
    user = "user"
    role = "role"
    product = "product"
    product_release = "product_release"
    remote_processing_element = "remote_processing_element"
    product_scope_evaluation = "product_scope_evaluation"
    audit_log_event = "audit_log_event"
    risk_assessment = "risk_assessment"
    risk_item = "risk_item"
    annex_requirement = "annex_requirement"
    requirement_mapping = "requirement_mapping"
    evidence_item = "evidence_item"
    support_period_record = "support_period_record"
    security_update = "security_update"
    lifecycle_notification = "lifecycle_notification"
    certification_record = "certification_record"
