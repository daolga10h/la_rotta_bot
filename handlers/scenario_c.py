import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from models.user_profile import UserProfileData, Intention, UnlockEntry
from services.memory import save_profile
from utils.state_manager import set_state, clear_state
from utils.formatters import make_keyboard

logger = logging.getLogger(__name__)

# â”€â”€ Toolkit mentale â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_TOOLKIT = {
    "respiro_box": {
        "name": "Respiro box",
        "instructions": "4 secondi inspira â€” 4 tieni â€” 4 espira â€” 4 tieni. Ripeti 4 volte. Ãˆ tutto.",
    },
    "gratitudine_pratica": {
        "name": "Gratitudine pratica",
        "instructions": "Nomina 3 cose per cui sei grata oggi â€” anche piccole. Scrivile qui se vuoi.",
    },
    "atto_gentilezza": {
        "name": "Un atto di gentilezza",
        "instructions": "Fai qualcosa di piccolo per qualcuno â€” un messaggio, un complimento, un pensiero. Non deve essere legato al lavoro.",
    },
    "best_possible_self": {
        "name": "Best possible self",
        "instructions": "Chiudi gli occhi per 2 minuti e visualizza come sarà la tua vita quando hai raggiunto quello che stai costruendo.",
    },
    "10_10_10": {
        "name": "10/10/10",
        "instructions": "Come ti sentirai riguardo a questa cosa tra 10 minuti? Tra 10 mesi? Tra 10 anni?",
    },
    "regola_5_percento": {
        "name": "La regola del 5%",
        "instructions": "Non fare la cosa bene â€” falla al 5% del meglio. L'obiettivo è solo iniziare.",
    },
    "non_ancora": {
        "name": "Non ancora",
        "instructions": "Sostituisci 'non riesco' con 'non ancora'. Cosa cambierebbe?",
    },
}

_TOOLKIT_BY_CONTEXT = {
    "stanchezza": ["respiro_box", "gratitudine_pratica", "atto_gentilezza"],
    "paura":      ["best_possible_self", "10_10_10", "regola_5_percento"],
    "confusione": ["regola_5_percento", "non_ancora", "respiro_box"],
}

_KB_BRANCH = make_keyboard([
    ["Stanchezza fisica â€” il corpo non ce la fa"],
    ["Paura â€” c'è qualcosa di specifico che mi spaventa"],
    ["Confusione â€” non so da dove iniziare"],
])
_KB_SI_NO = make_keyboard([["Sì"], ["No, grazie"]])
_KB_SAVE = make_keyboard([["Sì, salvala"], ["No"]])
_KB_TOOLKIT = make_keyboard([["Sì, mostrami"], ["No grazie"]])
_KB_UNLOCK = make_keyboard([["Sì, mi aiuta"], ["Non proprio"], ["Vai avanti"]])


async def _reply(update: Update, text: str, keyboard=None) -> None:
    kwargs = {"parse_mode": "Markdown"}
    if keyboard:
        kwargs["reply_markup"] = keyboard
    if update.message:
        await update.message.reply_text(text, **kwargs)
    else:
        await update.callback_query.message.reply_text(text, **kwargs)


# â”€â”€ Entry point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def start_scenario_c(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: str,
    telegram_id: int,
    profile: UserProfileData,
) -> None:
    profile.scenario_c_data = {}
    save_profile(telegram_id, profile)

    # Recupero dalla libreria sblocchi
    if profile.unlock_library:
        latest = profile.unlock_library[-1]
        set_state(user_id, "SCENARIO_C_UNLOCK")
        await _reply(
            update,
            f"La volta scorsa che ti sentivi bloccata, hai scritto:\n"
            f"_\"{latest.insight}\"_\n\n"
            f"Ãˆ ancora valida questa prospettiva?",
            _KB_UNLOCK,
        )
    else:
        set_state(user_id, "SCENARIO_C_CLASSIFY")
        await _reply(update, "Questo blocco come si sente?", _KB_BRANCH)


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
        "SCENARIO_C_UNLOCK":           _unlock_response,
        "SCENARIO_C_CLASSIFY":         _classify,
        # Branch stanchezza
        "SCENARIO_C_STANCHEZZA_INT":   _stanchezza_intention,
        "SCENARIO_C_STANCHEZZA_ANCHOR": _stanchezza_anchor,
        # Branch paura
        "SCENARIO_C_PAURA_1":          _paura_1,
        "SCENARIO_C_PAURA_2":          _paura_2,
        "SCENARIO_C_PAURA_3":          _paura_3,
        "SCENARIO_C_PAURA_SAVE":       _paura_save,
        "SCENARIO_C_PAURA_INT":        _paura_intention,
        # Branch confusione
        "SCENARIO_C_CONFUSIONE_1":     _confusione_1,
        "SCENARIO_C_CONFUSIONE_INT":   _confusione_intention,
        # Toolkit
        "SCENARIO_C_TOOLKIT":          _toolkit_response,
        "SCENARIO_C_TOOLKIT_DONE":     _toolkit_done,
    }
    fn = dispatch.get(state)
    if fn:
        await fn(update, context, user_id, telegram_id, text, profile)
    else:
        logger.warning("Stato Scenario C sconosciuto: %s", state)
        from utils.fallback import not_understood
        await not_understood(update, "Scusa, non ho capito. Puoi riformulare?")


# â”€â”€ Unlock library â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _unlock_response(update, context, user_id, telegram_id, text, profile):
    # Registra la risposta (utile per future analisi), poi procede
    set_state(user_id, "SCENARIO_C_CLASSIFY")
    await _reply(update, "Questo blocco come si sente?", _KB_BRANCH)


async def _classify(update, context, user_id, telegram_id, text, profile):
    text_lower = text.lower()
    if "stanchezza" in text_lower or "corpo" in text_lower:
        branch = "stanchezza"
        profile.scenario_c_data = {"branch": branch}
        save_profile(telegram_id, profile)
        set_state(user_id, "SCENARIO_C_STANCHEZZA_INT")
        await _reply(
            update,
            "Il corpo dice basta. Ha senso fermarsi.\n\n"
            "Cosa potresti fare domani, anche solo 15 minuti?",
        )

    elif "paura" in text_lower or "spaventa" in text_lower:
        branch = "paura"
        profile.scenario_c_data = {"branch": branch}
        save_profile(telegram_id, profile)
        set_state(user_id, "SCENARIO_C_PAURA_1")
        await _reply(update, "Cosa ti spaventa, nello specifico?")

    else:  # confusione
        branch = "confusione"
        obj1 = next((o for o in profile.objectives if o.rank == 1), None)
        obj1_title = obj1.title if obj1 else "il tuo obiettivo principale"
        profile.scenario_c_data = {"branch": branch}
        save_profile(telegram_id, profile)
        set_state(user_id, "SCENARIO_C_CONFUSIONE_1")
        await _reply(
            update,
            f"Cosa sai già con certezza su *{obj1_title}*?\nAnche una sola cosa.",
        )


# â”€â”€ Branch stanchezza â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _stanchezza_intention(update, context, user_id, telegram_id, text, profile):
    _save_intention(text, profile, telegram_id)
    set_state(user_id, "SCENARIO_C_STANCHEZZA_ANCHOR")
    await _reply(
        update,
        "Prima di chiudere: vuoi che ti ricordi perché hai iniziato tutto questo?",
        _KB_SI_NO,
    )


async def _stanchezza_anchor(update, context, user_id, telegram_id, text, profile):
    if text.lower().startswith("sì") or text.lower().startswith("si"):
        anchor = profile.motivation_anchor or "La tua motivazione di fondo."
        await _reply(update, f"_{anchor}_\n\nQuesto è quello che stai costruendo.")
    await _offer_toolkit(update, user_id, telegram_id, profile, "stanchezza")


# â”€â”€ Branch paura â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _paura_1(update, context, user_id, telegram_id, text, profile):
    data = profile.scenario_c_data or {}
    data["paura_1"] = text
    profile.scenario_c_data = data
    save_profile(telegram_id, profile)

    obj1 = next((o for o in profile.objectives if o.rank == 1), None)
    obj1_title = obj1.title if obj1 else "il tuo obiettivo"
    set_state(user_id, "SCENARIO_C_PAURA_2")
    await _reply(
        update,
        f"Cosa temi che potrebbe succedere se vai avanti con *{obj1_title}*?",
    )


async def _paura_2(update, context, user_id, telegram_id, text, profile):
    data = profile.scenario_c_data or {}
    data["paura_2"] = text
    profile.scenario_c_data = data
    save_profile(telegram_id, profile)
    set_state(user_id, "SCENARIO_C_PAURA_3")
    await _reply(
        update,
        "Ultima domanda: cosa consiglieresti a un'altra imprenditrice nella tua situazione, "
        "con questa stessa paura?",
    )


async def _paura_3(update, context, user_id, telegram_id, text, profile):
    data = profile.scenario_c_data or {}
    data["paura_3"] = text
    profile.scenario_c_data = data
    save_profile(telegram_id, profile)
    set_state(user_id, "SCENARIO_C_PAURA_SAVE")
    await _reply(
        update,
        "Quella risposta che hai appena scritto â€” è disponibile anche per te.\n"
        "Vuoi salvarla per rileggertela la prossima volta?",
        _KB_SAVE,
    )


async def _paura_save(update, context, user_id, telegram_id, text, profile):
    if text.lower().startswith("sì") or text.lower().startswith("si"):
        data = profile.scenario_c_data or {}
        insight = data.get("paura_3", "")
        if insight:
            entry = UnlockEntry(insight=insight, context="paura")
            profile.unlock_library.append(entry)
            save_profile(telegram_id, profile)
            await _reply(
                update,
                "Salvata. La prossima volta che ti senti così, te la riporto.",
            )

    set_state(user_id, "SCENARIO_C_PAURA_INT")
    await _reply(update, "Qual è il passo più piccolo possibile che potresti fare domani?")


async def _paura_intention(update, context, user_id, telegram_id, text, profile):
    _save_intention(text, profile, telegram_id)
    await _offer_toolkit(update, user_id, telegram_id, profile, "paura")


# â”€â”€ Branch confusione â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _confusione_1(update, context, user_id, telegram_id, text, profile):
    data = profile.scenario_c_data or {}
    data["confusione_1"] = text
    profile.scenario_c_data = data
    save_profile(telegram_id, profile)
    set_state(user_id, "SCENARIO_C_CONFUSIONE_INT")
    await _reply(
        update,
        "Ok. Partendo da lÃ¬: qual è il passo più piccolo possibile che potresti fare domani?",
    )


async def _confusione_intention(update, context, user_id, telegram_id, text, profile):
    _save_intention(text, profile, telegram_id)
    await _offer_toolkit(update, user_id, telegram_id, profile, "confusione")


# â”€â”€ Toolkit mentale â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async def _offer_toolkit(update, user_id, telegram_id, profile, branch: str):
    data = profile.scenario_c_data or {}
    data["toolkit_branch"] = branch
    profile.scenario_c_data = data
    save_profile(telegram_id, profile)
    set_state(user_id, "SCENARIO_C_TOOLKIT")
    await _reply(
        update,
        "C'è una tecnica veloce â€” 2-3 minuti â€” che a volte aiuta in momenti come questo. "
        "Vuoi provarla?",
        _KB_TOOLKIT,
    )


async def _toolkit_response(update, context, user_id, telegram_id, text, profile):
    if text.lower().startswith("sì") or text.lower().startswith("si"):
        data = profile.scenario_c_data or {}
        branch = data.get("toolkit_branch", "confusione")
        technique_id = _TOOLKIT_BY_CONTEXT.get(branch, ["respiro_box"])[0]
        technique = _TOOLKIT[technique_id]
        set_state(user_id, "SCENARIO_C_TOOLKIT_DONE")
        await _reply(
            update,
            f"*{technique['name']}*\n{technique['instructions']}\n\n"
            "Hai bisogno di qualcos'altro o puoi chiudere?",
        )
    else:
        await _finish(update, user_id, telegram_id, profile)


async def _toolkit_done(update, context, user_id, telegram_id, text, profile):
    await _finish(update, user_id, telegram_id, profile)


async def _finish(update, user_id, telegram_id, profile):
    profile.scenario_c_data = None
    save_profile(telegram_id, profile)
    clear_state(user_id)
    await _reply(update, "In bocca al lupo per domani.")


# â”€â”€ Helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _save_intention(text: str, profile: UserProfileData, telegram_id: int) -> None:
    profile.last_intention_declared = Intention(
        text=text,
        declared_at=datetime.now(timezone.utc),
    )
    save_profile(telegram_id, profile)
