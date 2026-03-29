from app.schemas.annex_requirement import AnnexRequirementCreate, AnnexRequirementRead
from app.schemas.auth import LoginRequest, TokenRead
from app.schemas.evidence_item import EvidenceItemCreate, EvidenceItemRead
from app.schemas.health import HealthRead
from app.schemas.admin_user import *
from app.schemas.annex_requirement import *
from app.schemas.auth import *
from app.schemas.common import *
from app.schemas.evidence_item import *
from app.schemas.health import *
from app.schemas.lifecycle_notification import *
from app.schemas.permission import *
from app.schemas.product import *
from app.schemas.product_release import *
from app.schemas.remote_processing_element import *
from app.schemas.requirement_mapping import *
from app.schemas.risk_assessment import *
from app.schemas.risk_item import *
from app.schemas.role import *
from app.schemas.scope_evaluation import *
from app.schemas.security_update import *
from app.schemas.support_period_record import *
from app.schemas.user import *
from app.schemas.product import (
    ProductCreate,
    ProductDetailRead,
    ProductRead,
    ProductSummaryRead,
    ProductUpdate,
)
from app.schemas.product_release import ProductReleaseCreate, ProductReleaseRead, ProductReleaseUpdate
from app.schemas.remote_processing_element import (
    RemoteProcessingElementCreate,
    RemoteProcessingElementRead,
    RemoteProcessingElementUpdate,
)
from app.schemas.requirement_mapping import RequirementMappingCreate, RequirementMappingRead, RequirementMappingUpdate
from app.schemas.risk_assessment import (
    RiskAssessmentCreate,
    RiskAssessmentDetailRead,
    RiskAssessmentRead,
    RiskAssessmentUpdate,
)
from app.schemas.risk_item import RiskItemCreate, RiskItemRead, RiskItemUpdate
from app.schemas.scope_evaluation import (
    ProductScopeEvaluationRead,
    ProductScopeEvaluationRequest,
    ProductScopeEvaluationResult,
)
from app.schemas.user import UserCreate, UserRead

__all__ = [
    "HealthRead",
    "LoginRequest",
    "ProductCreate",
    "ProductDetailRead",
    "ProductRead",
    "ProductSummaryRead",
    "ProductUpdate",
    "ProductReleaseCreate",
    "ProductReleaseRead",
    "ProductReleaseUpdate",
    "ProductScopeEvaluationRead",
    "ProductScopeEvaluationRequest",
    "ProductScopeEvaluationResult",
    "RemoteProcessingElementCreate",
    "RemoteProcessingElementRead",
    "RemoteProcessingElementUpdate",
    "TokenRead",
    "UserCreate",
    "UserRead",

    # CRA Risk Domain
    "RiskAssessmentCreate",
    "RiskAssessmentRead",
    "RiskAssessmentDetailRead",
    "RiskAssessmentUpdate",
    "RiskItemCreate",
    "RiskItemRead",
    "RiskItemUpdate",
    "AnnexRequirementCreate",
    "AnnexRequirementRead",
    "RequirementMappingCreate",
    "RequirementMappingRead",
    "RequirementMappingUpdate",
    "EvidenceItemCreate",
    "EvidenceItemRead",
]