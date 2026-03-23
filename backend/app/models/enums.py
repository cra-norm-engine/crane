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


class EvidenceType(StrEnum):
    document = "document"
    test_report = "test_report"
    sbom = "sbom"
    screenshot = "screenshot"
    link = "link"
    declaration = "declaration"
    annex_output = "annex_output"
    authority_package = "authority_package"


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


class AuditStatus(StrEnum):
    success = "success"
    failure = "failure"


class EntityType(StrEnum):
    user = "user"
    role = "role"
    product = "product"
    release = "release"
    audit_log_event = "audit_log_event"