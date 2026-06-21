# CLAUDE.md — La Rotta

## 1. Descrizione del progetto

**La Rotta** è un assistente AI personale su Telegram che aiuta un'imprenditrice a non perdere di vista gli obiettivi strategici mentre gestisce il caos operativo quotidiano. Il problema centrale non è la mancanza di organizzazione, ma un meccanismo psicologico di evitamento: l'operativo diventa rifugio dalla difficoltà dello strategico.

Il bot agisce su tre leve: consapevolezza quotidiana (check-in serale che apre conversazione, non solo registra), accountability loop (intenzione dichiarata la sera → ricordata la mattina), sblocco attivo nei momenti di blocco emotivo (Scenario C). Include anche un toolkit di tecniche di psicologia positiva offerte in modo contestuale.

**Scope MVP:** utente singola, uso personale. Nessuna integrazione esterna. Deploy su Railway, storage su Supabase, interfaccia esclusivamente Telegram.

---

## 2. Struttura del progetto

```
la-rotta/
├── CLAUDE.md
├── main.py                      # entry point, setup bot e scheduler
├── config.py                    # env vars, costanti, configurazione modelli
├── requirements.txt
├── .env                         # NON committare
├── handlers/
│   ├── onboarding.py
│   ├── checkin_evening.py       # check-in serale 21:30
│   ├── checkin_morning.py       # check-in mattutino contestuale
│   ├── parking.py               # parcheggio opportunità
│   ├── scenario_c.py            # gestione blocchi (3 branch)
│   ├── weekly_review.py
│   ├── free_message.py          # messaggi liberi → classificazione
│   └── re_engagement.py
├── services/
│   ├── classifier.py            # Claude Haiku → JSON categoria
│   ├── response_generator.py    # Claude Sonnet → testo risposta
│   ├── prompt_builder.py        # system prompt dinamico
│   ├── memory.py                # lettura/scrittura scheda strutturata
│   ├── scheduler.py             # APScheduler jobs
│   └── weekly_summary.py        # generazione riassunto narrativo
├── models/
│   ├── user_profile.py          # Pydantic: scheda strutturata utente
│   └── conversation.py          # Pydantic: sessioni e messaggi
├── db/
│   ├── client.py                # inizializzazione Supabase
│   └── queries.py               # query SQL riutilizzabili
├── utils/
│   ├── state_manager.py         # stato conversazione (IDLE / flusso attivo)
│   └── formatters.py            # formattazione messaggi Telegram
├── tests/
│   ├── test_classifier.py
│   ├── test_state_manager.py
│   └── test_flows.py            # integration test flussi completi
└── spec.md                              # spec tecnica completa
```

---

## 3. Tech Stack

| Componente | Tecnologia | Note |
|---|---|---|
| Linguaggio | Python 3.12 | |
| Bot framework | python-telegram-bot 21.x | async |
| LLM principale | Claude Sonnet 4.6 (`claude-sonnet-4-6`) | generazione risposte |
| LLM classificazione | Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | call leggera, output JSON |
| SDK AI | anthropic (latest) | |
| Database | Supabase (PostgreSQL) | piano free, EU region |
| ORM/client DB | supabase-py 2.x | |
| Validazione dati | pydantic 2.x | |
| Scheduler | APScheduler 3.x | check-in, revisione, re-engagement |
| Deploy | Railway | auto-deploy da GitHub |
| Config | python-dotenv | |

---

## 4. Architettura

```
Utente (Telegram)
    │
    ▼
Bot Handler (python-telegram-bot)
    │
    ├─► State Manager (Supabase) ──► Flusso attivo? ──► Step successivo flusso
    │                                       │
    │                                       └─ No ──► Message Classifier (Claude Haiku)
    │                                                       │
    │                              ┌────────────────────────┴──────────────────────┐
    │                           IDEA    UPDATE    BLOCCO    DOMANDA    AMBIGUO
    │                              │
    ▼                         Flow Router (Python deterministico)
Response Generator (Claude Sonnet)
    │
    └─► System prompt = base + profilo utente + ultimi 3 riassunti + flusso corrente
    │
    ▼
Supabase ← Memory Manager (scheda strutturata + riassunti narrativi settimanali)
```

**Principio chiave:** il routing dei flussi è Python deterministico. Claude genera solo il testo delle risposte, non decide dove andare. Questo garantisce comportamento prevedibile e debug semplice.

---

## 5. Decisioni chiave e motivazioni

| Decisione | Motivazione |
|---|---|
| Routing deterministico Python (non Claude) | Comportamento prevedibile; Claude solo per generazione testo |
| Due call Claude separate (Haiku classificazione + Sonnet risposta) | Costo ridotto; Haiku sufficiente per JSON strutturato |
| Memoria ibrida: scheda strutturata + riassunti narrativi settimanali | Scheda = precisione senza allucinazioni; riassunti = contesto narrativo per Claude |
| Stato conversazione in Supabase con `state_expires_at` | Nessun Redis necessario per MVP a utente singola; restart-safe |
| Supabase piano free | Zero infrastruttura da gestire; backup automatico; migrazione a VPS post-validazione |
| Railway deploy | Auto-deploy da GitHub; restart automatico; sufficiente per MVP |
| Check-in mattutino contestuale (non fisso) | Inviato solo se intenzione dichiarata la sera; riduce notifiche invasive |
| Scenario C profondità piena senza disclaimer | MVP per uso personale; disclaimer necessari solo per versione pubblica |
| Modello upgradabile via env var | Passare da Sonnet a Opus è una riga in `.env` |

---

## 6. Testing

**Dove:** `tests/`  
**Come:** `pytest tests/ -v`

### Checklist di verifica prima del deploy

- [ ] Classificazione messaggi: accuracy >85% su set di test manuale
- [ ] Scheduler: check-in serale inviato all'orario configurato
- [ ] Check-in mattutino: inviato solo se `last_intention_declared` presente
- [ ] Scenario C: tutti e 3 i branch (stanchezza / paura / confusione) completano senza errori
- [ ] Parcheggio: max 10 idee rispettato; conferma con pulsante di correzione funziona
- [ ] Versioning obiettivi: nuova versione creata, vecchia archiviata correttamente
- [ ] Re-engagement: nessun messaggio doppio; pausa funziona
- [ ] State manager: dopo `state_expires_at` → reset a IDLE
- [ ] Supabase RLS: utente accede solo ai propri dati

---

## 7. Documentazione

| File | Contenuto | Quando aggiornarlo |
|---|---|---|
| `CLAUDE.md` | Panoramica, stack, architettura, comandi | Cambio stack, struttura cartelle, comandi principali |
| `spec.md` | Spec tecnica completa: flussi, dialoghi, schema DB, memoria | Cambio flussi, funzionalità, modello dati, tono |
| `models/user_profile.py` | Schema Pydantic del profilo utente | Cambio struttura dati in `user_profile.data` |
| `db/queries.py` | Query SQL riutilizzabili | Nuova query o cambio schema DB |
| `config.py` | Costanti e variabili d'ambiente | Nuova env var o costante di sistema |

---

## 8. Comandi principali

```bash
# Avvio locale
python main.py

# Avvio in modalità dev (webhook locale via ngrok)
python main.py --dev

# Test
pytest tests/ -v
pytest tests/test_classifier.py -v   # solo un modulo

# Deploy (automatico via Railway al push)
git push origin main

# Log in produzione
railway logs --tail

# Migrazione schema DB
supabase db push

# Reset stato utente (debug)
python utils/reset_user_state.py --telegram-id <ID>
```

---

## 9. Sistema di auto-aggiornamento

**Regola principale:** ogni file ha una responsabilità precisa. Aggiornare solo il file responsabile di quella parte.

| File responsabile | Cosa governa | Come aggiornarlo |
|---|---|---|
| `CLAUDE.md` | Orientamento rapido nel progetto | Aggiornare manualmente a ogni cambio strutturale |
| `spec.md` | Specifica completa di flussi e dialoghi | Aggiornare prima di implementare qualsiasi modifica ai flussi |
| `models/user_profile.py` | Struttura dati in Supabase | Aggiornare + eseguire `supabase db push` |
| `services/prompt_builder.py` | Cosa entra nel contesto di Claude | Aggiornare quando cambia la memoria o il tono |
| `handlers/*.py` | Logica dei singoli flussi | Aggiornare in base alla spec; il routing resta deterministico |

**Meccanismo:** la spec tecnica (`docs/.../design.md`) è la fonte di verità. Prima si aggiorna la spec, poi si implementa. `CLAUDE.md` viene aggiornato solo quando cambiano stack, struttura cartelle o comandi — non ad ogni modifica funzionale.

**All'inizio di ogni sessione:** leggere questo file + `user_profile.py` + il file handler rilevante per il task. La spec completa si legge solo se il task riguarda flussi conversazionali o modello dati.
