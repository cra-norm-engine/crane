from app.models.enums import ConformityRoute, ProductClassification
from app.schemas.scope_evaluation import ProductScopeEvaluationRequest
from app.services.cra_rule_service import CRARuleService


def test_rule_service_marks_excluded_product_out_of_scope() -> None:
    service = CRARuleService()

    result = service.evaluate(
        ProductScopeEvaluationRequest(
            is_digital_product=True,
            has_network_connectivity=True,
            performs_remote_data_processing=False,
            safety_component=False,
            used_in_critical_sector=False,
            handles_sensitive_functions=False,
            excluded_category=True,
            notes=None,
        )
    )

    assert result.in_scope is False
    assert result.recommended_classification == ProductClassification.normal
    assert result.suggested_conformity_route == ConformityRoute.not_applicable


def test_rule_service_marks_critical_products_for_third_party_assessment() -> None:
    service = CRARuleService()

    result = service.evaluate(
        ProductScopeEvaluationRequest(
            is_digital_product=True,
            has_network_connectivity=True,
            performs_remote_data_processing=True,
            safety_component=False,
            used_in_critical_sector=True,
            handles_sensitive_functions=True,
            excluded_category=False,
            notes=None,
        )
    )

    assert result.in_scope is True
    assert result.recommended_classification == ProductClassification.critical
    assert result.suggested_conformity_route == ConformityRoute.third_party_assessment