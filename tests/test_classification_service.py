import pytest

from app.services.classification_service import (
    ClassificationError,
    parse_classification_response,
)


def test_parse_valid_classification():
    response = """
    {
        "category": "requirements_specification",
        "confidence": 0.96,
        "reason": "O documento apresenta requisitos funcionais.",
        "evidence": [
            "Requisitos funcionais",
            "Critérios de aceitação"
        ]
    }
    """

    result = parse_classification_response(response)

    assert result["category"] == "requirements_specification"
    assert result["confidence"] == 0.96
    assert len(result["evidence"]) == 2


def test_reject_invalid_category():
    response = """
    {
        "category": "random_category",
        "confidence": 0.90,
        "reason": "Teste.",
        "evidence": []
    }
    """

    with pytest.raises(ClassificationError):
        parse_classification_response(response)


def test_reject_invalid_confidence():
    response = """
    {
        "category": "user_story",
        "confidence": 1.5,
        "reason": "Teste.",
        "evidence": []
    }
    """

    with pytest.raises(ClassificationError):
        parse_classification_response(response)


def test_reject_invalid_json():
    response = '{"category": "user_story",'

    with pytest.raises(ClassificationError):
        parse_classification_response(response)
