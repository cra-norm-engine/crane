from __future__ import annotations

from enum import StrEnum


class ReleaseStatus(StrEnum):
    draft = "draft"
    in_review = "in_review"
    blocked = "blocked"
    approved = "approved"
    # Formal EU-market placement event (CRA Art. 3(20)).
    # Set separately from 'released' because internal release and market placement
    # may occur on different dates or be managed by different teams.
    placed_on_market = "placed_on_market"
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
    # Art. 13(7) + Art. 3(30): required for v2+ releases — documents whether the
    # change constitutes a substantial modification under CRA Art. 3(30).
    substantial_modification_analysis = "substantial_modification_analysis"


class VulnerabilityStatus(StrEnum):
    open = "open"
    under_review = "under_review"
    remediated = "remediated"
    accepted_risk = "accepted_risk"


# Gap 6 — Annex I Part II §2/§5: full lifecycle from first report to retirement.
class VulnerabilityLifecycleStatus(StrEnum):
    reported = "reported"
    triaged = "triaged"
    fix_in_progress = "fix_in_progress"
    fixed = "fixed"
    embargo = "embargo"
    disclosed = "disclosed"
    retired = "retired"


# Gap 2 — CVD policy publication state.
class CvdPolicyStatus(StrEnum):
    draft = "draft"
    active = "active"
    archived = "archived"


# Gap 3 — Security advisory publication state (includes embargo phase, Gap 7).
class AdvisoryStatus(StrEnum):
    draft = "draft"
    embargo = "embargo"
    published = "published"
    archived = "archived"


# Gap 10 — Machine-readable SBOM format (Annex I Part II §1).
class SbomFormat(StrEnum):
    cyclonedx = "cyclonedx"
    spdx = "spdx"
    swid = "swid"
    other = "other"


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


class AssessmentMethodology(StrEnum):
    stride = "stride"
    tara = "tara"
    custom = "custom"


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
    security_update_available = "security_update_available"


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


class ChangeType(StrEnum):
    """
    Type of change being recorded against a product version.
    'security' = security patch/fix (never substantial by definition under CRA)
    'feature'  = new capability (may expand attack surface → could be substantial)
    'repair'   = non-security bug fix
    'maintenance' = internal refactor, dependency update, etc.
    """
    security = "security"
    feature = "feature"
    repair = "repair"
    maintenance = "maintenance"


class ChangeStatus(StrEnum):
    """
    Lifecycle states for a change record.
    Transitions: draft → submitted → under_review → assessed → action_required | closed
    'action_required' is only reached when the assessment decides is_substantial = True.
    """
    draft = "draft"
    submitted = "submitted"
    under_review = "under_review"
    assessed = "assessed"
    action_required = "action_required"
    closed = "closed"


class ComplianceActionType(StrEnum):
    """
    Required follow-up actions when a change is deemed substantial.
    These correspond to the CRA obligations that must be re-satisfied.
    """
    renew_conformity_assessment = "renew_conformity_assessment"
    update_technical_docs = "update_technical_docs"
    update_declaration_of_conformity = "update_declaration_of_conformity"
    re_release_product = "re_release_product"


class ComplianceActionStatus(StrEnum):
    """Completion state of a single compliance action item."""
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


# CRA Art. 35 — market action types covering both voluntary/mandatory recalls
# and withdrawals of non-compliant products.
class MarketActionType(StrEnum):
    recall = "recall"
    withdrawal = "withdrawal"


class MarketActionStatus(StrEnum):
    draft = "draft"
    active = "active"
    authority_notified = "authority_notified"
    closed = "closed"


class RemoteProcessingElementType(StrEnum):
    """Type of remote processing element — used to guide CRA Art. 3(2) scope determination."""
    saas            = "saas"
    internal_cloud  = "internal_cloud"
    external_api    = "external_api"
    backend_service = "backend_service"
    data_processing = "data_processing"
    firmware_update = "firmware_update"
    other           = "other"


class RemoteProcessingClassification(StrEnum):
    """
    CRA Art. 3(2) scope classification for a remote processing element.
    Determined by the guided evaluation wizard (decision tree).
    """
    not_assessed              = "not_assessed"
    cra_art_3_2_in_scope      = "cra_art_3_2_in_scope"
    third_party_component     = "third_party_component"
    out_of_scope              = "out_of_scope"
    requires_legal_assessment = "requires_legal_assessment"


class VexStatus(StrEnum):
    """
    Vulnerability Exploitability eXchange (VEX) status values.
    Indicates whether a vulnerability is exploitable in a specific product context.
    """
    under_investigation = "under_investigation"
    affected = "affected"          # Exploitable under product's operational conditions
    not_affected = "not_affected"  # Present but not exploitable (e.g., unused code path)
    fixed = "fixed"                # Was exploitable; remediated in this or a newer release


class VulnerabilitySource(StrEnum):
    """Origin of a vulnerability report."""
    manual = "manual"       # Created by a user manually
    sbom_scan = "sbom_scan" # Auto-created from an SBOM component scan via OSV API


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
    change = "change"
    substantial_modification_assessment = "substantial_modification_assessment"
    change_compliance_action = "change_compliance_action"
    cvd_policy = "cvd_policy"
    security_advisory = "security_advisory"
    vulnerability_report = "vulnerability_report"
    sbom_record = "sbom_record"
    market_action = "market_action"
    comment = "comment"
    sbom_vulnerability_finding = "sbom_vulnerability_finding"
