# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from app.repositories.annex_requirement_repository import AnnexRequirementRepository
from app.repositories.base import BaseRepository
from app.repositories.evidence_item_repository import EvidenceItemRepository
from app.repositories.lifecycle_notification_repository import LifecycleNotificationRepository
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.product_scope_evaluation_repository import ProductScopeEvaluationRepository
from app.repositories.remote_processing_element_repository import RemoteProcessingElementRepository
from app.repositories.requirement_mapping_repository import RequirementMappingRepository
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.repositories.risk_item_repository import RiskItemRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.security_update_repository import SecurityUpdateRepository
from app.repositories.support_period_record_repository import SupportPeriodRecordRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "AnnexRequirementRepository",
    "BaseRepository",
    "EvidenceItemRepository",
    "LifecycleNotificationRepository",
    "ProductReleaseRepository",
    "ProductRepository",
    "ProductScopeEvaluationRepository",
    "RemoteProcessingElementRepository",
    "RequirementMappingRepository",
    "RiskAssessmentRepository",
    "RiskItemRepository",
    "RoleRepository",
    "SecurityUpdateRepository",
    "SupportPeriodRecordRepository",
    "UserRepository",
]