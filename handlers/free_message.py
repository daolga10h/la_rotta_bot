import logging
from telegram import Update
from telegram.ext import ContextTypes
from models.user_profile import UserProfileData
from services.classifier import classify_message
from db.queries import get_recent_messages, get_or_create_user

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.85


async def handle_free_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: str,
    telegram_id: int,
    text: str,
    profile: UserProfileData,
) -> None:
    recent = get_recent_messages(user_id, limit=3)
    result = classify_message(text, profile.objectives, recent)

    category = result["category"]
    confidence = result["confidence"]

    logger.info("Classificazione: user=%s cat=%s conf=%.2f", telegram_id, category, confidence)

    if confidence < CONFIDENCE_THRESHOLD or category == "AMBIGUO":
        await _ask_clarification(update, context, result)
        return

    await _confirm_and_route(update, context, user_id, telegram_id, text, profile, category, confidence)


async def _ask_clarification(update: Update, context: ContextTypes.DEFAULT_TYPE, result: dict) -> None:
    # TODO Fase 12 — mostra pulsanti per chiedere la categoria all'utente
    msg = update.message or update.callback_query.message
    await msg.reply_text("Sto cercando di capire meglio. [chiarimento — in arrivo]")


async def _confirm_and_route(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: str,
    telegram_id: int,
    text: str,
    profile: UserProfileData,
    category: str,
    confidence: float,
) -> None:
    # TODO Fase 12 — mostra conferma con pulsante correzione prima di procedere
    msg = update.message or update.callback_query.message

    if category == "IDEA":
        from handlers.parking import start_parking
        await start_parking(update, context, user_id, telegram_id, text, profile)

    elif category == "BLOCCO":
        from handlers.scenario_c import start_scenario_c
        await start_scenario_c(update, context, user_id, telegram_id, profile)

    elif category in ("UPDATE", "DOMANDA", "FEEDBACK"):
        await msg.reply_text(f"[{category} — risposta in arrivo]")

    else:
        await msg.reply_text("Capito. [routing in arrivo]")
