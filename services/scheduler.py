import logging
from datetime import time
from zoneinfo import ZoneInfo
from telegram.ext import Application

logger = logging.getLogger(__name__)
ROME_TZ = ZoneInfo("Europe/Rome")

_DAY_MAP = {
    "lunedì": 0, "martedì": 1, "mercoledì": 2, "giovedì": 3,
    "venerdì": 4, "sabato": 5, "domenica": 6,
}


def _parse_hm(time_str: str) -> tuple[int, int]:
    h, m = time_str.split(":")
    return int(h), int(m)


def _remove_user_jobs(app: Application, telegram_id: int) -> None:
    prefixes = [f"evening_{telegram_id}", f"morning_{telegram_id}",
                f"review_{telegram_id}", f"reengagement_{telegram_id}",
                f"summary_{telegram_id}"]
    for job in app.job_queue.jobs():
        if job.name in prefixes:
            job.schedule_removal()


def setup_user_jobs(app: Application, telegram_id: int, profile) -> None:
    """Configura o aggiorna tutti i job per un utente dopo onboarding."""
    _remove_user_jobs(app, telegram_id)
    jq = app.job_queue

    # Check-in serale
    h, m = _parse_hm(profile.checkin_time_evening)
    jq.run_daily(
        _job_evening_checkin,
        time=time(h, m, tzinfo=ROME_TZ),
        name=f"evening_{telegram_id}",
        data={"telegram_id": telegram_id},
    )

    # Check-in mattutino (7:30, condizionale)
    jq.run_daily(
        _job_morning_checkin,
        time=time(7, 30, tzinfo=ROME_TZ),
        name=f"morning_{telegram_id}",
        data={"telegram_id": telegram_id},
    )

    # Revisione settimanale
    review_h, review_m = _parse_hm(profile.review_time)
    review_day_num = _DAY_MAP.get(profile.review_day.lower(), 6)
    jq.run_daily(
        _job_weekly_review,
        time=time(review_h, review_m, tzinfo=ROME_TZ),
        days=(review_day_num,),
        name=f"review_{telegram_id}",
        data={"telegram_id": telegram_id},
    )

    # Re-engagement check giornaliero alle 9:00
    jq.run_daily(
        _job_reengagement,
        time=time(9, 0, tzinfo=ROME_TZ),
        name=f"reengagement_{telegram_id}",
        data={"telegram_id": telegram_id},
    )

    # Riassunto settimanale (domenica 20:00)
    jq.run_daily(
        _job_weekly_summary,
        time=time(20, 0, tzinfo=ROME_TZ),
        days=(6,),
        name=f"summary_{telegram_id}",
        data={"telegram_id": telegram_id},
    )

    logger.info("Job scheduler configurato per user=%s", telegram_id)


def setup_all_users(app: Application) -> None:
    """Chiamato all'avvio: configura i job per tutti gli utenti esistenti."""
    from db.client import supabase
    from services.memory import get_or_create_profile

    try:
        result = supabase.table("users").select("telegram_id").eq("onboarding_complete", True).execute()
        users = result.data or []
    except Exception as e:
        logger.error("Errore caricamento utenti per scheduler: %s", e)
        return

    for user in users:
        telegram_id = user["telegram_id"]
        try:
            profile = get_or_create_profile(telegram_id)
            if profile.onboarding_complete:
                setup_user_jobs(app, telegram_id, profile)
        except Exception as e:
            logger.error("Errore setup job per user=%s: %s", telegram_id, e)


# ── Job callbacks ─────────────────────────────────────────────────────────────

async def _job_evening_checkin(context) -> None:
    telegram_id = context.job.data["telegram_id"]
    try:
        from handlers.checkin_evening import send_checkin
        await send_checkin(telegram_id, context.bot)
    except Exception as e:
        logger.error("Errore job check-in serale: user=%s err=%s", telegram_id, e, exc_info=True)


async def _job_morning_checkin(context) -> None:
    telegram_id = context.job.data["telegram_id"]
    try:
        from handlers.checkin_morning import send_if_needed
        await send_if_needed(telegram_id, context.bot)
    except Exception as e:
        logger.error("Errore job check-in mattutino: user=%s err=%s", telegram_id, e, exc_info=True)


async def _job_weekly_review(context) -> None:
    telegram_id = context.job.data["telegram_id"]
    try:
        from handlers.weekly_review import send_weekly_review
        await send_weekly_review(telegram_id, context.bot)
    except Exception as e:
        logger.error("Errore job revisione settimanale: user=%s err=%s", telegram_id, e, exc_info=True)


async def _job_reengagement(context) -> None:
    telegram_id = context.job.data["telegram_id"]
    try:
        from handlers.re_engagement import check_and_send
        await check_and_send(telegram_id, context)
    except Exception as e:
        logger.error("Errore job re-engagement: user=%s err=%s", telegram_id, e, exc_info=True)


async def _job_weekly_summary(context) -> None:
    telegram_id = context.job.data["telegram_id"]
    try:
        from db.queries import get_or_create_user, get_recent_weekly_summaries
        from services.memory import get_or_create_profile
        from services.weekly_summary import generate_narrative, save_weekly_summary

        user = get_or_create_user(telegram_id)
        user_id = user["id"]
        profile = get_or_create_profile(telegram_id)
        summaries = get_recent_weekly_summaries(user_id, limit=3)

        week_data = {
            "strategic_sessions": profile.counters.total_strategic_sessions,
            "ideas_parked": len([p for p in profile.parking_lot if p.status == "parked"]),
        }
        narrative, tone = generate_narrative(profile, week_data, summaries)
        save_weekly_summary(user_id, week_data, narrative, tone)
        logger.info("Riassunto settimanale generato: user=%s", telegram_id)
    except Exception as e:
        logger.error("Errore job riassunto: user=%s err=%s", telegram_id, e, exc_info=True)
