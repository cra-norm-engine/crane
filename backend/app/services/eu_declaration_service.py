# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""
EU Declaration of Conformity (DoC) service.

CRA Art. 28 requires the manufacturer to draw up a single EU Declaration of
Conformity per product and keep it for 10 years after placing on the market;
Annex V prescribes its minimum content. This service assembles that content
from data CRANE already holds (product + release) and exposes it two ways from
ONE builder, mirroring ReleaseReportService:

  * build_declaration_data(release_id) -> JSON-serialisable dict (Annex V items),
    consumed by the in-app preview and the PDF template.
  * generate_pdf(release_id)           -> the formal DoC PDF via Jinja2 + WeasyPrint.

It also owns the lightweight DoC lifecycle (draft -> approved -> signed). Once a
DoC is signed it is locked: approve/sign are rejected and the PDF is stamped as
the formally drawn-up document.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select

from app.assets_doc import CE_MARK_DATA_URI
from app.core.exceptions import ConflictException, NotFoundException
from app.models.enums import ConformityRoute, DocStatus
from app.models.product import Product, ProductRelease
# Reuse the report service's rendering helpers and placeholder sentinel so the
# DoC formats dates/statuses identically to the compliance report.
from app.services.release_report_service import (
    _PLACEHOLDER,
    _fmt_date,
    _fmt_status,
)

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# The mandatory sole-responsibility statement from CRA Annex V(3). Emitted
# verbatim so every generated DoC carries the exact legally-expected wording.
_SOLE_RESPONSIBILITY_STATEMENT = (
    "This declaration of conformity is issued under the sole responsibility of "
    "the manufacturer."
)


class EuDeclarationService:
    """Builds the EU DoC data + PDF and drives its draft/approved/signed lifecycle."""

    def __init__(self, db) -> None:  # Session (kept untyped to match sibling services)
        self.db = db

    # ------------------------------------------------------------------
    # Public API — generation
    # ------------------------------------------------------------------

    def generate_pdf(self, release_id: UUID, generated_by: str | None = None) -> bytes:
        """Render the formal DoC PDF for a release. Raises NotFoundException if missing."""
        data = self.build_declaration_data(release_id, generated_by=generated_by)
        html = self._render_html(data)
        return self._html_to_pdf(html)

    def generate_filename(self, release_id: UUID) -> str:
        """Return a safe filename for Content-Disposition."""
        release = self._get_release(release_id)
        product = self.db.get(Product, release.product_id)
        product_code = (product.product_code if product else "product").lower().replace(" ", "-")
        return f"eu-doc-{product_code}-v{release.system_version}.pdf"

    def build_declaration_data(self, release_id: UUID, generated_by: str | None = None) -> dict:
        """Collect the Annex V DoC content as plain JSON-serialisable values."""
        release = self._get_release(release_id)
        product = self.db.get(Product, release.product_id)
        if product is None:
            raise NotFoundException("Product not found for this release")

        now = datetime.now(UTC)
        status = self._current_status(release)
        version_label = (
            release.software_version or release.user_version or f"v{release.system_version}"
        )

        return {
            "meta": {
                "generated_at": now.strftime("%Y-%m-%d %H:%M UTC"),
                "generated_by": generated_by or "—",
                "tool_name": "CRANE — CRA Norm Engine",
                # A signed DoC is the authoritative document; anything else is a draft
                # preview and is watermarked accordingly by the template.
                "is_signed": status == DocStatus.signed,
                "status": _fmt_status(status.value),
            },
            # Annex V(1) — unique DoC reference number.
            "reference_no": release.eu_doc_number or _PLACEHOLDER,
            # Annex V(2) — manufacturer identity + registered trade address.
            "manufacturer": {
                "name": product.manufacturer_name,
                "address": product.manufacturer_address or _PLACEHOLDER,
                "contact_email": product.security_contact_email or _PLACEHOLDER,
                "contact_url": product.security_contact_url or _PLACEHOLDER,
            },
            "authorised_rep": product.authorised_representative or _PLACEHOLDER,
            # Annex V(3) — sole-responsibility statement (fixed wording).
            "sole_responsibility": _SOLE_RESPONSIBILITY_STATEMENT,
            # Annex V(4) — object of the declaration (product identification).
            "product": {
                "name": product.name,
                "model": product.product_code,
                "type": _fmt_status(product.product_type),
                "version": version_label,
                "hardware_version": release.hardware_version or _PLACEHOLDER,
                "description": product.description or product.intended_use or _PLACEHOLDER,
            },
            # Annex V(5/6) — conformity route, module, applied standards, notified body.
            "conformity": {
                "route": _fmt_status(str(release.conformity_route_snapshot)),
                "module": release.conformity_module or _PLACEHOLDER,
                "standards": release.standards_applied or _PLACEHOLDER,
                "notified_body": release.eu_doc_notified_body or _PLACEHOLDER,
                "nb_number": release.notified_body_number or _PLACEHOLDER,
            },
            # Annex V(7) — additional info, plus the CE marking statement. The CE
            # mark image is shown once conformity is declared (route applies and a
            # DoC reference exists); the affixed-mark statement is separate text.
            "ce_marking": release.ce_marking_info or _PLACEHOLDER,
            "ce_eligible": (
                release.conformity_route_snapshot != ConformityRoute.not_applicable
                and bool(release.eu_doc_number)
            ),
            "ce_mark_uri": CE_MARK_DATA_URI,
            "simplified_url": release.eu_doc_url or _PLACEHOLDER,
            # Signature block (Annex V(6) — signatory, place, date).
            "signature": {
                "signatory": release.eu_doc_signatory or _PLACEHOLDER,
                "date": _fmt_date(release.eu_doc_date) if release.eu_doc_date else _PLACEHOLDER,
                "approved_by": release.eu_doc_approved_by or _PLACEHOLDER,
                "approved_at": (
                    release.eu_doc_approved_at.strftime("%Y-%m-%d %H:%M UTC")
                    if release.eu_doc_approved_at
                    else _PLACEHOLDER
                ),
                "signed_at": (
                    release.eu_doc_signed_at.strftime("%Y-%m-%d %H:%M UTC")
                    if release.eu_doc_signed_at
                    else _PLACEHOLDER
                ),
            },
        }

    # ------------------------------------------------------------------
    # Public API — listing (top-level Declarations page)
    # ------------------------------------------------------------------

    def list_declarations(self, product_id: UUID | None = None) -> list[dict]:
        """Return one summary row per release (optionally filtered by product) with
        its DoC status, for the Declarations landing page."""
        stmt = (
            select(ProductRelease, Product)
            .join(Product, Product.id == ProductRelease.product_id)
            .order_by(Product.name.asc(), ProductRelease.system_version.desc())
        )
        if product_id is not None:
            stmt = stmt.where(ProductRelease.product_id == product_id)
        rows: list[dict] = []
        for release, product in self.db.execute(stmt).all():
            version_label = (
                release.software_version or release.user_version or f"v{release.system_version}"
            )
            rows.append(
                {
                    "release_id": release.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "product_code": product.product_code,
                    "system_version": release.system_version,
                    "version_label": version_label,
                    "doc_status": self._current_status(release).value,
                    "doc_number": release.eu_doc_number,
                    "doc_date": release.eu_doc_date,
                    "signatory": release.eu_doc_signatory,
                    "approved_by": release.eu_doc_approved_by,
                    "approved_at": release.eu_doc_approved_at,
                    "signed_at": release.eu_doc_signed_at,
                }
            )
        return rows

    # ------------------------------------------------------------------
    # Public API — lifecycle (draft -> approved -> signed)
    # ------------------------------------------------------------------

    def update(self, release_id: UUID, changes: dict) -> ProductRelease:
        """Update editable DoC fields. Only permitted while the DoC is in draft;
        an approved or signed DoC is locked.

        `changes` should already exclude unset fields (use exclude_unset on the
        Pydantic model) so that omitted fields are left untouched.
        """
        release = self._get_release(release_id)
        if self._current_status(release) != DocStatus.draft:
            raise ConflictException(
                "The Declaration of Conformity can only be edited while it is in draft."
            )
        editable = {
            "eu_doc_number",
            "eu_doc_date",
            "eu_doc_signatory",
            "eu_doc_url",
            "eu_doc_notified_body",
            "notified_body_number",
            "conformity_module",
            "standards_applied",
            "ce_marking_info",
        }
        for field, value in changes.items():
            if field in editable:
                setattr(release, field, value)
        self.db.commit()
        self.db.refresh(release)
        return release

    def submit(self, release_id: UUID) -> ProductRelease:
        """Return an approved/signed DoC to draft so it can be edited again.

        Only draft and approved DoCs can be reset to draft; a signed DoC is locked.
        """
        release = self._get_release(release_id)
        if self._current_status(release) == DocStatus.signed:
            raise ConflictException("A signed Declaration of Conformity is locked and cannot be reopened.")
        release.eu_doc_status = DocStatus.draft.value
        release.eu_doc_approved_by = None
        release.eu_doc_approved_at = None
        self.db.commit()
        self.db.refresh(release)
        return release

    def approve(
        self, release_id: UUID, approver: str | None, signatory: str | None = None
    ) -> ProductRelease:
        """Approve a draft DoC and capture its signature in one step.

        Per CRA practice the person approving the DoC is also its signatory, so
        approval records both the approver (who actioned it) and the signatory
        (the name/function that appears on the declaration). The DoC date is set
        to today if not already provided. This moves the DoC to the ``approved``
        state; a subsequent ``sign`` call formally locks it.
        """
        release = self._get_release(release_id)
        status = self._current_status(release)
        if status == DocStatus.signed:
            raise ConflictException("The Declaration of Conformity is already signed.")
        # Annex V(1): a DoC without its unique reference number is incomplete.
        if not release.eu_doc_number:
            raise ConflictException("A DoC reference number is required before approval.")
        # Annex V(6): the declaration must carry a signatory. Prefer an explicit
        # signatory, else fall back to any already recorded, else the approver.
        resolved_signatory = signatory or release.eu_doc_signatory or approver
        if not resolved_signatory:
            raise ConflictException("A signatory is required to approve and sign the declaration.")
        now = datetime.now(UTC)
        release.eu_doc_status = DocStatus.approved.value
        release.eu_doc_approved_by = approver
        release.eu_doc_approved_at = now
        release.eu_doc_signatory = resolved_signatory
        if release.eu_doc_date is None:
            release.eu_doc_date = now.date()
        self.db.commit()
        self.db.refresh(release)
        return release

    def sign(self, release_id: UUID, signatory: str | None) -> ProductRelease:
        """Formally sign (draw up) an approved DoC. Locks it from further edits."""
        release = self._get_release(release_id)
        status = self._current_status(release)
        if status == DocStatus.signed:
            raise ConflictException("The Declaration of Conformity is already signed.")
        if status != DocStatus.approved:
            raise ConflictException("The Declaration of Conformity must be approved before it can be signed.")
        now = datetime.now(UTC)
        release.eu_doc_status = DocStatus.signed.value
        release.eu_doc_signed_at = now
        # Record the signatory on the release if one was supplied; otherwise keep any
        # signatory already captured on the DoC metadata.
        if signatory:
            release.eu_doc_signatory = signatory
        # Annex V(6): the DoC date is the date it is drawn up (signed) if not already set.
        if release.eu_doc_date is None:
            release.eu_doc_date = now.date()
        self.db.commit()
        self.db.refresh(release)
        return release

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _current_status(self, release: ProductRelease) -> DocStatus:
        """Resolve the release's DoC status, treating missing/legacy values as draft."""
        raw = (release.eu_doc_status or "").strip().lower()
        try:
            return DocStatus(raw)
        except ValueError:
            return DocStatus.draft

    def _get_release(self, release_id: UUID) -> ProductRelease:
        release = self.db.get(ProductRelease, release_id)
        if release is None:
            raise NotFoundException("Product release not found")
        return release

    def _render_html(self, data: dict) -> str:
        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )
        env.filters["fmt_date"] = _fmt_date
        env.filters["fmt_status"] = _fmt_status
        env.globals["PLACEHOLDER"] = _PLACEHOLDER
        template = env.get_template("eu_declaration.html")
        return template.render(**data)

    def _html_to_pdf(self, html: str) -> bytes:
        try:
            from weasyprint import HTML  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "WeasyPrint is not installed. Add 'weasyprint' to requirements.txt."
            ) from exc
        return HTML(string=html).write_pdf()
