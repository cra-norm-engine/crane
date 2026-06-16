# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

# Response schemas for the GET /dashboard/journeys endpoint.
#
# A "compliance journey" is a *computed* read-model: it sequences the per-entity
# states CRANE already tracks (scope, SBOM, risk assessment, release gate, …)
# into an ordered, human-readable checklist so a user can see, per release, what
# the next step is and whether it is done. Nothing here is persisted — every
# field is derived on the fly from existing Product/ProductRelease data.

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class JourneyStepStatus(StrEnum):
    """Resolved state of a single journey step (soft guidance — never blocks)."""

    complete = "complete"
    in_progress = "in_progress"
    todo = "todo"
    blocked = "blocked"
    not_applicable = "not_applicable"


class JourneyStep(BaseModel):
    """One step in a release's compliance journey, with a deep-link to act on it."""

    # Stable identifier for the step (e.g. "cra_scope") — used by the frontend
    # for keys and to highlight the "next" step.
    id: str
    # Short title shown in the stepper (e.g. "CRA scope").
    title: str
    # One-line description of what the step covers.
    description: str
    # Derived status for this release.
    status: JourneyStepStatus
    # Imperative label for the call-to-action button (e.g. "Decide CRA scope").
    next_action: str
    # Vue route target the step links to, consumed as
    # :to="{ name, params, query, hash }". query/hash make the link land on the
    # exact section (e.g. a product page anchor or a specific gate item) so
    # navigation is precise rather than dumping the user at the top of a page.
    route_name: str
    route_params: dict[str, str] = {}
    route_query: dict[str, str] = {}
    route_hash: str | None = None


class ReleaseJourney(BaseModel):
    """The full ordered journey for a single release (or a release-less product)."""

    # Release id when the journey is anchored on a release; None for an in-scope
    # product that has no release yet (the "create a release candidate" prompt).
    release_id: UUID | None
    product_id: UUID
    product_name: str
    # Human-friendly version label (e.g. "v1.2.0") or "—" when no release exists.
    version: str
    # Raw release status string, or None for the release-less product case.
    release_status: str | None
    # Progress counters (exclude not_applicable steps from the denominator).
    completed_steps: int
    total_steps: int
    # Id of the next actionable step, or None when the journey is fully done.
    next_step_id: str | None
    steps: list[JourneyStep]
