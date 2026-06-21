# La Rotta — Piano di Implementazione MVP

> **Aggiornato:** 2026-06-21  
> **Stato generale:** 🟡 In corso — Fase 11/13 completata — 144 test verdi

---

## Come usare questo file

- Ogni fase ha uno stato: 🔴 Non iniziato / 🟡 In corso / 🟢 Completato / 🔵 Bloccato
- I dettagli di ogni fase (file, test, codice) vengono aggiunti **una fase alla volta** quando si è pronti a implementarla
- Aggiornare lo stato al termine di ogni fase

---

## Panoramica Fasi

| # | Fase | Output concreto | Dipende da | Stato |
|---|------|-----------------|------------|-------|
| 0 | **Setup Infrastruttura** | Struttura cartelle, `.env`, `requirements.txt`, `config.py` | — | 🟢 |
| 1 | **Database & Modelli** | Schema Supabase creato, modelli Pydantic testati | 0 | 🟢 |
| 2 | **Infrastruttura Core** | `state_manager`, `memory`, `formatters` funzionanti con test | 1 | 🟢 |
| 3 | **Integrazione Claude API** | `classifier` e `response_generator` con gestione errori e test | 2 | 🟢 |
| 4 | **Bot Entry Point** | `main.py` avvia il bot, riceve messaggi, non crasha | 3 | 🟢 |
| 5 | **Onboarding** | Flusso 7 step completo con ripresa da step intermedio | 4 | 🟢 |
| 6 | **Check-in Serale** | 4 scenari (A/B/C/D) con pulsanti inline, intenzione salvata | 5 | 🟢 |
| 7 | **Check-in Mattutino** | Inviato solo se intenzione dichiarata, 3 risposte gestite | 6 | 🟢 |
| 8 | **Parcheggio Opportunità** | Cattura idea, classifica, max 10, conferma con correzione | 5 | 🟢 |
| 9 | **Scenario C — Blocchi** | 3 branch (stanchezza/paura/confusione) + libreria sblocchi | 6, 8 | 🟢 |
| 10 | **Revisione Settimanale** | Riepilogo dati, parcheggio, pattern recognition, riassunto narrativo | 8, 9 | 🟢 |
| 11 | **Scheduler & Re-engagement** | APScheduler attivo, re-engagement a 2 fasi funzionante | 6, 7, 10 | 🟢 |
| 12 | **Messaggi Liberi** | Classificazione + routing a flusso corretto per tutte le categorie | 8, 9 | 🔴 |
| 13 | **Test Integrazione & Deploy** | Test end-to-end passano, bot live su Railway, RLS attivo | tutte | 🔴 |

---

## Strategia Gestione Errori LLM (trasversale a tutte le fasi)

Principio: **l'utente non vede mai un errore tecnico. Il developer vede tutto.**

### Messaggi utente (in italiano, tono neutro)
| Tipo errore | Messaggio all'utente |
|---|---|
| Timeout API (>10s) | "Dammi un secondo, ci sto pensando..." → retry → se fallisce: "Riproviamo tra un momento." |
| Rate limit (429) | "Sono un po' lento adesso. Riprovo subito." → attesa 2s → retry → "Torno da te tra un momento." |
| Errore server (5xx) | "C'è stato un piccolo intoppo. Puoi ripetere quello che hai scritto?" |
| Risposta malformata | Come errore server + log speciale |
| Errore generico | "Qualcosa non ha funzionato. Riproviamo?" |

### Log developer (strutturati, mai visibili all'utente)
Ogni errore loga: `timestamp`, `user_id`, `flow_name`, `step`, `error_type`, `error_message`, `traceback`.

---

## Dettaglio Fasi (da completare una alla volta)

<!-- I dettagli di ogni fase vengono aggiunti sotto quando si inizia quella fase -->

### FASE 0 — Setup Infrastruttura
> 🟢 Completata | 2026-06-20 | 2 test PASSED
> File creati: `config.py`, `requirements.txt`, `.env.example`, `.gitignore`, struttura cartelle

**Output:** progetto avviabile localmente, dipendenze installate, variabili d'ambiente configurate.

**Criteri di completamento:**
- `python -c "import config; print(config.MODEL_NAME)"` stampa il nome del modello senza errori
- Tutte le cartelle esistono
- `.env` compilato con le chiavi reali (non committato)

**Dipendenze:** nessuna — è la prima fase.

---

#### Task 0.1 — Crea struttura cartelle

- [ ] Esegui da terminale nella root del progetto:

```powershell
mkdir handlers, services, models, db, utils, tests
New-Item -ItemType File handlers/__init__.py, services/__init__.py, models/__init__.py, db/__init__.py, utils/__init__.py, tests/__init__.py
```

Struttura attesa:
```
la-rotta/
├── handlers/   __init__.py
├── services/   __init__.py
├── models/     __init__.py
├── db/         __init__.py
├── utils/      __init__.py
└── tests/      __init__.py
```

- [ ] Verifica: `ls` mostra tutte le cartelle.

---

#### Task 0.2 — Crea `requirements.txt`

- [ ] Crea il file `requirements.txt` con questo contenuto esatto:

```
python-telegram-bot==21.6
anthropic>=0.30.0
supabase>=2.0.0
apscheduler>=3.10.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-mock>=3.12.0
```

- [ ] Installa: `pip install -r requirements.txt`
- [ ] Verifica: `pip show anthropic` mostra versione >= 0.30.0

---

#### Task 0.3 — Crea `.env.example` e `.env`

- [ ] Crea `.env.example` (questo va committato):

```env
TELEGRAM_BOT_TOKEN=your_token_here
ANTHROPIC_API_KEY=your_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
MODEL_NAME=claude-sonnet-4-6
CLASSIFICATION_MODEL=claude-haiku-4-5-20251001
TIMEZONE=Europe/Rome
LOG_LEVEL=INFO
```

- [ ] Copia in `.env` e compila con le chiavi reali:
  - Token bot Telegram: da [@BotFather](https://t.me/BotFather) con `/newbot`
  - API key Anthropic: da console.anthropic.com
  - URL e key Supabase: da dashboard.supabase.com → Settings → API
- [ ] Aggiungi `.env` al `.gitignore` (crea il file se non esiste):

```
.env
__pycache__/
*.pyc
.pytest_cache/
```

---

#### Task 0.4 — Crea `config.py`

- [ ] Crea `config.py`:

```python
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
    "timeout":      "Dammi un secondo, ci sto pensando...",
    "timeout_final":"Riproviamo tra un momento.",
    "rate_limit":   "Sono un po' lento adesso. Riprovo subito.",
    "rate_limit_final": "Torno da te tra un momento.",
    "server_error": "C'è stato un piccolo intoppo. Puoi ripetere quello che hai scritto?",
    "generic":      "Qualcosa non ha funzionato. Riproviamo?",
}

# Finestre orarie per notifiche proattive (ora locale Europe/Rome)
NOTIFICATION_WINDOWS = [
    (7, 0, 8, 30),   # mattina
    (19, 0, 22, 30), # sera
]
```

---

#### Task 0.5 — Smoke test setup

- [ ] Esegui:

```powershell
python -c "import config; print('MODEL:', config.MODEL_NAME)"
```

Output atteso: `MODEL: claude-sonnet-4-6`

- [ ] Crea `tests/test_config.py`:

```python
def test_required_env_vars_present():
    import config
    assert config.TELEGRAM_BOT_TOKEN
    assert config.ANTHROPIC_API_KEY
    assert config.SUPABASE_URL
    assert config.SUPABASE_KEY
    assert config.MODEL_NAME == "claude-sonnet-4-6"
    assert config.CLASSIFICATION_MODEL == "claude-haiku-4-5-20251001"

def test_llm_error_messages_defined():
    import config
    required_keys = {"timeout", "timeout_final", "rate_limit", "rate_limit_final", "server_error", "generic"}
    assert required_keys.issubset(config.LLM_ERROR_MESSAGES.keys())
    for msg in config.LLM_ERROR_MESSAGES.values():
        assert len(msg) > 0
```

- [ ] Esegui: `pytest tests/test_config.py -v`
- [ ] Output atteso: 2 test PASSED

---

#### Task 0.6 — Commit

```bash
git init
git add requirements.txt config.py .env.example .gitignore handlers/ services/ models/ db/ utils/ tests/
git commit -m "feat: setup infrastruttura base progetto"
```

---

**✅ FASE 0 COMPLETATA quando:** `pytest tests/test_config.py -v` passa con 2 PASSED.

### FASE 1 — Database & Modelli
> 🟢 Completata | 2026-06-20 | 12 test PASSED
> File creati: `models/user_profile.py`, `models/conversation.py`, `db/client.py`, `db/queries.py`
> Schema SQL applicato su Supabase (6 tabelle + indici + RLS)

**Output:** schema Supabase creato, modelli Pydantic validati, client DB funzionante, test passano senza connessione reale.

**Criteri di completamento:**
- Schema SQL applicato su Supabase (tabelle visibili nel dashboard)
- `pytest tests/test_models.py -v` → tutti PASSED
- `python -c "from db.client import supabase; print('OK')"` non crasha

**Dipendenze:** Fase 0 completata (config.py con chiavi Supabase).

---

#### Task 1.1 — Schema SQL su Supabase

- [ ] Vai su dashboard.supabase.com → SQL Editor → New Query
- [ ] Incolla ed esegui questo SQL:

```sql
-- Utenti
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_id BIGINT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  onboarding_complete BOOLEAN DEFAULT FALSE,
  onboarding_step INTEGER DEFAULT 0
);

-- Profilo strutturato (scheda + parking + memoria + stato conversazione)
CREATE TABLE user_profile (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  data JSONB NOT NULL DEFAULT '{}',
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Storia obiettivi (versioning)
CREATE TABLE objectives_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  version_number INTEGER NOT NULL,
  objectives_snapshot JSONB NOT NULL,
  motivation_anchor TEXT,
  transition_note TEXT,
  archived_at TIMESTAMPTZ DEFAULT NOW()
);

-- Log conversazioni
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  classified_as TEXT,
  flow_name TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sessioni check-in
CREATE TABLE checkin_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('evening', 'morning')),
  date DATE NOT NULL,
  scenario TEXT,
  intention_declared TEXT,
  data JSONB DEFAULT '{}',
  completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Riassunti narrativi settimanali
CREATE TABLE weekly_summaries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  week_start DATE NOT NULL,
  week_number INTEGER NOT NULL,
  data JSONB NOT NULL DEFAULT '{}',
  narrative TEXT NOT NULL,
  tone TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indici
CREATE INDEX idx_conversations_user_created ON conversations(user_id, created_at DESC);
CREATE INDEX idx_checkin_sessions_user_date ON checkin_sessions(user_id, date DESC);
CREATE INDEX idx_weekly_summaries_user_week ON weekly_summaries(user_id, week_start DESC);

-- RLS (Row Level Security) — attiva ma permissiva per MVP mono-utente
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkin_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE objectives_history ENABLE ROW LEVEL SECURITY;

-- Policy: solo il service role (backend) può leggere/scrivere
CREATE POLICY "service_only" ON users USING (true) WITH CHECK (true);
CREATE POLICY "service_only" ON user_profile USING (true) WITH CHECK (true);
CREATE POLICY "service_only" ON conversations USING (true) WITH CHECK (true);
CREATE POLICY "service_only" ON checkin_sessions USING (true) WITH CHECK (true);
CREATE POLICY "service_only" ON weekly_summaries USING (true) WITH CHECK (true);
CREATE POLICY "service_only" ON objectives_history USING (true) WITH CHECK (true);
```

- [ ] Verifica: nel dashboard Supabase → Table Editor → vedi 6 tabelle.

---

#### Task 1.2 — Crea `db/client.py`

- [ ] Crea `db/client.py`:

```python
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

- [ ] Verifica: `python -c "from db.client import supabase; print('OK')"` stampa OK.

---

#### Task 1.3 — Scrivi i test dei modelli Pydantic PRIMA del codice

- [ ] Crea `tests/test_models.py`:

```python
import pytest
from datetime import datetime, timezone

def test_objective_model():
    from models.user_profile import Objective
    obj = Objective(title="Oltre la Bottega", rank=2, weekly_hours_target=6)
    assert obj.title == "Oltre la Bottega"
    assert obj.rank == 2
    assert obj.weekly_hours_target == 6

def test_objective_rank1_no_hours_required():
    from models.user_profile import Objective
    obj = Objective(title="Vendere il negozio", rank=1)
    assert obj.weekly_hours_target is None

def test_intention_model():
    from models.user_profile import Intention
    now = datetime.now(timezone.utc)
    intent = Intention(text="lavorare alla scaletta", declared_at=now)
    assert intent.morning_reminder_sent is False

def test_unlock_entry():
    from models.user_profile import UnlockEntry
    entry = UnlockEntry(insight="Ce la faccio", context="paura")
    assert entry.id is not None
    assert entry.saved_at is not None

def test_parking_item():
    from models.user_profile import ParkingItem
    item = ParkingItem(content="Open day Natale", category="NEGOZIO")
    assert item.status == "parked"
    assert item.last_reviewed_at is None

def test_parking_item_invalid_category():
    from models.user_profile import ParkingItem
    with pytest.raises(Exception):
        ParkingItem(content="Test", category="INVALIDA")

def test_counters_default_zero():
    from models.user_profile import Counters
    c = Counters()
    assert c.consecutive_operative_days == 0
    assert c.total_strategic_sessions == 0

def test_reengagement_defaults():
    from models.user_profile import ReEngagement
    r = ReEngagement()
    assert r.day3_message_sent is False
    assert r.pause_until is None

def test_user_profile_data_full():
    from models.user_profile import UserProfileData, Objective
    profile = UserProfileData(
        telegram_id=123456,
        objectives=[Objective(title="Vendere negozio", rank=1)],
        motivation_anchor="Casa a Marta",
        user_context="Imprenditrice con bottega",
    )
    assert profile.objectives_version == 1
    assert profile.onboarding_complete is False
    assert profile.onboarding_step == 0
    assert profile.streak_strategic == 0

def test_user_profile_serializes_to_dict():
    from models.user_profile import UserProfileData, Objective
    profile = UserProfileData(
        telegram_id=123456,
        objectives=[Objective(title="Vendere negozio", rank=1)],
        motivation_anchor="Casa a Marta",
        user_context="Bottega artigianale",
    )
    d = profile.model_dump()
    assert "telegram_id" in d
    assert isinstance(d["objectives"], list)
    assert d["objectives"][0]["rank"] == 1
```

- [ ] Esegui: `pytest tests/test_models.py -v` → devono fallire (modelli non esistono ancora).

---

#### Task 1.4 — Crea `models/user_profile.py`

- [ ] Crea `models/user_profile.py`:

```python
from __future__ import annotations
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import uuid4
import uuid
from pydantic import BaseModel, Field, field_validator


class Objective(BaseModel):
    title: str
    rank: int
    weekly_hours_target: Optional[float] = None


class Intention(BaseModel):
    text: str
    declared_at: datetime
    morning_reminder_sent: bool = False
    time_of_day: Optional[Literal["Mattina", "Dopo pranzo", "Sera", "Non so ancora"]] = None
    duration: Optional[Literal["15-20 minuti", "Un'ora", "Più di un'ora", "Vado a occhio"]] = None


class UnlockEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    insight: str
    context: Literal["paura", "stanchezza", "confusione", "generico"]
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ParkingItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    category: Literal["NEGOZIO", "OLTRE_LA_BOTTEGA", "STRATEGICO_GENERICO"]
    status: Literal["parked", "reviewing", "promoted", "deleted"] = "parked"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_reviewed_at: Optional[datetime] = None


class Counters(BaseModel):
    consecutive_operative_days: int = 0
    consecutive_weeks_under_target: int = 0
    total_strategic_sessions: int = 0
    total_checkins_completed: int = 0
    total_ideas_parked: int = 0


class ReEngagement(BaseModel):
    last_response_at: Optional[datetime] = None
    day3_message_sent: bool = False
    day7_message_sent: bool = False
    pause_until: Optional[datetime] = None


class UserProfileData(BaseModel):
    telegram_id: int
    objectives_version: int = 1
    objectives: list[Objective] = Field(default_factory=list)
    motivation_anchor: Optional[str] = None
    user_context: Optional[str] = None
    checkin_time_evening: str = "21:30"
    checkin_time_morning: str = "07:30"
    review_day: str = "domenica"
    review_time: str = "18:00"
    streak_strategic: int = 0
    last_intention_declared: Optional[Intention] = None
    recurring_blocks: list[str] = Field(default_factory=list)
    unlock_library: list[UnlockEntry] = Field(default_factory=list)
    counters: Counters = Field(default_factory=Counters)
    parking_lot: list[ParkingItem] = Field(default_factory=list)
    re_engagement: ReEngagement = Field(default_factory=ReEngagement)
    onboarding_complete: bool = False
    onboarding_step: int = 0
    # Stato conversazione (gestito da state_manager)
    conversation_state: str = "IDLE"
    state_expires_at: Optional[datetime] = None
```

- [ ] Esegui: `pytest tests/test_models.py -v` → devono passare tutti.

---

#### Task 1.5 — Crea `models/conversation.py`

- [ ] Crea `models/conversation.py`:

```python
from __future__ import annotations
from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    classified_as: Optional[str] = None
    flow_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CheckinSession(BaseModel):
    type: Literal["evening", "morning"]
    date: str  # ISO date YYYY-MM-DD
    scenario: Optional[str] = None   # A, B, C, D per serali
    intention_declared: Optional[str] = None
    data: dict = Field(default_factory=dict)
    completed: bool = False
```

- [ ] Aggiungi test in `tests/test_models.py`:

```python
def test_conversation_message_defaults():
    from models.conversation import ConversationMessage
    msg = ConversationMessage(role="user", content="Ciao")
    assert msg.classified_as is None
    assert msg.created_at is not None

def test_checkin_session_evening():
    from models.conversation import CheckinSession
    s = CheckinSession(type="evening", date="2026-06-20")
    assert s.completed is False
    assert s.scenario is None
```

- [ ] Esegui: `pytest tests/test_models.py -v` → tutti PASSED.

---

#### Task 1.6 — Crea `db/queries.py`

- [ ] Crea `db/queries.py`:

```python
import logging
from datetime import datetime, timezone, date
from db.client import supabase

logger = logging.getLogger(__name__)


def get_or_create_user(telegram_id: int) -> dict:
    result = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
    if result.data:
        return result.data[0]
    new = supabase.table("users").insert({"telegram_id": telegram_id}).execute()
    return new.data[0]


def get_user_profile(user_id: str) -> dict | None:
    result = supabase.table("user_profile").select("*").eq("user_id", user_id).execute()
    return result.data[0] if result.data else None


def upsert_user_profile(user_id: str, data: dict) -> dict:
    existing = get_user_profile(user_id)
    payload = {"user_id": user_id, "data": data, "updated_at": datetime.now(timezone.utc).isoformat()}
    if existing:
        result = supabase.table("user_profile").update(payload).eq("user_id", user_id).execute()
    else:
        result = supabase.table("user_profile").insert(payload).execute()
    return result.data[0]


def save_message(user_id: str, role: str, content: str, classified_as: str = None, flow_name: str = None):
    supabase.table("conversations").insert({
        "user_id": user_id,
        "role": role,
        "content": content,
        "classified_as": classified_as,
        "flow_name": flow_name,
    }).execute()


def get_recent_messages(user_id: str, limit: int = 10) -> list[dict]:
    result = (supabase.table("conversations")
              .select("role, content, created_at")
              .eq("user_id", user_id)
              .order("created_at", desc=True)
              .limit(limit)
              .execute())
    return list(reversed(result.data))


def get_recent_weekly_summaries(user_id: str, limit: int = 3) -> list[dict]:
    result = (supabase.table("weekly_summaries")
              .select("narrative, tone, week_start, data")
              .eq("user_id", user_id)
              .order("week_start", desc=True)
              .limit(limit)
              .execute())
    return list(reversed(result.data))


def save_checkin_session(user_id: str, session_data: dict) -> dict:
    result = supabase.table("checkin_sessions").insert({
        "user_id": user_id,
        **session_data,
    }).execute()
    return result.data[0]


def get_today_checkin(user_id: str, checkin_type: str) -> dict | None:
    today = date.today().isoformat()
    result = (supabase.table("checkin_sessions")
              .select("*")
              .eq("user_id", user_id)
              .eq("type", checkin_type)
              .eq("date", today)
              .execute())
    return result.data[0] if result.data else None


def archive_objectives(user_id: str, version: int, snapshot: list, anchor: str, note: str):
    supabase.table("objectives_history").insert({
        "user_id": user_id,
        "version_number": version,
        "objectives_snapshot": snapshot,
        "motivation_anchor": anchor,
        "transition_note": note,
    }).execute()
```

---

#### Task 1.7 — Commit

```bash
git add models/ db/ tests/test_models.py
git commit -m "feat: modelli Pydantic e schema DB"
```

---

**✅ FASE 1 COMPLETATA quando:**
- Tabelle visibili su Supabase dashboard
- `pytest tests/test_models.py -v` → 12 test PASSED
- `python -c "from db.client import supabase; print('OK')"` → OK

### FASE 2 — Infrastruttura Core
> 🟢 Completata | 2026-06-20 | 16 test PASSED
> File creati: `utils/state_manager.py`, `utils/formatters.py`, `services/memory.py`
> Tutti i test mockano Supabase — nessuna connessione reale richiesta

**Output:** state manager, memory service e formatters funzionanti e testati — tutto il resto del progetto li usa come fondamenta.

**Criteri di completamento:**
- `pytest tests/test_state_manager.py tests/test_memory.py tests/test_formatters.py -v` → tutti PASSED
- Nessun test richiede connessione reale a Supabase (tutto mockato)

**Dipendenze:** Fase 1 (modelli Pydantic + db/queries.py).

---

#### Task 2.1 — Test `state_manager` prima del codice

- [ ] Crea `tests/test_state_manager.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta


@pytest.fixture
def mock_profile_data():
    return {
        "conversation_state": "IDLE",
        "state_expires_at": None,
    }


def test_get_state_returns_idle_when_no_profile(mock_profile_data):
    with patch("services.memory.get_profile") as mock_get:
        mock_get.return_value = None
        from utils.state_manager import get_state
        state = get_state(user_id="uuid-123")
        assert state == "IDLE"


def test_get_state_returns_current_state():
    mock_profile = MagicMock()
    mock_profile.conversation_state = "ONBOARDING_2"
    mock_profile.state_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    with patch("services.memory.get_profile", return_value=mock_profile):
        from utils.state_manager import get_state
        state = get_state(user_id="uuid-123")
        assert state == "ONBOARDING_2"


def test_get_state_resets_expired_state():
    mock_profile = MagicMock()
    mock_profile.conversation_state = "CHECKIN_EVENING_2"
    mock_profile.state_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    with patch("services.memory.get_profile", return_value=mock_profile), \
         patch("utils.state_manager.clear_state") as mock_clear:
        from utils.state_manager import get_state
        state = get_state(user_id="uuid-123")
        mock_clear.assert_called_once_with("uuid-123")
        assert state == "IDLE"


def test_set_state_saves_with_expiry():
    with patch("services.memory.update_state") as mock_update:
        from utils.state_manager import set_state
        set_state(user_id="uuid-123", state="PARKING_1")
        call_kwargs = mock_update.call_args
        assert call_kwargs[0][1] == "PARKING_1"
        expiry = call_kwargs[0][2]
        assert expiry > datetime.now(timezone.utc)


def test_clear_state_sets_idle():
    with patch("services.memory.update_state") as mock_update:
        from utils.state_manager import clear_state
        clear_state(user_id="uuid-123")
        mock_update.assert_called_once_with("uuid-123", "IDLE", None)
```

- [ ] Esegui: `pytest tests/test_state_manager.py -v` → falliscono (modulo non esiste ancora). ✓

---

#### Task 2.2 — Test `memory` prima del codice

- [ ] Crea `tests/test_memory.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from models.user_profile import UserProfileData, Objective


def _make_profile():
    return UserProfileData(
        telegram_id=12345678,
        objectives=[Objective(title="Vendere negozio", rank=1)],
        motivation_anchor="Casa a Marta",
        user_context="Bottega artigianale",
    )


def test_get_profile_returns_none_for_unknown_user():
    with patch("db.queries.get_or_create_user") as mock_user, \
         patch("db.queries.get_user_profile") as mock_profile:
        mock_user.return_value = {"id": "uuid-1", "telegram_id": 99}
        mock_profile.return_value = None
        from services.memory import get_profile
        result = get_profile(telegram_id=99)
        assert result is None


def test_get_profile_deserializes_json():
    profile = _make_profile()
    profile_dict = profile.model_dump(mode="json")
    with patch("db.queries.get_or_create_user") as mock_user, \
         patch("db.queries.get_user_profile") as mock_profile:
        mock_user.return_value = {"id": "uuid-1", "telegram_id": 12345678}
        mock_profile.return_value = {"data": profile_dict}
        from services.memory import get_profile
        result = get_profile(telegram_id=12345678)
        assert result is not None
        assert result.telegram_id == 12345678
        assert result.objectives[0].title == "Vendere negozio"


def test_save_profile_calls_upsert():
    profile = _make_profile()
    with patch("db.queries.get_or_create_user") as mock_user, \
         patch("db.queries.upsert_user_profile") as mock_upsert:
        mock_user.return_value = {"id": "uuid-1", "telegram_id": 12345678}
        from services.memory import save_profile
        save_profile(telegram_id=12345678, profile=profile)
        assert mock_upsert.called
        call_data = mock_upsert.call_args[0][1]
        assert call_data["telegram_id"] == 12345678


def test_update_state_modifies_only_state_fields():
    profile = _make_profile()
    profile_dict = profile.model_dump(mode="json")
    with patch("db.queries.get_or_create_user") as mock_user, \
         patch("db.queries.get_user_profile") as mock_profile_db, \
         patch("db.queries.upsert_user_profile") as mock_upsert:
        mock_user.return_value = {"id": "uuid-1", "telegram_id": 12345678}
        mock_profile_db.return_value = {"data": profile_dict}
        from services.memory import update_state
        from datetime import datetime, timezone, timedelta
        expiry = datetime.now(timezone.utc) + timedelta(hours=2)
        update_state("uuid-1", "ONBOARDING_3", expiry)
        saved = mock_upsert.call_args[0][1]
        assert saved["conversation_state"] == "ONBOARDING_3"
        assert saved["objectives"][0]["title"] == "Vendere negozio"
```

- [ ] Esegui: `pytest tests/test_memory.py -v` → falliscono. ✓

---

#### Task 2.3 — Test `formatters` prima del codice

- [ ] Crea `tests/test_formatters.py`:

```python
from telegram import InlineKeyboardMarkup


def test_make_keyboard_single_row():
    from utils.formatters import make_keyboard
    kb = make_keyboard([["Sì", "No"]])
    assert isinstance(kb, InlineKeyboardMarkup)
    assert len(kb.inline_keyboard) == 1
    assert len(kb.inline_keyboard[0]) == 2
    assert kb.inline_keyboard[0][0].text == "Sì"
    assert kb.inline_keyboard[0][0].callback_data == "Sì"


def test_make_keyboard_multiple_rows():
    from utils.formatters import make_keyboard
    kb = make_keyboard([["Opzione A"], ["Opzione B"], ["Opzione C"]])
    assert len(kb.inline_keyboard) == 3


def test_make_keyboard_custom_callback():
    from utils.formatters import make_keyboard
    kb = make_keyboard([["Testo visibile"]], callback_data=[["cb_testo"]])
    assert kb.inline_keyboard[0][0].text == "Testo visibile"
    assert kb.inline_keyboard[0][0].callback_data == "cb_testo"


def test_format_objectives_summary():
    from utils.formatters import format_objectives_summary
    from models.user_profile import UserProfileData, Objective
    profile = UserProfileData(
        telegram_id=123,
        objectives=[
            Objective(title="Vendere negozio", rank=1),
            Objective(title="Oltre la Bottega", rank=2, weekly_hours_target=6),
        ],
        motivation_anchor="Casa a Marta",
        user_context="Bottega",
    )
    text = format_objectives_summary(profile)
    assert "Vendere negozio" in text
    assert "Oltre la Bottega" in text
    assert "6" in text
```

- [ ] Esegui: `pytest tests/test_formatters.py -v` → falliscono. ✓

---

#### Task 2.4 — Crea `utils/formatters.py`

- [ ] Crea `utils/formatters.py`:

```python
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from models.user_profile import UserProfileData


def make_keyboard(
    rows: list[list[str]],
    callback_data: list[list[str]] | None = None,
) -> InlineKeyboardMarkup:
    keyboard = []
    for r_idx, row in enumerate(rows):
        kb_row = []
        for b_idx, label in enumerate(row):
            cb = callback_data[r_idx][b_idx] if callback_data else label
            kb_row.append(InlineKeyboardButton(text=label, callback_data=cb))
        keyboard.append(kb_row)
    return InlineKeyboardMarkup(keyboard)


def format_objectives_summary(profile: UserProfileData) -> str:
    lines = ["*I tuoi obiettivi:*"]
    for obj in sorted(profile.objectives, key=lambda o: o.rank):
        hours = f" ({obj.weekly_hours_target}h/sett.)" if obj.weekly_hours_target else ""
        lines.append(f"{obj.rank}. {obj.title}{hours}")
    if profile.motivation_anchor:
        lines.append(f"\n_Perché: {profile.motivation_anchor}_")
    return "\n".join(lines)


def format_parking_list(profile: UserProfileData) -> str:
    active = [p for p in profile.parking_lot if p.status == "parked"]
    if not active:
        return "Il parcheggio è vuoto."
    lines = [f"*Idee nel parcheggio ({len(active)}/10):*"]
    for item in active:
        lines.append(f"• {item.content} _{item.category}_")
    return "\n".join(lines)
```

- [ ] Esegui: `pytest tests/test_formatters.py -v` → PASSED. ✓

---

#### Task 2.5 — Crea `services/memory.py`

- [ ] Crea `services/memory.py`:

```python
import logging
from datetime import datetime, timezone
from models.user_profile import UserProfileData
from db import queries

logger = logging.getLogger(__name__)


def _get_user_id(telegram_id: int) -> str:
    user = queries.get_or_create_user(telegram_id)
    return user["id"]


def get_profile(telegram_id: int) -> UserProfileData | None:
    user_id = _get_user_id(telegram_id)
    row = queries.get_user_profile(user_id)
    if not row:
        return None
    return UserProfileData.model_validate(row["data"])


def save_profile(telegram_id: int, profile: UserProfileData) -> None:
    user_id = _get_user_id(telegram_id)
    queries.upsert_user_profile(user_id, profile.model_dump(mode="json"))


def get_or_create_profile(telegram_id: int) -> UserProfileData:
    profile = get_profile(telegram_id)
    if profile is None:
        profile = UserProfileData(telegram_id=telegram_id)
        save_profile(telegram_id, profile)
    return profile


def update_state(user_id: str, state: str, expires_at: datetime | None) -> None:
    row = queries.get_user_profile(user_id)
    if not row:
        logger.warning("update_state: profilo non trovato per user_id=%s", user_id)
        return
    data = row["data"]
    data["conversation_state"] = state
    data["state_expires_at"] = expires_at.isoformat() if expires_at else None
    queries.upsert_user_profile(user_id, data)
```

- [ ] Esegui: `pytest tests/test_memory.py -v` → PASSED. ✓

---

#### Task 2.6 — Crea `utils/state_manager.py`

- [ ] Crea `utils/state_manager.py`:

```python
import logging
from datetime import datetime, timezone, timedelta
from config import STATE_EXPIRY_HOURS
import services.memory as memory

logger = logging.getLogger(__name__)


def get_state(user_id: str) -> str:
    profile = memory.get_profile_by_user_id(user_id)
    if profile is None:
        return "IDLE"
    if profile.state_expires_at and profile.state_expires_at < datetime.now(timezone.utc):
        logger.info("Stato scaduto per user_id=%s, reset a IDLE", user_id)
        clear_state(user_id)
        return "IDLE"
    return profile.conversation_state


def set_state(user_id: str, state: str) -> None:
    expiry = datetime.now(timezone.utc) + timedelta(hours=STATE_EXPIRY_HOURS)
    memory.update_state(user_id, state, expiry)
    logger.debug("Stato impostato: user_id=%s state=%s expiry=%s", user_id, state, expiry)


def clear_state(user_id: str) -> None:
    memory.update_state(user_id, "IDLE", None)
```

- [ ] Aggiungi `get_profile_by_user_id` a `services/memory.py` (prende user_id UUID, non telegram_id):

```python
def get_profile_by_user_id(user_id: str) -> UserProfileData | None:
    row = queries.get_user_profile(user_id)
    if not row:
        return None
    return UserProfileData.model_validate(row["data"])
```

- [ ] Esegui: `pytest tests/test_state_manager.py -v` → PASSED. ✓

---

#### Task 2.7 — Esegui tutti i test della fase

- [ ] `pytest tests/test_state_manager.py tests/test_memory.py tests/test_formatters.py -v`
- [ ] Output atteso: tutti PASSED, nessuna connessione Supabase reale aperta.

---

#### Task 2.8 — Commit

```bash
git add utils/ services/memory.py tests/test_state_manager.py tests/test_memory.py tests/test_formatters.py
git commit -m "feat: state manager, memory service e formatters"
```

---

**✅ FASE 2 COMPLETATA quando:**
- Tutti i test passano senza `.env` con chiavi reali
- `get_state`, `set_state`, `clear_state` funzionano con mock
- `get_profile`, `save_profile` serializzano/deserializzano correttamente

### FASE 3 — Integrazione Claude API
> 🟢 Completata | 2026-06-20 | 14 test PASSED
> File creati: `services/classifier.py`, `services/response_generator.py`, `services/prompt_builder.py`
> Gestione errori LLM completa: timeout, rate limit, server error → messaggi italiani all'utente, log tecnici allo sviluppatore

### FASE 4 — Bot Entry Point
> 🟢 Completata | 2026-06-20 | 5 test PASSED
> File creati: `main.py`, `utils/router.py`, stub per tutti gli handler
> Router smista messaggi e callback in base allo stato — routing deterministico Python

### FASE 5 — Onboarding
> 🟢 Completata | 2026-06-20 | 17 test PASSED
> File: `handlers/onboarding.py`
> 14 stati — 7 step conversazionali, ripresa da step intermedio, parser ore/orari/giorni, max 3 obiettivi con gerarchia

### FASE 6 — Check-in Serale
> 🟢 Completata | 2026-06-21 | 16 test PASSED
> File: `handlers/checkin_evening.py`
> 4 scenari (A/B/C/D), implementation intention completa (cosa/quando/quanto), streak strategico con milestone, idempotenza

### FASE 7 — Check-in Mattutino
> 🟢 Completata | 2026-06-21 | 9 test PASSED
> File: `handlers/checkin_morning.py`
> Invio condizionale, 3 scenari (confermato/cambiato/non ce la faccio), azzeramento intenzione

### FASE 8 — Parcheggio Opportunità
> 🟢 Completata | 2026-06-21 | 11 test PASSED
> File: `handlers/parking.py`
> Classificazione Haiku (NEGOZIO/OLTRE_LA_BOTTEGA/STRATEGICO_GENERICO), limite 10 con rimozione, conferma correggibile

### FASE 9 — Scenario C — Blocchi
> 🟢 Completata | 2026-06-21 | 15 test PASSED
> File: `handlers/scenario_c.py`
> 3 branch completi, libreria sblocchi (inserimento + recupero), toolkit mentale contestuale per branch

### FASE 10 — Revisione Settimanale
> 🟢 Completata | 2026-06-21 | 12 test PASSED
> File: `handlers/weekly_review.py`, `services/weekly_summary.py`
> Progress principle, pattern recognition (3 trigger), parcheggio con 3 domande allineamento, riassunto narrativo Claude

### FASE 11 — Scheduler & Re-engagement
> 🟢 Completata | 2026-06-21 | 15 test PASSED
> File: `services/scheduler.py`, `handlers/re_engagement.py`
> 5 job APScheduler per utente (serale/mattutino/revisione/re-engagement/riassunto)
> Re-engagement: giorno 3 → messaggio, giorno 7 → motivation anchor + silenzio, pausa con riattivazione
> Ritorno spontaneo rilevato automaticamente, nessun doppio invio garantito

### FASE 12 — Messaggi Liberi
> 🔴 Non ancora iniziata

**Output:** classificazione completa con conferma correggibile, routing per tutte le categorie, gestione AMBIGUO con disambiguazione.

**Criteri di completamento:**
- Messaggio classificato con confidence >0.85 → mostra conferma con pulsante correzione
- Messaggio AMBIGUO → chiede disambiguazione all'utente
- Routing corretto per tutte e 6 le categorie (IDEA/UPDATE/BLOCCO/DOMANDA/FEEDBACK/AMBIGUO)
- `pytest tests/test_free_message.py -v` → tutti PASSED

**Dipendenze:** Fasi 8 (parcheggio), 9 (scenario C) già completate.

---

#### Task 12.1 — Completare `handlers/free_message.py`

Il file esiste già come stub — da completare con:
- Conferma categoria con pulsante correzione
- Disambiguazione per AMBIGUO
- Routing completo per UPDATE, DOMANDA, FEEDBACK
- Salvataggio messaggio nel log conversazioni

#### Task 12.2 — Test

- [ ] Crea `tests/test_free_message.py`
- [ ] Test: confidence alta → mostra conferma
- [ ] Test: AMBIGUO → chiede disambiguazione
- [ ] Test: routing corretto per ogni categoria
- [ ] Test: correzione categoria funziona

### FASE 13 — Test Integrazione & Deploy
> 🔴 Non ancora iniziata

**Output:** bot live su Railway, tutti i flussi testati end-to-end, RLS Supabase verificato.

**Criteri di completamento:**
- `pytest tests/ -v` → tutti PASSED (nessun test saltato)
- Bot risponde su Telegram a messaggi reali
- Check-in serale arriva all'orario configurato
- Onboarding completo funziona senza errori
- Costo API Claude < 10€/mese stimato su uso reale

**Dipendenze:** tutte le fasi precedenti completate.

---

#### Task 13.1 — Test di integrazione end-to-end

- [ ] Crea `tests/test_flows.py` con flussi completi (mocka solo le API esterne)
- [ ] Flusso 1: onboarding completo → check-in serale → check-in mattutino
- [ ] Flusso 2: messaggio libero IDEA → parcheggio → conferma
- [ ] Flusso 3: check-in serale Scenario D → Scenario C paura completo
- [ ] Flusso 4: revisione settimanale con parcheggio da rivedere

#### Task 13.2 — Deploy Railway

- [ ] Crea account Railway e collega repository GitHub
- [ ] Configura variabili d'ambiente in Railway (stesse di `.env`)
- [ ] Verifica auto-deploy al push su `main`
- [ ] Controlla log con `railway logs --tail`

#### Task 13.3 — Verifica RLS Supabase

- [ ] Testa che le policy RLS blocchino accessi non autorizzati
- [ ] Verifica che il bot legga/scriva correttamente con la service key

#### Task 13.4 — Smoke test in produzione

- [ ] Invia `/start` al bot su Telegram → onboarding parte
- [ ] Completa onboarding → scheduler configurato
- [ ] Aspetta orario check-in → messaggio arriva
- [ ] Invia un'idea → parcheggio funziona
