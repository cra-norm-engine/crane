# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""
Schemas for the compliance-readiness metric.

Readiness/coverage is a *per-release* property: each release has its own Annex I
requirement decisions and its own approval. So readiness is reported per release
(ReleaseReadinessRead), grouped under a product (ProductReadinessRead). Coverage
reuses the same "finalized" rule the requirement matrix enforces
(RequirementMappingService._is_finalized), so the numbers can never disagree.

Where a single product-level figure is unavoidable (the dashboard pie), the
*latest released* release (newest release whose status is on-market) represents
the product — not the highest version number, which may be an unreleased draft.
"""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class ReadinessCoverage(BaseModel):
    """Annex I Part I coverage for a single release."""

    total: int          # active Annex I Part I requirements (the denominator)
    assessed: int       # requirements with an applicability decision made
    met: int            # requirements fully handled per the finalize rule
    assessed_pct: int   # 0 when total == 0
    met_pct: int


class ReleaseReadinessRead(BaseModel):
    """Readiness of one release (the honest 1:1 unit)."""

    release_id: UUID
    # Human label ("Spring 2026") when set, else "v{system_version}".
    version_label: str
    system_version: int
    release_status: str
    # True for on-market statuses (placed_on_market / released).
    is_released: bool
    coverage: ReadinessCoverage
    # not_started | in_progress | substantially_ready | ready
    state: str
    # Requirement assessment for THIS release is formally approved.
    is_approved: bool = False


class ProductReadinessRead(BaseModel):
    """A product grouping its releases' readiness."""

    product_id: UUID
    product_code: str
    name: str
    scope_status: str

    # Every release, newest first, each with its own readiness.
    releases: list[ReleaseReadinessRead] = []
    # The release that represents the product for roll-ups: the latest *released*
    # one (fallback: latest by version). None when the product has no releases.
    representative_release_id: UUID | None = None
    # Convenience: is the representative release approved (drives conformance).
    is_conformant: bool = False

    # Secondary operational signals — product-scoped, informational only; they
    # never change any coverage percentage.
    has_open_critical_vuln: bool = False
    open_critical_vuln_count: int = 0
    risk_unapproved: bool = False
    support_expired: bool = False
    change_action_required: bool = False
    supplier_due_diligence_gap: bool = False


class ConformanceSummary(BaseModel):
    """
    High-level portfolio conformance for the dashboard pie.

    A product is *conformant* when its **latest released** release has an APPROVED
    requirement assessment. Out-of-scope products (and products with nothing yet
    on the market) carry no market obligation and are excluded from the
    percentage (reported separately for context).
    """

    total: int              # all products
    in_scope: int           # in-scope products with a released release (counted)
    out_of_scope: int       # excluded: out-of-scope OR nothing released yet
    conformant: int         # counted + latest released release approved
    not_conformant: int     # counted but latest released release not approved
    conformant_pct: int     # 0 when in_scope == 0
