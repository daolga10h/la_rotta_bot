import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-4-6")
CLASSIFICATION_MODEL = os.getenv("CLASSIFICATION_MODEL", "claude-haiku-4-5-20251001")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Rome")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Limiti flussi
MAX_PARKING_IDEAS = 10
MORNING_CHECKIN_HOUR = 7
MORNING_CHECKIN_MINUTE = 30
REENGAGEMENT_DAY3 = 3
REENGAGEMENT_DAY7 = 7
WEEKLY_SUMMARY_HOUR = 20
STATE_EXPIRY_HOURS = 2

# Messaggi di errore LLM (visibili all'utente — tono neutro, italiano)
LLM_ERROR_MESSAGES = {
    "timeout":           "Dammi un secondo, ci sto pensando...",
    "timeout_final":     "Riproviamo tra un momento.",
    "rate_limit":        "Sono un po' lento adesso. Riprovo subito.",
    "rate_limit_final":  "Torno da te tra un momento.",
    "server_error":      "C'è stato un piccolo intoppo. Puoi ripetere quello che hai scritto?",
    "generic":           "Qualcosa non ha funzionato. Riproviamo?",
}

# Finestre orarie per notifiche proattive (ora locale Europe/Rome)
NOTIFICATION_WINDOWS = [
    (7, 0, 8, 30),    # mattina
    (19, 0, 22, 30),  # sera
]
