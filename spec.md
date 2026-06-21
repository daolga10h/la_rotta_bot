# La Rotta — Specifica Tecnica Completa

**Data:** 2026-06-18  
**Versione:** 1.0 — MVP  
**Autore:** Discovery Interview + analisi idea.md / research.md / critica.md  

---

## 1. Obiettivi del progetto

### 1.1 Problema da risolvere

L'utente sa esattamente cosa vorrebbe fare. Il problema è che alla fine della giornata ha lavorato molto, ma sulle cose urgenti e quotidiane — non su quelle importanti e strategiche. Il meccanismo è di evitamento: l'operativo diventa un rifugio sicuro dalla difficoltà dello strategico.

Un semplice promemoria non risolve questo problema — può aggravarlo aggiungendo senso di colpa. Il bot deve agire sul meccanismo causale, non solo sul tracciamento.

### 1.2 Meccanismo causale

Il bot cambia il comportamento attraverso tre leve:

1. **Consapevolezza quotidiana** — il check-in serale non registra solo "hai fatto X", ma apre una conversazione su *perché* non è successo o su cosa stava bloccando. Nel tempo, l'utente internalizza la distinzione operativo/strategico.
2. **Accountability loop** — la dichiarazione serale dell'intenzione per il giorno dopo, ricordata il mattino successivo, chiude un cerchio che trasforma l'intenzione in impegno concreto.
3. **Sblocco attivo** — nei momenti di bassa motivazione o blocco, il bot non registra e passa oltre. Entra nella conversazione con domande calibrate per aiutare a identificare la natura del blocco e trovare un primo passo possibile.

### 1.3 Obiettivi MVP

- Strumento personale a utente singola (l'autrice del progetto)
- Validare il meccanismo conversazionale prima di scalarlo ad altri utenti
- Raccogliere dati reali su pattern di utilizzo, momenti di abbandono, efficacia dello Scenario C

### 1.4 Obiettivi futuri (fuori scope MVP)

- Versione multi-utente per "Oltre la Bottega"
- Integrazioni esterne (agenda, task manager, CRM)
- Analytics per l'utente

---

## 2. Scope MVP

### 2.1 Funzionalità incluse nell'MVP

| # | Funzionalità |
|---|---|
| 1 | Onboarding conversazionale |
| 2 | Check-in serale (21:30) con pulsanti inline |
| 3 | Check-in mattutino contestuale (solo se intenzione dichiarata) |
| 4 | Parcheggio delle opportunità |
| 5 | Scenario C — gestione blocchi in profondità |
| 6 | Revisione settimanale |
| 7 | Re-engagement a due fasi |
| 8 | Classificazione AI dei messaggi liberi con conferma |
| 9 | Pattern recognition Livello 1 (counter semplici) |
| 10 | Versioning degli obiettivi |
| 11 | Libreria di sblocchi personali (parte integrante Scenario C) |

### 2.2 Esplicitamente fuori dall'MVP

- Reminder contestuale one-shot (riconosce "provo dopo le 16" e schedula un follow-up)
- Streak strategico con celebrazione milestone
- Domanda di calibrazione operativo/strategico settimanale
- Pattern recognition Livello 2 (NLP su correlazioni narrative)
- Multi-utente
- Integrazioni esterne
- Analytics per l'utente
- Disclaimer e meccanismo di escalation per lo Scenario C (necessari solo per versione pubblica)

---

## 3. Architettura generale

```
[Telegram] ←→ [Bot Handler — Python]
                    │
                    ├── [State Manager] ← capisce in quale flusso siamo
                    │
                    ├── [Message Classifier] ← Claude (call leggera)
                    │
                    ├── [Flow Router] ← routing deterministico Python
                    │         │
                    │         ├── Onboarding
                    │         ├── Check-in serale
                    │         ├── Check-in mattutino
                    │         ├── Parcheggio
                    │         ├── Scenario C
                    │         ├── Revisione settimanale
                    │         └── Messaggi liberi
                    │
                    ├── [Response Generator] ← Claude (call principale)
                    │         │
                    │         └── System prompt dinamico (profilo + memoria + flusso)
                    │
                    ├── [Memory Manager] ← legge/scrive su Supabase
                    │
                    └── [Scheduler] ← APScheduler (check-in, revisione, re-engagement)

[Supabase/PostgreSQL] ← storage persistente
```

### 3.1 Principio chiave di architettura

Il routing dei flussi è **deterministico Python** — Claude non decide dove andare. Claude genera solo il testo delle risposte all'interno del flusso già determinato. Questo garantisce comportamento prevedibile e facilità di debug.

Claude viene chiamato per:
1. **Classificazione messaggi** — call leggera, risposta strutturata JSON
2. **Generazione testo** — call principale, con system prompt completo

---

## 4. Funzionalità — Specifica dettagliata

### 4.1 Onboarding

**Trigger:** primo messaggio dell'utente al bot (o comando `/start`)  
**Modalità:** una domanda alla volta, testo libero  
**Completamento parziale:** se l'utente abbandona l'onboarding a metà, il bot salva le risposte date e riprende da dove si era fermata al messaggio successivo

**Sequenza:**

```
1. "Benvenuta. Sono qui per aiutarti a non perdere di vista 
   quello che conta davvero mentre gestisci il caos quotidiano.
   Ti faccio qualche domanda per conoscerti — una alla volta.
   
   Prima: cosa fai, in due righe?"
   → testo libero → salva in user_profile.context

2. "Quali sono i tuoi obiettivi principali adesso? 
   Dimmi il primo — il più importante."
   → testo libero → salva come obiettivo rank 1
   
   "Ce n'è un secondo?"
   [Sì] [No, per ora è uno solo]
   → Se sì: ripete per rank 2, poi rank 3 (massimo 3)

3. Per ogni obiettivo con rank > 1:
   "Quante ore a settimana vuoi dedicare a [obiettivo]?"
   → risposta numerica o testuale → salva weekly_hours_target

4. "C'è una motivazione di fondo che guida tutto questo? 
   Qualcosa che vuoi per la tua vita, non solo per il lavoro."
   → testo libero → salva come motivation_anchor
   (Questo testo verrà richiamato nei momenti di bassa motivazione)

5. "A che ora vuoi il check-in serale? 
   Il default è 21:30 — va bene o preferisci un altro orario?"
   [21:30 va bene] [Cambio orario]
   → Se cambia: "Che ora preferisci?" → input testuale

6. "Quando vuoi la revisione settimanale?
   [Domenica sera 18:00] [Scelgo giorno e ora]"

7. Riepilogo:
   "Ecco quello che ho capito:
   [riepilogo obiettivi con gerarchia]
   [motivation_anchor]
   [check-in ore X:XX]
   [revisione: giorno, ore X:XX]
   
   È tutto corretto?"
   [Sì, iniziamo] [Voglio correggere qualcosa]
   → Se corregge: torna alla domanda specifica
```

**Gestione onboarding parziale:**
- Salva ogni risposta immediatamente nel database
- Campo `onboarding_step` in `users` — tiene traccia dell'ultimo step completato
- Se l'utente scrive un messaggio libero con onboarding incompleto: risponde "Prima di iniziare, ho bisogno di altre [N] informazioni. Continuiamo da dove ci siamo fermati?"

---

### 4.2 Check-in serale (orario configurato, default 21:30)

**Trigger:** scheduler fisso all'orario configurato in onboarding  
**Modalità:** una domanda con 4 pulsanti inline  

**Messaggio del bot:**
```
"Dove hai messo l'energia principale oggi?"

[Ho lavorato sull'operativo]
[Ho lavorato su qualcosa di strategico]  
[Niente di significativo oggi]
[Non ho voglia / ho dubbi]
```

---

**Scenario A — "Ho lavorato sull'operativo"**

```
Bot: "Il negozio aveva bisogno. Succede.
     C'è stato qualcosa, anche piccolo, per [obiettivo strategico rank 1]?"
     [Sì, qualcosa c'è stato] [No, niente oggi]

→ Se sì:
   "Cosa?" → testo libero → registra nella sessione
   "Vuoi dichiarare un'intenzione per domani?" 
   [Sì] [No, non ora]
   → Se sì: "Su cosa lavorerai domani?" → testo libero 
             → salva last_intention_declared
             → attiva check-in mattutino

→ Se no:
   "Ok. Vuoi dichiarare un'intenzione per domani — anche solo 20 minuti?"
   [Sì] [No, non ora]
   → stessa logica sopra

Chiusura: "A domani." (niente altro)
```

---

**Scenario B — "Ho lavorato su qualcosa di strategico"**

```
Bot: "Su cosa hai lavorato?" → testo libero → registra

Bot: "Bene. Questo conta."
     streak_strategic += 1
     [Se streak multiplo di 5]: "Quinta volta questa settimana. Stai tenendo la rotta."
     
     "Vuoi dichiarare un'intenzione per domani?"
     [Sì] [No, a domani]
     → Se sì: "Su cosa?" → testo libero → salva last_intention_declared → attiva check-in mattutino

Chiusura: "A domani."
```

---

**Scenario C — "Niente di significativo oggi"**

```
Bot: "Capita. Cosa potrebbe bloccare anche domani?"
     → testo libero → registra

Bot: "Vuoi dichiarare un'intenzione minima per domani — anche solo 15 minuti?"
     [Sì, ho qualcosa] [No, aspetto]
     → Se sì: "Cosa?" → testo libero → salva → attiva check-in mattutino

Chiusura: "A domani."
```

---

**Scenario D — "Non ho voglia / ho dubbi"**  
→ Vedi sezione 4.5 Scenario C completo

---

**Chiusura universale del check-in:**

Alla fine di qualsiasi scenario (A, B, C), prima della chiusura:
```
"Hai qualche idea nuova prima di chiudere?"
[Sì, ho un'idea] [No, buonanotte]
```
→ Se sì: entra nel flusso Parcheggio (sezione 4.4)

---

### 4.3 Check-in mattutino contestuale (default 7:30)

**Trigger:** APScheduler alle 7:30 — **solo** se `last_intention_declared` è impostato e `morning_reminder_sent = false`  
**Modalità:** pulsanti inline  

```
Bot: "Buongiorno. Ieri sera hai detto che oggi avresti lavorato su:
     '[last_intention_declared.text]'
     È ancora il piano?"

[Sì, è il piano] [Ho cambiato idea] [Non ce la faccio oggi]
```

→ **Sì, è il piano:**
```
"In bocca al lupo."
→ morning_reminder_sent = true
→ chiude
```

→ **Ho cambiato idea:**
```
"Su cosa lavorerai invece?"
→ testo libero → aggiorna last_intention_declared
→ "In bocca al lupo."
→ morning_reminder_sent = true
```

→ **Non ce la faccio oggi:**
```
"Va bene. Vuoi dirmi cos'è cambiato?"
[Sì] [No, è così e basta]
→ Se sì: testo libero → registra → "Ok. A domani."
→ Se no: "Ok. A domani."
→ morning_reminder_sent = true
→ azzera last_intention_declared
```

---

### 4.4 Parcheggio delle opportunità

**Trigger:** messaggio libero classificato come IDEA, oppure pulsante "Sì, ho un'idea" nel check-in serale

**Flusso di cattura:**

```
1. Claude classifica la categoria:
   - NEGOZIO (riguarda principalmente il negozio fisico/operativo)
   - OLTRE_LA_BOTTEGA (riguarda il progetto futuro)
   - STRATEGICO_GENERICO (non chiaramente assegnabile)

2. Bot mostra conferma:
   "Ho capito: nuova idea per [categoria].
   Salvata nel Parcheggio.
   ✓ Corretto  |  ✗ Non è questo"
   
   → Se "✗ Non è questo":
     [Per il Negozio] [Per Oltre la Bottega] [Altro]
     → Aggiorna categoria

3. Reindirizzamento post-parcheggio (sempre):
   "Sei in negozio adesso o hai un momento? 
   C'è qualcosa su cui vuoi tornare?"
   [Sì, torno a X] [No, grazie]
   → Registra risposta, poi chiude
```

**Regole del parcheggio:**
- Massimo 10 idee contemporaneamente
- Se si supera il limite: "Ho già 10 idee nel parcheggio. Prima di aggiungerne un'altra, vuoi rimuoverne una?" → mostra lista con pulsanti [Rimuovi] per ciascuna
- Idee senza revisione da più di 30 giorni: segnalate nella revisione settimanale con etichetta "⏰ In attesa da 30+ giorni"
- Status possibili: `parked` → `reviewing` → `promoted` | `deleted`

**Valutazione nella revisione settimanale (non al momento della cattura):**

```
"[Titolo/estratto idea] — [categoria]"
[Sviluppa questa settimana] [Rimanda di una settimana] [Elimina]

→ Se "Sviluppa questa settimana":
   3 domande di allineamento (una alla volta):
   1. "Questa idea serve principalmente la Bottega o Oltre la Bottega?"
   2. "Quanto tempo richiederebbe a regime — ore a settimana?"
   3. "Hai già qualcosa di simile in sospeso o già provato?"
   → Status: promoted, aggiunge note di valutazione
```

---

### 4.5 Scenario C — Gestione blocchi (profondità piena)

**Trigger:** pulsante "Non ho voglia / ho dubbi" nel check-in serale, oppure messaggio libero classificato come BLOCCO

**Step 1 — Classificazione del blocco:**

```
"Questo blocco come si sente?"

[Stanchezza fisica — il corpo non ce la fa]
[Paura — c'è qualcosa di specifico che mi spaventa]
[Confusione — non so da dove iniziare]
```

---

**Branch 1a — Stanchezza fisica:**

```
Bot: "Il corpo dice basta. Ha senso fermarsi.

     Cosa potresti fare domani, anche solo 15 minuti?"
     → testo libero → salva come last_intention_declared → attiva check-in mattutino

Bot: "Prima di chiudere: vuoi che ti ricordi 
     perché hai iniziato tutto questo?"
     [Sì] [No, grazie]

→ Se sì:
   Bot: "[motivation_anchor dall'onboarding]
        Questo è quello che stai costruendo."
   → chiude
```

---

**Branch 1b — Paura:**

```
Bot: "Cosa ti spaventa, nello specifico?"
     → testo libero → registra (1/3)

Bot: "Cosa temi che potrebbe succedere 
     se vai avanti con [obiettivo]?"
     → testo libero → registra (2/3)

Bot: "Ultima domanda: cosa consiglieresti 
     a un'altra imprenditrice nella tua situazione,
     con questa stessa paura?"
     → testo libero → registra (3/3)

Bot: "Quella risposta che hai appena scritto —
     è disponibile anche per te.
     Vuoi salvarla per rileggertela la prossima volta?"
     [Sì, salvala] [No]
     
→ Se sì: salva in unlock_library con contesto "paura"
   Bot: "Salvata. La prossima volta che ti senti così,
        te la riporto."

Bot (finale): "Qual è il passo più piccolo possibile 
              che potresti fare domani?"
              → testo libero → salva come last_intention_declared → attiva check-in mattutino
```

---

**Branch 1c — Confusione:**

```
Bot: "Cosa sai già con certezza su [obiettivo rank 1]?
     Anche una sola cosa."
     → testo libero → registra

Bot: "Ok. Partendo da lì: qual è il passo 
     più piccolo possibile che potresti fare domani?"
     → testo libero → salva come last_intention_declared → attiva check-in mattutino

Bot: "In bocca al lupo per domani."
→ chiude
```

---

**Recupero dalla libreria di sblocchi:**

Quando si entra in Scenario C e la libreria non è vuota:
```
Bot (all'inizio): "La volta scorsa che ti sentivi bloccata, hai scritto:
                  '[insight più recente rilevante]'
                  È ancora valida questa prospettiva?"
                  [Sì, mi aiuta] [Non proprio] [Vai avanti]
→ Registra risposta, poi procede normalmente
```

---

### 4.6 Revisione settimanale

**Trigger:** scheduler fisso (giorno e ora configurati in onboarding, default domenica 18:00)

**Messaggio 1 — Riepilogo dati:**

```
"Settimana appena finita.

→ Giorni con lavoro strategico: X/7
→ Ore Oltre la Bottega: X su [target] target
→ Idee nel parcheggio: N in attesa

[Se consecutive_weeks_under_target >= 2]:
"Questa è la seconda settimana consecutiva sotto obiettivo 
per Oltre la Bottega."

Le ore mancanti: il negozio aveva davvero bisogno di te, 
o qualcosa le ha assorbite che potevi rimandare?"

[Erano necessarie] [Potevo gestirlo diversamente] [Non voglio rispondere ora]
```

→ Se "Potevo gestirlo diversamente":
```
"Cosa ha assorbito quelle ore?"
→ testo libero → registra (utile per pattern recognition)
```

**Messaggio 2 — Parcheggio:**

```
"Hai [N] idee nel parcheggio. Le rivediamo?"
[Sì, le vedo tutte] [Solo quelle vecchie] [Dopo]

→ Se sì: mostra idee una alla volta con le 3 opzioni (Sviluppa / Rimanda / Elimina)
   → Per le idee "Sviluppa": avvia flusso 3 domande di allineamento
   → Per le idee >30gg: etichetta "⏰ In attesa da 30+ giorni"
```

**Messaggio 3 — Chiusura:**

```
"Vuoi cambiare qualcosa per la settimana che viene?"
[No, va bene così] [Sì, voglio aggiornare qualcosa]

→ Se sì: 
  [Cambio un obiettivo] [Cambio le ore target] [Altro]
  → Routing al flusso di aggiornamento obiettivi (versioning)
```

---

### 4.7 Re-engagement

**Trigger:** APScheduler — controlla ogni mattina se l'utente ha risposto al check-in negli ultimi N giorni

**Giorno 3 senza risposta:**
```
Bot: "Sono tre giorni che non ci parliamo. Tutto bene?"
     [Sì, torno] [Ho bisogno di una pausa]

→ Se "Sì, torno": 
   "Bentornata. A stasera con il check-in."
   → reset re-engagement counter

→ Se "Ho bisogno di una pausa":
   "Ok. Ti scrivo tra una settimana."
   → scheduler pausa: sospende check-in per 7 giorni
   → dopo 7 giorni: "Sono passati 7 giorni. Quando vuoi riprendere?"
     [Adesso] [Tra un'altra settimana] [Fammi scrivere io quando sono pronta]
```

**Giorno 7 senza risposta (se non ha risposto al messaggio del giorno 3):**
```
Bot: "[motivation_anchor dall'onboarding]

     Questo è ancora lì."

→ Poi silenzio totale — il bot non invia più messaggi finché l'utente non scrive
```

**Giorno 7+ — quando l'utente torna spontaneamente:**
```
Bot: "Bentornata. Vuoi riprendere da dove ci siamo fermati?"
     [Sì, ripartiamo] [Voglio aggiornare qualcosa prima]
```

---

### 4.8 Classificazione messaggi liberi

**Trigger:** qualsiasi messaggio dell'utente fuori da un flusso attivo

**Categorie:**

| Categoria | Descrizione | Esempio |
|---|---|---|
| `IDEA` | Nuova idea/opportunità da parcheggiare | "Ho pensato di organizzare un open day a Natale" |
| `UPDATE` | Aggiornamento su lavoro in corso | "Ho finito la scaletta del primo modulo" |
| `BLOCCO` | Richiesta di aiuto/sblocco | "Non riesco ad andare avanti con la ristrutturazione" |
| `DOMANDA` | Domanda diretta al bot | "Quante idee ho nel parcheggio?" |
| `FEEDBACK` | Commento su una risposta del bot | "Quella risposta non era quello che intendevo" |
| `AMBIGUO` | Classificazione incerta | "Oggi ho incontrato un'azienda interessante" |

**Logica di classificazione:**

```
1. Chiamata Claude leggera (classificazione):
   Input: messaggio utente + ultimi 3 messaggi di contesto + obiettivi utente
   Output: JSON { categoria, confidence (0-1), categoria_alternativa }

2. Se confidence > 0.85:
   Mostra classificazione con pulsante di correzione:
   "Ho capito: [categoria descritta in linguaggio naturale]
   ✓ Corretto  |  ✗ Non è questo"
   → Se "✗": mostra pulsanti con categorie → utente sceglie → riprende flusso

3. Se confidence < 0.85 (AMBIGUO):
   "Sto cercando di capire meglio:
   stai [descrizione opzione A] o [descrizione opzione B]?"
   → pulsanti → utente sceglie → procede
```

**Routing per categoria:**
- `IDEA` → flusso Parcheggio (4.4)
- `UPDATE` → registra nel log, risposta breve di riconoscimento, propone intenzione per domani
- `BLOCCO` → Scenario C (4.5)
- `DOMANDA` → risposta diretta da dati strutturati o memoria
- `FEEDBACK` → registra, chiede cosa avrebbe preferito, aggiorna profilo
- `AMBIGUO` → chiede classificazione prima di procedere

---

### 4.9 Toolkit Mentale

Una libreria di tecniche brevi (2-5 minuti) offerte dal bot in modo contestuale — non come parte del tracciamento degli obiettivi, ma come supporto al piano mentale ed emotivo. Il bot le propone come suggerimenti, mai come obblighi.

#### Libreria delle tecniche

| ID | Tecnica | Descrizione per il bot | Durata |
|---|---|---|---|
| `gratitudine_pratica` | Gratitudine pratica | Nomina 3 cose per cui sei grata oggi — anche piccole | 2 min |
| `lettera_gratitudine` | Lettera di gratitudine | Scrivi 3 righe a qualcuno che ti ha aiutata di recente. Non devi inviarla | 3 min |
| `best_possible_self` | Best possible self | Chiudi gli occhi per 2 minuti e visualizza come sarà la tua vita quando hai raggiunto quello che stai costruendo | 2 min |
| `regola_5_percento` | La regola del 5% | Non fare la cosa bene — falla al 5% del meglio. L'obiettivo è solo iniziare | 1 min |
| `10_10_10` | 10/10/10 | Come ti sentirai riguardo a questa cosa tra 10 minuti? Tra 10 mesi? Tra 10 anni? | 2 min |
| `non_ancora` | Non ancora | Sostituisci "non riesco" con "non ancora". Cosa cambierebbe? | 1 min |
| `atto_gentilezza` | Un atto di gentilezza | Fai qualcosa di piccolo per qualcuno — un messaggio, un complimento, un pensiero. Non deve essere legato al lavoro | 3 min |
| `respiro_box` | Respiro box | 4 secondi inspira — 4 tieni — 4 espira — 4 tieni. Ripeti 4 volte. È tutto | 2 min |
| `tre_vittorie` | Tre vittorie | Nomina 3 cose che hai fatto bene questa settimana. Anche piccole. Anche operative | 2 min |

#### Mapping contestuale — quando offrire quale tecnica

| Contesto | Tecniche proposte (in ordine di priorità) |
|---|---|
| Scenario C — stanchezza fisica | `respiro_box`, `gratitudine_pratica`, `atto_gentilezza` |
| Scenario C — paura | `best_possible_self`, `10_10_10`, `regola_5_percento` |
| Scenario C — confusione | `regola_5_percento`, `non_ancora`, `respiro_box` |
| Revisione settimanale negativa (sotto obiettivo) | `tre_vittorie`, `lettera_gratitudine`, `gratitudine_pratica` |
| Re-engagement (torna dopo assenza) | `best_possible_self`, `gratitudine_pratica` |
| Trigger esplicito dall'utente | Qualsiasi — il bot chiede il tipo di momento |

#### Flusso di proposta

Alla fine di ogni Scenario C completato, prima della chiusura:

```
Bot: "C'è una tecnica veloce — 2-3 minuti — che a volte aiuta 
     in momenti come questo. Vuoi provarla?"
     [Sì, mostrami] [No grazie]

→ Se sì: 
   Bot: "[nome tecnica]
        [istruzioni in 2-3 righe, tono caldo e diretto]
        Hai bisogno di qualcos'altro o puoi chiudere?"
   → testo libero opzionale → chiude
```

Nella revisione settimanale, se il tono è negativo o il dato delle ore è sotto target per 2+ settimane:

```
Bot: "Prima di chiudere: c'è una cosa piccola che potrebbe 
     aiutare a iniziare la settimana con un piano mentale diverso.
     Vuoi che te la mostri?"
     [Sì] [No, a domenica prossima]
```

Trigger esplicito — quando l'utente scrive "ho bisogno di una spinta" o simile (classificato come `BLOCCO` con sottotipo `motivazione`):

```
Bot: "Com'è il momento adesso?"
     [Stanca] [Spaventata] [Confusa] [Solo ho bisogno di qualcosa]
     → sceglie tecnica dal mapping → propone → chiude
```

#### Principi di erogazione

- **Mai obbligatorie** — sempre precedute da "vuoi provare?" con opzione di rifiuto
- **Mai più di una per sessione** — una tecnica, non una lista
- **Tono diretto, non da wellness** — niente "questo cambierà la tua vita". Solo: "questa cosa funziona su molte persone, prova"
- **Il bot non valuta** — non chiede "ti ha aiutato?" — lascia che l'utente decida da sola
- **Non legate agli obiettivi** — sono tecniche mentali generali, non coaching sul percorso

---

### 4.10 Tecniche motivazionali integrate nei flussi principali

Oltre al Toolkit Mentale (su proposta), tre tecniche sono integrate strutturalmente nei flussi esistenti:

**1. Implementation intention (check-in mattutino)**

Quando l'utente dichiara l'intenzione serale, il bot non chiede solo *cosa* farà, ma anche *quando* e *per quanto*:

```
Bot: "Su cosa lavorerai domani?"
→ testo libero

Bot: "A che ora hai in mente di farlo, anche approssimativamente?"
     [Mattina] [Dopo pranzo] [Sera] [Non so ancora]

Bot: "Per quanto tempo — anche un'idea?"
     [15-20 minuti] [Un'ora] [Più di un'ora] [Vado a occhio]
```

Questo triplica la probabilità di follow-through rispetto alla sola dichiarazione di intenzione (ricerca di Gollwitzer sulle implementation intentions).

**2. Progress principle (Scenario B — lavoro strategico fatto)**

Quando l'utente riporta lavoro strategico completato, il bot non risponde in modo generico:

```
→ L'utente descrive cosa ha fatto (testo libero)

Bot: "[Rispecchia l'azione specifica menzionata dall'utente].
     Questo è [collegamento concreto all'obiettivo rank 1 o 2].
     Non è poco."
```

Il bot usa le parole dell'utente, non le sue — rispecchio specifico, non lode generica.

**3. Reframe del progresso nella revisione settimanale**

Prima del riepilogo numerico, il bot chiede:

```
Bot: "Prima di guardare i numeri: cosa hai fatto questa settimana 
     di cui sei soddisfatta — anche una sola cosa?"
→ testo libero → registra

→ Poi mostra il riepilogo numerico

Bot: "[quello che hai nominato] + [dati settimana].
     Come valuti questa settimana complessivamente?"
     [Buona] [Mista] [Difficile]
```

Questo attiva il **progress principle** (Amabile): la percezione di progresso, anche parziale, è il motore motivazionale più potente nel lavoro creativo e strategico.

---

### 4.11 Versioning degli obiettivi

**Trigger:** utente dichiara un cambio di obiettivo durante la revisione settimanale o con messaggio libero

**Flusso:**
```
Bot: "Stai aggiornando i tuoi obiettivi.
     Prima di procedere: cosa sta cambiando 
     e perché?"
     → testo libero → registra come nota di transizione

Bot: "Ok. Qual è il nuovo obiettivo?"
     → testo libero → salva nuovo obiettivo

Bot: "Qual è la sua gerarchia rispetto agli altri?"
     → pulsanti con lista obiettivi attuali + "È il più importante"

→ Sistema:
   - Archivia versione corrente in objectives_history con timestamp
   - Crea nuova versione con objectives_version + 1
   - Salva nota di transizione collegata al cambio di versione
```

**Accesso alla storia:**
- Il bot può fare riferimento alla storia: "Tre mesi fa il tuo obiettivo principale era [X], adesso è [Y]."
- Nella revisione settimanale: se gli obiettivi sono stati aggiornati di recente, il bot lo nomina come punto di orientamento.

---

## 5. Sistema di memoria

### 5.1 Scheda strutturata (Livello 1)

Aggiornata ad ogni interazione rilevante. Non viene mai compressa — è la fonte di verità.

```json
{
  "user_id": "uuid",
  "telegram_id": "12345678",
  "objectives_version": 1,
  "objectives": [
    {
      "title": "Portare il negozio a livello premium e prepararlo alla vendita",
      "rank": 1,
      "weekly_hours_target": null
    },
    {
      "title": "Oltre la Bottega",
      "rank": 2,
      "weekly_hours_target": 6
    }
  ],
  "motivation_anchor": "Comprare casa a Marta e avere più tempo per me",
  "user_context": "Imprenditrice con bottega artigianale fisica...",
  "checkin_time_evening": "21:30",
  "checkin_time_morning": "07:30",
  "review_day": "domenica",
  "review_time": "18:00",
  "streak_strategic": 3,
  "last_intention_declared": {
    "text": "lavorare alla scaletta del primo modulo",
    "declared_at": "2026-06-17T21:35:00Z",
    "morning_reminder_sent": false
  },
  "recurring_blocks": ["paura di iniziare", "negozio che assorbe"],
  "unlock_library": [
    {
      "id": "uuid",
      "insight": "...",
      "context": "paura",
      "saved_at": "2026-06-10T22:10:00Z"
    }
  ],
  "counters": {
    "consecutive_operative_days": 2,
    "consecutive_weeks_under_target": 1,
    "total_strategic_sessions": 12,
    "total_checkins_completed": 18,
    "total_ideas_parked": 7
  },
  "parking_lot": [
    {
      "id": "uuid",
      "content": "Open day tematico per Natale",
      "category": "NEGOZIO",
      "status": "parked",
      "created_at": "2026-06-12T10:15:00Z",
      "last_reviewed_at": null
    }
  ],
  "re_engagement": {
    "last_response_at": "2026-06-17T21:40:00Z",
    "day3_message_sent": false,
    "day7_message_sent": false,
    "pause_until": null
  },
  "onboarding_complete": true,
  "onboarding_step": 7
}
```

### 5.2 Riassunti narrativi settimanali (Livello 2)

Generati automaticamente ogni domenica sera dopo la revisione settimanale. Si accumulano fino a 8 settimane; poi vengono compressi in un riassunto trimestrale.

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "week_start": "2026-06-09",
  "week_number": 3,
  "data": {
    "strategic_days": 3,
    "oltre_bottega_hours": 4.5,
    "checkins_completed": 6,
    "ideas_parked": 2,
    "scenario_c_count": 1,
    "scenario_c_types": ["paura"]
  },
  "narrative": "Settimana mista. Tre giorni strategici, buona progressione su Oltre la Bottega nonostante il target non raggiunto. Un momento di blocco per paura martedì — elaborato con domanda sulla consulenza a un'altra imprenditrice. Due idee parcheggiate entrambe per Oltre la Bottega.",
  "tone": "mixed",
  "created_at": "2026-06-14T18:45:00Z"
}
```

### 5.3 Versioning obiettivi

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "version_number": 1,
  "archived_at": "2026-08-01T10:00:00Z",
  "transition_note": "La bottega è stata venduta. Adesso l'obiettivo principale è lanciare Oltre la Bottega.",
  "objectives_snapshot": [...],
  "motivation_anchor": "..."
}
```

### 5.4 Costruzione del system prompt per Claude

Ad ogni chiamata di generazione risposta, il system prompt è costruito dinamicamente:

```
[SEZIONE 1 — Identità e tono]
Sei un assistente conversazionale personale. 
Parli in prima persona, senza nome.
Tono: caldo e onesto come base. 
Autorevole quando nomini pattern o resistenze che l'utente sta evitando.
Mai entusiasmo falso. Mai moralizzare. 
Mai dire "dovresti" — usa domande invece.
Lingua: italiano.

[SEZIONE 2 — Profilo utente]
{scheda strutturata serializzata — obiettivi, anchor, contesto, counters, parking_lot}

[SEZIONE 3 — Contesto storico]
{ultimi 3 riassunti narrativi settimanali, se esistono}

[SEZIONE 4 — Libreria sblocchi]
{unlock_library — per richiamarla nello Scenario C se rilevante}

[SEZIONE 5 — Flusso attuale]
Sei nel flusso: {nome_flusso}
Step corrente: {step}
Istruzioni specifiche: {istruzioni del flusso}

[SEZIONE 6 — Contesto conversazione recente]
{ultimi 10 messaggi della sessione corrente}
```

---

## 6. Schema database (Supabase/PostgreSQL)

```sql
-- Utenti
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_id BIGINT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  onboarding_complete BOOLEAN DEFAULT FALSE,
  onboarding_step INTEGER DEFAULT 0
);

-- Profilo strutturato (scheda + parking + memoria)
CREATE TABLE user_profile (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  data JSONB NOT NULL,  -- scheda strutturata completa
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
  classified_as TEXT,  -- categoria classificazione AI
  flow_name TEXT,      -- in quale flusso era questo messaggio
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sessioni check-in
CREATE TABLE checkin_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL CHECK (type IN ('evening', 'morning')),
  date DATE NOT NULL,
  scenario TEXT,  -- A, B, C, D per serali
  intention_declared TEXT,
  data JSONB,     -- dati aggiuntivi della sessione
  completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Riassunti settimanali (memoria narrativa)
CREATE TABLE weekly_summaries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  week_start DATE NOT NULL,
  week_number INTEGER NOT NULL,
  data JSONB NOT NULL,     -- dati strutturati (ore, giorni, ecc.)
  narrative TEXT NOT NULL, -- riassunto narrativo generato da Claude
  tone TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indici
CREATE INDEX idx_conversations_user_created ON conversations(user_id, created_at DESC);
CREATE INDEX idx_checkin_sessions_user_date ON checkin_sessions(user_id, date DESC);
CREATE INDEX idx_weekly_summaries_user_week ON weekly_summaries(user_id, week_start DESC);
```

---

## 7. Stack tecnico

### 7.1 Dipendenze Python

```
python-telegram-bot==21.x       # framework bot Telegram (async)
anthropic>=0.30.0               # SDK Claude
supabase>=2.0.0                 # client Supabase
apscheduler>=3.10.0             # scheduling check-in e revisione
python-dotenv>=1.0.0            # gestione variabili d'ambiente
pydantic>=2.0.0                 # validazione dati strutturati
```

### 7.2 Variabili d'ambiente

```env
TELEGRAM_BOT_TOKEN=...
ANTHROPIC_API_KEY=...
SUPABASE_URL=...
SUPABASE_KEY=...
MODEL_NAME=claude-sonnet-4-6                    # upgradabile a claude-opus-4-8
CLASSIFICATION_MODEL=claude-haiku-4-5-20251001  # modello leggero per classificazione
TIMEZONE=Europe/Rome
LOG_LEVEL=INFO
```

### 7.3 Struttura del progetto

```
la-rotta/
├── main.py                    # entry point, setup bot e scheduler
├── config.py                  # carica env vars, costanti
├── handlers/
│   ├── onboarding.py          # flusso onboarding
│   ├── checkin_evening.py     # check-in serale
│   ├── checkin_morning.py     # check-in mattutino
│   ├── parking.py             # parcheggio opportunità
│   ├── scenario_c.py          # gestione blocchi
│   ├── weekly_review.py       # revisione settimanale
│   ├── free_message.py        # messaggi liberi
│   └── re_engagement.py       # logica re-engagement
├── services/
│   ├── classifier.py          # classificazione messaggi via Claude
│   ├── response_generator.py  # generazione risposte via Claude
│   ├── prompt_builder.py      # costruzione system prompt dinamico
│   ├── memory.py              # lettura/scrittura scheda strutturata
│   ├── scheduler.py           # setup APScheduler jobs
│   └── weekly_summary.py      # generazione riassunto settimanale
├── models/
│   ├── user_profile.py        # Pydantic models per scheda strutturata
│   └── conversation.py        # Pydantic models per sessioni
├── db/
│   ├── client.py              # inizializzazione Supabase
│   └── queries.py             # query SQL riutilizzabili
└── utils/
    ├── state_manager.py       # gestione stato conversazione attivo
    └── formatters.py          # formattazione messaggi Telegram
```

### 7.4 Gestione stato conversazione

Ogni utente ha uno stato corrente che determina come viene gestito il messaggio successivo:

```python
# Stati possibili
STATES = {
    "IDLE",                    # nessun flusso attivo — classifica il messaggio
    "ONBOARDING_{STEP}",       # onboarding step N
    "CHECKIN_EVENING_{STEP}",  # check-in serale step N
    "CHECKIN_MORNING_{STEP}",  # check-in mattutino step N
    "PARKING_{STEP}",          # flusso parcheggio step N
    "SCENARIO_C_{BRANCH}_{STEP}", # Scenario C
    "WEEKLY_REVIEW_{STEP}",    # revisione settimanale step N
    "OBJECTIVES_UPDATE_{STEP}" # aggiornamento obiettivi
}
```

Lo stato è salvato nella tabella `user_profile` in Supabase (campo JSONB `conversation_state`) con un campo `state_expires_at`. Se il timestamp è scaduto al momento del messaggio successivo, lo stato viene resettato a IDLE. Per l'MVP a utente singola non è necessario Redis.

---

## 8. Integrazione Claude API

### 8.1 Due tipi di chiamata

**Call di classificazione (model: claude-haiku-4-5-20251001)**
- Usata per: classificare messaggi liberi, determinare la categoria di un'idea
- Input: messaggio + contesto minimo (obiettivi utente, ultimi 3 messaggi)
- Output: JSON strutturato `{ category, confidence, alternative_category }`
- Max tokens risposta: 100
- Temperatura: 0.1 (comportamento deterministico)

**Call di generazione (model: claude-sonnet-4-6)**
- Usata per: generare il testo di tutte le risposte del bot
- Input: system prompt completo + messaggi sessione corrente
- Output: testo della risposta
- Max tokens risposta: 300 (messaggi brevi per design)
- Temperatura: 0.7

### 8.2 Gestione degli errori API

- Timeout (>10s): risposta fallback "Dammi un secondo." + retry una volta
- Errore 429 (rate limit): attesa 2s + retry una volta, poi risposta fallback "Torno da te tra un momento."
- Errore 500: log dell'errore, risposta fallback generica, continua il flusso
- Risposta fuori contesto: meccanismo di feedback — "Questa risposta aveva senso per te?" [Sì] [No, non era quello che intendevo] → se No: registra, rigenerata con nota nel prompt

### 8.3 Costi stimati

Con uso personale intenso (1 check-in serale + 1 scenario C a settimana + 5 messaggi liberi/giorno):
- ~50 chiamate/giorno
- ~2.000 token/chiamata media (input + output)
- Claude Sonnet 4.6: circa **2-5 € al mese**

---

## 9. Scheduler e notifiche

### 9.1 Jobs APScheduler

```python
# Check-in serale — trigger fisso
scheduler.add_job(
    send_evening_checkin,
    trigger='cron',
    hour=user.checkin_hour,
    minute=user.checkin_minute,
    timezone='Europe/Rome',
    id=f'evening_checkin_{user_id}'
)

# Check-in mattutino — trigger condizionale
# Eseguito ogni mattina alle 7:30, ma invia solo se intenzione dichiarata
scheduler.add_job(
    send_morning_checkin_if_needed,
    trigger='cron',
    hour=7,
    minute=30,
    timezone='Europe/Rome',
    id=f'morning_checkin_{user_id}'
)

# Revisione settimanale
scheduler.add_job(
    send_weekly_review,
    trigger='cron',
    day_of_week=user.review_day,  # es. 'sun'
    hour=user.review_hour,
    minute=user.review_minute,
    timezone='Europe/Rome',
    id=f'weekly_review_{user_id}'
)

# Re-engagement check — ogni giorno
scheduler.add_job(
    check_reengagement,
    trigger='cron',
    hour=9,
    minute=0,
    timezone='Europe/Rome',
    id=f'reengagement_{user_id}'
)

# Generazione riassunto settimanale (domenica sera dopo la revisione)
scheduler.add_job(
    generate_weekly_summary,
    trigger='cron',
    day_of_week='sun',
    hour=20,
    minute=0,
    timezone='Europe/Rome',
    id=f'weekly_summary_{user_id}'
)
```

### 9.2 Finestre temporali per notifiche

Per rispettare le ore di lavoro in negozio, i messaggi che richiedono riflessione vengono inviati **solo** nelle finestre:
- Mattina: 07:00–08:30
- Sera: 19:00–22:30

I messaggi di risposta diretta a un input dell'utente vengono inviati sempre, indipendentemente dall'orario.

---

## 10. Pattern recognition Livello 1

Basato su counter semplici — nessun NLP necessario.

### 10.1 Counter tracciati

| Counter | Aggiornamento | Soglia di attivazione |
|---|---|---|
| `consecutive_operative_days` | Ogni check-in serale | 5 giorni → messaggio in revisione settimanale |
| `consecutive_weeks_under_target` | Ogni revisione settimanale | 2 settimane → nominato esplicitamente |
| `ideas_per_week` | Ogni idea parcheggiata | Non usato come soglia — informativo |
| `scenario_c_frequency` | Ogni Scenario C completato | 3 in una settimana → nota nella revisione |

### 10.2 Messaggi di pattern recognition

Attivati durante la revisione settimanale:

```
[consecutive_operative_days >= 5]:
"Questa settimana — e quella prima — sono state completamente operative.
Vuoi capire cosa sta succedendo o preferisci solo registrarlo?"
[Capire cosa succede] [Solo registrarlo]

[consecutive_weeks_under_target >= 2]:
"Questa è la seconda settimana consecutiva sotto obiettivo per Oltre la Bottega.
Le ore mancanti: erano necessarie o le hai cedute?"

[scenario_c_frequency >= 3 in una settimana]:
"Questa settimana ci siamo ritrovati tre volte in un momento di blocco.
C'è qualcosa di più grande che sta pesando?"
[Sì, probabilmente] [No, è solo stata una settimana difficile]
```

---

## 11. Flussi operativi — diagrammi testuali

### 11.1 Messaggio libero in arrivo

```
Messaggio utente
    │
    ▼
State Manager: c'è un flusso attivo?
    │
    ├── Sì → route al prossimo step del flusso attivo
    │
    └── No → Classifier (Claude Haiku)
                │
                ├── IDEA → Flusso Parcheggio
                ├── UPDATE → Registra + risposta breve
                ├── BLOCCO → Scenario C
                ├── DOMANDA → Risposta da dati strutturati
                ├── FEEDBACK → Registra + aggiorna profilo
                └── AMBIGUO → Chiede classificazione all'utente
```

### 11.2 Generazione risposta

```
Input: [flusso, step, messaggio utente]
    │
    ▼
Prompt Builder:
    ├── Base prompt (tono, regole)
    ├── Profilo strutturato
    ├── Ultimi 3 riassunti narrativi
    ├── Unlock library (se Scenario C)
    ├── Istruzioni flusso corrente
    └── Ultimi 10 messaggi sessione
    │
    ▼
Claude Sonnet 4.6 (max 300 token)
    │
    ▼
Risposta + pulsanti inline se previsti dal flusso
    │
    ▼
Salva in conversations log
    │
    ▼
Aggiorna scheda strutturata se necessario
```

---

## 12. Requisiti tecnici

### 12.1 Performance
- Tempo di risposta: < 3 secondi per messaggio normale, < 5 secondi per Scenario C
- Uptime: 99%+ (Railway restart automatico in caso di crash)
- Latenza scheduler: ±2 minuti dall'orario target

### 12.2 Affidabilità
- Idempotenza scheduler: se il check-in è già stato inviato oggi, non ne manda un secondo
- Gestione restart: lo stato conversazione viene recuperato da Supabase, non è in-memory only
- Backup Supabase: automatico ogni 24h (piano free incluso)

### 12.3 Osservabilità
- Log strutturati per ogni interazione (user_id, flusso, step, durata call Claude)
- Nessuna analytics per l'utente — è infrastruttura interna
- Alert su Railway se il processo crasha

### 12.4 Sicurezza
- API keys in variabili d'ambiente, mai in codice
- Supabase RLS (Row Level Security): ogni utente accede solo ai propri dati
- Nessuna trasmissione dati a terze parti oltre Anthropic API e Supabase
- I dati utente (obiettivi, stati emotivi, conversazioni) sono accessibili solo tramite le API keys del progetto

### 12.5 Privacy
- Dati salvati su server Supabase (region EU se disponibile, altrimenti US)
- Retention: dati conservati indefinitamente per l'MVP personale
- Cancellazione: comando `/cancella_tutto` — elimina tutti i dati dell'utente dal database
- Nota: prima del lancio pubblico sarà necessaria una privacy policy formale

---

## 13. Criteri di successo MVP

### 13.1 Criteri di utilizzo (dopo 4 settimane)

| Metrica | Obiettivo |
|---|---|
| Tasso completamento check-in serale | ≥ 5/7 giorni a settimana |
| Tasso attivazione check-in mattutino | ≥ 3 volte/settimana (quando dichiarata intenzione) |
| Scenario C completato (non abbandonato a metà) | ≥ 80% delle volte che viene aperto |
| Idee correttamente classificate al primo tentativo | ≥ 85% |
| Re-engagement dopo assenza | Almeno 1 volta su 2, l'utente risponde al messaggio del giorno 3 |

### 13.2 Criteri qualitativi (dopo 4 settimane)

- L'utente percepisce una distinzione più chiara tra lavoro operativo e strategico
- Almeno 1 ora a settimana su Oltre la Bottega è stata protetta grazie al bot
- Nessuna risposta inappropriata del bot in momenti di blocco emotivo (Scenario C)
- Il parcheggio viene effettivamente usato (idee parcheggiate invece di inseguite subito)

### 13.3 Criteri tecnici

- Zero perdita di dati
- Zero notifiche doppie
- Zero crash non gestiti che interrompono un flusso a metà
- Costo API Anthropic < 10€/mese

---

## 14. Decisioni post-MVP (V2)

Queste funzionalità sono documentate ma esplicitamente escluse dall'MVP:

| Funzionalità | Motivazione del rinvio |
|---|---|
| Reminder contestuale one-shot | Richiede NLP per riconoscere intenzioni temporali ("provo dopo le 16") + scheduling flessibile |
| Streak strategico con celebrazione milestone | Utile ma non critico — da aggiungere dopo che il check-in è consolidato |
| Domanda calibrazione operativo/strategico settimanale | Una volta a settimana nel check-in — da aggiungere in V2 per non sovraccaricare l'MVP |
| Pattern recognition Livello 2 | Richiede NLP su correlazioni narrative tra eventi e cali di lavoro strategico |
| Disclaimer e meccanismo escalation Scenario C | Necessari per la versione pubblica, non per uso personale |
| Multi-utente | Dopo validazione personale |
| Analytics per l'utente | Dopo validazione del valore del tracciamento |
| Integrazioni esterne | Fuori scope fino a dopo la validazione del core |

---

*Specifica scritta sulla base di: idea.md (concept), research.md (pattern conversazionali), critica.md (criticità e raccomandazioni), Discovery Interview (12 decisioni di prodotto e tecniche).*
