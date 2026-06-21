import pytest
from unittest.mock import patch, MagicMock
from models.user_profile import UserProfileData, Objective
import anthropic

PROFILE = UserProfileData(
    telegram_id=12345,
    objectives=[Objective(title="Vendere negozio", rank=1)],
    motivation_anchor="Casa a Marta",
    user_context="Bottega artigianale",
)

MESSAGES = [{"role": "user", "content": "Ho finito la scaletta"}]


def _mock_response(text: str):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    return msg


def test_generate_response_success():
    with patch("services.response_generator._client") as mock_client:
        mock_client.messages.create.return_value = _mock_response("Bene. Questo conta.")
        from services.response_generator import generate_response
        text, is_fallback = generate_response(PROFILE, "CHECKIN_EVENING_B", "...", MESSAGES)
        assert text == "Bene. Questo conta."
        assert is_fallback is False


def test_generate_response_rate_limit_fallback():
    with patch("services.response_generator._client") as mock_client, \
         patch("time.sleep"):
        mock_client.messages.create.side_effect = anthropic.RateLimitError(
            message="rate limit", response=MagicMock(status_code=429), body={}
        )
        from services.response_generator import generate_response
        text, is_fallback = generate_response(PROFILE, "CHECKIN_EVENING_B", "...", MESSAGES)
        assert is_fallback is True
        assert "momento" in text.lower()


def test_generate_response_server_error_fallback():
    with patch("services.response_generator._client") as mock_client:
        mock_client.messages.create.side_effect = anthropic.APIStatusError(
            message="server error", response=MagicMock(status_code=500), body={}
        )
        from services.response_generator import generate_response
        text, is_fallback = generate_response(PROFILE, "CHECKIN_EVENING_B", "...", MESSAGES)
        assert is_fallback is True
        assert text  # non è stringa vuota


def test_generate_response_timeout_fallback():
    with patch("services.response_generator._client") as mock_client:
        mock_client.messages.create.side_effect = anthropic.APITimeoutError(
            request=MagicMock()
        )
        from services.response_generator import generate_response
        text, is_fallback = generate_response(PROFILE, "CHECKIN_EVENING_B", "...", MESSAGES)
        assert is_fallback is True


def test_generate_truncates_to_10_messages():
    with patch("services.response_generator._client") as mock_client:
        mock_client.messages.create.return_value = _mock_response("Ok.")
        many_messages = [{"role": "user", "content": f"msg {i}"} for i in range(15)]
        from services.response_generator import generate_response
        generate_response(PROFILE, "IDLE", "...", many_messages)
        call_messages = mock_client.messages.create.call_args[1]["messages"]
        assert len(call_messages) == 10


def test_prompt_builder_includes_profile_data():
    from services.prompt_builder import build_system_prompt
    prompt = build_system_prompt(
        profile=PROFILE,
        flow_name="CHECKIN_EVENING",
        flow_instructions="Chiedi come è andata la giornata.",
    )
    assert "Vendere negozio" in prompt
    assert "Casa a Marta" in prompt
    assert "CHECKIN_EVENING" in prompt


def test_prompt_builder_includes_summaries():
    from services.prompt_builder import build_system_prompt
    summaries = [{"week_start": "2026-06-14", "tone": "mixed", "narrative": "Settimana mista."}]
    prompt = build_system_prompt(
        profile=PROFILE,
        flow_name="CHECKIN_EVENING",
        flow_instructions="...",
        weekly_summaries=summaries,
    )
    assert "Settimana mista." in prompt
