"""
Fallback condiviso: quando il bot non capisce un messaggio
mostra un messaggio gentile e mantiene lo stato corrente.
"""
import logging
from telegram import Update

logger = logging.getLogger(__name__)

_MESSAGES = [
    "Scusa, non ho capito. Puoi spiegarti meglio?",
    "Non sono sicuro di aver capito. Puoi riformulare?",
    "Hmm, non ho colto. Cosa intendi?",
]


async def not_understood(update: Update, hint: str = "") -> None:
    """Risponde con un messaggio di non comprensione gentile."""
    text = hint if hint else _MESSAGES[0]
    kwargs = {}
    if update.message:
        await update.message.reply_text(text, **kwargs)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, **kwargs)
