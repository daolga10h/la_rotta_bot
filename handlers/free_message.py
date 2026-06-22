import logging
from telegram import Update
from telegram.ext import ContextTypes
from models.user_profile import UserProfileData
from services.classifier import classify_message
from services.response_generator import generate_response
from services.memory import save_profile
from utils.state_manager import set_state, clear_state
from utils.formatters import make_keyboard
from db.queries import get_recent_messages, save_message

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.85

_CATEGORY_LABELS = {
    "IDEA":     "un'idea da parcheggiare",
    "UPDATE":   "un aggiornamento su qualcosa che stai facendo",
    "BLOCCO":   "una richiesta di aiuto o sblocco",
    "DOMANDA":  "una domanda per me",
    "FEEDBACK": "un commento su una mia risposta",
}

_KB_CONFIRM = make_keyboard([["✓ Corretto", "✗ Non è questo"]])
_KB_CATEGORIES = make_keyboard([
    ["Un'idea"],
    ["Un aggiornamento"],
    ["Ho un blocco"],
    ["Una domanda"],
    ["Feedback su qualcosa che hai detto"],
])
_KB_INTENTION_YN = make_keyboard([["Sì"], ["No, grazie"]])


async def _reply(update: Update, text: str, keyboard=None) -> None:
    kwargs = {"parse_mode": "Markdown"}
    if keyboard:
        kwargs["reply_markup"] = keyboard
    if update.message:
        await update.message.reply_text(text, **kwargs)
    else:
        await update.callback_query.message.reply_text(text, **kwargs)


# ── Entry point (stato IDLE) ──────────────────────────────────────────────────

async def handle_free_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: str,
    telegram_id: int,
    text: str,
    profile: UserProfileData,
) -> None:
    save_message(user_id, "user", text, flow_name="FREE_MSG")
    recent = get_recent_messages(user_id, limit=3)
    result = classify_message(text, profile.objectives, recent)

    category = result["category"]
    confidence = result["confidence"]

    logger.info("Classificazione messaggio libero: user=%s cat=%s conf=%.2f", telegram_id, category, confidence)

    if confidence < CONFIDENCE_THRESHOLD or category == "AMBIGUO":
        await _ask_clarification(update, user_id, telegram_id, text, profile, result)
        return

    await _show_confirmation(update, user_id, telegram_id, text, profile, category)


# ── Dispatcher per stati FREE_MSG ─────────────────────────────────────────────

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
        "FREE_MSG_CONFIRM":      _confirm,
        "FREE_MSG_CORRECT_CAT":  _correct_category,
        "FREE_MSG_FEEDBACK_1":   _feedback_text,
        "FREE_MSG_UPDATE_INT":   _update_intention,
    }
    fn = dispatch.get(state)
    if fn:
        await fn(update, context, user_id, telegram_id, text, profile)
    else:
        logger.warning("Stato FREE_MSG sconosciuto: %s", state)
        clear_state(user_id)


# ── Conferma categoria ────────────────────────────────────────────────────────

async def _show_confirmation(update, user_id, telegram_id, text, profile, category):
    profile.free_msg_pending = {"text": text, "category": category}
    save_profile(telegram_id, profile)
    set_state(user_id, "FREE_MSG_CONFIRM")

    label = _CATEGORY_LABELS.get(category, "qualcosa")
    await _reply(update, f"Ho capito: {label}.\n✓ Corretto  |  ✗ Non è questo", _KB_CONFIRM)


async def _confirm(update, context, user_id, telegram_id, text, profile):
    if "✓" in text or "corretto" in text.lower():
        pending = profile.free_msg_pending or {}
        category = pending.get("category", "AMBIGUO")
        original_text = pending.get("text", "")
        profile.free_msg_pending = None
        save_profile(telegram_id, profile)
        clear_state(user_id)
        await _route_by_category(update, context, user_id, telegram_id, original_text, profile, category)
    else:
        set_state(user_id, "FREE_MSG_CORRECT_CAT")
        await _reply(update, "Di cosa si tratta?", _KB_CATEGORIES)


async def _correct_category(update, context, user_id, telegram_id, text, profile):
    text_lower = text.lower()
    if "idea" in text_lower:
        category = "IDEA"
    elif "aggiornamento" in text_lower:
        category = "UPDATE"
    elif "blocco" in text_lower or "aiuto" in text_lower:
        category = "BLOCCO"
    elif "domanda" in text_lower:
        category = "DOMANDA"
    elif "feedback" in text_lower or "detto" in text_lower:
        category = "FEEDBACK"
    else:
        category = "AMBIGUO"

    pending = profile.free_msg_pending or {}
    original_text = pending.get("text", "")
    profile.free_msg_pending = None
    save_profile(telegram_id, profile)
    clear_state(user_id)
    await _route_by_category(update, context, user_id, telegram_id, original_text, profile, category)


# ── Disambiguazione AMBIGUO ───────────────────────────────────────────────────

async def _ask_clarification(update, user_id, telegram_id, text, profile, result):
    profile.free_msg_pending = {"text": text, "category": result.get("category", "AMBIGUO")}
    save_profile(telegram_id, profile)
    set_state(user_id, "FREE_MSG_CORRECT_CAT")

    alt = result.get("alternative_category")
    if alt and alt != "AMBIGUO":
        label_a = _CATEGORY_LABELS.get(result["category"], result["category"])
        label_b = _CATEGORY_LABELS.get(alt, alt)
        await _reply(
            update,
            f"Sto cercando di capire meglio: stai condividendo *{label_a}* "
            f"o *{label_b}*?",
            _KB_CATEGORIES,
        )
    else:
        await _reply(update, "Di cosa si tratta?", _KB_CATEGORIES)


# ── Routing per categoria ─────────────────────────────────────────────────────

async def _route_by_category(update, context, user_id, telegram_id, text, profile, category):
    if category == "IDEA":
        from handlers.parking import start_parking
        await start_parking(update, context, user_id, telegram_id, text, profile)

    elif category == "BLOCCO":
        from handlers.scenario_c import start_scenario_c
        await start_scenario_c(update, context, user_id, telegram_id, profile)

    elif category == "UPDATE":
        await _handle_update(update, context, user_id, telegram_id, text, profile)

    elif category == "DOMANDA":
        await _handle_domanda(update, context, user_id, telegram_id, text, profile)

    elif category == "FEEDBACK":
        await _handle_feedback(update, user_id, telegram_id, text, profile)

    else:
        await _reply(update, "Ok, ho capito.")


# ── UPDATE ────────────────────────────────────────────────────────────────────

async def _handle_update(update, context, user_id, telegram_id, text, profile):
    save_message(user_id, "assistant", "", flow_name="UPDATE")

    obj1 = next((o for o in profile.objectives if o.rank == 1), None)
    flow_instructions = (
        f"L'utente ha condiviso un aggiornamento: \"{text}\".\n"
        f"Rispecchia brevemente l'azione menzionata — usa le sue parole.\n"
        f"Collegala se possibile a '{obj1.title if obj1 else 'obiettivo principale'}'.\n"
        f"Poi chiedi: 'Vuoi dichiarare un'intenzione per domani su questo?'"
    )
    response, _ = generate_response(
        profile=profile,
        flow_name="UPDATE",
        flow_instructions=flow_instructions,
        session_messages=[{"role": "user", "content": text}],
    )

    profile.free_msg_pending = {"text": text, "category": "UPDATE"}
    save_profile(telegram_id, profile)
    set_state(user_id, "FREE_MSG_UPDATE_INT")
    await _reply(update, response, _KB_INTENTION_YN)


async def _update_intention(update, context, user_id, telegram_id, text, profile):
    pending = profile.free_msg_pending or {}
    profile.free_msg_pending = None

    if text.lower().startswith("sì"):
        clear_state(user_id)
        # Passa al sub-flusso intenzione del check-in serale
        set_state(user_id, "CHECKIN_EVENING_INT_TEXT")
        from utils.formatters import make_keyboard as _kb
        await _reply(update, "Su cosa lavorerai domani?")
    else:
        save_profile(telegram_id, profile)
        clear_state(user_id)
        await _reply(update, "Ok.")


# ── DOMANDA ───────────────────────────────────────────────────────────────────

async def _handle_domanda(update, context, user_id, telegram_id, text, profile):
    text_lower = text.lower()

    # Risposte dirette da dati strutturati
    if "parcheggio" in text_lower or "idee" in text_lower:
        active = [p for p in profile.parking_lot if p.status == "parked"]
        if active:
            lista = "\n".join(f"• {p.content} _{p.category}_" for p in active)
            await _reply(update, f"Nel parcheggio hai *{len(active)} {'idea' if len(active)==1 else 'idee'}*:\n{lista}")
        else:
            await _reply(update, "Il parcheggio è vuoto al momento.")
        return

    if "obiettiv" in text_lower:
        objs = sorted(profile.objectives, key=lambda o: o.rank)
        if objs:
            lista = "\n".join(f"{o.rank}. {o.title}" + (f" ({o.weekly_hours_target}h/sett.)" if o.weekly_hours_target else "") for o in objs)
            await _reply(update, f"*I tuoi obiettivi:*\n{lista}")
        else:
            await _reply(update, "Non hai ancora definito obiettivi.")
        return

    if "streak" in text_lower or "sessioni" in text_lower or "strategico" in text_lower:
        await _reply(update, f"Hai fatto *{profile.counters.total_strategic_sessions}* sessioni strategiche in totale.\nStreak attuale: *{profile.streak_strategic}*.")
        return

    # Domanda generica → Claude risponde con contesto profilo
    from db.queries import get_recent_weekly_summaries, get_or_create_user
    user = get_or_create_user(telegram_id)
    summaries = get_recent_weekly_summaries(user["id"], limit=3)

    response, _ = generate_response(
        profile=profile,
        flow_name="DOMANDA",
        flow_instructions=f"L'utente ha fatto una domanda: \"{text}\". Rispondi brevemente usando i dati del profilo se rilevanti.",
        session_messages=[{"role": "user", "content": text}],
        weekly_summaries=summaries,
    )
    await _reply(update, response)


# ── FEEDBACK ──────────────────────────────────────────────────────────────────

async def _handle_feedback(update, user_id, telegram_id, text, profile):
    save_message(user_id, "user", text, classified_as="FEEDBACK", flow_name="FEEDBACK")
    set_state(user_id, "FREE_MSG_FEEDBACK_1")
    await _reply(update, "Ho capito. Cosa avresti preferito sentire?")


async def _feedback_text(update, context, user_id, telegram_id, text, profile):
    save_message(user_id, "user", text, classified_as="FEEDBACK_DETAIL", flow_name="FEEDBACK")
    clear_state(user_id)
    await _reply(update, "Grazie. Lo tengo a mente.")
