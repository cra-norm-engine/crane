from __future__ import annotations

from app.models.enums import ConformityRoute, ProductClassification
from app.schemas.scope_evaluation import ProductScopeEvaluationRequest, ProductScopeEvaluationResult


class CRARuleService:
    def evaluate(self, payload: ProductScopeEvaluationRequest) -> ProductScopeEvaluationResult:
        in_scope = self._derive_in_scope(payload)
        classification = self._derive_classification(payload=payload, in_scope=in_scope)
        route = self._derive_conformity_route(in_scope=in_scope, classification=classification)
        rationale = self._build_rationale(
            payload=payload,
            in_scope=in_scope,
            classification=classification,
            route=route,
        )

        return ProductScopeEvaluationResult(
            in_scope=in_scope,
            rationale=rationale,
            recommended_classification=classification,
            suggested_conformity_route=route,
        )

    def _derive_in_scope(self, payload: ProductScopeEvaluationRequest) -> bool:
        if payload.excluded_category:
            return False

        return any(
            [
                payload.is_digital_product,
                payload.has_network_connectivity,
                payload.performs_remote_data_processing,
                payload.safety_component,
            ]
        )

    def _derive_classification(
        self,
        *,
        payload: ProductScopeEvaluationRequest,
        in_scope: bool,
    ) -> ProductClassification:
        if not in_scope:
            return ProductClassification.normal

        if payload.used_in_critical_sector and payload.handles_sensitive_functions:
            return ProductClassification.critical

        if payload.used_in_critical_sector:
            return ProductClassification.important_class_2

        if payload.handles_sensitive_functions or payload.safety_component:
            return ProductClassification.important_class_1

        return ProductClassification.normal

    def _derive_conformity_route(
        self,
        *,
        in_scope: bool,
        classification: ProductClassification,
    ) -> ConformityRoute:
        if not in_scope:
            return ConformityRoute.not_applicable

        if classification in {
            ProductClassification.important_class_2,
            ProductClassification.critical,
        }:
            return ConformityRoute.third_party_assessment

        if classification in {
            ProductClassification.normal,
            ProductClassification.important_class_1,
        }:
            return ConformityRoute.self_assessment

        return ConformityRoute.undecided

    def _build_rationale(
        self,
        *,
        payload: ProductScopeEvaluationRequest,
        in_scope: bool,
        classification: ProductClassification,
        route: ConformityRoute,
    ) -> str:
        reasons: list[str] = []

        if payload.excluded_category:
            reasons.append("The product is marked as belonging to an excluded category.")
        if payload.is_digital_product:
            reasons.append("The product is a digital product.")
        if payload.has_network_connectivity:
            reasons.append("The product has network connectivity.")
        if payload.performs_remote_data_processing:
            reasons.append("The product performs remote data processing.")
        if payload.safety_component:
            reasons.append("The product acts as a safety-relevant component.")
        if payload.used_in_critical_sector:
            reasons.append("The product is used in a critical sector.")
        if payload.handles_sensitive_functions:
            reasons.append("The product handles sensitive or security-relevant functions.")
        if payload.notes:
            reasons.append(f"Additional notes were provided: {payload.notes}")

        scope_text = "in scope" if in_scope else "out of scope"
        return (
            f"CRA evaluation determined the product is {scope_text}. "
            f"Recommended classification: {classification.value}. "
            f"Suggested conformity route: {route.value}. "
            + " ".join(reasons)
        )