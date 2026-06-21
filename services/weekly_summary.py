import logging
from models.user_profile import UserProfileData
from services.response_generator import generate_response

logger = logging.getLogger(__name__)


def generate_narrative(
    profile: UserProfileData,
    week_data: dict,
    weekly_summaries: list[dict],
) -> tuple[str, str]:
    """
    Genera riassunto narrativo della settimana con Claude.
    Restituisce (narrative, tone) — tone: "good" | "mixed" | "difficult"
    """
    evaluation = week_data.get("evaluation", "mista")
    strategic = week_data.get("strategic_sessions", 0)
    ideas = week_data.get("ideas_parked", 0)
    scenario_c = week_data.get("scenario_c_count", 0)
    week_highlight = week_data.get("week_highlight", "")

    flow_instructions = (
        f"Genera un breve riassunto narrativo (3-5 righe) della settimana di questa imprenditrice.\n"
        f"Dati disponibili:\n"
        f"- Sessioni strategiche: {strategic}\n"
        f"- Idee parcheggiate: {ideas}\n"
        f"- Momenti di blocco (Scenario C): {scenario_c}\n"
        f"- Valutazione dell'utente: {evaluation}\n"
        f"- Cosa è andato bene (parole dell'utente): {week_highlight}\n\n"
        f"Tono: onesto, non retorico. Riconosci sia i progressi che le difficoltà.\n"
        f"Non usare elenchi — solo prosa fluida.\n"
        f"Parla in seconda persona ('hai lavorato', 'ti sei fermata')."
    )

    narrative, is_fallback = generate_response(
        profile=profile,
        flow_name="WEEKLY_SUMMARY",
        flow_instructions=flow_instructions,
        session_messages=[{"role": "user", "content": f"Genera il riassunto della settimana."}],
        weekly_summaries=weekly_summaries[-2:] if weekly_summaries else None,
    )

    if is_fallback:
        narrative = f"Settimana {evaluation}. {strategic} sessioni strategiche, {ideas} idee parcheggiate."

    # Mappa valutazione → tone
    tone_map = {"buona": "good", "mista": "mixed", "difficile": "difficult"}
    tone = tone_map.get(evaluation.lower(), "mixed")

    return narrative, tone


def save_weekly_summary(
    user_id: str,
    week_data: dict,
    narrative: str,
    tone: str,
) -> None:
    from db.client import supabase
    from datetime import datetime, timezone, timedelta

    today = datetime.now(timezone.utc).date()
    # Lunedì della settimana corrente
    week_start = today - timedelta(days=today.weekday())

    # Numero di settimana dall'inizio dell'anno
    week_number = today.isocalendar()[1]

    try:
        supabase.table("weekly_summaries").insert({
            "user_id": user_id,
            "week_start": week_start.isoformat(),
            "week_number": week_number,
            "data": week_data,
            "narrative": narrative,
            "tone": tone,
        }).execute()
        logger.info("Riassunto settimanale salvato: user=%s week=%s", user_id, week_start)
    except Exception as e:
        logger.error("Errore salvataggio riassunto settimanale: %s", e)
