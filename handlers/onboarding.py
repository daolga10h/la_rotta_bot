import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from models.user_profile import UserProfileData, Objective
from services.memory import get_or_create_profile, save_profile
from utils.state_manager import set_state, clear_state
from utils.formatters import make_keyboard
from db.queries import get_or_create_user
from db.client import supabase

logger = logging.getLogger(__name__)

# Testi fissi dalla spec
_Q1 = (
    "Benvenuta. Sono qui per aiutarti a non perdere di vista quello che conta davvero "
    "mentre gestisci il caos quotidiano.\n"
    "Ti faccio qualche domanda per conoscerti — una alla volta.\n\n"
    "Prima: cosa fai, in due righe?"
)
_Q2 = "Quali sono i tuoi obiettivi principali adesso?\nDimmi il primo — il più importante."
_Q2_MORE = "Ce n'è un secondo?"
_Q2_SECOND = "Qual è il secondo obiettivo?"
_Q2_MORE2 = "Ce n'è un terzo?"
_Q2_THIRD = "Qual è il terzo obiettivo?"
_Q4 = (
    "C'è una motivazione di fondo che guida tutto questo?\n"
    "Qualcosa che vuoi per la tua vita, non solo per il lavoro."
)
_Q5 = "A che ora vuoi il check-in serale?\nIl default è 21:30 — va bene o preferisci un altro orario?"
_Q5B = "Che ora preferisci? (es. 20:00)"
_Q6 = "Quando vuoi la revisione settimanale?"
_Q6B = "Dimmi giorno e ora (es. 'sabato 17:00')"


async def _reply(update: Update, text: str, keyboard=None) -> None:
    kwargs = {"parse_mode": "Markdown"}
    if keyboard:
        kwargs["reply_markup"] = keyboard
    if update.message:
        await update.message.reply_text(text, **kwargs)
    else:
        await update.callback_query.message.reply_text(text, **kwargs)


def _hours_q(obj: Objective) -> str:
    return f"Quante ore a settimana vuoi dedicare a *{obj.title}*?\n(puoi rispondere con un numero, es. '6')"


def _summary(profile: UserProfileData) -> str:
    objs = "\n".join(
        f"  {o.rank}. {o.title}" + (f" ({o.weekly_hours_target}h/sett.)" if o.weekly_hours_target else "")
        for o in sorted(profile.objectives, key=lambda o: o.rank)
    )
    anchor = f"Motivazione: _{profile.motivation_anchor}_" if profile.motivation_anchor else ""
    return (
        f"Ecco quello che ho capito:\n{objs}\n{anchor}\n"
        f"Check-in: ore *{profile.checkin_time_evening}*\n"
        f"Revisione: *{profile.review_day} {profile.review_time}*\n\n"
        "È tutto corretto?"
    )


def _parse_hours(text: str) -> float | None:
    nums = re.findall(r'\d+(?:[.,]\d+)?', text)
    if nums:
        return float(nums[0].replace(',', '.'))
    return None


def _parse_time(text: str) -> str:
    match = re.search(r'\b(\d{1,2})[:\.](\d{2})\b', text)
    if match:
        return f"{int(match.group(1)):02d}:{match.group(2)}"
    match = re.search(r'\b(\d{1,2})\b', text)
    if match:
        return f"{int(match.group(1)):02d}:00"
    return "21:30"


def _parse_review(text: str) -> tuple[str, str]:
    giorni = {
        "lun": "lunedì", "mar": "martedì", "mer": "mercoledì",
        "gio": "giovedì", "ven": "venerdì", "sab": "sabato", "dom": "domenica",
    }
    day = "domenica"
    for prefix, name in giorni.items():
        if prefix in text.lower():
            day = name
            break
    time = _parse_time(text) if re.search(r'\d', text) else "18:00"
    return day, time


# ── Entry points ──────────────────────────────────────────────────────────────

async def start_onboarding(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user_id: str, telegram_id: int,
) -> None:
    profile = get_or_create_profile(telegram_id)
    profile.onboarding_step = 1
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_1")
    await _reply(update, _Q1)


async def resume_onboarding(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user_id: str, telegram_id: int, profile: UserProfileData,
) -> None:
    step = profile.onboarding_step
    await _reply(
        update,
        f"Prima di iniziare, ho bisogno di altre informazioni. "
        f"Continuiamo da dove ci siamo fermati?",
        make_keyboard([["Sì, continuiamo"]]),
    )
    set_state(user_id, f"ONBOARDING_{step}")


# ── Step dispatcher ───────────────────────────────────────────────────────────

async def handle_step(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user_id: str, telegram_id: int,
    state: str, text: str, profile: UserProfileData,
) -> None:
    dispatch = {
        "ONBOARDING_1":       _step1,
        "ONBOARDING_2":       _step2,
        "ONBOARDING_2_MORE":  _step2_more,
        "ONBOARDING_2B":      _step2b,
        "ONBOARDING_2B_MORE": _step2b_more,
        "ONBOARDING_2C":      _step2c,
        "ONBOARDING_3":       _step3,
        "ONBOARDING_3B":      _step3b,
        "ONBOARDING_4":       _step4,
        "ONBOARDING_5":       _step5,
        "ONBOARDING_5B":      _step5b,
        "ONBOARDING_6":       _step6,
        "ONBOARDING_6B":      _step6b,
        "ONBOARDING_7":       _step7,
    }
    fn = dispatch.get(state)
    if fn:
        await fn(update, context, user_id, telegram_id, text, profile)
    else:
        logger.warning("Stato onboarding sconosciuto: %s", state)
        await _reply(update, "Qualcosa non ha funzionato. Riproviamo?")
        set_state(user_id, "ONBOARDING_1")


async def handle_objectives_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user_id: str, telegram_id: int,
    state: str, text: str, profile: UserProfileData,
) -> None:
    # Flusso aggiornamento obiettivi (Fase 12)
    msg = update.message or update.callback_query.message
    await msg.reply_text("[aggiornamento obiettivi — in arrivo]")


# ── Step implementations ──────────────────────────────────────────────────────

async def _step1(update, context, user_id, telegram_id, text, profile):
    profile.user_context = text
    profile.onboarding_step = 2
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_2")
    await _reply(update, _Q2)


async def _step2(update, context, user_id, telegram_id, text, profile):
    obj = Objective(title=text, rank=1)
    profile.objectives = [obj]
    profile.onboarding_step = 3
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_2_MORE")
    await _reply(update, _Q2_MORE, make_keyboard([["Sì"], ["No, per ora è uno solo"]]))


async def _step2_more(update, context, user_id, telegram_id, text, profile):
    if text.lower().startswith("sì") or text.lower().startswith("si"):
        set_state(user_id, "ONBOARDING_2B")
        await _reply(update, _Q2_SECOND)
    else:
        # Salta a motivazione (nessun obiettivo rank>1 → nessun step ore)
        profile.onboarding_step = 4
        save_profile(telegram_id, profile)
        set_state(user_id, "ONBOARDING_4")
        await _reply(update, _Q4)


async def _step2b(update, context, user_id, telegram_id, text, profile):
    obj = Objective(title=text, rank=2)
    objectives = [o for o in profile.objectives if o.rank != 2]
    objectives.append(obj)
    profile.objectives = objectives
    profile.onboarding_step = 4
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_2B_MORE")
    await _reply(update, _Q2_MORE2, make_keyboard([["Sì"], ["No, è tutto"]]))


async def _step2b_more(update, context, user_id, telegram_id, text, profile):
    if text.lower().startswith("sì") or text.lower().startswith("si"):
        set_state(user_id, "ONBOARDING_2C")
        await _reply(update, _Q2_THIRD)
    else:
        # Ha 2 obiettivi → chiede le ore per il rank 2
        obj2 = next((o for o in profile.objectives if o.rank == 2), None)
        if obj2:
            set_state(user_id, "ONBOARDING_3")
            await _reply(update, _hours_q(obj2))
        else:
            set_state(user_id, "ONBOARDING_4")
            await _reply(update, _Q4)


async def _step2c(update, context, user_id, telegram_id, text, profile):
    obj = Objective(title=text, rank=3)
    objectives = [o for o in profile.objectives if o.rank != 3]
    objectives.append(obj)
    profile.objectives = objectives
    save_profile(telegram_id, profile)
    # Ha 3 obiettivi → chiede le ore per il rank 2
    obj2 = next((o for o in profile.objectives if o.rank == 2), None)
    if obj2:
        set_state(user_id, "ONBOARDING_3")
        await _reply(update, _hours_q(obj2))
    else:
        set_state(user_id, "ONBOARDING_4")
        await _reply(update, _Q4)


async def _step3(update, context, user_id, telegram_id, text, profile):
    hours = _parse_hours(text)
    objectives = []
    for o in profile.objectives:
        if o.rank == 2:
            objectives.append(Objective(title=o.title, rank=2, weekly_hours_target=hours))
        else:
            objectives.append(o)
    profile.objectives = objectives
    save_profile(telegram_id, profile)

    obj3 = next((o for o in profile.objectives if o.rank == 3), None)
    if obj3:
        set_state(user_id, "ONBOARDING_3B")
        await _reply(update, _hours_q(obj3))
    else:
        set_state(user_id, "ONBOARDING_4")
        await _reply(update, _Q4)


async def _step3b(update, context, user_id, telegram_id, text, profile):
    hours = _parse_hours(text)
    objectives = []
    for o in profile.objectives:
        if o.rank == 3:
            objectives.append(Objective(title=o.title, rank=3, weekly_hours_target=hours))
        else:
            objectives.append(o)
    profile.objectives = objectives
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_4")
    await _reply(update, _Q4)


async def _step4(update, context, user_id, telegram_id, text, profile):
    profile.motivation_anchor = text
    profile.onboarding_step = 5
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_5")
    await _reply(update, _Q5, make_keyboard([["21:30 va bene"], ["Cambio orario"]]))


async def _step5(update, context, user_id, telegram_id, text, profile):
    if "cambio" in text.lower():
        set_state(user_id, "ONBOARDING_5B")
        await _reply(update, _Q5B)
    else:
        profile.checkin_time_evening = "21:30"
        profile.onboarding_step = 6
        save_profile(telegram_id, profile)
        set_state(user_id, "ONBOARDING_6")
        await _reply(update, _Q6, make_keyboard([["Domenica sera 18:00"], ["Scelgo giorno e ora"]]))


async def _step5b(update, context, user_id, telegram_id, text, profile):
    profile.checkin_time_evening = _parse_time(text)
    profile.onboarding_step = 6
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_6")
    await _reply(update, _Q6, make_keyboard([["Domenica sera 18:00"], ["Scelgo giorno e ora"]]))


async def _step6(update, context, user_id, telegram_id, text, profile):
    if "scelgo" in text.lower():
        set_state(user_id, "ONBOARDING_6B")
        await _reply(update, _Q6B)
    else:
        profile.review_day = "domenica"
        profile.review_time = "18:00"
        profile.onboarding_step = 7
        save_profile(telegram_id, profile)
        set_state(user_id, "ONBOARDING_7")
        await _reply(update, _summary(profile), make_keyboard([["Sì, iniziamo"], ["Voglio correggere qualcosa"]]))


async def _step6b(update, context, user_id, telegram_id, text, profile):
    day, time = _parse_review(text)
    profile.review_day = day
    profile.review_time = time
    profile.onboarding_step = 7
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_7")
    await _reply(update, _summary(profile), make_keyboard([["Sì, iniziamo"], ["Voglio correggere qualcosa"]]))


async def _step7(update, context, user_id, telegram_id, text, profile):
    if "sì" in text.lower() or "si," in text.lower() or text.lower().startswith("sì"):
        profile.onboarding_complete = True
        save_profile(telegram_id, profile)
        # Aggiorna anche la tabella users
        user = get_or_create_user(telegram_id)
        supabase.table("users").update({
            "onboarding_complete": True,
            "onboarding_step": 7,
        }).eq("id", user["id"]).execute()
        clear_state(user_id)
        await _reply(
            update,
            "Perfetto. Da stasera alle {} ti mando il check-in.\n\nBuona rotta.".format(
                profile.checkin_time_evening
            ),
        )
    else:
        # L'utente vuole correggere qualcosa
        set_state(user_id, "ONBOARDING_1")
        profile.onboarding_step = 1
        save_profile(telegram_id, profile)
        await _reply(
            update,
            "Certo. Ricominciamo dall'inizio — sarà più veloce.\n\n" + _Q1,
        )
