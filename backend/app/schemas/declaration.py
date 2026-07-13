# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""Schemas for the EU Declaration of Conformity workflow and listing page."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DeclarationSummaryRead(BaseModel):
    """One row on the top-level Declarations page: a release + its DoC status."""

    release_id: UUID
    product_id: UUID
    product_name: str
    product_code: str
    system_version: int
    version_label: str
    doc_status: str  # DocStatus value: draft | approved | signed
    doc_number: str | None = None
    doc_date: date | None = None
    signatory: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    signed_at: datetime | None = None


class DeclarationUpdate(BaseModel):
    """Editable EU DoC fields (Annex V). Only allowed while the DoC is in draft."""

    eu_doc_number: str | None = Field(default=None, max_length=100)
    eu_doc_date: date | None = None
    eu_doc_signatory: str | None = Field(default=None, max_length=255)
    eu_doc_url: str | None = Field(default=None, max_length=2048)
    eu_doc_notified_body: str | None = Field(default=None, max_length=255)
    notified_body_number: str | None = Field(default=None, max_length=255)
    conformity_module: str | None = Field(default=None, max_length=255)
    standards_applied: str | None = None
    ce_marking_info: str | None = None


class DeclarationApproveRequest(BaseModel):
    """Signature captured at approval time (approval records the signatory)."""

    signatory: str | None = None


class DeclarationSignRequest(BaseModel):
    """Optional signatory (name & function) supplied when signing a DoC."""

    signatory: str | None = None
