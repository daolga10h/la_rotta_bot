import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from models.user_profile import UserProfileData, Intention
from services.memory import save_profile
from services.response_generator import generate_response
from utils.state_manager import set_state, clear_state
from utils.formatters import make_keyboard
from db.queries import save_checkin_session, get_today_checkin, save_message

logger = logging.getLogger(__name__)

_KB_INITIAL = make_keyboard([
    ["Ho lavorato sull'operativo"],
    ["Ho lavorato su qualcosa di strategico"],
    ["Niente di significativo oggi"],
    ["Non ho voglia / ho dubbi"],
])
_KB_SI_NO = make_keyboard([["Sì"], ["No"]])
_KB_INTENTION = make_keyboard([["Sì"], ["No, non ora"]])
_KB_CHIUDI = make_keyboard([["Sì, ho un'idea"], ["No, buonanotte"]])
_KB_TIME = make_keyboard([["Mattina", "Dopo pranzo"], ["Sera", "Non so ancora"]])
_KB_DURATION = make_keyboard([["15-20 minuti", "Un'ora"], ["Più di un'ora", "Vado a occhio"]])
_KB_YES_NO_ANCHOR = make_keyboard([["Sì"], ["No, grazie"]])


async def _reply(update: Update, text: str, keyboard=None) -> None:
    kwargs = {"parse_mode": "Markdown"}
    if keyboard:
        kwargs["reply_markup"] = keyboard
    if update.message:
        await update.message.reply_text(text, **kwargs)
    else:
        await update.callback_query.message.reply_text(text, **kwargs)


async def send_checkin(telegram_id: int, bot) -> None:
    """Inviato dal scheduler — nessun context Telegram disponibile."""
    from db.queries import get_or_create_user
    from utils.state_manager import set_state as _set_state
    from services.memory import get_or_create_profile

    user = get_or_create_user(telegram_id)
    user_id = user["id"]

    # Idempotenza: non inviare se già inviato oggi
    if get_today_checkin(user_id, "evening"):
        logger.info("Check-in serale già inviato oggi per user=%s", telegram_id)
        return

    save_checkin_session(user_id, {"type": "evening", "date": _today()})
    _set_state(user_id, "CHECKIN_EVENING_START")
    await bot.send_message(
        chat_id=telegram_id,
        text="Dove hai messo l'energia principale oggi?",
        reply_markup=_KB_INITIAL,
    )


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


# ── Dispatcher ────────────────────────────────────────────────────────────────

async def handle_step(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user_id: str, telegram_id: int,
    state: str, text: str, profile: UserProfileData,
) -> None:
    dispatch = {
        "CHECKIN_EVENING_START":        _start,
        "CHECKIN_EVENING_A_STRATEGIC":  _a_strategic,
        "CHECKIN_EVENING_A_WHAT":       _a_what,
        "CHECKIN_EVENING_A_INTENTION":  _ask_intention_yn,
        "CHECKIN_EVENING_B_WHAT":       _b_what,
        "CHECKIN_EVENING_B_INTENTION":  _ask_intention_yn,
        "CHECKIN_EVENING_C_BLOCKER":    _c_blocker,
        "CHECKIN_EVENING_C_INTENTION":  _ask_intention_yn,
        "CHECKIN_EVENING_INT_TEXT":     _intention_text,
        "CHECKIN_EVENING_INT_TIME":     _intention_time,
        "CHECKIN_EVENING_INT_DURATION": _intention_duration,
        "CHECKIN_EVENING_CLOSE":        _close,
    }
    fn = dispatch.get(state)
    if fn:
        await fn(update, context, user_id, telegram_id, text, profile)
    else:
        logger.warning("Stato check-in serale sconosciuto: %s", state)
        clear_state(user_id)


# ── Initial dispatch ──────────────────────────────────────────────────────────

async def _start(update, context, user_id, telegram_id, text, profile):
    obj1 = next((o for o in profile.objectives if o.rank == 1), None)
    obj1_title = obj1.title if obj1 else "il tuo obiettivo principale"

    if "operativo" in text.lower():
        set_state(user_id, "CHECKIN_EVENING_A_STRATEGIC")
        await _reply(
            update,
            f"Il negozio aveva bisogno. Succede.\n"
            f"C'è stato qualcosa, anche piccolo, per *{obj1_title}*?",
            _KB_SI_NO,
        )

    elif "strategico" in text.lower():
        set_state(user_id, "CHECKIN_EVENING_B_WHAT")
        await _reply(update, "Su cosa hai lavorato?")

    elif "niente" in text.lower():
        set_state(user_id, "CHECKIN_EVENING_C_BLOCKER")
        await _reply(update, "Capita. Cosa potrebbe bloccare anche domani?")

    else:
        # "Non ho voglia / ho dubbi" → Scenario C completo (Fase 9)
        clear_state(user_id)
        from handlers.scenario_c import start_scenario_c
        await start_scenario_c(update, context, user_id, telegram_id, profile)


# ── Scenario A ────────────────────────────────────────────────────────────────

async def _a_strategic(update, context, user_id, telegram_id, text, profile):
    if text.lower().startswith("sì") or text.lower().startswith("si"):
        set_state(user_id, "CHECKIN_EVENING_A_WHAT")
        await _reply(update, "Cosa?")
    else:
        set_state(user_id, "CHECKIN_EVENING_A_INTENTION")
        await _reply(
            update,
            "Ok. Vuoi dichiarare un'intenzione per domani — anche solo 20 minuti?",
            _KB_INTENTION,
        )


async def _a_what(update, context, user_id, telegram_id, text, profile):
    save_message(user_id, "user", text, flow_name="CHECKIN_EVENING_A")
    set_state(user_id, "CHECKIN_EVENING_A_INTENTION")
    await _reply(
        update,
        "Vuoi dichiarare un'intenzione per domani?",
        _KB_INTENTION,
    )


# ── Scenario B ────────────────────────────────────────────────────────────────

async def _b_what(update, context, user_id, telegram_id, text, profile):
    save_message(user_id, "user", text, flow_name="CHECKIN_EVENING_B")

    # Aggiorna streak strategico
    profile.streak_strategic += 1
    profile.counters.total_strategic_sessions += 1
    profile.counters.consecutive_operative_days = 0
    save_profile(telegram_id, profile)

    # Risposta con rispecchio usando Claude
    obj1 = next((o for o in profile.objectives if o.rank == 1), None)
    flow_instructions = (
        f"L'utente ha appena detto cosa ha fatto di strategico: \"{text}\".\n"
        f"Rispecchia l'azione specifica che ha menzionato. "
        f"Collegala concretamente a '{obj1.title if obj1 else 'obiettivo principale'}'.\n"
        f"Poi chiedi: 'Vuoi dichiarare un'intenzione per domani?'\n"
        f"Non aggiungere i pulsanti nella risposta — li mandiamo noi."
    )
    response, is_fallback = generate_response(
        profile=profile,
        flow_name="CHECKIN_EVENING_B",
        flow_instructions=flow_instructions,
        session_messages=[{"role": "user", "content": text}],
    )

    streak_msg = ""
    if profile.streak_strategic > 0 and profile.streak_strategic % 5 == 0:
        streak_msg = f"\n_{profile.streak_strategic}° sessione strategica. Stai tenendo la rotta._"

    set_state(user_id, "CHECKIN_EVENING_B_INTENTION")
    await _reply(update, response + streak_msg, _KB_INTENTION)


# ── Scenario C ────────────────────────────────────────────────────────────────

async def _c_blocker(update, context, user_id, telegram_id, text, profile):
    save_message(user_id, "user", text, flow_name="CHECKIN_EVENING_C")
    set_state(user_id, "CHECKIN_EVENING_C_INTENTION")
    await _reply(
        update,
        "Vuoi dichiarare un'intenzione minima per domani — anche solo 15 minuti?",
        _KB_INTENTION,
    )


# ── Shared: intention yn ──────────────────────────────────────────────────────

async def _ask_intention_yn(update, context, user_id, telegram_id, text, profile):
    if text.lower().startswith("sì") or text.lower().startswith("si"):
        set_state(user_id, "CHECKIN_EVENING_INT_TEXT")
        await _reply(update, "Su cosa lavorerai domani?")
    else:
        set_state(user_id, "CHECKIN_EVENING_CLOSE")
        await _reply(update, "Hai qualche idea nuova prima di chiudere?", _KB_CHIUDI)


# ── Shared: implementation intention sub-flow ─────────────────────────────────

async def _intention_text(update, context, user_id, telegram_id, text, profile):
    profile.last_intention_declared = Intention(
        text=text,
        declared_at=datetime.now(timezone.utc),
    )
    save_profile(telegram_id, profile)
    set_state(user_id, "CHECKIN_EVENING_INT_TIME")
    await _reply(update, "A che ora hai in mente di farlo, anche approssimativamente?", _KB_TIME)


async def _intention_time(update, context, user_id, telegram_id, text, profile):
    if profile.last_intention_declared:
        profile.last_intention_declared.time_of_day = text
        save_profile(telegram_id, profile)
    set_state(user_id, "CHECKIN_EVENING_INT_DURATION")
    await _reply(update, "Per quanto tempo — anche un'idea?", _KB_DURATION)


async def _intention_duration(update, context, user_id, telegram_id, text, profile):
    if profile.last_intention_declared:
        profile.last_intention_declared.duration = text
        save_profile(telegram_id, profile)
    set_state(user_id, "CHECKIN_EVENING_CLOSE")
    await _reply(update, "Hai qualche idea nuova prima di chiudere?", _KB_CHIUDI)


# ── Universal closing ─────────────────────────────────────────────────────────

async def _close(update, context, user_id, telegram_id, text, profile):
    profile.counters.total_checkins_completed += 1
    profile.re_engagement.last_response_at = datetime.now(timezone.utc)
    profile.re_engagement.day3_message_sent = False
    profile.re_engagement.day7_message_sent = False
    save_profile(telegram_id, profile)

    if text.lower().startswith("sì") or text.lower().startswith("si"):
        clear_state(user_id)
        from handlers.parking import start_parking
        await start_parking(update, context, user_id, telegram_id, text, profile)
    else:
        clear_state(user_id)
        await _reply(update, "A domani.")
