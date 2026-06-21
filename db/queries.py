import logging
from datetime import datetime, timezone, date
from db.client import supabase

logger = logging.getLogger(__name__)


def get_or_create_user(telegram_id: int) -> dict:
    result = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    if result.data:
        return result.data[0]
    new = supabase.table("users").insert({"telegram_id": telegram_id}).execute()
    return new.data[0]


def get_user_profile(user_id: str) -> dict | None:
    result = supabase.table("user_profile").select("*").eq("user_id", user_id).execute()
    return result.data[0] if result.data else None


def upsert_user_profile(user_id: str, data: dict) -> dict:
    existing = get_user_profile(user_id)
    payload = {
        "user_id": user_id,
        "data": data,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if existing:
        result = supabase.table("user_profile").update(payload).eq("user_id", user_id).execute()
    else:
        result = supabase.table("user_profile").insert(payload).execute()
    return result.data[0]


def save_message(user_id: str, role: str, content: str, classified_as: str = None, flow_name: str = None):
    supabase.table("conversations").insert({
        "user_id": user_id,
        "role": role,
        "content": content,
        "classified_as": classified_as,
        "flow_name": flow_name,
    }).execute()


def get_recent_messages(user_id: str, limit: int = 10) -> list[dict]:
    result = (
        supabase.table("conversations")
        .select("role, content, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(result.data))


def get_recent_weekly_summaries(user_id: str, limit: int = 3) -> list[dict]:
    result = (
        supabase.table("weekly_summaries")
        .select("narrative, tone, week_start, data")
        .eq("user_id", user_id)
        .order("week_start", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(result.data))


def save_checkin_session(user_id: str, session_data: dict) -> dict:
    result = supabase.table("checkin_sessions").insert({
        "user_id": user_id,
        **session_data,
    }).execute()
    return result.data[0]


def get_today_checkin(user_id: str, checkin_type: str) -> dict | None:
    today = date.today().isoformat()
    result = (
        supabase.table("checkin_sessions")
        .select("*")
        .eq("user_id", user_id)
        .eq("type", checkin_type)
        .eq("date", today)
        .execute()
    )
    return result.data[0] if result.data else None


def archive_objectives(user_id: str, version: int, snapshot: list, anchor: str, note: str):
    supabase.table("objectives_history").insert({
        "user_id": user_id,
        "version_number": version,
        "objectives_snapshot": snapshot,
        "motivation_anchor": anchor,
        "transition_note": note,
    }).execute()
