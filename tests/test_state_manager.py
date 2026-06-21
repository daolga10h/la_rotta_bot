import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta


def test_get_state_returns_idle_when_no_profile():
    with patch("services.memory.get_profile_by_user_id", return_value=None):
        from utils.state_manager import get_state
        assert get_state("uuid-123") == "IDLE"


def test_get_state_returns_current_state():
    mock_profile = MagicMock()
    mock_profile.conversation_state = "ONBOARDING_2"
    mock_profile.state_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    with patch("services.memory.get_profile_by_user_id", return_value=mock_profile):
        from utils.state_manager import get_state
        assert get_state("uuid-123") == "ONBOARDING_2"


def test_get_state_resets_expired_state():
    mock_profile = MagicMock()
    mock_profile.conversation_state = "CHECKIN_EVENING_2"
    mock_profile.state_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    with patch("services.memory.get_profile_by_user_id", return_value=mock_profile), \
         patch("services.memory.update_state") as mock_update:
        from utils.state_manager import get_state
        result = get_state("uuid-123")
        mock_update.assert_called_once_with("uuid-123", "IDLE", None)
        assert result == "IDLE"


def test_set_state_saves_with_expiry():
    with patch("services.memory.update_state") as mock_update:
        from utils.state_manager import set_state
        set_state("uuid-123", "PARKING_1")
        args = mock_update.call_args[0]
        assert args[0] == "uuid-123"
        assert args[1] == "PARKING_1"
        assert args[2] > datetime.now(timezone.utc)


def test_clear_state_sets_idle():
    with patch("services.memory.update_state") as mock_update:
        from utils.state_manager import clear_state
        clear_state("uuid-123")
        mock_update.assert_called_once_with("uuid-123", "IDLE", None)
