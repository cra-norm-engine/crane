from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.annex_requirements import router as annex_requirements_router
from app.api.routes.auth import router as auth_router
from app.api.routes.evidence_items import router as evidence_items_router
from app.api.routes.health import router as health_router
from app.api.routes.lifecycle_notifications import router as lifecycle_notifications_router
from app.api.routes.product_releases import router as product_releases_router
from app.api.routes.products import router as products_router
from app.api.routes.remote_processing_elements import router as remote_processing_elements_router
from app.api.routes.requirement_mappings import router as requirement_mappings_router
from app.api.routes.risk_assessments import router as risk_assessments_router
from app.api.routes.risk_items import router as risk_items_router
from app.api.routes.security_updates import router as security_updates_router
from app.api.routes.support_periods import router as support_periods_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])

api_router.include_router(products_router, prefix="/products", tags=["products"])
api_router.include_router(product_releases_router, prefix="/product-releases", tags=["product-releases"])
api_router.include_router(
    remote_processing_elements_router,
    prefix="/remote-processing-elements",
    tags=["remote-processing-elements"],
)

api_router.include_router(
    support_periods_router,
    prefix="/support-periods",
    tags=["support-periods"],
)
api_router.include_router(
    security_updates_router,
    prefix="/security-updates",
    tags=["security-updates"],
)
api_router.include_router(
    lifecycle_notifications_router,
    prefix="/lifecycle-notifications",
    tags=["lifecycle-notifications"],
)

api_router.include_router(
    risk_assessments_router,
    prefix="/risk-assessments",
    tags=["risk-assessments"],
)
api_router.include_router(
    risk_items_router,
    prefix="/risk-items",
    tags=["risk-items"],
)
api_router.include_router(
    annex_requirements_router,
    prefix="/annex-requirements",
    tags=["annex-requirements"],
)
api_router.include_router(
    requirement_mappings_router,
    prefix="/requirement-mappings",
    tags=["requirement-mappings"],
)
api_router.include_router(
    evidence_items_router,
    prefix="/evidence-items",
    tags=["evidence-items"],
)

api_router.include_router(admin_router)