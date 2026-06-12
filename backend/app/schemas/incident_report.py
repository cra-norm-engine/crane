# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import IncidentReportStatus, SecurityUpdateSeverity


class IncidentReportBase(BaseModel):
    product_release_id: UUID
    title: str = Field(min_length=1)

    # i13 — mandatory: suspected unlawful or malicious act?
    suspected_malicious_act: bool = False

    # i14–i19 — required by 72h, optional at 24h
    incident_nature: str | None = None
    detected_at: datetime | None = None
    occurred_at: datetime | None = None
    initial_assessment: str | None = None
    corrective_measures_taken: str | None = None
    user_corrective_measures: str | None = None

    # i20 — sensitivity flag
    information_sensitivity: str | None = None

    # i21–i25 — required in final report (1 month after 72h notification)
    incident_impact_category: str | None = None
    severity: SecurityUpdateSeverity | None = None
    incident_impact: str | None = None
    threat_type_root_cause: str | None = None
    applied_mitigations: str | None = None

    # Internal fields
    status: IncidentReportStatus = IncidentReportStatus.reported
    assigned_to_user_id: UUID | None = None

    # ENISA SRP tracking
    enisa_reporting_required: bool = False
    enisa_reference_number: str | None = None


class IncidentReportCreate(IncidentReportBase):
    pass


class IncidentReportUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    suspected_malicious_act: bool | None = None
    incident_nature: str | None = None
    detected_at: datetime | None = None
    occurred_at: datetime | None = None
    initial_assessment: str | None = None
    corrective_measures_taken: str | None = None
    user_corrective_measures: str | None = None
    information_sensitivity: str | None = None
    incident_impact_category: str | None = None
    severity: SecurityUpdateSeverity | None = None
    incident_impact: str | None = None
    threat_type_root_cause: str | None = None
    applied_mitigations: str | None = None
    status: IncidentReportStatus | None = None
    assigned_to_user_id: UUID | None = None
    enisa_reporting_required: bool | None = None
    enisa_reference_number: str | None = None


class IncidentReportRead(IncidentReportBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

    # ENISA SRP stored submission timestamps
    enisa_early_warning_sent_at: datetime | None = None
    enisa_initial_report_sent_at: datetime | None = None
    enisa_final_report_sent_at: datetime | None = None

    # Computed deadlines (derived from detected_at / enisa_initial_report_sent_at)
    # Early warning: 24h after detection
    enisa_early_warning_deadline: datetime | None = None
    # Vulnerability notification: 72h after detection
    enisa_initial_report_deadline: datetime | None = None
    # Final report: 1 month (30 days) after the 72h notification was sent
    enisa_final_report_deadline: datetime | None = None

    @model_validator(mode="after")
    def compute_enisa_deadlines(self) -> "IncidentReportRead":
        """Populate Art. 14 deadline fields from detected_at / enisa_initial_report_sent_at."""
        if self.enisa_reporting_required and self.detected_at:
            self.enisa_early_warning_deadline = self.detected_at + timedelta(hours=24)
            self.enisa_initial_report_deadline = self.detected_at + timedelta(hours=72)
        # Final report deadline: 1 month after the 72h notification was actually sent.
        # Falls back to detected_at + 72h + 30 days if 72h hasn't been sent yet.
        if self.enisa_initial_report_sent_at:
            self.enisa_final_report_deadline = self.enisa_initial_report_sent_at + timedelta(days=30)
        elif self.detected_at:
            self.enisa_final_report_deadline = self.detected_at + timedelta(hours=72, days=30)
        return self


class IncidentEnisaMarkSentRequest(BaseModel):
    """Payload for the three ENISA Art. 14 mark-sent endpoints (incident branch)."""
    sent_at: datetime | None = None
    reference_number: str | None = None
