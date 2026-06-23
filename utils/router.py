import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.state_manager import get_state, clear_state
from db.queries import get_or_create_user

logger = logging.getLogger(__name__)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    user = get_or_create_user(telegram_id)
    user_id = user["id"]
    clear_state(user_id)

    from handlers.onboarding import start_onboarding
    await start_onboarding(update, context, user_id, telegram_id)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    telegram_id = update.effective_user.id
    user = get_or_create_user(telegram_id)
    user_id = user["id"]

    state = get_state(user_id)
    logger.info("Messaggio ricevuto: user=%s state=%s", telegram_id, state)

    await _route(update, context, user_id, telegram_id, state, text=update.message.text)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.callback_query:
        return

    await update.callback_query.answer()
    telegram_id = update.effective_user.id
    user = get_or_create_user(telegram_id)
    user_id = user["id"]

    state = get_state(user_id)
    logger.info("Callback ricevuto: user=%s state=%s data=%s", telegram_id, state, update.callback_query.data)

    await _route(update, context, user_id, telegram_id, state, text=update.callback_query.data)


async def _route(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: str,
    telegram_id: int,
    state: str,
    text: str,
) -> None:
    from services.memory import get_or_create_profile

    # Onboarding non completato — priorità assoluta
    profile = get_or_create_profile(telegram_id)
    if not profile.onboarding_complete and not state.startswith("ONBOARDING"):
        from handlers.onboarding import resume_onboarding
        await resume_onboarding(update, context, user_id, telegram_id, profile)
        return

    # Routing per stato attivo
    if state.startswith("ONBOARDING"):
        from handlers.onboarding import handle_step
        await handle_step(update, context, user_id, telegram_id, state, text, profile)

    elif state.startswith("CHECKIN_EVENING"):
        from handlers.checkin_evening import handle_step
        await handle_step(update, context, user_id, telegram_id, state, text, profile)

    elif state.startswith("CHECKIN_MORNING"):
        from handlers.checkin_morning import handle_step
        await handle_step(update, context, user_id, telegram_id, state, text, profile)

    elif state.startswith("PARKING"):
        from handlers.parking import handle_step
        await handle_step(update, context, user_id, telegram_id, state, text, profile)

    elif state.startswith("SCENARIO_C"):
        from handlers.scenario_c import handle_step
        await handle_step(update, context, user_id, telegram_id, state, text, profile)

    elif state.startswith("WEEKLY_REVIEW"):
        from handlers.weekly_review import handle_step
        await handle_step(update, context, user_id, telegram_id, state, text, profile)

    elif state.startswith("OBJECTIVES_UPDATE"):
        from handlers.onboarding import handle_objectives_update
        await handle_objectives_update(update, context, user_id, telegram_id, state, text, profile)

    elif state.startswith("REENGAGEMENT"):
        from handlers.re_engagement import handle_step, _detect_spontaneous_return
        await handle_step(update, context, user_id, telegram_id, state, text, profile)

    elif state.startswith("FREE_MSG"):
        from handlers.free_message import handle_step
        await handle_step(update, context, user_id, telegram_id, state, text, profile)

    elif text in ("Sì, iniziamo", "Voglio correggere qualcosa") and not profile.onboarding_complete:
        # Safety net: pulsanti onboarding ricevuti con stato IDLE — riprendi dall'ultimo step
        from utils.state_manager import set_state as _set_state
        _set_state(user_id, f"ONBOARDING_{profile.onboarding_step or 7}")
        from handlers.onboarding import handle_step
        await handle_step(update, context, user_id, telegram_id,
                          f"ONBOARDING_{profile.onboarding_step or 7}", text, profile)

    else:
        # Controlla ritorno spontaneo dopo silenzio lungo
        from handlers.re_engagement import _detect_spontaneous_return
        if _detect_spontaneous_return(profile):
            from utils.state_manager import set_state as _set_state
            _set_state(user_id, "REENGAGEMENT_RETURN")
            from handlers.re_engagement import handle_step
            await handle_step(update, context, user_id, telegram_id, "REENGAGEMENT_RETURN", text, profile)
            return

        # IDLE — classifica il messaggio
        from handlers.free_message import handle_free_message
        await handle_free_message(update, context, user_id, telegram_id, text, profile)
