import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from models.user_profile import UserProfileData, ParkingItem
from services.memory import save_profile
from services.classifier import classify_parking_category
from utils.state_manager import set_state, clear_state
from utils.formatters import make_keyboard
from config import MAX_PARKING_IDEAS

logger = logging.getLogger(__name__)

_CATEGORY_LABELS = {
    "NEGOZIO": "il Negozio",
    "OLTRE_LA_BOTTEGA": "Oltre la Bottega",
    "STRATEGICO_GENERICO": "obiettivi strategici",
}

_TRIGGER_PHRASES = {"sì, ho un'idea", "si, ho un'idea", "sì ho un'idea"}

_KB_CONFIRM = make_keyboard([["âœ“ Corretto", "âœ— Non è questo"]])
_KB_CATEGORY = make_keyboard([["Per il Negozio"], ["Per Oltre la Bottega"], ["Altro"]])
_KB_REDIRECT = make_keyboard([["Sì, torno a qualcosa"], ["No, grazie"]])


async def _reply(update: Update, text: str, keyboard=None) -> None:
    kwargs = {"parse_mode": "Markdown"}
    if keyboard:
        kwargs["reply_markup"] = keyboard
    if update.message:
        await update.message.reply_text(text, **kwargs)
    else:
        await update.callback_query.message.reply_text(text, **kwargs)


# â”€â”€ Entry point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def start_parking(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: str,
    telegram_id: int,
    text: str,
    profile: UserProfileData,
) -> None:
    if text.lower().strip() in _TRIGGER_PHRASES or len(text.strip()) < 8:
        # Venuto da pulsante: chiedi prima l'idea
        set_state(user_id, "PARKING_CAPTURE")
        await _reply(update, "Dimmi l'idea.")
    else:
        await _classify_and_confirm(update, user_id, telegram_id, text, profile)


# â”€â”€ Dispatcher â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
        "PARKING_CAPTURE":  _capture,
        "PARKING_1":        _confirm,
        "PARKING_CORRECT":  _correct_category,
        "PARKING_REDIRECT": _redirect,
    }

    # Gestione rimozione idea (callback "REMOVE_<id>")
    if text.startswith("REMOVE_"):
        await _remove_idea(update, user_id, telegram_id, text, profile)
        return

    fn = dispatch.get(state)
    if fn:
        await fn(update, context, user_id, telegram_id, text, profile)
    else:
        logger.warning("Stato parcheggio sconosciuto: %s", state)
        from utils.fallback import not_understood
        await not_understood(update, "Scusa, non ho capito. Puoi riformulare?")


# â”€â”€ Steps â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _capture(update, context, user_id, telegram_id, text, profile):
    await _classify_and_confirm(update, user_id, telegram_id, text, profile)


async def _classify_and_confirm(update, user_id, telegram_id, text, profile):
    active = [p for p in profile.parking_lot if p.status == "parked"]

    if len(active) >= MAX_PARKING_IDEAS:
        await _show_full_parking(update, user_id, telegram_id, text, profile)
        return

    category = classify_parking_category(text, profile.objectives)
    profile.parking_pending = {"text": text, "category": category}
    save_profile(telegram_id, profile)

    label = _CATEGORY_LABELS.get(category, "obiettivi strategici")
    set_state(user_id, "PARKING_1")
    await _reply(
        update,
        f"Ho capito: nuova idea per *{label}*.\nSalvata nel Parcheggio.",
        _KB_CONFIRM,
    )


async def _confirm(update, context, user_id, telegram_id, text, profile):
    if "âœ“" in text or "corretto" in text.lower():
        await _save_idea(update, user_id, telegram_id, profile)
    else:
        set_state(user_id, "PARKING_CORRECT")
        await _reply(update, "In quale categoria va?", _KB_CATEGORY)


async def _correct_category(update, context, user_id, telegram_id, text, profile):
    if "negozio" in text.lower():
        new_cat = "NEGOZIO"
    elif "oltre" in text.lower():
        new_cat = "OLTRE_LA_BOTTEGA"
    else:
        new_cat = "STRATEGICO_GENERICO"

    if profile.parking_pending:
        profile.parking_pending["category"] = new_cat
        save_profile(telegram_id, profile)

    await _save_idea(update, user_id, telegram_id, profile)


async def _save_idea(update, user_id, telegram_id, profile):
    pending = profile.parking_pending or {}
    text = pending.get("text", "")
    category = pending.get("category", "STRATEGICO_GENERICO")

    item = ParkingItem(
        content=text,
        category=category,
        created_at=datetime.now(timezone.utc),
    )
    profile.parking_lot.append(item)
    profile.counters.total_ideas_parked += 1
    profile.parking_pending = None
    save_profile(telegram_id, profile)

    set_state(user_id, "PARKING_REDIRECT")
    await _reply(
        update,
        "Sei in negozio adesso o hai un momento?\nC'è qualcosa su cui vuoi tornare?",
        _KB_REDIRECT,
    )


async def _redirect(update, context, user_id, telegram_id, text, profile):
    clear_state(user_id)
    if "sì" in text.lower() or "si," in text.lower() or text.lower().startswith("sì"):
        await _reply(update, "Su cosa vuoi tornare?")
    else:
        await _reply(update, "Ok.")


# â”€â”€ Parking pieno â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _show_full_parking(update, user_id, telegram_id, text, profile):
    active = [p for p in profile.parking_lot if p.status == "parked"]

    # Salva l'idea in sospeso anche in questo caso
    category = classify_parking_category(text, profile.objectives)
    profile.parking_pending = {"text": text, "category": category}
    save_profile(telegram_id, profile)

    rows = [[f"Rimuovi: {item.content[:30]}"] for item in active]
    # Usa callback_data con il prefisso REMOVE_ + id
    cbs = [[f"REMOVE_{item.id}"] for item in active]
    kb = make_keyboard(rows, callback_data=cbs)

    set_state(user_id, "PARKING_1")
    await _reply(
        update,
        f"Ho già *{MAX_PARKING_IDEAS} idee* nel parcheggio. "
        f"Prima di aggiungerne un'altra, vuoi rimuoverne una?",
        kb,
    )


async def _remove_idea(update, user_id, telegram_id, text, profile):
    idea_id = text.replace("REMOVE_", "")
    profile.parking_lot = [
        (ParkingItem(**{**p.model_dump(), "status": "deleted"}) if p.id == idea_id else p)
        for p in profile.parking_lot
    ]
    save_profile(telegram_id, profile)

    # Ora procede con il salvataggio dell'idea in sospeso
    await _save_idea(update, user_id, telegram_id, profile)
