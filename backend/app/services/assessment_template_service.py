"""Assessment template service for STRIDE and TARA methodologies.

Provides stateless rule engines for threat assessment questions and CRA criteria mapping.
"""

from typing import Any

from app.models.enums import ChangeType


class AssessmentQuestion:
    """Represents a single assessment question."""

    def __init__(
        self,
        id: str,
        text: str,
        threat_category: str,
        cra_criteria_key: str,
        hint: str | None = None,
    ) -> None:
        self.id = id
        self.text = text
        self.threat_category = threat_category
        self.cra_criteria_key = cra_criteria_key
        self.hint = hint

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "threat_category": self.threat_category,
            "cra_criteria_key": self.cra_criteria_key,
            "hint": self.hint,
        }


# STRIDE: 6 threat categories, one question per category
STRIDE_QUESTIONS = [
    AssessmentQuestion(
        id="S1",
        text="Could this change allow impersonation of users, services, or components?",
        threat_category="Spoofing",
        cra_criteria_key="increases_cybersecurity_risk",
        hint="E.g. bypassing authentication, weakening identity verification",
    ),
    AssessmentQuestion(
        id="S2",
        text="Does this change alter how data is stored, transmitted, or validated?",
        threat_category="Tampering",
        cra_criteria_key="increases_cybersecurity_risk",
        hint="E.g. changing encryption, removing integrity checks, altering data handling",
    ),
    AssessmentQuestion(
        id="S3",
        text="Could this affect logging, audit trails, or ability to trace actions?",
        threat_category="Repudiation",
        cra_criteria_key="changes_hazard_nature",
        hint="E.g. removing logs, weakening non-repudiation, hiding who did what",
    ),
    AssessmentQuestion(
        id="S4",
        text="Could this expose sensitive data to unauthorised parties?",
        threat_category="Information Disclosure",
        cra_criteria_key="expands_attack_surface",
        hint="E.g. exposing secrets, leaking user data, weakening access controls",
    ),
    AssessmentQuestion(
        id="S5",
        text="Could this affect availability, resilience, or performance of the product?",
        threat_category="Denial of Service",
        cra_criteria_key="changes_hazard_nature",
        hint="E.g. resource limits, error handling, cascade failures",
    ),
    AssessmentQuestion(
        id="S6",
        text="Could this grant unintended access, elevated privileges, or bypass controls?",
        threat_category="Elevation of Privilege",
        cra_criteria_key="expands_attack_surface",
        hint="E.g. new permissions, privilege escalation, weakened enforcement",
    ),
]

# TARA: 4 risk assessment phases
TARA_QUESTIONS = [
    AssessmentQuestion(
        id="T1",
        text="Does this change add, remove, or significantly modify a security-relevant asset?",
        threat_category="Asset Identification",
        cra_criteria_key="alters_intended_use",
        hint="E.g. new trust boundary, removed security component, reused in new context",
    ),
    AssessmentQuestion(
        id="T2",
        text="Does this change introduce new threat scenarios not covered by existing mitigations?",
        threat_category="Threat Analysis",
        cra_criteria_key="increases_cybersecurity_risk",
        hint="E.g. new attack vectors, unexpected interactions, cascade effects",
    ),
    AssessmentQuestion(
        id="T3",
        text="Does the residual risk increase after this change compared to the previous version?",
        threat_category="Risk Assessment",
        cra_criteria_key="changes_hazard_nature",
        hint="E.g. more probable harm, greater impact, weaker mitigations",
    ),
    AssessmentQuestion(
        id="T4",
        text="Does this change remove, weaken, or bypass existing security controls?",
        threat_category="Control Selection",
        cra_criteria_key="expands_attack_surface",
        hint="E.g. less strict validation, disabled checks, removed defenses",
    ),
]


class CriteriaMappingResult:
    """Result of mapping assessment answers to CRA criteria."""

    def __init__(
        self,
        alters_intended_use: bool,
        increases_cybersecurity_risk: bool,
        changes_hazard_nature: bool,
        expands_attack_surface: bool,
    ) -> None:
        self.alters_intended_use = alters_intended_use
        self.increases_cybersecurity_risk = increases_cybersecurity_risk
        self.changes_hazard_nature = changes_hazard_nature
        self.expands_attack_surface = expands_attack_surface


def get_questions(methodology: str) -> list[AssessmentQuestion]:
    """Return the list of questions for a given methodology.

    Args:
        methodology: "stride" or "tara"

    Returns:
        List of AssessmentQuestion objects
    """
    if methodology == "stride":
        return STRIDE_QUESTIONS
    elif methodology == "tara":
        return TARA_QUESTIONS
    else:
        return []


def map_answers_to_criteria(
    methodology: str,
    answers: dict[str, bool],
) -> CriteriaMappingResult:
    """Map assessment answers to CRA Article 3(3)(c) substantiality criteria.

    Args:
        methodology: "stride" or "tara"
        answers: dict mapping question IDs to boolean responses (True = yes, False/None = no)

    Returns:
        CriteriaMappingResult with the four CRA criteria as booleans
    """
    questions = get_questions(methodology)
    criteria_votes = {
        "alters_intended_use": 0,
        "increases_cybersecurity_risk": 0,
        "changes_hazard_nature": 0,
        "expands_attack_surface": 0,
    }

    # Count affirmative answers per criterion
    for question in questions:
        if answers.get(question.id, False):
            key = question.cra_criteria_key
            criteria_votes[key] += 1

    # Any "yes" answer implies the criterion is satisfied
    return CriteriaMappingResult(
        alters_intended_use=criteria_votes["alters_intended_use"] > 0,
        increases_cybersecurity_risk=criteria_votes["increases_cybersecurity_risk"] > 0,
        changes_hazard_nature=criteria_votes["changes_hazard_nature"] > 0,
        expands_attack_surface=criteria_votes["expands_attack_surface"] > 0,
    )


def recommend_actions(
    is_substantial: bool,
    change_type: ChangeType,
) -> list[str]:
    """Recommend compliance actions based on assessment outcome.

    Args:
        is_substantial: True if assessed as a substantial modification
        change_type: Type of change (feature, bugfix, security, etc.)

    Returns:
        List of action strings recommended for this change
    """
    actions: list[str] = []

    # CRA Art. 3(4): Security fixes are never substantial
    if change_type == ChangeType.security:
        return ["Review for regression risk", "Run full test suite"]

    if is_substantial:
        actions.extend([
            "Conduct risk assessment (STRIDE/TARA)",
            "Update hazard analysis",
            "Review threat model",
            "Test against compliance profile",
            "Document security change rationale",
            "Notify relevant competent authorities if applicable",
        ])
    else:
        actions.extend([
            "Document change rationale",
            "Update test coverage if applicable",
        ])

    return actions
