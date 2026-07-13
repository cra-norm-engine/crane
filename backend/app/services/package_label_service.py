# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""
Package label service.

Generates a small printable product label carrying the CRA transparency
information a user sees on the packaging: CE marking, product identification,
manufacturer, the DoC reference, the support-until date (CRA Art. 13(19)) and
the security/vulnerability-disclosure contact (Annex I Part II §6). A QR code
links to the simplified EU DoC URL (falling back to the security contact URL)
so users can reach the full declaration from the physical package.

Built on the same Jinja2 + WeasyPrint pipeline as the compliance report and the
EU DoC. The QR code is embedded as an inline SVG data URI so it stays crisp at
any print size and needs no external asset.
"""

from __future__ import annotations

import base64
import io
import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import segno
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select

from app.assets_doc import CE_MARK_DATA_URI
from app.core.exceptions import NotFoundException
from app.models.enums import ConformityRoute
from app.models.product import Product, ProductRelease
from app.models.support_period_record import SupportPeriodRecord
from app.services.release_report_service import _PLACEHOLDER, _fmt_date

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class PackageLabelService:
    """Builds the package-label data and renders the printable label PDF."""

    def __init__(self, db) -> None:  # Session (untyped to match sibling services)
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_pdf(self, release_id: UUID) -> bytes:
        """Render the label PDF for a release. Raises NotFoundException if missing."""
        data = self.build_label_data(release_id)
        html = self._render_html(data)
        return self._html_to_pdf(html)

    def generate_filename(self, release_id: UUID) -> str:
        """Return a safe filename for Content-Disposition."""
        release = self._get_release(release_id)
        product = self.db.get(Product, release.product_id)
        product_code = (product.product_code if product else "product").lower().replace(" ", "-")
        return f"package-label-{product_code}-v{release.system_version}.pdf"

    def build_label_data(self, release_id: UUID) -> dict:
        """Collect the label content as plain JSON-serialisable values."""
        release = self._get_release(release_id)
        product = self.db.get(Product, release.product_id)
        if product is None:
            raise NotFoundException("Product not found for this release")

        version_label = (
            release.software_version or release.user_version or f"v{release.system_version}"
        )
        support = self._latest_support_period(release_id, product.id)

        # QR target: prefer the simplified DoC URL (CRA Art. 28), fall back to the
        # security contact page so the QR is still useful when no DoC URL exists.
        qr_target = release.eu_doc_url or product.security_contact_url or ""
        qr_data_uri = self._make_qr_data_uri(qr_target) if qr_target else None

        # CE marking is only affixed once conformity is declared. We show the mark
        # when a signed/known conformity route applies and a DoC reference exists.
        ce_eligible = (
            release.conformity_route_snapshot != ConformityRoute.not_applicable
            and bool(release.eu_doc_number)
        )

        return {
            "meta": {
                "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
                "tool_name": "CRANE — CRA Norm Engine",
            },
            "ce_marking": ce_eligible,
            "ce_mark_uri": CE_MARK_DATA_URI,
            "product": {
                "name": product.name,
                "model": product.product_code,
                "version": version_label,
                "manufacturer": product.manufacturer_name,
            },
            # DoC reference (Annex V) so the label ties back to the declaration.
            "doc_reference": release.eu_doc_number or _PLACEHOLDER,
            # CRA Art. 13(19) — support period must be made available to the user.
            "support_until": _fmt_date(support.support_end_date) if support else _PLACEHOLDER,
            # Annex I Part II §6 — vulnerability-disclosure contact for end users.
            "security_contact": {
                "email": product.security_contact_email or _PLACEHOLDER,
                "url": product.security_contact_url or _PLACEHOLDER,
            },
            "qr_target": qr_target or _PLACEHOLDER,
            "qr_data_uri": qr_data_uri,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _make_qr_data_uri(self, target: str) -> str:
        """Render the QR code for `target` as an inline SVG data URI.

        SVG keeps the code crisp at any print size and WeasyPrint renders data
        URIs without any external asset fetch.
        """
        qr = segno.make(target, error="m")
        buf = io.BytesIO()
        # scale/border are in SVG "modules"; the template constrains the final size.
        qr.save(buf, kind="svg", scale=4, border=2)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    def _latest_support_period(
        self, release_id: UUID, product_id: UUID
    ) -> SupportPeriodRecord | None:
        """Most recent support-period record for this release, else the product's."""
        return self.db.scalar(
            select(SupportPeriodRecord)
            .where(
                (SupportPeriodRecord.product_release_id == release_id)
                | (
                    (SupportPeriodRecord.product_id == product_id)
                    & (SupportPeriodRecord.product_release_id.is_(None))
                )
            )
            .order_by(SupportPeriodRecord.support_start_date.desc())
        )

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
        env.globals["PLACEHOLDER"] = _PLACEHOLDER
        template = env.get_template("package_label.html")
        return template.render(**data)

    def _html_to_pdf(self, html: str) -> bytes:
        try:
            from weasyprint import HTML  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "WeasyPrint is not installed. Add 'weasyprint' to requirements.txt."
            ) from exc
        return HTML(string=html).write_pdf()
