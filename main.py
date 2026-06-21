import logging
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from config import TELEGRAM_BOT_TOKEN, LOG_LEVEL
from utils.router import handle_start, handle_message, handle_callback

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Avvio La Rotta...")

    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Setup scheduler dopo build
    from services.scheduler import setup_all_users
    app.post_init = lambda a: setup_all_users(a)

    logger.info("Bot in ascolto.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
