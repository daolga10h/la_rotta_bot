import json
import logging
import time
import anthropic
from config import ANTHROPIC_API_KEY, CLASSIFICATION_MODEL, LLM_ERROR_MESSAGES
from services.prompt_builder import build_classification_prompt

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

VALID_CATEGORIES = {"IDEA", "UPDATE", "BLOCCO", "DOMANDA", "FEEDBACK", "AMBIGUO"}
VALID_PARKING_CATEGORIES = {"NEGOZIO", "OLTRE_LA_BOTTEGA", "STRATEGICO_GENERICO"}


def classify_message(
    message: str,
    objectives: list,
    recent_messages: list[dict],
) -> dict:
    """
    Restituisce: {"category": str, "confidence": float, "alternative_category": str | None}
    In caso di errore restituisce categoria AMBIGUO con confidence 0.
    """
    prompt = build_classification_prompt(message, objectives, recent_messages)

    for attempt in range(2):
        try:
            response = _client.messages.create(
                model=CLASSIFICATION_MODEL,
                max_tokens=100,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            result = json.loads(raw)

            if result.get("category") not in VALID_CATEGORIES:
                logger.warning("Categoria non valida ricevuta: %s", result.get("category"))
                return {"category": "AMBIGUO", "confidence": 0.0, "alternative_category": None}

            return {
                "category": result["category"],
                "confidence": float(result.get("confidence", 0.5)),
                "alternative_category": result.get("alternative_category"),
            }

        except anthropic.RateLimitError as e:
            logger.warning("Rate limit classificazione (tentativo %d): %s", attempt + 1, e)
            if attempt == 0:
                time.sleep(2)
                continue
            break

        except anthropic.APIStatusError as e:
            logger.error("Errore API classificazione: status=%s msg=%s", e.status_code, e.message)
            break

        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Risposta classificazione malformata: %s | raw=%s", e, locals().get("raw", ""))
            break

        except Exception as e:
            logger.error("Errore inatteso classificazione: %s", e, exc_info=True)
            break

    return {"category": "AMBIGUO", "confidence": 0.0, "alternative_category": None}


def classify_parking_category(idea_text: str, objectives: list) -> str:
    """
    Classifica un'idea parcheggiata in: NEGOZIO, OLTRE_LA_BOTTEGA, STRATEGICO_GENERICO.
    Restituisce STRATEGICO_GENERICO in caso di errore.
    """
    obj_text = "; ".join(f"{o.rank}. {o.title}" for o in objectives)
    prompt = (
        f"Obiettivi utente: {obj_text}\n\n"
        f"Idea da classificare: \"{idea_text}\"\n\n"
        f"Classifica questa idea:\n"
        f"- NEGOZIO: riguarda il negozio fisico o le operazioni quotidiane\n"
        f"- OLTRE_LA_BOTTEGA: riguarda il progetto futuro / business digitale\n"
        f"- STRATEGICO_GENERICO: non chiaramente assegnabile\n\n"
        f"Rispondi SOLO con JSON: {{\"category\": \"CATEGORIA\"}}"
    )
    try:
        response = _client.messages.create(
            model=CLASSIFICATION_MODEL,
            max_tokens=50,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        result = json.loads(raw)
        cat = result.get("category", "STRATEGICO_GENERICO")
        return cat if cat in VALID_PARKING_CATEGORIES else "STRATEGICO_GENERICO"
    except Exception as e:
        logger.error("Errore classificazione parcheggio: %s", e)
        return "STRATEGICO_GENERICO"
