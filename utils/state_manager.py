import logging
from datetime import datetime, timezone, timedelta
from config import STATE_EXPIRY_HOURS
import services.memory as memory

logger = logging.getLogger(__name__)


def get_state(user_id: str) -> str:
    profile = memory.get_profile_by_user_id(user_id)
    if profile is None:
        return "IDLE"
    if profile.state_expires_at and profile.state_expires_at < datetime.now(timezone.utc):
        logger.info("Stato scaduto per user_id=%s, reset a IDLE", user_id)
        clear_state(user_id)
        return "IDLE"
    return profile.conversation_state


def set_state(user_id: str, state: str) -> None:
    expiry = datetime.now(timezone.utc) + timedelta(hours=STATE_EXPIRY_HOURS)
    memory.update_state(user_id, state, expiry)
    logger.debug("Stato impostato: user_id=%s state=%s", user_id, state)


def clear_state(user_id: str) -> None:
    memory.update_state(user_id, "IDLE", None)
