# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

# Compliance Journey read-model.
#
# This service computes a *guided, soft* step-by-step roadmap for getting a
# release CRA-ready. It does NOT store anything and does NOT enforce ordering —
# it simply derives, from the per-entity states CRANE already tracks, the answer
# to "what is the next step, and is it done?" for each active release.
#
# The 12 steps mirror the real manufacturer workflow:
#   product setup (1-4) → release work (5-12). Steps 1-4 read from the parent
# product, so they show as already done for an established product line.

import logging
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.enums import (
    ArtifactReviewDecision,
    ReleaseGateItemCode,
    ReleaseGateWorkflowStatus,
    ReleaseStatus,
    RequirementApplicabilityDecision,
    RiskAssessmentStatus,
)
from app.models.product import Product, ProductRelease, RemoteProcessingElement
from app.models.requirement_mapping import ProductRequirementDecision
from app.schemas.release_journey import (
    JourneyStep,
    JourneyStepStatus,
    ReleaseJourney,
)

logger = logging.getLogger(__name__)

# Release statuses that mean the journey is over and should drop off the widget.
_FINISHED_RELEASE_STATUSES = {
    ReleaseStatus.withdrawn,
    ReleaseStatus.recalled,
    ReleaseStatus.end_of_support,
}

# Gate item statuses that count as "evidence has been submitted for review".
_SUBMITTED_REVIEW = {
    ArtifactReviewDecision.accepted,
    ArtifactReviewDecision.rejected,
    ArtifactReviewDecision.needs_update,
    ArtifactReviewDecision.waived,
}

# Gate item statuses that count as a satisfied (accepted) requirement.
_SATISFIED_REVIEW = {ArtifactReviewDecision.accepted, ArtifactReviewDecision.waived}


# Ordered catalog of step metadata. Status is computed per release below; this
# table only holds the static parts (id, title, description, level).
# level: "product" → derived from the parent product; "release" → from the release.
#
# Note: "Create product" is deliberately NOT a step. A journey only exists for an
# already-registered product, so it would always be complete (noise). Product
# creation is a precondition handled by the page's empty state instead.
_STEP_CATALOG: list[dict[str, str]] = [
    {"id": "remote_processing", "title": "Remote processing solution", "level": "product",
     "description": "Identify and classify any remote data processing (CRA Art. 3(2))."},
    {"id": "cra_scope", "title": "CRA scope", "level": "product",
     "description": "Decide whether the product is in scope of the CRA."},
    {"id": "support_period", "title": "Support period", "level": "product",
     "description": "Define the security support period (CRA Art. 13(8))."},
    {"id": "create_release", "title": "Create release candidate", "level": "release",
     "description": "Create the release/version to take through conformity."},
    {"id": "risk_assessment", "title": "Perform risk assessment", "level": "release",
     "description": "Complete and approve a risk assessment for the release."},
    {"id": "annex_mapping", "title": "Annex I mapping", "level": "release",
     "description": "Decide applicability and evidence for each Annex I requirement."},
    {"id": "artifact_submission", "title": "Artifact submission", "level": "release",
     "description": "Attach evidence to the release gate checklist items."},
    {"id": "technical_documentation", "title": "Compile technical documentation", "level": "release",
     "description": "Provide the technical documentation (CRA Annex VII)."},
    {"id": "declaration_of_conformity", "title": "Declaration of Conformity", "level": "release",
     "description": "Draw up the EU Declaration of Conformity (CRA Art. 28)."},
    {"id": "approve_release", "title": "Approve release", "level": "release",
     "description": "Clear the release gate (no known exploitable vulnerabilities)."},
    {"id": "placement_date", "title": "Determine placement-on-market date", "level": "release",
     "description": "Record the EU market placement date (CRA Art. 3(20))."},
]


def _step(
    spec: dict[str, str],
    status: JourneyStepStatus,
    next_action: str,
    route_name: str,
    route_params: dict[str, str],
    route_query: dict[str, str] | None = None,
    route_hash: str | None = None,
) -> JourneyStep:
    """Assemble a JourneyStep from its static spec plus the computed status/CTA."""
    return JourneyStep(
        id=spec["id"],
        title=spec["title"],
        description=spec["description"],
        status=status,
        next_action=next_action,
        route_name=route_name,
        route_params=route_params,
        route_query=route_query or {},
        route_hash=route_hash,
    )


def _product_steps(product: Product) -> tuple[list[JourneyStep], bool]:
    """
    Compute the four product-level steps. Returns the steps plus a flag telling
    whether the product is explicitly out of scope (which makes every release
    step not_applicable).
    """
    spec_by_id = {s["id"]: s for s in _STEP_CATALOG}
    pid = {"productId": str(product.id)}
    steps: list[JourneyStep] = []

    # Remote processing solution — every element must be classified. A product
    #    with no remote processing has nothing to assess, so it is complete.
    elements = list(product.remote_processing_elements)
    unassessed = sum(1 for e in elements if _rpe_unassessed(e))
    if not elements or unassessed == 0:
        rpe_status = JourneyStepStatus.complete
    elif unassessed == len(elements):
        rpe_status = JourneyStepStatus.todo
    else:
        rpe_status = JourneyStepStatus.in_progress
    steps.append(_step(spec_by_id["remote_processing"], rpe_status,
                       "Classify remote processing", "product-detail", pid,
                       route_hash="#remote-processing"))

    # CRA scope — decided once scope_status is no longer "undecided".
    scope = (product.scope_status or "undecided").lower()
    out_of_scope = scope == "out_of_scope"
    scope_status = JourneyStepStatus.complete if scope != "undecided" else JourneyStepStatus.todo
    steps.append(_step(spec_by_id["cra_scope"], scope_status,
                       "Decide CRA scope", "product-detail", pid,
                       route_hash="#cra-scope"))

    # Support period — at least one active support period record.
    has_support = any(r.is_active for r in product.support_period_records)
    support_status = JourneyStepStatus.complete if has_support else JourneyStepStatus.todo
    steps.append(_step(spec_by_id["support_period"], support_status,
                       "Define support period", "product-detail", pid,
                       route_hash="#support-periods"))

    return steps, out_of_scope


def _rpe_unassessed(element: RemoteProcessingElement) -> bool:
    """True when a remote processing element still needs classification."""
    # classification is stored as the enum value "not_assessed" until evaluated.
    return str(element.classification) in ("not_assessed", "RemoteProcessingClassification.not_assessed")


def _release_steps(
    release: ProductRelease,
    *,
    annex_total: int,
    annex_undecided: int,
    out_of_scope: bool,
) -> list[JourneyStep]:
    """Compute the eight release-level steps for a single release."""
    spec_by_id = {s["id"]: s for s in _STEP_CATALOG}
    rid = {"releaseId": str(release.id)}
    pid = {"productId": str(release.product_id)}
    na = JourneyStepStatus.not_applicable
    steps: list[JourneyStep] = []

    # When the product is out of scope, the release work simply does not apply.
    if out_of_scope:
        for sid in ("create_release", "risk_assessment", "annex_mapping",
                    "artifact_submission", "technical_documentation",
                    "declaration_of_conformity", "approve_release", "placement_date"):
            steps.append(_step(spec_by_id[sid], na, "Not applicable (out of scope)",
                               "product-detail", pid))
        return steps

    # Create release candidate — the release exists by definition here; the
    # release page (the gate view) is the release itself.
    steps.append(_step(spec_by_id["create_release"], JourneyStepStatus.complete,
                       "Open release", "release-gate", rid))

    # Risk assessment — complete when any linked assessment is approved.
    # Deep-link to the specific assessment when one exists; otherwise to the
    # risk-assessments list where a new one is created.
    assessments = list(release.risk_assessments)
    approved = [a for a in assessments if a.status == RiskAssessmentStatus.approved]
    pending = [a for a in assessments if a.status != RiskAssessmentStatus.approved]
    if approved:
        ra_status = JourneyStepStatus.complete
        ra_route, ra_params = "risk-assessment-detail", {"assessmentId": str(approved[0].id)}
    elif pending:
        ra_status = JourneyStepStatus.in_progress
        ra_route, ra_params = "risk-assessment-detail", {"assessmentId": str(pending[0].id)}
    else:
        ra_status = JourneyStepStatus.todo
        ra_route, ra_params = "risk-assessments", {}
    steps.append(_step(spec_by_id["risk_assessment"], ra_status,
                       "Complete risk assessment", ra_route, ra_params))

    # Annex I mapping — deep-link to the matrix pre-filtered to this product+release.
    if annex_total == 0:
        annex_status = JourneyStepStatus.todo
    elif annex_undecided > 0:
        annex_status = JourneyStepStatus.in_progress
    else:
        annex_status = JourneyStepStatus.complete
    steps.append(_step(spec_by_id["annex_mapping"], annex_status,
                       "Map Annex I requirements", "annex-matrix", {},
                       route_query={
                           "product_id": str(release.product_id),
                           "release_id": str(release.id),
                       }))

    # Gate-derived steps (8-11). Index items by their code for quick lookup.
    gate = release.release_gate
    items_by_code: dict[ReleaseGateItemCode, object] = {}
    required_items: list[object] = []
    if gate is not None:
        for item in gate.items:
            if item.code is not None:
                items_by_code[item.code] = item
            if item.is_required:
                required_items.append(item)

    # 8. Artifact submission — required gate items have evidence submitted.
    if gate is None or not required_items:
        submit_status = JourneyStepStatus.todo
    else:
        submitted = sum(1 for i in required_items if i.status in _SUBMITTED_REVIEW)
        if submitted == len(required_items):
            submit_status = JourneyStepStatus.complete
        elif submitted > 0:
            submit_status = JourneyStepStatus.in_progress
        else:
            submit_status = JourneyStepStatus.todo
    steps.append(_step(spec_by_id["artifact_submission"], submit_status,
                       "Submit gate evidence", "release-gate", rid,
                       route_hash="#evidence-checklist"))

    # Technical documentation — the dedicated gate item is accepted/waived.
    steps.append(_step(
        spec_by_id["technical_documentation"],
        _gate_item_status(items_by_code.get(ReleaseGateItemCode.technical_documentation)),
        "Compile technical documentation", "release-gate", rid,
        route_hash="#gate-item-technical_documentation",
    ))

    # Declaration of Conformity — gate item accepted AND DoC metadata present.
    doc_item_status = _gate_item_status(items_by_code.get(ReleaseGateItemCode.declaration_of_conformity))
    doc_metadata = bool(release.eu_doc_date and release.eu_doc_number)
    if doc_item_status == JourneyStepStatus.complete and doc_metadata:
        doc_status = JourneyStepStatus.complete
    elif doc_item_status == JourneyStepStatus.complete or doc_metadata:
        doc_status = JourneyStepStatus.in_progress
    else:
        doc_status = JourneyStepStatus.todo
    steps.append(_step(spec_by_id["declaration_of_conformity"], doc_status,
                       "Draw up Declaration of Conformity", "release-gate", rid,
                       route_hash="#gate-item-declaration_of_conformity"))

    # Approve release — gate workflow status, blocked by known exploitable vulns.
    approve_hash: str | None = "#gate-actions"
    if release.has_known_exploitable_vulnerabilities:
        # Legal blocker (CRA Annex I Part I §2(a)): cannot ship with known KEVs.
        approve_status = JourneyStepStatus.blocked
        approve_action = "Resolve known exploitable vulnerabilities"
        approve_route, approve_params = "vulnerability-handling", {}
        approve_hash = None
    elif gate is None:
        approve_status, approve_action = JourneyStepStatus.todo, "Open the release gate"
        approve_route, approve_params = "release-gate", rid
    else:
        approve_action, approve_route, approve_params = "Approve the release gate", "release-gate", rid
        if gate.status == ReleaseGateWorkflowStatus.approved:
            approve_status = JourneyStepStatus.complete
        elif gate.status == ReleaseGateWorkflowStatus.blocked:
            approve_status = JourneyStepStatus.blocked
        elif gate.status == ReleaseGateWorkflowStatus.in_review:
            approve_status = JourneyStepStatus.in_progress
        else:
            approve_status = JourneyStepStatus.todo
    steps.append(_step(spec_by_id["approve_release"], approve_status,
                       approve_action, approve_route, approve_params,
                       route_hash=approve_hash))

    # Placement-on-market date — recorded on the release form (product page),
    # not the gate. Deep-link to the product's Releases section.
    placement_status = (
        JourneyStepStatus.complete if release.placed_on_market_date else JourneyStepStatus.todo
    )
    steps.append(_step(spec_by_id["placement_date"], placement_status,
                       "Record placement-on-market date", "product-detail", pid,
                       route_hash="#releases"))

    return steps


def _gate_item_status(item: object | None) -> JourneyStepStatus:
    """Map a single gate item's review decision onto a journey step status."""
    if item is None:
        return JourneyStepStatus.todo
    status = getattr(item, "status", None)
    if status in _SATISFIED_REVIEW:
        return JourneyStepStatus.complete
    if status == ArtifactReviewDecision.pending_review or status is None:
        return JourneyStepStatus.todo
    # rejected / needs_update → work is underway but not yet accepted.
    return JourneyStepStatus.in_progress


def _assemble_journey(
    *,
    product: Product,
    release: ProductRelease | None,
    annex_total: int,
    annex_undecided: int,
) -> ReleaseJourney:
    """Combine product + release steps into a single ordered journey object."""
    product_steps, out_of_scope = _product_steps(product)

    if release is not None:
        release_steps = _release_steps(
            release,
            annex_total=annex_total,
            annex_undecided=annex_undecided,
            out_of_scope=out_of_scope,
        )
        version = f"v{release.system_version}" if getattr(release, "system_version", None) else "—"
        release_status: str | None = str(release.release_status)
        release_id: UUID | None = release.id
    else:
        # In-scope product with no release yet: prompt to create a candidate,
        # and mark the remaining release work not_applicable until one exists.
        spec_by_id = {s["id"]: s for s in _STEP_CATALOG}
        pid = {"productId": str(product.id)}
        release_steps = [_step(spec_by_id["create_release"], JourneyStepStatus.todo,
                               "Create a release candidate", "product-detail", pid,
                               route_hash="#releases")]
        for sid in ("risk_assessment", "annex_mapping", "artifact_submission",
                    "technical_documentation", "declaration_of_conformity",
                    "approve_release", "placement_date"):
            release_steps.append(_step(spec_by_id[sid], JourneyStepStatus.not_applicable,
                                       "Create a release first", "product-detail", pid))
        version = "—"
        release_status = None
        release_id = None

    steps = product_steps + release_steps

    # Progress: count complete steps; exclude not_applicable from the total.
    applicable = [s for s in steps if s.status != JourneyStepStatus.not_applicable]
    completed = sum(1 for s in applicable if s.status == JourneyStepStatus.complete)
    next_step_id = next(
        (s.id for s in steps if s.status in (
            JourneyStepStatus.todo, JourneyStepStatus.in_progress, JourneyStepStatus.blocked
        )),
        None,
    )

    return ReleaseJourney(
        release_id=release_id,
        product_id=product.id,
        product_name=product.name,
        version=version,
        release_status=release_status,
        completed_steps=completed,
        total_steps=len(applicable),
        next_step_id=next_step_id,
        steps=steps,
    )


# Loader options shared by every release query, so a journey can be computed
# without N+1 round-trips for the product, risk assessments and gate.
def _release_load_options() -> tuple:
    return (
        joinedload(ProductRelease.product).selectinload(Product.remote_processing_elements),
        joinedload(ProductRelease.product).selectinload(Product.support_period_records),
        selectinload(ProductRelease.risk_assessments),
        selectinload(ProductRelease.release_gate),
    )


def _annex_counts(
    db: Session, release_ids: list[UUID]
) -> tuple[dict[UUID, int], dict[UUID, int]]:
    """Bulk-load Annex I requirement-decision totals/undecided counts per release."""
    total: dict[UUID, int] = {}
    undecided: dict[UUID, int] = {}
    if not release_ids:
        return total, undecided
    rows = db.execute(
        select(
            ProductRequirementDecision.product_release_id,
            func.count().label("total"),
            # Count rows still left undecided for this release.
            func.sum(
                case(
                    (
                        ProductRequirementDecision.applicability_decision
                        == RequirementApplicabilityDecision.undecided,
                        1,
                    ),
                    else_=0,
                )
            ).label("undecided"),
        )
        .where(ProductRequirementDecision.product_release_id.in_(release_ids))
        .group_by(ProductRequirementDecision.product_release_id)
    ).all()
    for release_id, total_count, undecided_count in rows:
        total[release_id] = int(total_count or 0)
        undecided[release_id] = int(undecided_count or 0)
    return total, undecided


def _journeys_from_releases(
    db: Session, releases: list[ProductRelease]
) -> list[ReleaseJourney]:
    """Assemble a journey for each release, sharing one Annex-count query."""
    total, undecided = _annex_counts(db, [r.id for r in releases])
    return [
        _assemble_journey(
            product=r.product,
            release=r,
            annex_total=total.get(r.id, 0),
            annex_undecided=undecided.get(r.id, 0),
        )
        for r in releases
    ]


def _release_less_product_journey(db: Session, product_id: UUID) -> list[ReleaseJourney]:
    """Journey for a product that has no release yet (prompts step 5)."""
    product = (
        db.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.remote_processing_elements),
                selectinload(Product.support_period_records),
            )
        )
        .unique()
        .scalar_one_or_none()
    )
    if product is None:
        return []
    return [_assemble_journey(product=product, release=None, annex_total=0, annex_undecided=0)]


def list_journeys(
    db: Session,
    *,
    product_id: UUID | None = None,
    release_id: UUID | None = None,
) -> list[ReleaseJourney]:
    """
    Return compliance journeys, optionally filtered.

    - release_id set → exactly that release's journey (any status).
    - product_id set → every release of that product (any status), newest first;
      or the "create a release candidate" prompt if it has none.
    - neither → the active overview (see list_active_release_journeys).
    """
    if release_id is not None:
        release = (
            db.execute(
                select(ProductRelease)
                .where(ProductRelease.id == release_id)
                .options(*_release_load_options())
            )
            .unique()
            .scalar_one_or_none()
        )
        return _journeys_from_releases(db, [release]) if release is not None else []

    if product_id is not None:
        releases = list(
            db.execute(
                select(ProductRelease)
                .where(ProductRelease.product_id == product_id)
                .options(*_release_load_options())
                .order_by(ProductRelease.system_version.desc())
            )
            .unique()
            .scalars()
            .all()
        )
        if releases:
            return _journeys_from_releases(db, releases)
        return _release_less_product_journey(db, product_id)

    return list_active_release_journeys(db)


def list_active_release_journeys(db: Session, limit: int = 5) -> list[ReleaseJourney]:
    """
    Build compliance journeys for the active overview (default, unfiltered view).

    Includes (a) active releases not yet finished and still having a next step,
    and (b) in-scope products that have no active release yet (so the "create a
    release candidate" prompt shows). All relationships are eager-loaded.
    """
    finished = [s.value for s in _FINISHED_RELEASE_STATUSES]

    # (a) Active releases, newest first, with everything the journey needs.
    releases = list(
        db.execute(
            select(ProductRelease)
            .where(ProductRelease.release_status.notin_(finished))
            .options(*_release_load_options())
            .order_by(ProductRelease.created_at.desc())
        )
        .unique()
        .scalars()
        .all()
    )

    journeys: list[ReleaseJourney] = []
    products_with_release: set[UUID] = set()
    for journey in _journeys_from_releases(db, releases):
        products_with_release.add(journey.product_id)
        # Drop releases whose journey is fully done — nothing left to guide.
        if journey.next_step_id is not None:
            journeys.append(journey)

    # (b) In-scope products without any active release → show step-5 guidance.
    if len(journeys) < limit:
        product_stmt = (
            select(Product)
            .where(Product.scope_status == "in_scope")
            .options(
                selectinload(Product.remote_processing_elements),
                selectinload(Product.support_period_records),
            )
        )
        for product in db.execute(product_stmt).unique().scalars().all():
            if product.id in products_with_release:
                continue
            journeys.append(_assemble_journey(
                product=product, release=None, annex_total=0, annex_undecided=0,
            ))

    return journeys[:limit]
