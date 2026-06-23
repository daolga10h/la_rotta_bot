import asyncio
import logging
import time
import anthropic
from config import ANTHROPIC_API_KEY, MODEL_NAME, LLM_ERROR_MESSAGES
from models.user_profile import UserProfileData
from services.prompt_builder import build_system_prompt

logger = logging.getLogger(__name__)


async def generate_response_async(
    profile: UserProfileData,
    flow_name: str,
    flow_instructions: str,
    session_messages: list[dict],
    weekly_summaries: list[dict] | None = None,
) -> tuple[str, bool]:
    """Versione async di generate_response — non blocca l'event loop."""
    return await asyncio.to_thread(
        generate_response,
        profile, flow_name, flow_instructions, session_messages, weekly_summaries,
    )

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def generate_response(
    profile: UserProfileData,
    flow_name: str,
    flow_instructions: str,
    session_messages: list[dict],
    weekly_summaries: list[dict] | None = None,
) -> tuple[str, bool]:
    """
    Genera il testo di risposta del bot.
    Restituisce (testo, is_fallback).
    is_fallback=True significa che Claude ha avuto problemi e si usa un testo di emergenza.
    """
    system_prompt = build_system_prompt(
        profile=profile,
        flow_name=flow_name,
        flow_instructions=flow_instructions,
        weekly_summaries=weekly_summaries,
    )

    # Limita la cronologia agli ultimi 10 messaggi
    messages = session_messages[-10:]

    for attempt in range(2):
        try:
            response = _client.messages.create(
                model=MODEL_NAME,
                max_tokens=300,
                temperature=0.7,
                system=system_prompt,
                messages=messages,
            )
            if not response.content or not hasattr(response.content[0], "text"):
                logger.error("Risposta Claude vuota o malformata: user=%s flow=%s", profile.telegram_id, flow_name)
                return LLM_ERROR_MESSAGES["generic"], True
            return response.content[0].text.strip(), False

        except anthropic.RateLimitError as e:
            logger.warning("Rate limit generazione (tentativo %d): user=%s flow=%s err=%s",
                           attempt + 1, profile.telegram_id, flow_name, e)
            if attempt == 0:
                time.sleep(2)
                continue
            return LLM_ERROR_MESSAGES["rate_limit_final"], True

        except anthropic.APITimeoutError as e:
            logger.warning("Timeout generazione (tentativo %d): user=%s flow=%s",
                           attempt + 1, profile.telegram_id, flow_name)
            if attempt == 0:
                continue
            return LLM_ERROR_MESSAGES["timeout_final"], True

        except anthropic.APIStatusError as e:
            logger.error("Errore API generazione: status=%s user=%s flow=%s msg=%s",
                         e.status_code, profile.telegram_id, flow_name, e.message)
            return LLM_ERROR_MESSAGES["server_error"], True

        except Exception as e:
            logger.error("Errore inatteso generazione: user=%s flow=%s err=%s",
                         profile.telegram_id, flow_name, e, exc_info=True)
            return LLM_ERROR_MESSAGES["generic"], True

    return LLM_ERROR_MESSAGES["generic"], True
