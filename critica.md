# La Rotta — Critica e Raccomandazioni per le Specifiche

**Data:** giugno 2026
**Metodo:** analisi multi-agente con tre prospettive indipendenti — critico di prodotto, fact-checker della ricerca, analista competitivo.

---

## PARTE 1 — CRITICA DELL'IDEA

### 1.1 Il problema centrale non è risolto

**Gravità: CRITICA**

Il documento identifica correttamente il problema: "si svurgola — si nasconde dietro le piccole cose operative." Questo è un meccanismo psicologico di evitamento, non un problema di organizzazione. L'utente *sa* cosa dovrebbe fare. Non lo fa.

Il bot come descritto risolve: tracciamento, promemoria, parcheggio idee.
Il bot non risolve: il motivo per cui l'utente sceglie consapevolmente l'operativo sullo strategico.

Un check-in serale che chiede "hai lavorato su X?" a qualcuno che già sa di non averlo fatto non abbassa la resistenza psicologica — può aumentarla aggiungendo senso di colpa. L'unico punto in cui il bot tenta di affrontare la causa è lo Scenario C (mancanza di voglia), ma è trattato come eccezione, non come meccanismo centrale.

**Prima di sviluppare qualsiasi cosa, serve una risposta a:** perché questo bot cambierebbe il comportamento invece di aiutare a documentarlo?

---

### 1.2 La classificazione automatica dei messaggi è il componente più critico e il meno specificato

**Gravità: CRITICA**

La sezione 6.2 descrive un "layer AI che interpreta i messaggi dell'utente, capisce il contesto (sta aggiornando? sta parcheggiando un'idea? sta chiedendo aiuto?)." Questo riceve quattro righe nel documento.

Un messaggio come "oggi ho incontrato questa azienda che potrebbe essere interessante per Oltre la Bottega" può essere un'idea da parcheggiare, un aggiornamento operativo, o l'inizio di una conversazione strategica. La scelta cambia completamente il flusso successivo.

Non è specificato:
- Come l'utente comunica l'intenzione (prefissi testuali? flow guidato? classificazione implicita?)
- Cosa succede quando la classificazione è sbagliata
- Come l'utente corregge una classificazione errata
- Quante categorie esistono e se si escludono a vicenda

Questo è il punto di fallimento più probabile dell'MVP.

---

### 1.3 Nessuna strategia per l'abbandono post-luna di miele

**Gravità: CRITICA**

Il tasso di abbandono dei bot di journaling e coaching è tipicamente molto alto nella seconda e terza settimana, esattamente quando la novità cala. L'utente è descritta come qualcuno che "si perde tra idee nuove" — il bot stesso potrebbe diventare una di quelle idee che sembrano buone ma non vengono mai consolidate.

Il documento non descrive:
- Cosa fa il bot se l'utente smette di rispondere per 3 giorni
- Come gestisce il re-engagement senza essere invadente
- Quale meccanismo tiene l'utente agganciata oltre la funzionalità stessa

Non c'è nessuna strategia di retention. Questo non è un problema tecnico — è un problema di product design che va risolto prima dello sviluppo.

---

### 1.4 Lo Scenario C senza fallback umano è un rischio non gestito

**Gravità: CRITICA**

La sezione 7.4 descrive il bot che gestisce "mancanza di voglia" e "dubbi", dà "il permesso di fermarsi senza senso di colpa", chiede cosa genera il blocco. Questo è pericolosamente vicino alla simulazione di supporto emotivo.

Il fallback umano viene eliminato dall'MVP con "zero casi d'uso concreti per ora" — ma lo Scenario C è esattamente quel caso d'uso. Un LLM non può distinguere stanchezza ordinaria da burnout o situazioni che richiedono supporto reale. Una risposta sbagliata del bot in un momento di blocco non è solo inutile: può essere dannosa.

**Decisione da prendere prima dello sviluppo:** o il bot non gestisce stati emotivi oltre la superficie, o esiste un meccanismo minimo di escalation (anche solo "se hai bisogno di parlare con qualcuno, ecco un contatto").

---

### 1.5 La memoria compressa non è specificata a sufficienza per essere sviluppata

**Gravità: ALTA**

La sezione 6.4 descrive la memoria come "riassunto periodico degli aggiornamenti." Non è specificato: chi genera il riassunto, con quale frequenza, su quale orizzonte temporale, quali informazioni sono critiche vs eliminabili, come viene garantita la fedeltà.

Un LLM che comprime conversazioni può allucinare o sintetizzare in modo distorto. "Ho dubbi sulla vendita della bottega" potrebbe diventare "sta valutando la vendita della bottega." Questa compressione determina la qualità di tutte le risposte successive. Se è distorta, tutto il ragionamento è distorto.

---

### 1.6 Contraddizioni interne

**Il check-in è mattutino o serale?**
- Sezione 1: "fa un check-in la mattina ogni giorno alle 7:30"
- Sezione 4: "check-in serale alle 21.30"
- Sezione 7.2: check-in mattutino "opzionale — da valutare dopo i primi giorni"
- Sezione 8: "check-in ogni sera alle 21:30"

Il documento non ha deciso. Sono funzionalmente diversi (pianificazione vs rendiconto) e definiscono la funzione core del prodotto.

**"Non invasivo" vs frequenza reale delle notifiche:**
La sezione 6.5 dichiara "nessun reminder invasivo durante il giorno." Ma il documento elenca: check-in serale, possibile check-in mattutino, alert settimanale, richiami per le ore di Oltre la Bottega, reminder quando gli obiettivi non vengono toccati "per troppo tempo" (soglia non definita). In pratica il bot potrebbe mandare messaggi ogni giorno, più volte.

---

### 1.7 Funzionalità eccessivamente complesse per l'MVP

**Valutazione automatica delle idee (sezione 7.3):**
"Fa una valutazione se l'idea è utile al raggiungimento degli obiettivi. Se non è utile non ne parla più. Se si avvia una conversazione..." — non è specificato quando parte la conversazione, chi decide, su quale base. Richiede un LLM con ragionamento strategico e memoria degli obiettivi. La complessità reale è molto maggiore di quanto il documento suggerisca.

**Revisione settimanale ridondante:**
Se i check-in serali funzionano, l'utente ha già queste informazioni. Una revisione settimanale su un'utente già sopraffatta dagli input quotidiani aggiunge un punto di contatto in eccesso.

---

### 1.8 Cosa manca completamente

- **Gestione dei cambiamenti agli obiettivi:** cosa succede quando la bottega viene venduta? Il bot ha tutta la sua logica costruita intorno a obiettivi che non esistono più. Il "versioning" è menzionato in una riga senza nessun dettaglio su come funziona.
- **Privacy e sicurezza dei dati:** completamente assente. L'utente condividerà dubbi, paure, obiettivi finanziari, stati emotivi. Non è menzionato dove vengono salvati, chi vi accede, per quanto tempo, come cancellarli.
- **Gestione degli errori del modello AI:** nessun meccanismo di feedback, correzione, o rilevamento di risposte fuori contesto o inappropriate.
- **Onboarding parziale:** cosa succede se l'utente non completa l'onboarding? Il bot ha un profilo parziale? Aspetta? Riparte da zero?
- **Il check-in theater:** l'utente risponde ai check-in in modo da sembrare produttiva senza che nulla cambi nella realtà. Nessun meccanismo per rilevare questo pattern.
- **Dipendenza psicologica:** se il bot funziona, l'utente smette progressivamente di esercitare il muscolo della prioritizzazione autonoma. Nessun meccanismo per trasferire autonomia nel tempo.

---

## PARTE 2 — FACT-CHECKING DELLA RICERCA

### 2.1 Valutazione complessiva: 4/10

Il documento di ricerca è utile come esercizio di design thinking e fonte di ispirazione per pattern conversazionali. **Non è affidabile come ricerca di mercato** e non va usato per validare affermazioni di differenziazione competitiva.

---

### 2.2 Errori fattuali

**Woebot non è nato su Telegram — FALSO**
Il documento afferma: "nato come bot Telegram nel 2017." Woebot è nato come bot Facebook Messenger nel 2017. Questo è un errore factual netto sul caso di studio più documentato della ricerca.

**DailyBot su Telegram — PROBABILMENTE INVENTATO**
DailyBot è nato e rimasto prevalentemente una soluzione per team aziendali su Slack e Microsoft Teams. Non risulta avere un'integrazione Telegram come canale primario o documentato.

**Rosebud "integrazione Telegram" — NON VERIFICABILE, probabilmente inventato**
Rosebud opera come app web e app mobile. Non risulta avere un'integrazione Telegram documentata.

**Notion AI + Telegram — Non è un prodotto, è un'architettura teorica**
Presentato come il settimo "strumento analizzato", in realtà è una configurazione che qualcuno può costruire con Make/Zapier. Non esiste come prodotto con utenti, supporto o documentazione propria. I dialoghi mostrano comportamenti (tagging intelligente per obiettivo strategico) che richiedono un AI layer custom non incluso nelle integrazioni standard.

**Accountability Bot su Telegram — Non è un prodotto identificabile**
È un "pattern diffuso in community IndieHackers" presentato con lo stesso peso dei tool reali. `@accountability_bot` come username specifico non ha documentazione pubblica verificabile.

---

### 2.3 Affermazioni parzialmente verificate o non verificabili

| Affermazione | Stato |
|---|---|
| Woebot: "oltre 30 pubblicazioni scientifiche" | PARZIALMENTE VERIFICATO — plausibile ma molte sono studi interni di Woebot Health, non peer review indipendenti |
| Rocky.ai: funzioni "parking lot" e "gerarchia temporale" come dichiarate | NON VERIFICABILE — potrebbero essere interpretazioni del ricercatore, non feature con quel nome |
| Rosebud: "pattern recognition dopo 4-6 settimane" | NON VERIFICABILE come funzione dichiarata — sembra idealizzazione |
| "Nessun bot risponde attivamente nei momenti di crisi motivazionale" | IMPRECISO — Woebot fa esattamente questo; la lacuna reale è più specifica: nessun bot italiano per imprenditori artigiani lo fa |
| "La perdita pesa, non il guadagno" sugli streak | VERIFICATO — è loss aversion (Kahneman & Tversky, Prospect Theory 1979), applicazione documentata nella letteratura sulla gamification |

---

### 2.4 Dialoghi tipici: rischio di aspettative distorte

I dialoghi più sofisticati (Rocky, Rosebud, Accountability Bot) descrivono comportamenti che attualmente richiedono un LLM con prompt engineering avanzato, memoria persistente personalizzata, e logica di classificazione intento avanzata. Presentarli come "funzionamento effettivo" di prodotti esistenti crea aspettative che portano a sottovalutare la complessità tecnica di implementazione.

I dialoghi più attendibili: **Woebot** (tecniche CBT documentate) e **Habitbot** (funzionalità standard dei bot Telegram di questa categoria).

---

### 2.5 Metodologia: limiti reali

- Nessuna verifica live dei bot in prima persona
- Nessun dato quantitativo: utenti, retention, pricing, rating sugli store
- Selezione non sistematica dei 7 tool (nessun criterio esplicito)
- Confidenza uniforme su tutto, indipendentemente dalla verifica sottostante
- Mancano tool rilevanti: Coach.me, Fabulous, Stoic, Reflectly

---

## PARTE 3 — PUNTI DI FORZA DELLA RICERCA E BEST PRACTICES

### 3.1 Funzionalità efficaci da includere nelle specifiche

**Pulsanti inline nel check-in serale** *(da Habitbot)*
La sera, dopo una giornata in negozio, l'attrito di scrivere è abbastanza alto da causare il salto del check-in. Il check-in serale deve presentare 3 pulsanti, non aspettare testo libero:
```
[Ho lavorato sull'operativo]
[Ho lavorato su qualcosa di strategico]
[Niente di significativo oggi]
```
Il testo libero rimane disponibile ma non è richiesto. Il tap attiva lo scenario corretto (A, B, C).

**Loop chiuso mattina-sera** *(da DailyBot)*
Ciò che l'utente dichiara la sera ("la mia priorità per domani è X") viene richiamato esplicitamente la mattina dopo. Senza questo loop, il check-in serale diventa un atto isolato — si dichiara un'intenzione e nessuno la verifica. Il check-in mattutino non è opzionale: è il motore dell'accountability. Va nell'MVP con possibilità di disattivarlo su richiesta, non come feature da decidere dopo.

**Reindirizzamento post-parcheggio** *(da Rocky.ai)*
Dopo ogni conferma idea, il bot non si ferma alla conferma. Aggiunge sempre: "Sei in negozio adesso o hai un momento? C'è qualcosa su cui vuoi tornare?" Senza il reindirizzamento, il parcheggio accumula idee ma non protegge il focus.

**3 domande di allineamento per le idee** *(da Rosebud)*
Quando si valuta un'idea (in revisione, non al momento della cattura), tre domande strutturate:
1. Questa idea serve principalmente la Bottega o Oltre la Bottega?
2. Quanto tempo richiederebbe a regime (ore/settimana)?
3. Hai già qualcosa di simile in sospeso o già provato?

**Distinzione imprevisto reale vs cessione volontaria** *(da Rosebud)*
Nella revisione settimanale, dopo il dato sulle ore di Oltre la Bottega: "Le ore mancanti: il negozio aveva davvero bisogno di te, o qualcosa le ha assorbite che potevi rimandare?" Non è un giudizio — è la domanda più onesta e potente dell'intera ricerca.

**Tassonomia dei blocchi nello Scenario C** *(da Woebot)*
La distinzione "generale vs specifico" nell'idea è troppo binaria. Usare tre categorie:
- Stanchezza fisica (il corpo non ce la fa)
- Paura (c'è qualcosa nello specifico che spaventa)
- Confusione (non so da dove iniziare / non vedo il percorso)

Ogni categoria richiede una risposta diversa del bot.

**Frase di ancoraggio al perché originario**
Nei momenti di bassa motivazione, richiamare la motivazione dichiarata durante l'onboarding: "Hai detto che vuoi questo perché vuoi comprare casa a Marta e avere più tempo per te. Questo è quello che stai costruendo." Assente nell'idea — va aggiunto al toolkit dello Scenario C.

**Pattern recognition Livello 1** *(da Rosebud, implementabile subito)*
Non serve NLP. Bastano counter semplici sui log:
- Settimane consecutive sotto quota ore per Oltre la Bottega
- Giorni di fila completamente operativi
- Correlazione giorno/settimana con tipo di lavoro

Dopo 2 settimane consecutive sotto obiettivo, il bot lo nomina in revisione: "Questa è la seconda settimana consecutiva. Vuoi che ne parliamo?" Non 4-6 settimane come in Rosebud — 2 settimane, per intervenire prima che diventi pattern consolidato.

---

### 3.2 Pattern UX da rispettare nelle specifiche

**Pulsanti vs testo libero:**
- Usare pulsanti quando le opzioni sono finite e note in anticipo (check-in serale, conferma parcheggio, revisione idee settimanale, check-in mattutino)
- Usare testo libero quando il contenuto è aperto (Scenario C, cattura idee, onboarding, follow-up post-blocco)
- Regola pratica: se il bot conosce le opzioni prima che l'utente risponda, usa i pulsanti

**Progressione "1/3, 2/3, 3/3":**
- Usare nei flussi strutturati che è importante completare: Scenario C, onboarding
- Non usare nel check-in serale normale (1 domanda, niente numerazione)
- Non usare nella cattura rapida di idee (deve essere istantanea)

**Conferma parcheggio — formato standardizzato (2 righe massimo):**
```
"Salvata — [titolo breve idea] nel Parcheggio.
Categoria: [Bottega / Oltre la Bottega]. Te la riporto domenica."
```
Nessuna valutazione nel momento della cattura. Se la classificazione AI è ad alta confidenza, aggiungere facoltativamente: "Sembra rilevante per Oltre la Bottega. Vuoi valutarla prima di domenica?"

**Normalizzazione senza compiacenza:**
- NO: "Tranquilla, è normale! / Sei comunque stata produttiva!"
- SÌ: "Il negozio aveva bisogno. Succede. Cosa potrebbe bloccare anche domani?"
- Dopo una settimana intera senza lavoro strategico — NO: "Hai comunque fatto molto per il negozio!" / SÌ: "Questa settimana niente Oltre la Bottega. È la seconda di fila. Vuoi capire cosa sta succedendo o preferisci solo registrarlo?"

**Una domanda alla volta — regola assoluta per:**
- Check-in serale (una domanda, basta)
- Cattura idea (zero domande, solo conferma)
- Reminder (messaggio unidirezionale)
- Scenario B (una domanda di follow-up, poi chiude)

---

### 3.3 I 3 differenziatori più potenti (non presenti nell'idea attuale)

**1. Reminder a orario concordato nella conversazione**
Quando l'utente usa frasi come "provo dopo le 16", "stasera ci provo", il bot rileva l'intenzione temporale e chiede: "Vuoi che ti scriva alle 16:15?" Se risponde sì, viene creato un reminder contestuale one-shot. Non è il check-in fisso — è un follow-up legato all'impegno specifico dichiarato in quella conversazione.

Implementazione: riconoscimento frasi temporali, conferma con pulsante, scheduler one-shot. Tecnicamente richiede scheduling flessibile.

**2. La distinzione operativo/strategico insegnata, non solo registrata**
Nelle prime 2-3 settimane, quando l'utente racconta una giornata operativa, il bot fa sistematicamente la domanda (una volta a settimana, non a ogni check-in): "È stato operativo necessario o qualcosa che avresti potuto rimandare o delegare?" Non come giudizio — come calibrazione progressiva. Nel tempo, l'utente inizia a fare questa distinzione autonomamente. La consapevolezza si internalizza.

**3. La libreria di sblocchi personali**
Quando l'utente elabora un blocco nello Scenario C e arriva a un'intuizione utile, il bot chiede: "Vuoi salvare questa come nota per la prossima volta che ti senti così?" Le prossime volte che si ripresenta uno scenario simile, il bot richiama: "La volta scorsa quando ti sentivi così, hai scritto: '[frase]. È ancora valida?" Non consigli generici — le sue stesse parole nei suoi momenti più lucidi.

---

### 3.4 Red flag di design da evitare

| Pattern da evitare | Perché | Alternativa |
|---|---|---|
| Valutare le idee nel momento della cattura | Se l'utente è con clienti, 3 domande di follow-up rompono il ritmo | Le 3 domande solo in revisione settimanale o su richiesta esplicita |
| Revisione domenicale con troppe domande | Flussi di revisione lunghi causano abbandono | 3 dati + 1 domanda aperta + pulsanti per le idee, niente conversazione aperta |
| Streak azzerato comunicato in modo prominente | La perdita è così dolorosa che alcuni utenti abbandonano il bot | Non nominare l'azzeramento — ricominciare a contare silenziosamente |
| Tono da wellness/positività tossica | L'utente percepisce le risposte come automatiche e smette di fidarsi | Riconoscimento fattuale: "Hai tenuto lo streak per 7 giorni" invece di "Stai andando alla grande!" |
| Check-in aperto senza struttura | Effetto blank page — l'utente rimanda perché "non sa cosa rispondere" | Sempre pulsanti come opzione principale. "Niente di significativo oggi" deve essere una risposta pari dignità |
| Notifiche durante le ore di negozio | Interrompe il lavoro con i clienti, causa disattivazione delle notifiche | Tutti i messaggi che richiedono riflessione solo nelle finestre 7:00-8:30 e 19:00-22:30 |

---

## PARTE 4 — RACCOMANDAZIONI CONCRETE PER LE SPECIFICHE DI SVILUPPO

### 4.1 Decisioni da prendere prima di iniziare lo sviluppo

Queste domande non sono specifiche tecniche — sono decisioni di prodotto che definiscono cosa si sta costruendo. Senza risposta, le scelte implementative saranno arbitrarie.

1. **Qual è il meccanismo causale tra "il bot ti ricorda" e "l'utente cambia comportamento duraturo"?** Se non c'è una risposta chiara, il prodotto è un diario con promemoria, non un coach.

2. **Il check-in è serale o c'è anche quello mattutino?** Decidere definitivamente. Il loop mattina-sera è il motore dell'accountability — tenerlo "opzionale" ne riduce l'efficacia.

3. **Lo Scenario C: il bot gestisce stati emotivi o no?** Se sì, serve un meccanismo minimo di escalation. Se no, lo Scenario C va ridimensionato a "proposta di azione minima", non a gestione del blocco emotivo.

4. **Come l'utente indica l'intenzione al bot?** (prefisso testuale tipo "IDEA:", flusso guidato, classificazione implicita AI, o ibrido?) Questa decisione precede tutta l'implementazione del motore di conversazione.

5. **Dove vengono salvati i dati e chi vi accede?** Risposta richiesta prima dello sviluppo, non dopo.

---

### 4.2 Specifiche MVP — Lista ordinata per priorità

| # | Specifica | Motivazione |
|---|---|---|
| 1 | **Check-in serale con pulsanti inline** — 3 opzioni tap, niente testo obbligatorio | Riduce l'attrito abbastanza da aumentare il tasso di completamento |
| 2 | **Classificazione dei messaggi — specifica funzionale completa** — categorie, gestione ambiguità, correzione errori | Componente più critico e più sottostimato dell'MVP |
| 3 | **Check-in mattutino come loop chiuso** — richiama esplicitamente l'intenzione della sera precedente | Trasforma il check-in da atto isolato ad accountability loop |
| 4 | **Reindirizzamento post-parcheggio** — dopo ogni conferma, sempre "vuoi tornare a quello su cui stavi lavorando?" | Converte il parcheggio da accumulo a protezione del focus |
| 5 | **Scenario C con tassonomia a 3 tipi** — stanchezza fisica / paura / confusione, ognuna con risposta diversa | La distinzione "generale vs specifico" è troppo binaria per essere utile |
| 6 | **Frase di ancoraggio al perché originario** — nel toolkit dello Scenario C, richiamare la motivazione dell'onboarding | Funzionalità più diretta per lo sblocco, assente nell'idea attuale |
| 7 | **Schema della memoria — specifica tecnica completa** — campi strutturati, frequenza di compressione, meccanismo di fedeltà, versioning obiettivi | La vaghezza attuale porta a scelte implementative che saranno difficili da correggere |
| 8 | **3 domande di allineamento per le idee** — solo in revisione o su richiesta, mai al momento della cattura | L'evaluation nel momento di carica emotiva è il pattern da evitare |
| 9 | **Distinzione imprevisto reale vs cessione volontaria** nella revisione settimanale | La domanda più onesta e potente dell'intera ricerca |
| 10 | **Pattern recognition Livello 1** — counter semplici: settimane consecutive sotto obiettivo, soglia di attivazione a 2 settimane | Implementabile con semplici query sui log, alto impatto |
| 11 | **Privacy e sicurezza dati** — specifica su storage, accesso, retention, cancellazione | Mancanza legale e di fiducia, non un dettaglio tecnico |
| 12 | **Strategia di re-engagement** — cosa fa il bot se l'utente non risponde per 3 giorni | Senza questo il bot muore silenziosamente e l'utente si sente in colpa |
| 13 | **Meccanismo di feedback sulle risposte del bot** — come l'utente segnala una risposta fuori contesto | Soprattutto critico nello Scenario C |

---

### 4.3 Specifiche V2 — Dopo validazione MVP

| # | Specifica |
|---|---|
| 1 | Reminder contestuale one-shot — riconoscimento intenzioni temporali nella conversazione + scheduling flessibile |
| 2 | Streak strategico — con celebrazione milestone (3, 7, 21 giorni) e azzeramento silenzioso |
| 3 | Libreria di sblocchi personali — salvataggio e recupero pensieri alternativi elaborati nello Scenario C |
| 4 | Domanda di calibrazione operativo/strategico — una volta a settimana nel check-in, non a ogni sessione |
| 5 | Pattern recognition Livello 2 — correlazioni tra eventi narrati e cali di lavoro strategico (richiede NLP) |

---

### 4.4 Nota sull'uso della ricerca

Il documento research.md è utile come fonte di ispirazione per i pattern conversazionali. Non è affidabile per affermare che "il mercato non fa X" o per validare affermazioni di differenziazione competitiva.

Affermazioni verificate e usabili:
- I pattern UX descritti (pulsanti inline, una domanda alla volta, streak, capture-then-decide) sono principi solidi
- Woebot e le sue tecniche CBT sono documentati e accurati (eccetto la piattaforma di origine)
- La distinzione imprevisto/cessione volontaria di Rosebud è un meccanismo reale e potente
- Il meccanismo di loss aversion sugli streak è supportato dalla psicologia comportamentale

Affermazioni da non usare per decisioni di sviluppo:
- Le "lacune di mercato" come verdetti verificati — sono deduzioni logiche su 7 tool selezionati
- I dialoghi di Rocky.ai, Rosebud e Accountability Bot come "comportamento effettivo" — sono esercizi di design fiction
- L'integrazione Telegram di DailyBot e Rosebud — non verificata, probabilmente inesistente
- Notion AI + Telegram come settimo "competitor" — è un'architettura teorica, non un prodotto

---

*Questo documento va letto insieme a idea.md e research.md. Le raccomandazioni sono input per la fase di definizione delle specifiche — non vanno implementate direttamente senza prima prendere le decisioni elencate in 4.1.*
