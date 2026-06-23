import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from models.user_profile import UserProfileData, Objective
from services.memory import get_or_create_profile, save_profile, save_profile_async
from services.response_generator import generate_response, generate_response_async
from utils.state_manager import set_state, clear_state, set_state_async, clear_state_async
from utils.formatters import make_keyboard
from db.queries import get_or_create_user
from db.client import supabase

logger = logging.getLogger(__name__)

_KB_GENDER = make_keyboard([["Al maschile"], ["Al femminile"]])
_KB_SI_NO_OBJ = make_keyboard([["Sì"], ["No, per ora è uno solo"]])
_KB_SI_NO_TRE = make_keyboard([["Sì"], ["No, è tutto"]])
_KB_CHECKIN = make_keyboard([["21:30 va bene"], ["Cambio orario"]])
_KB_REVIEW = make_keyboard([["Domenica sera 18:00"], ["Scelgo giorno e ora"]])
_KB_CONFIRM = make_keyboard([["Sì, iniziamo"], ["Voglio correggere qualcosa"]])
_KB_CORRECT = make_keyboard([
    ["Il nome"],
    ["Il mio contesto"],
    ["Gli obiettivi"],
    ["La motivazione"],
    ["Gli orari"],
])


async def _reply(update: Update, text: str, keyboard=None) -> None:
    kwargs = {"parse_mode": "Markdown"}
    if keyboard:
        kwargs["reply_markup"] = keyboard
    if update.message:
        await update.message.reply_text(text, **kwargs)
    else:
        await update.callback_query.message.reply_text(text, **kwargs)


async def _claude(profile, instructions, user_text) -> str:
    """Chiamata Claude non bloccante — usa asyncio.to_thread."""
    response, _ = await generate_response_async(
        profile=profile,
        flow_name="ONBOARDING",
        flow_instructions=instructions,
        session_messages=[{"role": "user", "content": user_text}],
    )
    return response


def _hours_q(obj: Objective) -> str:
    return f"Quante ore a settimana vuoi dedicare a *{obj.title}*?\n(anche un numero approssimativo va bene)"


def _summary(profile: UserProfileData) -> str:
    name = profile.user_name or "Benvenuta"
    objs = "\n".join(
        f"  {o.rank}. {o.title}" + (f" ({o.weekly_hours_target}h/sett.)" if o.weekly_hours_target else "")
        for o in sorted(profile.objectives, key=lambda o: o.rank)
    )
    anchor = f"Motivazione: _{profile.motivation_anchor}_" if profile.motivation_anchor else ""
    return (
        f"Ecco quello che ho capito:\n{objs}\n{anchor}\n"
        f"Check-in: ore *{profile.checkin_time_evening}*\n"
        f"Revisione: *{profile.review_day} {profile.review_time}*\n\n"
        f"È tutto corretto?"
    )


def _parse_hours(text: str) -> float | None:
    nums = re.findall(r'\d+(?:[.,]\d+)?', text)
    return float(nums[0].replace(',', '.')) if nums else None


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

def _is_yes(text: str) -> bool:
    """Riconosce 'sì' in tutte le varianti (accento, encoding, testo pulsante)."""
    t = text.lower().strip()
    return (
        t.startswith("sì") or t.startswith("si,") or t.startswith("si ") or
        t == "si" or t == "sì" or "iniziamo" in t
    )


async def start_onboarding(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user_id: str, telegram_id: int,
) -> None:
    profile = get_or_create_profile(telegram_id)
    # Reset completo a ogni /start — garantisce stato consistente
    profile.onboarding_complete = False
    profile.onboarding_step = 0
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_0")
    await _reply(
        update,
        "Ciao. Sono qui per aiutarti a non perdere di vista quello che conta davvero "
        "mentre gestisci il caos quotidiano.\n\n"
        "Prima di tutto: come ti chiami?"
    )


async def resume_onboarding(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user_id: str, telegram_id: int, profile: UserProfileData,
) -> None:
    name = profile.user_name or ""
    greeting = f"{name}, c" if name else "C"
    await _reply(
        update,
        f"{greeting}ontinuiamo da dove ci siamo fermati.",
        make_keyboard([["Sì, continuiamo"]]),
    )
    set_state(user_id, f"ONBOARDING_{profile.onboarding_step}")


# ── Dispatcher ────────────────────────────────────────────────────────────────

_CORRECTION_PHRASES = [
    "ho sbagliato", "sbagliato nome", "nome sbagliato",
    "scusa ho sbagliato", "mi sono sbagliata", "mi sono sbagliato",
    "aspetta", "no aspetta", "voglio correggere", "posso correggere",
    "errore", "è errato", "errato", "è sbagliato", "sbagliato",
    "ho scritto male", "volevo dire altro", "mi sono confusa",
    "no aspetta", "scusa", "ops",
]

# Pattern per rilevare "mi chiamo X" come correzione del nome
import re as _re
_MI_CHIAMO_RE = _re.compile(r'\bmi chiamo\b', _re.IGNORECASE)


def _is_correction_request(text: str) -> bool:
    t = text.lower().strip()
    if _MI_CHIAMO_RE.search(t):
        return True
    return any(phrase in t for phrase in _CORRECTION_PHRASES)


def _correction_target(text: str) -> str | None:
    """Restituisce il campo da correggere se menzionato esplicitamente."""
    t = text.lower()
    if "nome" in t or _MI_CHIAMO_RE.search(t):
        return "nome"
    if "obiettiv" in t:
        return "obiettivi"
    if "motivazione" in t or "ancora" in t:
        return "motivazione"
    if "ora" in t or "orario" in t or "check" in t:
        return "orari"
    return None


def _extract_name_from_text(text: str) -> str | None:
    """Estrae il nome da frasi tipo 'mi chiamo Olga' o 'sono Olga'."""
    match = _re.search(r'mi chiamo\s+(\w+)', text, _re.IGNORECASE)
    if match:
        return match.group(1).capitalize()
    match = _re.search(r'\bsono\s+(\w+)', text, _re.IGNORECASE)
    if match:
        return match.group(1).capitalize()
    return None


async def handle_step(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user_id: str, telegram_id: int,
    state: str, text: str, profile: UserProfileData,
) -> None:
    # Intercetta richieste di correzione in qualsiasi punto dell'onboarding
    if state not in ("ONBOARDING_0", "ONBOARDING_7", "ONBOARDING_CORRECT") and _is_correction_request(text):
        target = _correction_target(text)
        if target == "nome":
            extracted = _extract_name_from_text(text)
            if extracted:
                profile.user_name = extracted
                profile.onboarding_step = 1
                save_profile(telegram_id, profile)
                set_state(user_id, "ONBOARDING_1")
                await _reply(update, f"Corretto — {extracted}. Cosa fai, in due righe?")
            else:
                profile.onboarding_step = 0
                save_profile(telegram_id, profile)
                set_state(user_id, "ONBOARDING_0")
                await _reply(update, "Nessun problema. Come ti chiami?")
        elif target:
            # Correzione specifica: simula ONBOARDING_CORRECT con la scelta già fatta
            set_state(user_id, "ONBOARDING_CORRECT")
            await _step_correct(update, context, user_id, telegram_id, target, profile)
        else:
            # Non specifica cosa correggere: mostra menu
            set_state(user_id, "ONBOARDING_CORRECT")
            await _reply(update, "Certo. Cosa vuoi correggere?", _KB_CORRECT)
        return

    dispatch = {
        "ONBOARDING_0":        _step0,
        "ONBOARDING_0B":       _step0b,
        "ONBOARDING_1":        _step1,
        "ONBOARDING_2":        _step2,
        "ONBOARDING_2_MORE":   _step2_more,
        "ONBOARDING_2B":       _step2b,
        "ONBOARDING_2B_PROBE": _step2b_probe,
        "ONBOARDING_2B_MORE":  _step2b_more,
        "ONBOARDING_2C":       _step2c,
        "ONBOARDING_3":       _step3,
        "ONBOARDING_3B":      _step3b,
        "ONBOARDING_4":       _step4,
        "ONBOARDING_5":       _step5,
        "ONBOARDING_5B":      _step5b,
        "ONBOARDING_6":       _step6,
        "ONBOARDING_6B":      _step6b,
        "ONBOARDING_7":       _step7,
        "ONBOARDING_CORRECT": _step_correct,
    }
    fn = dispatch.get(state)
    if fn:
        await fn(update, context, user_id, telegram_id, text, profile)
    else:
        logger.warning("Stato onboarding sconosciuto: %s", state)
        from utils.fallback import not_understood
        await not_understood(update, "Scusa, non ho capito. Puoi riformulare?")


async def handle_objectives_update(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
    user_id: str, telegram_id: int,
    state: str, text: str, profile: UserProfileData,
) -> None:
    msg = update.message or update.callback_query.message
    await msg.reply_text("[aggiornamento obiettivi — in arrivo]")


# ── Step 0: Nome ──────────────────────────────────────────────────────────────

async def _step0(update, context, user_id, telegram_id, text, profile):
    # Estrae il nome anche da "mi chiamo X" o "sono X"
    extracted = _extract_name_from_text(text)
    raw = extracted if extracted else (text.strip().split() or [""])[0]
    if not raw:
        await _reply(update, "Non ho capito. Come ti chiami?")
        return
    name = raw.capitalize()
    profile.user_name = name
    profile.onboarding_step = 0
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_0B")
    await _reply(
        update,
        f"Ciao {name}! Come preferisci che mi rivolga a te?",
        _KB_GENDER,
    )


async def _step0b(update, context, user_id, telegram_id, text, profile):
    profile.user_gender = "M" if "maschile" in text.lower() else "F"
    profile.onboarding_step = 1
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_1")
    gender_note = "È un uomo." if profile.user_gender == "M" else "È una donna."
    name = profile.user_name or ""
    response = await _claude(
        profile,
        f"L'utente si chiama {name}. {gender_note} "
        f"Fai un breve benvenuto — caldo, diretto, una frase sola. "
        f"Usa il genere corretto negli aggettivi. "
        f"NON fare riferimento a sessioni precedenti o informazioni già note. "
        f"Poi chiedi solo: 'Cosa fai, in due righe?'",
        text,
    )
    await _reply(update, response)


# ── Step 1: Contesto ──────────────────────────────────────────────────────────

async def _step1(update, context, user_id, telegram_id, text, profile):
    profile.user_context = text
    profile.onboarding_step = 2
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_2")
    name = profile.user_name or ""
    response = await _claude(
        profile,
        f"L'utente ha descritto cosa fa: \"{text}\".\n"
        f"In una frase, rispecchia quello che hai capito del loro lavoro — usa le loro parole.\n"
        f"Poi guida verso gli obiettivi in modo che la persona pensi a cosa è davvero importante, "
        f"non solo urgente. Chiedi: qual è la cosa più importante su cui vuoi muoverti adesso — "
        f"non la più urgente, quella che tra un anno ricorderai di aver fatto.",
        text,
    )
    await _reply(update, response)


# ── Step 2: Primo obiettivo ───────────────────────────────────────────────────

async def _step2(update, context, user_id, telegram_id, text, profile):
    obj = Objective(title=text, rank=1)
    profile.objectives = [obj]
    profile.onboarding_step = 3
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_2_MORE")
    response = await _claude(
        profile,
        f"L'utente ha dichiarato il suo primo obiettivo: \"{text}\".\n"
        f"Riconosci in modo concreto perché questo conta — non lodarlo, mostra che hai capito il peso.\n"
        f"Poi chiedi: 'Ce n'è un secondo?' Non aggiungere pulsanti nel testo.",
        text,
    )
    await _reply(update, response, _KB_SI_NO_OBJ)


async def _step2_more(update, context, user_id, telegram_id, text, profile):
    if _is_yes(text):
        obj1 = next((o for o in profile.objectives if o.rank == 1), None)
        set_state(user_id, "ONBOARDING_2B")
        await _reply(
            update,
            f"Oltre a *{obj1.title if obj1 else 'questo'}*, c'è qualcosa di importante "
            f"che vuoi costruire o avviare?\n\n"
            f"Pensa a cosa — tra 6 mesi — ti farebbe dire "
            f"'sono {_g(profile, 'contento', 'contenta')} di averlo fatto'. "
            f"Non cosa è urgente adesso."
        )
    else:
        profile.onboarding_step = 4
        save_profile(telegram_id, profile)
        set_state(user_id, "ONBOARDING_4")
        await _reply(update, _Q4())


async def _step2b(update, context, user_id, telegram_id, text, profile):
    obj = Objective(title=text, rank=2)
    objectives = [o for o in profile.objectives if o.rank != 2]
    objectives.append(obj)
    profile.objectives = objectives
    profile.onboarding_step = 4
    save_profile(telegram_id, profile)

    # Controlla se l'obiettivo è un progetto concreto o un risultato di vita
    is_project = await _is_actionable_project(text, profile)

    if not is_project:
        # Obiettivo outcome-based: aiuta a trovare il progetto concreto dietro
        set_state(user_id, "ONBOARDING_2B_PROBE")
        response = await _claude(
            profile,
            f"L'utente ha dichiarato come secondo obiettivo: \"{text}\".\n"
            f"Questo sembra un risultato desiderato, non un progetto su cui si lavora direttamente.\n"
            f"Riconosci che è un obiettivo importante, poi aiutala a identificare "
            f"il progetto concreto dietro: cosa deve costruire, cambiare o avviare "
            f"per arrivarci davvero? Fai una domanda sola, aperta.",
            text,
        )
        await _reply(update, response)
    else:
        set_state(user_id, "ONBOARDING_2B_MORE")
        response = await _claude(
            profile,
            f"L'utente ha aggiunto un secondo obiettivo: \"{text}\".\n"
            f"Riconosci brevemente come si collega al primo '{profile.objectives[0].title}'.\n"
            f"Poi chiedi: 'Ce n'è un terzo?' Non aggiungere pulsanti.",
            text,
        )
        await _reply(update, response, _KB_SI_NO_TRE)


async def _step2b_probe(update, context, user_id, telegram_id, text, profile):
    """L'utente ha risposto alla domanda sul progetto concreto dietro l'obiettivo outcome."""
    # Aggiorna l'obiettivo rank 2 con la versione più concreta
    old_obj = next((o for o in profile.objectives if o.rank == 2), None)
    old_title = old_obj.title if old_obj else ""

    # Salva la risposta come obiettivo rank 2 aggiornato (più concreto)
    new_title = text if len(text) > 10 else old_title
    objectives = [o for o in profile.objectives if o.rank != 2]
    objectives.append(Objective(title=new_title, rank=2))
    profile.objectives = objectives
    save_profile(telegram_id, profile)

    set_state(user_id, "ONBOARDING_2B_MORE")
    response = await _claude(
        profile,
        f"L'utente ha chiarito il suo secondo obiettivo: \"{text}\" "
        f"(partendo da '{old_title}').\n"
        f"Riconosci brevemente questa chiarezza — ora è qualcosa su cui può lavorare.\n"
        f"Poi chiedi: 'Ce n'è un terzo?' Non aggiungere pulsanti.",
        text,
    )
    await _reply(update, response, _KB_SI_NO_TRE)


async def _step2b_more(update, context, user_id, telegram_id, text, profile):
    if _is_yes(text):
        set_state(user_id, "ONBOARDING_2C")
        await _reply(
            update,
            "E il terzo — se c'è — qual è?\n\n"
            "_Attenzione: tre obiettivi sono già tanti. "
            "Il terzo ha senso solo se è davvero separato dai primi due, "
            "non un modo per fare l'operativo mentre eviti lo strategico._"
        )
    else:
        await _go_to_hours_or_anchor(update, user_id, telegram_id, profile, rank=2)


async def _step2c(update, context, user_id, telegram_id, text, profile):
    obj = Objective(title=text, rank=3)
    objectives = [o for o in profile.objectives if o.rank != 3]
    objectives.append(obj)
    profile.objectives = objectives
    save_profile(telegram_id, profile)
    await _go_to_hours_or_anchor(update, user_id, telegram_id, profile, rank=2)


# ── Step 3: Ore target ────────────────────────────────────────────────────────

async def _step3(update, context, user_id, telegram_id, text, profile):
    hours = _parse_hours(text)
    if hours is None:
        obj2 = next((o for o in profile.objectives if o.rank == 2), None)
        title = obj2.title if obj2 else "questo obiettivo"
        await _reply(
            update,
            f"Non ho trovato un numero. Per *{title}*, quante ore a settimana puoi realisticamente dedicarci?\n"
            f"Anche un'idea vaga — tipo '3 ore', 'un paio di ore', '6'."
        )
        return
    profile.objectives = [
        Objective(title=o.title, rank=2, weekly_hours_target=hours) if o.rank == 2 else o
        for o in profile.objectives
    ]
    await save_profile_async(telegram_id, profile)
    await _go_to_hours_or_anchor(update, user_id, telegram_id, profile, rank=3)


async def _step3b(update, context, user_id, telegram_id, text, profile):
    hours = _parse_hours(text)
    if hours is None:
        obj3 = next((o for o in profile.objectives if o.rank == 3), None)
        title = obj3.title if obj3 else "questo obiettivo"
        await _reply(
            update,
            f"Non ho trovato un numero. Per *{title}*, quante ore a settimana?\n"
            f"Anche approssimativo — tipo '2 ore', '4', 'un paio'."
        )
        return
    profile.objectives = [
        Objective(title=o.title, rank=3, weekly_hours_target=hours) if o.rank == 3 else o
        for o in profile.objectives
    ]
    await save_profile_async(telegram_id, profile)
    await set_state_async(user_id, "ONBOARDING_4")
    await _reply(update, _Q4())


async def _go_to_hours_or_anchor(update, user_id, telegram_id, profile, rank: int):
    """
    Per ogni obiettivo rank>1: classifica il tipo e usa una domanda fissa
    per evitare allucinazioni di Claude.
    """
    obj = next((o for o in profile.objectives if o.rank == rank), None)
    if not obj:
        set_state(user_id, "ONBOARDING_4")
        await _reply(update, _Q4())
        return

    is_project = await _is_actionable_project(obj.title, profile)

    if is_project:
        state = "ONBOARDING_3" if rank == 2 else "ONBOARDING_3B"
        set_state(user_id, state)
        await _reply(
            update,
            f"Quante ore a settimana puoi realisticamente dedicare a *{obj.title}*?\n"
            f"Anche una stima vaga va bene.",
        )
    else:
        # Outcome o obiettivo di qualità di vita: non ha senso chiedere ore
        # Vai direttamente alla motivazione di fondo
        set_state(user_id, "ONBOARDING_4")
        await _reply(
            update,
            f"_{obj.title}_ è più un desiderio su come vuoi vivere che un progetto "
            f"con ore da contare — e ha senso che sia così.\n\n"
            + _Q4(),
        )


# ── Step 4: Motivazione ───────────────────────────────────────────────────────

def _Q4():
    return (
        "C'è una motivazione di fondo che guida tutto questo?\n"
        "Qualcosa che vuoi per la tua vita, non solo per il lavoro."
    )


async def _step4(update, context, user_id, telegram_id, text, profile):
    profile.motivation_anchor = text
    profile.onboarding_step = 5
    save_profile(telegram_id, profile)
    set_state(user_id, "ONBOARDING_5")
    response = await _claude(
        profile,
        f"L'utente ha condiviso la sua motivazione profonda: \"{text}\".\n"
        f"Riconosci in una frase quanto questo conti — senza retorica, senza enfasi eccessiva.\n"
        f"Poi chiedi l'orario del check-in serale: il default è 21:30, va bene o preferisce cambiarlo?\n"
        f"Non aggiungere pulsanti nel testo.",
        text,
    )
    await _reply(update, response, _KB_CHECKIN)


# ── Step 5: Orario check-in ───────────────────────────────────────────────────

async def _step5(update, context, user_id, telegram_id, text, profile):
    if "cambio" in text.lower():
        set_state(user_id, "ONBOARDING_5B")
        await _reply(update, "Che ora preferisci? (es. 20:00)")
    else:
        profile.checkin_time_evening = "21:30"
        profile.onboarding_step = 6
        save_profile(telegram_id, profile)
        set_state(user_id, "ONBOARDING_6")
        await _reply(update, "Quando vuoi la revisione settimanale?", _KB_REVIEW)


async def _step5b(update, context, user_id, telegram_id, text, profile):
    parsed = _parse_time(text)
    if parsed == "21:30" and text.strip() not in ("21:30", "21.30"):
        # L'input non era un orario riconoscibile
        await _reply(update, f"Non ho capito l'orario. Scrivilo così: *22:00* o *20:30*")
        return
    profile.checkin_time_evening = parsed
    profile.onboarding_step = 6
    await save_profile_async(telegram_id, profile)
    await set_state_async(user_id, "ONBOARDING_6")
    await _reply(update, "Quando vuoi la revisione settimanale?", _KB_REVIEW)


# ── Step 6: Revisione ─────────────────────────────────────────────────────────

async def _step6(update, context, user_id, telegram_id, text, profile):
    if "scelgo" in text.lower():
        set_state(user_id, "ONBOARDING_6B")
        await _reply(update, "Dimmi giorno e ora (es. 'sabato 17:00')")
    else:
        profile.review_day = "domenica"
        profile.review_time = "18:00"
        profile.onboarding_step = 7
        save_profile(telegram_id, profile)
        set_state(user_id, "ONBOARDING_7")
        await _reply(update, _summary(profile), _KB_CONFIRM)


async def _step6b(update, context, user_id, telegram_id, text, profile):
    day, time_str = _parse_review(text)

    # Valida che il giorno sia stato riconosciuto
    giorni_validi = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
    t = text.lower()
    day_found = any(g[:3] in t for g in giorni_validi)
    time_found = bool(_re.search(r'\d', text))

    if not day_found and not time_found:
        await _reply(
            update,
            "Non ho capito bene. Dimmi giorno e ora così:\n"
            "*sabato 17:00* oppure *domenica 19:30*"
        )
        return

    if not day_found:
        await _reply(update, f"Che giorno preferisci? (es. sabato, domenica, venerdì)")
        return

    if not time_found:
        await _reply(update, f"A che ora il *{day}*? (es. 17:00, 18:30)")
        return

    profile.review_day = day
    profile.review_time = time_str
    profile.onboarding_step = 7
    await save_profile_async(telegram_id, profile)
    await set_state_async(user_id, "ONBOARDING_7")
    await _reply(update, _summary(profile), _KB_CONFIRM)


# ── Step 7: Conferma ──────────────────────────────────────────────────────────

async def _step7(update, context, user_id, telegram_id, text, profile):
    if _is_yes(text):
        profile.onboarding_complete = True
        save_profile(telegram_id, profile)

        try:
            user = get_or_create_user(telegram_id)
            supabase.table("users").update({
                "onboarding_complete": True,
                "onboarding_step": 7,
            }).eq("id", user["id"]).execute()
        except Exception as e:
            logger.error("Errore aggiornamento users.onboarding_complete: %s", e)

        # Reply PRIMA di clear_state — se qualcosa va storto dopo, lo stato è ancora ONBOARDING_7
        name = profile.user_name or ""
        await _reply(
            update,
            f"{'Bene, ' + name + '.' if name else 'Bene.'} "
            f"Da stasera alle {profile.checkin_time_evening} ti mando il check-in.\n\nBuona rotta."
        )

        # Ora è sicuro resettare lo stato
        clear_state(user_id)

        # Scheduler job — non critico, errori non bloccano l'onboarding
        try:
            from services.scheduler import setup_user_jobs
            if context and hasattr(context, 'application'):
                setup_user_jobs(context.application, telegram_id, profile)
        except Exception as e:
            logger.error("Errore setup scheduler dopo onboarding: %s", e)

    else:
        # Mostra menu di cosa correggere — non ricomincia da zero
        set_state(user_id, "ONBOARDING_CORRECT")
        await _reply(
            update,
            "Cosa vuoi correggere?",
            _KB_CORRECT,
        )


# ── Correzione specifica ──────────────────────────────────────────────────────

def _infer_gender(name: str) -> str:
    """Inferisce il genere dal nome italiano. Fallback: F."""
    n = name.lower().strip()
    male_endings = ("o", "e", "i")
    female_endings = ("a",)
    # Nomi comuni maschili che finiscono in 'e' o ambigui
    known_male = {"luca", "andrea", "nicola", "mattia", "elia", "enea", "joshua",
                  "dante", "simone", "michele", "gabriele", "daniele", "samuele",
                  "raffaele", "emanuele", "pasquale", "angelo", "lorenzo", "marco",
                  "luigi", "giuseppe", "giovanni", "roberto", "mario", "franco"}
    if n in known_male:
        return "M"
    if n.endswith("a") and n not in known_male:
        return "F"
    if n.endswith(("o", "i")):
        return "M"
    return "F"  # default


def _g(profile, male: str, female: str) -> str:
    """Restituisce la forma maschile o femminile in base al genere del profilo."""
    if profile.user_gender == "M":
        return male
    return female


def _normalize_for_matching(text: str) -> str:
    """Normalizza typo e varianti di accenti comuni nell'italiano."""
    t = text.lower()
    replacements = {
        "piá": "più", "piú": "più", "piu ": "più ", "piu'": "più",
        "e'": "è", "a'": "à", "i'": "ì", "o'": "ò", "u'": "ù",
        "pió": "più", "pio ": "più ",
    }
    for wrong, right in replacements.items():
        t = t.replace(wrong, right)
    return t


async def _is_actionable_project(objective_text: str, profile: UserProfileData) -> bool:
    """
    Determina se un obiettivo è un progetto concreto (ci lavori attivamente,
    misurabile in ore) o un risultato/outcome di vita.
    Usa prima euristica keywords, poi Claude come fallback.
    """
    text_lower = _normalize_for_matching(objective_text)

    # Segnali di OUTCOME (risultati desiderati, sogni, stati di vita, desideri personali)
    outcome_signals = [
        "avere più tempo", "più tempo libero", "più tempo per", "ritagliare il tempo",
        "essere più", "sentirsi", "vivere meglio", "stare meglio", "vivere",
        "guadagnare di più", "più soldi", "mettere da parte", "risparmiare",
        "libertà", "felicità", "serenità", "equilibrio",
        "meno stress", "più serenità", "più equilibrio",
        "smettere di", "non dover più", "potermi permettere", "permettermi",
        "andare in", "andare a", "andare al", "viaggiare", "visitare",
        "comprare casa", "comprare un", "comprare la",
        "avere un", "trovare il tempo", "trovare tempo",
        "vorrei avere", "vorrei essere", "vorrei poter", "vorrei riuscire",
        "vorrei andare", "vorrei fare", "vorrei vedere", "vorrei sentire",
        "sogno", "mi piacerebbe", "speranza", "aspiro",
        "concerto", "vacanza", "viaggio", "riposo", "relax",
    ]
    if any(signal in text_lower for signal in outcome_signals):
        return False

    # Segnali di PROGETTO (azioni concrete, attività misurabili)
    project_signals = [
        "lanciare", "costruire", "avviare", "sviluppare", "vendere",
        "portare a", "creare", "aprire", "riordinare", "sistemare",
        "completare", "scrivere", "produrre", "formare", "assumere",
        "ristrutturare", "progettare", "realizzare", "digitalizzare",
        "corso", "modulo", "programma", "servizio", "prodotto",
        "sito", "e-commerce", "brand", "lavorare su",
    ]
    if any(signal in text_lower for signal in project_signals):
        return True

    # Ambiguo: chiedi a Claude Haiku — usa asyncio.to_thread per non bloccare l'event loop
    import json
    import asyncio
    from services.classifier import _client, CLASSIFICATION_MODEL

    prompt = (
        f"Obiettivo dichiarato: \"{objective_text}\"\n\n"
        f"È un PROGETTO (si lavora attivamente ogni settimana, misurabile in ore) "
        f"o un OUTCOME (risultato desiderato, sogno, desiderio personale)?\n"
        f"Se c'è dubbio, rispondi outcome.\n"
        f"Rispondi SOLO: {{\"type\": \"project\"}} oppure {{\"type\": \"outcome\"}}"
    )

    def _call_api():
        return _client.messages.create(
            model=CLASSIFICATION_MODEL,
            max_tokens=30,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(_call_api),
            timeout=5.0,
        )
        result = json.loads(response.content[0].text.strip())
        return result.get("type") == "project"
    except Exception:
        return False  # in dubbio → outcome, non chiede le ore


async def _step_correct(update, context, user_id, telegram_id, text, profile):
    text_lower = text.lower()

    if "nome" in text_lower:
        profile.onboarding_step = 0
        save_profile(telegram_id, profile)
        set_state(user_id, "ONBOARDING_0")
        await _reply(update, "Come ti chiami?")

    elif "contesto" in text_lower:
        set_state(user_id, "ONBOARDING_1")
        await _reply(update, "Cosa fai, in due righe?")

    elif "obiettiv" in text_lower:
        profile.objectives = []
        save_profile(telegram_id, profile)
        set_state(user_id, "ONBOARDING_2")
        await _reply(update, "Qual è il tuo obiettivo più importante adesso?")

    elif "motivazione" in text_lower or "ancora" in text_lower:
        set_state(user_id, "ONBOARDING_4")
        await _reply(update, _Q4())

    elif "orari" in text_lower or "ora" in text_lower or "check" in text_lower or "revision" in text_lower:
        set_state(user_id, "ONBOARDING_5")
        await _reply(
            update,
            f"Orario check-in serale attuale: *{profile.checkin_time_evening}*. Cambiarlo?",
            _KB_CHECKIN,
        )

    else:
        set_state(user_id, "ONBOARDING_7")
        await _reply(update, _summary(profile), _KB_CONFIRM)
