import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from models.user_profile import UserProfileData, Intention
from services.memory import get_or_create_profile, save_profile
from utils.state_manager import set_state, clear_state
from utils.formatters import make_keyboard
from db.queries import save_message

logger = logging.getLogger(__name__)

_KB_INITIAL = make_keyboard([
    ["Sì, è il piano"],
    ["Ho cambiato idea"],
    ["Non ce la faccio oggi"],
])
_KB_SI_NO = make_keyboard([["Sì"], ["No, è così e basta"]])


async def _reply(update: Update, text: str, keyboard=None) -> None:
    kwargs = {}
    if keyboard:
        kwargs["reply_markup"] = keyboard
    if update.message:
        await update.message.reply_text(text, **kwargs)
    else:
        await update.callback_query.message.reply_text(text, **kwargs)


async def send_if_needed(telegram_id: int, bot) -> None:
    """Inviato dal scheduler â€” solo se intenzione dichiarata e reminder non ancora inviato."""
    from db.queries import get_or_create_user

    user = get_or_create_user(telegram_id)
    user_id = user["id"]
    profile = get_or_create_profile(telegram_id)

    intention = profile.last_intention_declared
    if not intention:
        return
    if intention.morning_reminder_sent:
        return

    set_state(user_id, "CHECKIN_MORNING_START")
    await bot.send_message(
        chat_id=telegram_id,
        text=(
            f"Buongiorno. Ieri sera hai detto che oggi avresti lavorato su:\n"
            f"_\"{intention.text}\"_\n\n"
            f"Ãˆ ancora il piano?"
        ),
        reply_markup=_KB_INITIAL,
        parse_mode="Markdown",
    )
    logger.info("Check-in mattutino inviato: user=%s", telegram_id)


# â”€â”€ Dispatcher â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def handle_step(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user_id: str, telegram_id: int,
    state: str, text: str, profile: UserProfileData,
) -> None:
    dispatch = {
        "CHECKIN_MORNING_START":    _start,
        "CHECKIN_MORNING_CHANGED":  _changed,
        "CHECKIN_MORNING_CANT_WHY": _cant_why,
        "CHECKIN_MORNING_CANT_TEXT": _cant_text,
    }
    fn = dispatch.get(state)
    if fn:
        await fn(update, context, user_id, telegram_id, text, profile)
    else:
        logger.warning("Stato check-in mattutino sconosciuto: %s", state)
        from utils.fallback import not_understood
        await not_understood(update, "Scusa, non ho capito. Puoi riformulare?")


# â”€â”€ Step implementations â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _start(update, context, user_id, telegram_id, text, profile):
    if text == "Sì, è il piano":
        await _mark_sent(profile, telegram_id)
        clear_state(user_id)
        await _reply(update, "In bocca al lupo.")

    elif text == "Ho cambiato idea":
        set_state(user_id, "CHECKIN_MORNING_CHANGED")
        await _reply(update, "Su cosa lavorerai invece?")

    else:  # "Non ce la faccio oggi"
        set_state(user_id, "CHECKIN_MORNING_CANT_WHY")
        await _reply(
            update,
            "Va bene. Vuoi dirmi cos'è cambiato?",
            _KB_SI_NO,
        )


async def _changed(update, context, user_id, telegram_id, text, profile):
    profile.last_intention_declared = Intention(
        text=text,
        declared_at=datetime.now(timezone.utc),
        morning_reminder_sent=True,
    )
    save_profile(telegram_id, profile)
    save_message(user_id, "user", text, flow_name="CHECKIN_MORNING")
    clear_state(user_id)
    await _reply(update, "In bocca al lupo.")


async def _cant_why(update, context, user_id, telegram_id, text, profile):
    if text.lower().startswith("sì") or text.lower().startswith("si"):
        set_state(user_id, "CHECKIN_MORNING_CANT_TEXT")
        await _reply(update, "Cosa è cambiato?")
    else:
        await _cant_close(update, user_id, telegram_id, profile)


async def _cant_text(update, context, user_id, telegram_id, text, profile):
    save_message(user_id, "user", text, flow_name="CHECKIN_MORNING_CANT")
    await _cant_close(update, user_id, telegram_id, profile)


async def _cant_close(update, user_id, telegram_id, profile):
    profile.last_intention_declared = None
    await _mark_sent(profile, telegram_id)
    clear_state(user_id)
    await _reply(update, "Ok. A domani.")


async def _mark_sent(profile: UserProfileData, telegram_id: int) -> None:
    if profile.last_intention_declared:
        profile.last_intention_declared.morning_reminder_sent = True
    save_profile(telegram_id, profile)
