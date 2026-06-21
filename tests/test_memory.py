import pytest
from unittest.mock import patch
from models.user_profile import UserProfileData, Objective


def _make_profile():
    return UserProfileData(
        telegram_id=12345678,
        objectives=[Objective(title="Vendere negozio", rank=1)],
        motivation_anchor="Casa a Marta",
        user_context="Bottega artigianale",
    )


def test_get_profile_returns_none_for_unknown_user():
    with patch("db.queries.get_or_create_user") as mock_user, \
         patch("db.queries.get_user_profile") as mock_profile:
        mock_user.return_value = {"id": "uuid-1", "telegram_id": 99}
        mock_profile.return_value = None
        from services.memory import get_profile
        result = get_profile(telegram_id=99)
        assert result is None


def test_get_profile_deserializes_json():
    profile = _make_profile()
    profile_dict = profile.model_dump(mode="json")
    with patch("db.queries.get_or_create_user") as mock_user, \
         patch("db.queries.get_user_profile") as mock_profile:
        mock_user.return_value = {"id": "uuid-1", "telegram_id": 12345678}
        mock_profile.return_value = {"data": profile_dict}
        from services.memory import get_profile
        result = get_profile(telegram_id=12345678)
        assert result is not None
        assert result.telegram_id == 12345678
        assert result.objectives[0].title == "Vendere negozio"


def test_save_profile_calls_upsert():
    profile = _make_profile()
    with patch("db.queries.get_or_create_user") as mock_user, \
         patch("db.queries.upsert_user_profile") as mock_upsert:
        mock_user.return_value = {"id": "uuid-1", "telegram_id": 12345678}
        from services.memory import save_profile
        save_profile(telegram_id=12345678, profile=profile)
        assert mock_upsert.called
        call_data = mock_upsert.call_args[0][1]
        assert call_data["telegram_id"] == 12345678


def test_update_state_modifies_only_state_fields():
    profile = _make_profile()
    profile_dict = profile.model_dump(mode="json")
    with patch("db.queries.get_or_create_user"), \
         patch("db.queries.get_user_profile") as mock_profile_db, \
         patch("db.queries.upsert_user_profile") as mock_upsert:
        mock_profile_db.return_value = {"data": profile_dict}
        from services.memory import update_state
        from datetime import datetime, timezone, timedelta
        expiry = datetime.now(timezone.utc) + timedelta(hours=2)
        update_state("uuid-1", "ONBOARDING_3", expiry)
        saved = mock_upsert.call_args[0][1]
        assert saved["conversation_state"] == "ONBOARDING_3"
        assert saved["objectives"][0]["title"] == "Vendere negozio"


def test_get_or_create_profile_creates_when_missing():
    with patch("db.queries.get_or_create_user") as mock_user, \
         patch("db.queries.get_user_profile") as mock_get, \
         patch("db.queries.upsert_user_profile") as mock_upsert:
        mock_user.return_value = {"id": "uuid-1", "telegram_id": 999}
        mock_get.return_value = None
        mock_upsert.return_value = {}
        from services.memory import get_or_create_profile
        profile = get_or_create_profile(telegram_id=999)
        assert profile.telegram_id == 999
        assert mock_upsert.called
