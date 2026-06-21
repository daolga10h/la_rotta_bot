import pytest
from unittest.mock import patch, MagicMock
from models.user_profile import Objective

OBJECTIVES = [
    Objective(title="Vendere negozio", rank=1),
    Objective(title="Oltre la Bottega", rank=2, weekly_hours_target=6),
]


def _mock_response(text: str):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


def test_classify_idea():
    with patch("services.classifier._client") as mock_client:
        mock_client.messages.create.return_value = _mock_response(
            '{"category": "IDEA", "confidence": 0.95, "alternative_category": null}'
        )
        from services.classifier import classify_message
        result = classify_message("Ho pensato di fare un open day", OBJECTIVES, [])
        assert result["category"] == "IDEA"
        assert result["confidence"] == 0.95


def test_classify_blocco():
    with patch("services.classifier._client") as mock_client:
        mock_client.messages.create.return_value = _mock_response(
            '{"category": "BLOCCO", "confidence": 0.90, "alternative_category": "AMBIGUO"}'
        )
        from services.classifier import classify_message
        result = classify_message("Non riesco ad andare avanti", OBJECTIVES, [])
        assert result["category"] == "BLOCCO"
        assert result["alternative_category"] == "AMBIGUO"


def test_classify_returns_ambiguo_on_invalid_category():
    with patch("services.classifier._client") as mock_client:
        mock_client.messages.create.return_value = _mock_response(
            '{"category": "SCONOSCIUTA", "confidence": 0.80, "alternative_category": null}'
        )
        from services.classifier import classify_message
        result = classify_message("messaggio", OBJECTIVES, [])
        assert result["category"] == "AMBIGUO"
        assert result["confidence"] == 0.0


def test_classify_returns_ambiguo_on_json_error():
    with patch("services.classifier._client") as mock_client:
        mock_client.messages.create.return_value = _mock_response("testo non JSON")
        from services.classifier import classify_message
        result = classify_message("messaggio", OBJECTIVES, [])
        assert result["category"] == "AMBIGUO"
        assert result["confidence"] == 0.0


def test_classify_returns_ambiguo_on_rate_limit():
    import anthropic
    with patch("services.classifier._client") as mock_client:
        mock_client.messages.create.side_effect = anthropic.RateLimitError(
            message="rate limit", response=MagicMock(status_code=429), body={}
        )
        from services.classifier import classify_message
        result = classify_message("messaggio", OBJECTIVES, [])
        assert result["category"] == "AMBIGUO"


def test_classify_returns_ambiguo_on_api_error():
    import anthropic
    with patch("services.classifier._client") as mock_client:
        mock_client.messages.create.side_effect = anthropic.APIStatusError(
            message="server error", response=MagicMock(status_code=500), body={}
        )
        from services.classifier import classify_message
        result = classify_message("messaggio", OBJECTIVES, [])
        assert result["category"] == "AMBIGUO"


def test_classify_all_valid_categories():
    valid = ["IDEA", "UPDATE", "BLOCCO", "DOMANDA", "FEEDBACK", "AMBIGUO"]
    for cat in valid:
        with patch("services.classifier._client") as mock_client:
            mock_client.messages.create.return_value = _mock_response(
                f'{{"category": "{cat}", "confidence": 0.9, "alternative_category": null}}'
            )
            from services.classifier import classify_message
            result = classify_message("test", OBJECTIVES, [])
            assert result["category"] == cat
