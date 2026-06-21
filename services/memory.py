import logging
from datetime import datetime, timezone
from models.user_profile import UserProfileData
from db import queries

logger = logging.getLogger(__name__)


def _get_user_id(telegram_id: int) -> str:
    user = queries.get_or_create_user(telegram_id)
    return user["id"]


def get_profile(telegram_id: int) -> UserProfileData | None:
    user_id = _get_user_id(telegram_id)
    row = queries.get_user_profile(user_id)
    if not row:
        return None
    return UserProfileData.model_validate(row["data"])


def get_profile_by_user_id(user_id: str) -> UserProfileData | None:
    row = queries.get_user_profile(user_id)
    if not row:
        return None
    return UserProfileData.model_validate(row["data"])


def save_profile(telegram_id: int, profile: UserProfileData) -> None:
    user_id = _get_user_id(telegram_id)
    queries.upsert_user_profile(user_id, profile.model_dump(mode="json"))


def get_or_create_profile(telegram_id: int) -> UserProfileData:
    profile = get_profile(telegram_id)
    if profile is None:
        profile = UserProfileData(telegram_id=telegram_id)
        save_profile(telegram_id, profile)
    return profile


def update_state(user_id: str, state: str, expires_at: datetime | None) -> None:
    row = queries.get_user_profile(user_id)
    if not row:
        logger.warning("update_state: profilo non trovato per user_id=%s", user_id)
        return
    data = row["data"]
    data["conversation_state"] = state
    data["state_expires_at"] = expires_at.isoformat() if expires_at else None
    queries.upsert_user_profile(user_id, data)
