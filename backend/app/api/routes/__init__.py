from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.annex_requirements import router as annex_requirements_router
from app.api.routes.artifacts import router as artifacts_router
from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.evidence_items import router as evidence_items_router
from app.api.routes.health import router as health_router
from app.api.routes.lifecycle_notifications import router as lifecycle_notifications_router
from app.api.routes.product_releases import router as product_releases_router
from app.api.routes.products import router as products_router
from app.api.routes.release_gates import router as release_gates_router
from app.api.routes.remote_processing_elements import router as remote_processing_elements_router
from app.api.routes.requirement_mappings import router as requirement_mappings_router
from app.api.routes.risk_assessments import router as risk_assessments_router
from app.api.routes.risk_items import router as risk_items_router
from app.api.routes.security_updates import router as security_updates_router
from app.api.routes.certification_records import router as certification_records_router
from app.api.routes.changes import router as changes_router
from app.api.routes.cvd_policies import router as cvd_policies_router
from app.api.routes.sbom_records import router as sbom_records_router
from app.api.routes.security_advisories import router as security_advisories_router
from app.api.routes.support_periods import router as support_periods_router
from app.api.routes.vulnerability_reports import router as vulnerability_reports_router
from app.api.routes.comments import router as comments_router
from app.api.routes.market_actions import router as market_actions_router
from app.api.routes.my_tasks import router as my_tasks_router
from app.api.routes.dashboard import router as dashboard_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(audit_router)

api_router.include_router(products_router, prefix="/products", tags=["products"])
api_router.include_router(product_releases_router, prefix="/product-releases", tags=["product-releases"])
api_router.include_router(release_gates_router, tags=["release-gates"])
api_router.include_router(artifacts_router, prefix="/artifacts", tags=["artifacts"])
api_router.include_router(
    remote_processing_elements_router,
    prefix="/remote-processing-elements",
    tags=["remote-processing-elements"],
)

api_router.include_router(
    certification_records_router,
    prefix="/certification-records",
    tags=["certification-records"],
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

api_router.include_router(
    changes_router,
    prefix="/changes",
    tags=["changes"],
)
api_router.include_router(
    cvd_policies_router,
    prefix="/cvd-policies",
    tags=["cvd-policies"],
)
api_router.include_router(
    security_advisories_router,
    prefix="/security-advisories",
    tags=["security-advisories"],
)
api_router.include_router(
    vulnerability_reports_router,
    prefix="/vulnerability-reports",
    tags=["vulnerability-reports"],
)
api_router.include_router(
    sbom_records_router,
    prefix="/sbom-records",
    tags=["sbom-records"],
)

api_router.include_router(
    market_actions_router,
    prefix="/market-actions",
    tags=["market-actions"],
)

api_router.include_router(
    comments_router,
    prefix="/comments",
    tags=["comments"],
)

api_router.include_router(
    my_tasks_router,
    prefix="/my-tasks",
    tags=["my-tasks"],
)

api_router.include_router(admin_router)

api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
