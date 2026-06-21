import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from models.user_profile import UserProfileData
from services.memory import get_or_create_profile, save_profile
from utils.state_manager import set_state, clear_state
from utils.formatters import make_keyboard

logger = logging.getLogger(__name__)

_KB_DAY3 = make_keyboard([["Sì, torno"], ["Ho bisogno di una pausa"]])
_KB_PAUSE_END = make_keyboard([["Adesso"], ["Tra un'altra settimana"], ["Fammi scrivere io quando sono pronta"]])
_KB_RETURN = make_keyboard([["Sì, ripartiamo"], ["Voglio aggiornare qualcosa prima"]])


async def check_and_send(telegram_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Chiamato dal job scheduler ogni mattina alle 9:00."""
    from db.queries import get_or_create_user
    user = get_or_create_user(telegram_id)
    user_id = user["id"]
    profile = get_or_create_profile(telegram_id)
    re = profile.re_engagement

    now = datetime.now(timezone.utc)

    # Pausa in corso — controlla se è scaduta
    if re.pause_until:
        if now < re.pause_until:
            logger.info("Re-engagement: pausa attiva per user=%s fino a %s", telegram_id, re.pause_until)
            return
        # Pausa scaduta: manda messaggio di ritorno
        re.pause_until = None
        save_profile(telegram_id, profile)
        set_state(user_id, "REENGAGEMENT_PAUSE_END")
        await context.bot.send_message(
            chat_id=telegram_id,
            text="Sono passati 7 giorni. Quando vuoi riprendere?",
            reply_markup=_KB_PAUSE_END,
        )
        return

    if not re.last_response_at:
        return

    days_silent = (now - re.last_response_at).days

    # Giorno 7 — messaggio con motivation anchor poi silenzio
    if days_silent >= 7 and not re.day7_message_sent:
        re.day7_message_sent = True
        save_profile(telegram_id, profile)
        anchor = profile.motivation_anchor or "Il tuo obiettivo è ancora lì."
        await context.bot.send_message(
            chat_id=telegram_id,
            text=f"_{anchor}_\n\nQuesto è ancora lì.",
            parse_mode="Markdown",
        )
        logger.info("Re-engagement giorno 7 inviato: user=%s", telegram_id)
        return

    # Giorno 3 — primo contatto
    if days_silent >= 3 and not re.day3_message_sent:
        re.day3_message_sent = True
        save_profile(telegram_id, profile)
        set_state(user_id, "REENGAGEMENT_DAY3")
        await context.bot.send_message(
            chat_id=telegram_id,
            text="Sono tre giorni che non ci parliamo. Tutto bene?",
            reply_markup=_KB_DAY3,
        )
        logger.info("Re-engagement giorno 3 inviato: user=%s", telegram_id)


# ── Dispatcher ────────────────────────────────────────────────────────────────

async def handle_step(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: str,
    telegram_id: int,
    state: str,
    text: str,
    profile: UserProfileData,
) -> None:
    dispatch = {
        "REENGAGEMENT_DAY3":      _day3_response,
        "REENGAGEMENT_PAUSE_END": _pause_end_response,
        "REENGAGEMENT_RETURN":    _return_response,
    }
    fn = dispatch.get(state)
    if fn:
        await fn(update, context, user_id, telegram_id, text, profile)
    else:
        clear_state(user_id)


async def _day3_response(update, context, user_id, telegram_id, text, profile):
    re = profile.re_engagement

    if text == "Sì, torno":
        re.day3_message_sent = False
        re.day7_message_sent = False
        save_profile(telegram_id, profile)
        clear_state(user_id)
        await _reply(update, "Bentornata. A stasera con il check-in.")

    else:  # "Ho bisogno di una pausa"
        pause_until = datetime.now(timezone.utc) + timedelta(days=7)
        re.pause_until = pause_until
        save_profile(telegram_id, profile)
        clear_state(user_id)
        await _reply(update, "Ok. Ti scrivo tra una settimana.")


async def _pause_end_response(update, context, user_id, telegram_id, text, profile):
    re = profile.re_engagement

    if text == "Adesso":
        re.day3_message_sent = False
        re.day7_message_sent = False
        re.last_response_at = datetime.now(timezone.utc)
        save_profile(telegram_id, profile)
        clear_state(user_id)
        await _reply(update, "Bentornata. A stasera con il check-in.")

    elif "altra settimana" in text.lower():
        re.pause_until = datetime.now(timezone.utc) + timedelta(days=7)
        save_profile(telegram_id, profile)
        clear_state(user_id)
        await _reply(update, "Ok. Ti scrivo tra un'altra settimana.")

    else:  # "Fammi scrivere io quando sono pronta"
        re.pause_until = None
        re.day3_message_sent = True
        re.day7_message_sent = True  # Silenzio totale fino a che non scrive lei
        save_profile(telegram_id, profile)
        clear_state(user_id)
        await _reply(update, "Ok. Sono qui quando vuoi.")


async def _return_response(update, context, user_id, telegram_id, text, profile):
    """Quando l'utente torna spontaneamente dopo silenzio lungo."""
    re = profile.re_engagement
    re.day3_message_sent = False
    re.day7_message_sent = False
    re.last_response_at = datetime.now(timezone.utc)
    save_profile(telegram_id, profile)
    clear_state(user_id)

    if "aggiornare" in text.lower():
        await _reply(update, "Certo. Da dove vuoi iniziare?")
    else:
        await _reply(update, "Bentornata. A stasera con il check-in.")


def _detect_spontaneous_return(profile: UserProfileData) -> bool:
    """True se l'utente ha il day7 inviato — il primo messaggio è un ritorno spontaneo."""
    return profile.re_engagement.day7_message_sent


async def _reply(update: Update, text: str, keyboard=None) -> None:
    kwargs = {}
    if keyboard:
        kwargs["reply_markup"] = keyboard
    if update.message:
        await update.message.reply_text(text, **kwargs)
    else:
        await update.callback_query.message.reply_text(text, **kwargs)
