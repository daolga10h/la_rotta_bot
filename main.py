import asyncio
import logging

# Deve stare prima di qualsiasi import che usa asyncio (es. Supabase realtime)
asyncio.set_event_loop(asyncio.new_event_loop())

from telegram.ext import Application, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from config import TELEGRAM_BOT_TOKEN, LOG_LEVEL
from utils.router import handle_start, handle_message, handle_callback

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


async def _post_init(app: Application) -> None:
    from services.scheduler import setup_all_users
    setup_all_users(app)
    logger.info("Scheduler configurato.")


async def _error_handler(update, context) -> None:
    """Fallback globale — nessuna eccezione deve silenziare il bot."""
    logger.error("Errore non gestito: %s", context.error, exc_info=context.error)
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Scusa, qualcosa non ha funzionato. Puoi ripetere quello che hai scritto?"
            )
    except Exception:
        pass  # non fare nulla se anche il reply fallisce


def main() -> None:
    logger.info("Avvio La Rotta...")

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(_error_handler)

    logger.info("Bot in ascolto.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
