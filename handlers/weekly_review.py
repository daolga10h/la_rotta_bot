import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from models.user_profile import UserProfileData, ParkingItem
from services.memory import save_profile
from utils.state_manager import set_state, clear_state
from utils.formatters import make_keyboard

logger = logging.getLogger(__name__)

_KB_EVAL = make_keyboard([["Buona"], ["Mista"], ["Difficile"]])
_KB_HOURS = make_keyboard([["Erano necessarie"], ["Potevo gestirlo diversamente"], ["Non voglio rispondere ora"]])
_KB_PATTERN_OP = make_keyboard([["Capire cosa succede"], ["Solo registrarlo"]])
_KB_PATTERN_SC = make_keyboard([["Sì, probabilmente"], ["No, è solo stata una settimana difficile"]])
_KB_PARKING_YN = make_keyboard([["Sì, le vedo tutte"], ["Solo quelle vecchie"], ["Dopo"]])
_KB_PARKING_ITEM = make_keyboard([["Sviluppa questa settimana"], ["Rimanda di una settimana"], ["Elimina"]])
_KB_CHANGE = make_keyboard([["No, va bene così"], ["Sì, voglio aggiornare qualcosa"]])
_KB_CHANGE_WHAT = make_keyboard([["Cambio un obiettivo"], ["Cambio le ore target"]])


async def _reply(update: Update, text: str, keyboard=None) -> None:
    kwargs = {"parse_mode": "Markdown"}
    if keyboard:
        kwargs["reply_markup"] = keyboard
    if update.message:
        await update.message.reply_text(text, **kwargs)
    else:
        await update.callback_query.message.reply_text(text, **kwargs)


# â”€â”€ Entry point (scheduler) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def send_weekly_review(telegram_id: int, bot) -> None:
    from db.queries import get_or_create_user
    from services.memory import get_or_create_profile

    user = get_or_create_user(telegram_id)
    user_id = user["id"]
    profile = get_or_create_profile(telegram_id)

    profile.weekly_review_data = {"strategic_sessions": profile.counters.total_strategic_sessions}
    save_profile(telegram_id, profile)

    set_state(user_id, "WEEKLY_REVIEW_PROGRESS_Q")
    await bot.send_message(
        chat_id=telegram_id,
        text=(
            "Settimana appena finita.\n\n"
            "Prima di guardare i numeri: cosa hai fatto questa settimana "
            "di cui sei soddisfatta â€” anche una sola cosa?"
        ),
        parse_mode="Markdown",
    )


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
        "WEEKLY_REVIEW_PROGRESS_Q":   _progress_q,
        "WEEKLY_REVIEW_EVAL":         _evaluation,
        "WEEKLY_REVIEW_HOURS":        _hours_response,
        "WEEKLY_REVIEW_HOURS_WHY":    _hours_why,
        "WEEKLY_REVIEW_PATTERN_OP":   _pattern_operative,
        "WEEKLY_REVIEW_PATTERN_SC":   _pattern_scenario_c,
        "WEEKLY_REVIEW_PARKING_YN":   _parking_yn,
        "WEEKLY_REVIEW_PARKING_ITEM": _parking_item,
        "WEEKLY_REVIEW_PARKING_DEV1": _parking_dev1,
        "WEEKLY_REVIEW_PARKING_DEV2": _parking_dev2,
        "WEEKLY_REVIEW_PARKING_DEV3": _parking_dev3,
        "WEEKLY_REVIEW_CLOSE":        _close,
        "WEEKLY_REVIEW_CHANGE":       _change_what,
    }
    fn = dispatch.get(state)
    if fn:
        await fn(update, context, user_id, telegram_id, text, profile)
    else:
        logger.warning("Stato revisione settimanale sconosciuto: %s", state)
        from utils.fallback import not_understood
        await not_understood(update, "Scusa, non ho capito. Puoi riformulare?")


# â”€â”€ Step 1: Progresso soggettivo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _progress_q(update, context, user_id, telegram_id, text, profile):
    data = profile.weekly_review_data or {}
    data["week_highlight"] = text
    profile.weekly_review_data = data
    save_profile(telegram_id, profile)

    # Riepilogo numerico
    c = profile.counters
    obj2 = next((o for o in profile.objectives if o.rank == 2), None)
    hours_target = obj2.weekly_hours_target if obj2 else None
    target_str = f" su {hours_target}h target" if hours_target else ""

    summary_lines = [
        f"*{text}*",
        "",
        "â†’ Sessioni strategiche: *{}*".format(c.total_strategic_sessions),
        "â†’ Idee nel parcheggio: *{}* in attesa".format(
            len([p for p in profile.parking_lot if p.status == "parked"])
        ),
    ]
    if c.consecutive_weeks_under_target >= 2:
        summary_lines.append(
            f"\nQuesta è la *{c.consecutive_weeks_under_target}Âª settimana consecutiva* "
            f"sotto obiettivo per Oltre la Bottega."
        )

    summary_lines.append("\nCome valuti questa settimana complessivamente?")
    set_state(user_id, "WEEKLY_REVIEW_EVAL")
    await _reply(update, "\n".join(summary_lines), _KB_EVAL)


# â”€â”€ Step 2: Valutazione â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _evaluation(update, context, user_id, telegram_id, text, profile):
    data = profile.weekly_review_data or {}
    data["evaluation"] = text.lower()
    profile.weekly_review_data = data
    save_profile(telegram_id, profile)

    # Pattern recognition operative
    if profile.counters.consecutive_operative_days >= 5:
        set_state(user_id, "WEEKLY_REVIEW_PATTERN_OP")
        await _reply(
            update,
            "Questa settimana â€” e quella prima â€” sono state completamente operative.\n"
            "Vuoi capire cosa sta succedendo o preferisci solo registrarlo?",
            _KB_PATTERN_OP,
        )
        return

    # Pattern recognition Scenario C
    sc_count = data.get("scenario_c_count", 0)
    if sc_count >= 3:
        set_state(user_id, "WEEKLY_REVIEW_PATTERN_SC")
        await _reply(
            update,
            "Questa settimana ci siamo ritrovati tre volte in un momento di blocco.\n"
            "C'è qualcosa di più grande che sta pesando?",
            _KB_PATTERN_SC,
        )
        return

    await _go_to_hours(update, user_id, telegram_id, profile)


# â”€â”€ Pattern recognition â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _pattern_operative(update, context, user_id, telegram_id, text, profile):
    await _go_to_hours(update, user_id, telegram_id, profile)


async def _pattern_scenario_c(update, context, user_id, telegram_id, text, profile):
    await _go_to_hours(update, user_id, telegram_id, profile)


async def _go_to_hours(update, user_id, telegram_id, profile):
    obj2 = next((o for o in profile.objectives if o.rank == 2), None)
    if obj2 and obj2.weekly_hours_target:
        set_state(user_id, "WEEKLY_REVIEW_HOURS")
        await _reply(
            update,
            f"Le ore per *{obj2.title}*: il negozio aveva davvero bisogno di te, "
            f"o qualcosa le ha assorbite che potevi rimandare?",
            _KB_HOURS,
        )
    else:
        await _go_to_parking(update, user_id, telegram_id, profile)


# â”€â”€ Step 3: Ore target â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _hours_response(update, context, user_id, telegram_id, text, profile):
    if "diversamente" in text.lower():
        set_state(user_id, "WEEKLY_REVIEW_HOURS_WHY")
        await _reply(update, "Cosa ha assorbito quelle ore?")
    else:
        if "necessarie" in text.lower():
            profile.counters.consecutive_weeks_under_target = 0
            save_profile(telegram_id, profile)
        await _go_to_parking(update, user_id, telegram_id, profile)


async def _hours_why(update, context, user_id, telegram_id, text, profile):
    data = profile.weekly_review_data or {}
    data["hours_absorbed_by"] = text
    profile.weekly_review_data = data
    profile.counters.consecutive_weeks_under_target += 1
    save_profile(telegram_id, profile)
    await _go_to_parking(update, user_id, telegram_id, profile)


# â”€â”€ Step 4: Parcheggio â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _go_to_parking(update, user_id, telegram_id, profile):
    active = [p for p in profile.parking_lot if p.status == "parked"]
    if not active:
        await _go_to_close(update, user_id, telegram_id, profile)
        return

    set_state(user_id, "WEEKLY_REVIEW_PARKING_YN")
    await _reply(
        update,
        f"Hai *{len(active)} {'idea' if len(active) == 1 else 'idee'}* nel parcheggio. Le rivediamo?",
        _KB_PARKING_YN,
    )


async def _parking_yn(update, context, user_id, telegram_id, text, profile):
    text_lower = text.lower()
    if "dopo" in text_lower:
        await _go_to_close(update, user_id, telegram_id, profile)
        return

    active = [p for p in profile.parking_lot if p.status == "parked"]
    old_only = "vecchie" in text_lower
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    if old_only:
        items_to_review = [p for p in active if p.created_at < thirty_days_ago]
    else:
        items_to_review = active

    if not items_to_review:
        await _reply(update, "Nessuna idea vecchia da rivedere.")
        await _go_to_close(update, user_id, telegram_id, profile)
        return

    # Salva lista da rivedere e indice corrente
    data = profile.weekly_review_data or {}
    data["items_to_review"] = [p.id for p in items_to_review]
    data["review_index"] = 0
    profile.weekly_review_data = data
    save_profile(telegram_id, profile)

    set_state(user_id, "WEEKLY_REVIEW_PARKING_ITEM")
    await _show_parking_item(update, profile)


async def _show_parking_item(update, profile):
    data = profile.weekly_review_data or {}
    items_ids = data.get("items_to_review", [])
    idx = data.get("review_index", 0)

    if idx >= len(items_ids):
        return  # chiamante gestisce il passaggio allo step successivo

    item_id = items_ids[idx]
    item = next((p for p in profile.parking_lot if p.id == item_id), None)
    if not item:
        return

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    old_tag = " â° _In attesa da 30+ giorni_" if item.created_at < thirty_days_ago else ""

    await _reply(
        update,
        f"*{item.content}*{old_tag}\n_{item.category}_",
        _KB_PARKING_ITEM,
    )


async def _parking_item(update, context, user_id, telegram_id, text, profile):
    data = profile.weekly_review_data or {}
    items_ids = data.get("items_to_review", [])
    idx = data.get("review_index", 0)

    if idx < len(items_ids):
        item_id = items_ids[idx]
        item = next((p for p in profile.parking_lot if p.id == item_id), None)

        if item:
            if "sviluppa" in text.lower():
                data["developing_item_id"] = item_id
                profile.weekly_review_data = data
                save_profile(telegram_id, profile)
                set_state(user_id, "WEEKLY_REVIEW_PARKING_DEV1")
                await _reply(update, "Questa idea serve principalmente la Bottega o Oltre la Bottega?")
                return

            elif "elimina" in text.lower():
                profile.parking_lot = [
                    (ParkingItem(**{**p.model_dump(), "status": "deleted"}) if p.id == item_id else p)
                    for p in profile.parking_lot
                ]

            # Rimanda o eliminata: vai al prossimo item

    data["review_index"] = idx + 1
    profile.weekly_review_data = data
    save_profile(telegram_id, profile)

    if data["review_index"] >= len(items_ids):
        await _go_to_close(update, user_id, telegram_id, profile)
    else:
        await _show_parking_item(update, profile)


# â”€â”€ Flusso sviluppo idea (3 domande) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _parking_dev1(update, context, user_id, telegram_id, text, profile):
    data = profile.weekly_review_data or {}
    data["dev_1"] = text
    profile.weekly_review_data = data
    save_profile(telegram_id, profile)
    set_state(user_id, "WEEKLY_REVIEW_PARKING_DEV2")
    await _reply(update, "Quanto tempo richiederebbe a regime â€” ore a settimana?")


async def _parking_dev2(update, context, user_id, telegram_id, text, profile):
    data = profile.weekly_review_data or {}
    data["dev_2"] = text
    profile.weekly_review_data = data
    save_profile(telegram_id, profile)
    set_state(user_id, "WEEKLY_REVIEW_PARKING_DEV3")
    await _reply(update, "Hai già qualcosa di simile in sospeso o già provato?")


async def _parking_dev3(update, context, user_id, telegram_id, text, profile):
    data = profile.weekly_review_data or {}
    item_id = data.get("developing_item_id")
    if item_id:
        profile.parking_lot = [
            (ParkingItem(**{**p.model_dump(), "status": "promoted", "last_reviewed_at": datetime.now(timezone.utc)})
             if p.id == item_id else p)
            for p in profile.parking_lot
        ]

    # Avanza alla prossima idea
    data["review_index"] = data.get("review_index", 0) + 1
    profile.weekly_review_data = data
    save_profile(telegram_id, profile)

    items_ids = data.get("items_to_review", [])
    if data["review_index"] >= len(items_ids):
        set_state(user_id, "WEEKLY_REVIEW_PARKING_ITEM")
        await _go_to_close(update, user_id, telegram_id, profile)
    else:
        set_state(user_id, "WEEKLY_REVIEW_PARKING_ITEM")
        await _show_parking_item(update, profile)


# â”€â”€ Step 5: Chiusura â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _go_to_close(update, user_id, telegram_id, profile):
    set_state(user_id, "WEEKLY_REVIEW_CLOSE")
    await _reply(
        update,
        "Vuoi cambiare qualcosa per la settimana che viene?",
        _KB_CHANGE,
    )


async def _close(update, context, user_id, telegram_id, text, profile):
    if text.lower().startswith("sì"):
        set_state(user_id, "WEEKLY_REVIEW_CHANGE")
        await _reply(update, "Cosa vuoi aggiornare?", _KB_CHANGE_WHAT)
    else:
        await _finish(update, user_id, telegram_id, profile)


async def _change_what(update, context, user_id, telegram_id, text, profile):
    # Routing verso aggiornamento obiettivi
    clear_state(user_id)
    from handlers.onboarding import handle_objectives_update
    set_state(user_id, "OBJECTIVES_UPDATE_1")
    await handle_objectives_update(update, context, user_id, telegram_id, "OBJECTIVES_UPDATE_1", text, profile)


async def _finish(update, user_id, telegram_id, profile):
    # Genera riassunto narrativo
    from services.weekly_summary import generate_narrative, save_weekly_summary
    from db.queries import get_or_create_user, get_recent_weekly_summaries

    user = get_or_create_user(telegram_id)
    user_id_db = user["id"]
    summaries = get_recent_weekly_summaries(user_id_db, limit=3)

    week_data = profile.weekly_review_data or {}
    week_data["strategic_sessions"] = profile.counters.total_strategic_sessions
    week_data["ideas_parked"] = len([p for p in profile.parking_lot if p.status == "parked"])

    narrative, tone = generate_narrative(profile, week_data, summaries)
    save_weekly_summary(user_id_db, week_data, narrative, tone)

    # Reset dati temporanei
    profile.weekly_review_data = None
    save_profile(telegram_id, profile)
    clear_state(user_id)

    await _reply(update, "A domenica prossima.")
