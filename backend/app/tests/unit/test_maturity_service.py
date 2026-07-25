from types import SimpleNamespace

from app.services.maturity_service import MaturityService


def assessment(scores: list[int | None]):
    responses = [SimpleNamespace(question_code=f"{index // 5 + 1}.{index % 5 + 1}", score=score) for index, score in enumerate(scores)]
    return SimpleNamespace(responses=responses, catalog_snapshot_json=[{}] * 25)


def test_maturity_profile_boundaries() -> None:
    assert MaturityService.results(assessment([1] * 25))["profile"] == "basic"
    assert MaturityService.results(assessment([2] * 10 + [3] * 15))["overall_score"] == 2.6
    assert MaturityService.results(assessment([2] * 10 + [3] * 15))["profile"] == "intermediate"
    assert MaturityService.results(assessment([4] * 25))["profile"] == "advanced"


def test_incomplete_assessment_has_no_overall_score() -> None:
    result = MaturityService.results(assessment([5] * 24 + [None]))
    assert result["complete"] is False
    assert result["overall_score"] is None
    assert result["profile"] is None
