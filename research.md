# La Rotta — Research: Chatbot AI di successo come riferimento

**Data ricerca:** giugno 2026  
**Fonte:** analisi multi-agente basata su conoscenza documentata fino ad agosto 2025  
**Scopo:** identificare pattern, funzionalità e approcci conversazionali da cui trarre ispirazione per lo sviluppo del bot

---

## Nota metodologica

La ricerca è stata condotta con tre agenti paralleli, ciascuno con un focus diverso:
- **Agente 1:** produttività, habit tracking, check-in quotidiani su Telegram
- **Agente 2:** AI coaching, supporto motivazionale, gestione dei momenti di blocco
- **Agente 3:** goal tracking, protezione del tempo strategico, gestione idee per imprenditori

I bot descritti sono strumenti reali documentati. I dialoghi esemplificativi sono costruiti sul loro funzionamento effettivo, non trascrizioni letterali.

---

## I 7 esempi analizzati

---

### 1. Habitbot — Habit Tracker su Telegram

**Username Telegram:** `@Habitbot`

#### Problema che risolve
Aiuta a costruire e mantenere abitudini quotidiane direttamente dentro Telegram, senza installare app separate. Il meccanismo degli streak crea attaccamento emotivo alla continuità.

#### Funzionalità principali
- Creazione di abitudini personalizzate con frequenza configurabile (giornaliera, giorni specifici)
- Promemoria automatici all'orario scelto
- Conferma dell'abitudine con pulsanti inline (tap, non scrittura)
- Visualizzazione streak (serie di giorni consecutivi)
- Report settimanali e mensili

#### Dialogo tipico

```
BOT (ore 21:30):
"Buonasera! Ecco i tuoi check-in di oggi:
[ ] Lettura 20 minuti
[ ] Pianificazione domani
[ ] Nessun social dopo le 20"

UTENTE: [tocca "Lettura 20 minuti" → spunta verde]
[tocca "Pianificazione domani" → spunta verde]

BOT: "Ottimo! 2/3 completate.
Lettura: streak 14 giorni.
Vuoi segnare anche l'ultima?"

UTENTE: No, salto oggi

BOT: "Capito. Il tuo streak su 'Nessun social' si azzera.
Vuoi impostare un obiettivo diverso per quella abitudine?"
```

#### Cosa lo rende utile e apprezzato
- Zero attrito: rispondere a un messaggio è più veloce che aprire un'app
- Gli streak creano un meccanismo di gamification efficace: la perdita pesa, non il guadagno
- Il bot non moralizza se si salta — mostra il dato nudo e lascia la riflessione all'utente
- I report visivi rivelano pattern nel tempo ("il lunedì è sempre il giorno peggiore")

#### Elementi ispiratori per La Rotta
- **I pulsanti inline per il check-in serale**: non chiedere di scrivere frasi lunghe, proporre opzioni tap-tap-tap. Scrivere è un attrito troppo alto alle 21:30 dopo una giornata in negozio
- **Lo streak come rinforzo positivo** (non punitivo): "Questa è la 5ª sera che lavori su Oltre la Bottega questa settimana" crea momentum senza pressione
- **Il promemoria fisso all'orario esatto** come motore principale dell'abitudine

---

### 2. DailyBot — Check-in e Journaling Strutturato

**Sito:** dailybot.me  
**Dove opera:** Slack e Telegram, anche uso personale

#### Problema che risolve
La giornata finisce senza mai fermarsi a riflettere. L'operativo fagocita tutto e non c'è un momento strutturato per capire cosa è andato e cosa conta davvero per domani. DailyBot forza una pausa serale con domande guidate.

#### Funzionalità principali
- Check-in serale con domande configurabili ("Cosa hai completato?", "Cosa ti ha bloccato?", "Priorità di domani")
- Alcune versioni integrano GPT per un feedback o riassunto sintetico
- Storico consultabile delle risposte
- Esportazione del journal in formato testo
- Il bot ricorda la priorità dichiarata la sera e la richiama la mattina dopo

#### Dialogo tipico

```
BOT (ore 21:00):
"Ciao! È il momento della tua riflessione serale.

1/3 — Qual è stata la tua vittoria più grande di oggi?"

UTENTE: "Ho finalmente mandato l'offerta al cliente
         che rimandavo da una settimana"

BOT: "2/3 — Cosa ti ha rubato più energia o tempo oggi?"

UTENTE: "Ho perso 2 ore a sistemare un problema
         con il fornitore di tessuti"

BOT: "3/3 — Qual è la cosa più importante da fare domani?"

UTENTE: "Chiamare la banca per il mutuo del negozio"

BOT: "Perfetto. Ho salvato il tuo check-in.
     Domani mattina alle 8:30 ti ricorderò
     la tua priorità: chiamare la banca."
```

#### Cosa lo rende utile e apprezzato
- Le domande guidate evitano il blocco da pagina bianca — si sa esattamente cosa rispondere
- La struttura "vittoria / ostacolo / priorità domani" è un framework consolidato (GTD + Agile retrospective)
- La progressione "1/3, 2/3, 3/3" crea senso di completamento — l'utente vuole arrivare alla fine
- Il tono è neutro e privo di giudizio — registra, non valuta

#### Elementi ispiratori per La Rotta
- La funzione **"ti ricordo domani mattina"** chiude il cerchio: il check-in serale diventa un loop attivo con il giorno successivo
- La struttura numerata **"domanda 1 di 3"** crea progressione e riduce l'abbandono a metà
- Adattamento chiave per La Rotta: aggiungere una domanda esplicita "oggi hai lavorato più sull'operativo o sullo strategico?" con risposta a pulsante. Questa domanda sola porta consapevolezza senza fare la predica

---

### 3. Rocky.ai — AI Coach per Imprenditori

**Sito:** rocky.ai  
**Dove opera:** app web dedicata con integrazioni aziendali via Slack

#### Problema che risolve
Gli imprenditori sono intrappolati nella routine operativa e perdono la bussola sugli obiettivi strategici. Rocky non è un task manager: è un interlocutore che ogni settimana chiede "perché stai facendo quello che stai facendo?". È progettato esplicitamente per professionisti e imprenditori, non per il wellness generico.

#### Funzionalità principali
- **Check-in a cascata:** non registra solo la risposta, ma risponde a sua volta — se dici "ho perso tempo", Rocky chiede "cosa intendi per perso? cosa avresti voluto fare invece?"
- **Gestione del blocco:** usa tecniche di coaching cognitivo-comportamentale — quando sei bloccata, fa domande di chiarimento invece di dare consigli
- **Gerarchia temporale:** sessioni "oggi" vs "questa settimana" vs "questo trimestre" vs "questo anno" — le sessioni quotidiane sono operative, quelle settimanali di allineamento strategico
- **Parking lot integrato:** quando arriva un'idea nuova dice "Interessante. Lo metto nel parcheggio. Vuoi continuare con quello su cui stavi lavorando?"
- **Memoria e continuità:** ricorda quello che hai detto la settimana scorsa e lo riprende in modo organico

#### Dialogo tipico

```
ROCKY: Buonasera. Fine settimana lavorativa.
       Una domanda: rispetto a quello che volevi
       fare questa settimana, dove sei arrivata?

UTENTE: Ho fatto mille cose ma non quelle importanti.
        Ho gestito clienti, fornitori, un problema con la cassa.

ROCKY: Capito. Quelle cose urgenti erano necessarie
       o avresti potuto delegarne o rimandarne qualcuna?

UTENTE: Alcune sì, ma il problema della cassa no.

ROCKY: Ok. A parte la cassa, c'era qualcosa che hai
       lasciato indietro che ti pesa di più?

UTENTE: Sì, non ho lavorato per niente
        alla ristrutturazione del negozio.

ROCKY: Perché pensi che sia successo?
       È una questione di tempo, di energia,
       o di qualcos'altro?

UTENTE: Onestamente mi spaventa un po'.
        È grande, non so da dove iniziare.

ROCKY: Questo è utile sapere. La prossima volta
       che apriamo questo argomento, iniziamo da lì:
       qual è il passo più piccolo possibile
       per cominciare. Va bene?
```

#### Cosa lo rende utile e apprezzato
- Non giudica mai e non elargisce elogi vuoti
- Le domande sono concrete, non filosofiche ("dove sei arrivata?" non "come ti senti?")
- La continuità tra sessioni fa sentire l'utente ascoltato invece di ripetersi ogni volta
- Il linguaggio è da imprenditore, non da wellness

#### Elementi ispiratori per La Rotta
- Il **parking lot integrato nella conversazione**: è una funzione dichiarata, non un ripiego — "lo metto nel parcheggio, vuoi continuare su quello che stavi facendo?"
- Le **domande sul perché non è successo** sono più potenti di qualsiasi promemoria
- La **gerarchia temporale** (oggi / settimana / trimestre) è un modello da replicare per dare a ogni check-in il giusto peso

---

### 4. Woebot — AI per il Supporto nei Momenti di Blocco

**Dove opera:** app mobile iOS/Android — nato come bot Telegram nel 2017  
**Nota:** il modello conversazionale è il più studiato accademicamente (oltre 30 pubblicazioni scientifiche)

#### Problema che risolve
I momenti di blocco, mancanza di voglia, auto-sabotaggio. Woebot usa tecniche di terapia cognitivo-comportamentale (CBT) per aiutare a identificare pensieri automatici negativi e trovare prospettive alternative. È direttamente rilevante per lo "Scenario C" del check-in di La Rotta (non ho voglia / ho dubbi).

#### Funzionalità principali
- **Check-in emotivo con escalation:** scala di umore 1-7 con emoji — in base alla risposta, apre un dialogo completamente diverso
- **Distinzione tra tipi di blocco:** distingue esplicitamente "non ho voglia", "sono bloccata" e "sono sopraffatta" — e risponde in modo diverso a ciascuno
- **Thought record:** guida a identificare il pensiero automatico negativo, valutarlo ("quanto ci credi, da 0 a 100?"), trovare un pensiero alternativo
- **Domande che ribaltano la prospettiva:** "cosa diresti a una tua amica nella stessa situazione?"
- **Micro-lezioni:** 3-5 minuti su temi specifici (procrastinazione, perfezionismo) ancorate a quello che l'utente ha detto nelle sessioni precedenti

#### Dialogo tipico (momento di blocco — Scenario C)

```
WOEBOT: Come stai stasera? [emoji scala]

UTENTE: [sceglie "un po' giù"]

WOEBOT: Capito. Vuoi dirmi cosa è successo oggi?

UTENTE: Avevo un piano preciso ma non ho
        combinato niente. Mi sento inutile.

WOEBOT: "Mi sento inutile" è una frase forte.
        Quando dici questo, stai parlando di
        oggi specificamente o è un pensiero
        più generale che hai su di te?

UTENTE: Più generale credo. Quando non produco, non valgo.

WOEBOT: Questo pensiero — "se non produco, non valgo" —
        quanto lo credi, da 0 a 100?

UTENTE: Tipo 80.

WOEBOT: Ok. Se una tua amica ti dicesse questa cosa
        di se stessa, cosa le risponderesti?

UTENTE: Le direi che è assurdo, che una persona
        vale per quello che è, non per quello che produce.

WOEBOT: Esatto. Quella risposta che hai dato alla tua
        amica — è disponibile anche per te. Non adesso
        magari, ma esiste. Vuoi salvare questo pensiero
        alternativo per rileggerlo quando ti capita di nuovo?
```

#### Cosa lo rende utile e apprezzato
- Le domande socratiche sono molto più potenti dei consigli diretti
- Non moralizza mai e non dice "dovresti"
- Riconosce esplicitamente che certi giorni non si riesce e normalizza questo senza compiacenza
- Il tono è caldo ma mai sdolcinato
- Fa mantenere la rotta verso l'obiettivo 

#### Elementi ispiratori per La Rotta
- La distinzione **"stanchezza fisica / stanchezza mentale / senso di vuoto"** — adattata al lavoro: "questo è operativo che ti ha esaurita, o è blocco strategico, o è paura?"
- Le domande che ribaltano la prospettiva per l'auto-sabotaggio: "cosa consiglieresti a un'altra imprenditrice nella tua situazione?"
- **Il pensiero alternativo salvato**: "vuoi salvarlo per rileggerlo la prossima volta?" — meccanismo di continuità tra sessioni
- Il modello dello Scenario C di La Rotta può essere costruito quasi direttamente su questo framework

---

### 5. Rosebud AI Journal — Journaling Conversazionale per Fondatori

**Sito:** rosebud.app  
**Dove opera:** app web + integrazione Telegram

#### Problema che risolve
L'imprenditore non riesce a fare chiarezza strategica perché non si ferma mai a riflettere. Rosebud usa domande socratiche per distinguere urgente da importante, processare la tensione tra obiettivi diversi e riconoscere i pattern ricorrenti. Pensato esplicitamente per founder e imprenditori.

#### Funzionalità principali
- **Journaling conversazionale:** il bot fa domande aperte, non form da riempire — è una vera conversazione
- **Goal alignment check:** quando nomini una nuova idea, il bot la confronta con i tuoi obiettivi dichiarati e fa 2-3 domande di chiarimento
- **Pattern recognition nel tempo:** dopo 4-6 settimane l'AI identifica pattern ricorrenti e li porta alla luce ("noto che ogni volta che parli di Oltre la Bottega dici 'ma prima devo...' — cosa significa?")
- **Bias detection:** riconosce quando stai razionalizzando una distrazione
- **Distinzione tra imprevisto reale e cessione volontaria del tempo** nella weekly review

#### Dialogo tipico

```
UTENTE: Sto pensando di aprire un profilo Instagram
        dedicato alla storia dei produttori locali.
        Potrebbe fare content per il negozio e per
        il corso. Cosa ne pensi?

BOT: Interessante. Prima di esplorarlo, alcune domande:

     1. Questa idea serve principalmente il negozio
        attuale o 'Oltre la Bottega'?
     2. Quanto tempo richiederebbe a regime (ore/settimana)?
     3. C'è qualcosa di simile che hai già provato
        e non hai continuato?

     Non devi decidere ora. Vuoi parcheggiarla
     e tornarci domenica?

UTENTE: Sì, parcheggiala

BOT: Salvata. Domenica la esaminiamo con le altre 4 idee.

     Intanto: hai 90 minuti bloccati domani mattina
     per 'Oltre la Bottega'. Su cosa lavorerai?
```

```
[Weekly review]

BOT: Ho notato qualcosa: nelle ultime 3 settimane
     hai generato 11 nuove idee, ma nessuna delle
     ore bloccate per 'Oltre la Bottega' è stata
     usata per il corso.

     Come mai, secondo te?

UTENTE: Il negozio assorbe tutto

BOT: È una spiegazione, ma voglio capire meglio.
     Delle ore bloccate, quante erano realmente
     indisponibili per imprevisti del negozio,
     e quante le hai cedute tu volontariamente?
```

#### Cosa lo rende utile e apprezzato
- Non chiede "hai fatto X?" ma "perché non hai fatto X?" e poi ancora "cosa lo ha impedito davvero?"
- La domanda sulla cessione volontaria del tempo è brutalmente onesta ma non giudicante
- Il pattern recognition trasforma il bot da tool a specchio strategico nel tempo

#### Elementi ispiratori per La Rotta
- Le **3 domande per valutare un'idea** prima di parcheggiarla: quale obiettivo serve? quanto tempo richiede? hai già qualcosa di simile in sospeso?
- Il **pattern recognition nel tempo**: dopo alcune settimane il bot può dire "noto che ogni volta che si avvicina una scadenza del negozio, le ore di Oltre la Bottega spariscono" — questa è la funzionalità più differenziante
- La **distinzione imprevisto reale vs cessione volontaria** nella weekly review è la domanda più potente dell'intera ricerca

---

### 6. Accountability Bot su Telegram — Operativo vs Strategico in Tempo Reale

**Pattern diffuso in:** community IndieHackers, Building in Public  
**Esempi:** `@accountability_bot`, bot custom in community Telegram di imprenditori

#### Problema che risolve
La solitudine dell'imprenditore: nessuno che chieda "hai fatto quello che dovevi fare oggi?". Il bot fa da accountability partner silenzioso, 24/7. La distinzione tra operativo e strategico viene fatta in tempo reale ogni giorno, creando un'abitudine mentale progressiva.

#### Funzionalità principali
- **Morning check-in** con domanda sulla priorità strategica del giorno (non operativa)
- **Follow-up gentile** quando la risposta è operativa: "ok, e per il tuo progetto strategico oggi?"
- **Check-in a orario concordato** se l'utente ha detto "forse dopo le 17" — il bot scrive alle 17:15
- **Check-out serale** con report di 2 righe su cosa è stato fatto sul fronte strategico
- **Streak** dei giorni consecutivi con almeno un'azione strategica completata

#### Dialogo tipico

```
BOT (lunedì mattina, 8:00):
"Buongiorno! Qual è la tua intenzione strategica
per oggi? (Operativo = quello che il negozio richiede.
Strategico = quello che costruisce il tuo futuro)"

UTENTE: "Devo sistemare il magazzino e
         preparare l'ordine di novembre"

BOT: "Annotato. Sembra operativo — necessario
     ma non strategico.
     C'è uno spazio oggi, anche solo 30 minuti,
     per 'Oltre la Bottega'?"

UTENTE: "Forse dopo le 17"

BOT: "Perfetto. Ti scrivo alle 17:15
     per il check-in strategico."

[Lunedì, 17:15]

BOT: "Check-in strategico!
     Hai lavorato su 'Oltre la Bottega'?"

UTENTE: "Sì, ho scritto la scaletta del
         primo modulo del corso"

BOT: "Eccellente! Streak strategico: 3 giorni.
     Vuoi salvare questo come progresso
     nel progetto Oltre la Bottega?"
```

#### Cosa lo rende utile e apprezzato
- La distinzione operativo/strategico fatta in tempo reale ogni giorno è il contributo principale
- Il follow-up gentile quando la risposta è operativa insegna lentamente a separare i due mondi
- Non è un task manager — è un interlocutore che ricorda CHI stai cercando di diventare, non solo COSA devi fare oggi

#### Elementi ispiratori per La Rotta
- Il **follow-up gentile sull'operativo**: quando l'utente racconta una giornata operativa, il bot non la rifiuta ma chiede "è stata una scelta consapevole o è successo senza accorgertene?" — questa domanda sola porta consapevolezza
- Il **check-in a orario concordato durante la conversazione** (non preimpostato in anticipo) crea accountability concreta e contestuale
- Lo **streak strategico** separato da qualsiasi altro streak operativo

---

### 7. Notion AI + Telegram — Secondo Cervello per Imprenditori

**Tecnologia:** integrazione tramite Make/Zapier/n8n  
**Dove opera:** Telegram come punto di ingresso veloce, Notion come database strutturato

#### Problema che risolve
Le idee arrivano nel momento sbagliato — mentre si serve un cliente, mentre si apre la bottega. Senza un sistema, vengono elaborate subito (distrazione) o dimenticate (frustrazione). Notion AI funge da secondo cervello strutturato; Telegram è il punto di ingresso già in tasca.

#### Funzionalità principali
- **Cattura rapida da Telegram**: messaggio vocale o testuale → trascrizione → inserimento nel database "Parcheggio Idee"
- **Tagging automatico per obiettivo**: l'AI valuta se l'idea è collegata a quale obiettivo strategico e con quale priorità
- **Weekly review automatizzata**: domenica sera il bot invia il riepilogo degli obiettivi e le idee in attesa di valutazione
- **Separazione netta** tra momento della cattura e momento della valutazione — mai chiedere di valutare nel momento di carica emotiva

#### Dialogo tipico

```
[Martedì mattina, aprendo la bottega]

UTENTE → BOT: "Idea: organizzare un open day tematico
               per Natale con degustazioni"

BOT → UTENTE: "Idea salvata nel Parcheggio Idee.
               Categoria: Bottega Premium.
               Coerenza con i tuoi obiettivi: ALTA.

               Questa settimana hai 3 ore bloccate
               per 'Oltre la Bottega'. Vuoi pianificarla
               per il mese prossimo o valutarla
               nella review di domenica?"

UTENTE: "Domenica"

BOT: "Ok. Te la riporto domenica alle 18:00."
```

```
[Domenica sera — Weekly Review]

BOT: "Revisione settimanale:

OBIETTIVI STRATEGICI
- Bottega Premium: 2/3 azioni ✓
- Oltre la Bottega: 0/2 azioni ⚠
- Preparazione vendita: nessuna azione questa settimana

PARCHEGGIO IDEE (3 in attesa):
1. Open day Natale [valuta]
2. Collaborazione con il negoziante accanto [valuta]
3. Nuovo fornitore ceramiche [sembra operativo — delega?]

Come valuti la settimana?
[Ottima] [Buona] [Difficile]"
```

#### Cosa lo rende utile e apprezzato
- La separazione fisica tra cattura (Telegram, 5 secondi) e valutazione (Notion, con calma) è la chiave del sistema
- La classificazione automatica per obiettivo riduce lo sforzo cognitivo post-cattura
- Il sistema di riproposta programmata evita che le idee muoiano nell'inbox dimenticato

#### Elementi ispiratori per La Rotta
- Il **"capture now, decide later"** è il pattern centrale del Parcheggio delle Opportunità — non chiedere mai di valutare nel momento di entusiasmo
- La **weekly review con dati concreti** (completato/non completato per obiettivo) rende impossibile l'auto-inganno
- La **conferma immediata breve** ("salvata — te la riporto domenica") rassicura l'utente che l'idea non è persa senza distrarlo dal lavoro

---

## Analisi comparativa: cosa manca nel mercato

Tutti i bot analizzati hanno un limite comune che La Rotta ha l'opportunità di colmare:

### Lacuna 1 — Nessun bot distingue operativo da strategico in modo personalizzato
I bot di produttività trattano tutti i task alla stessa maniera. Per un'imprenditrice con bottega, "rispondere a una email del fornitore" e "decidere come posizionare il negozio per la vendita" finiscono nella stessa lista. La distinzione è il cuore del problema — e nessuno la fa con questo livello di personalizzazione sulla storia specifica dell'utente.

### Lacuna 2 — Nessun bot risponde attivamente nei momenti di crisi motivazionale
I bot esistenti sono reattivi (aspettano il check-in) o emettono promemoria passivi. Nessuno dice "So che non hai voglia stasera — ecco perché hai iniziato questo percorso" con un tono caldo e personalizzato. Lo Scenario C di La Rotta è un vuoto reale nel mercato.

### Lacuna 3 — Nessun bot collega le idee nuove alla bussola strategica personale
Il parcheggio delle idee esiste come meccanismo, ma nessun bot chiede "Questa idea è in linea con il tuo obiettivo di portare la bottega a livello premium?" — ovvero, nessuno filtra le idee attraverso gli obiettivi dichiarati durante l'onboarding.

### Lacuna 4 — Nessun bot fa pattern recognition accessibile in italiano per l'artigianato
Rocky.ai e Rosebud si avvicinano, ma sono strumenti anglofoni, costosi e non ottimizzati per la realtà dell'imprenditrice artigiana italiana. La Rotta può fare "noto che ogni volta che si avvicina una fiera, le ore di Oltre la Bottega spariscono" con il contesto specifico della bottega.

---

## Schema conversazionale raccomandato per La Rotta

Sintesi dei pattern più efficaci trovati nella ricerca, adattati al concept di La Rotta:

### Sera (21:30) — Check-in

```
Una domanda calibrata (rotazione o adattiva)
Esempio: "Oggi dove hai messo l'energia principale?"

├── Se risposta operativa → risposta gentile, non giudicante
│   "Il negozio aveva bisogno, succede.
│    C'è stato qualcosa, anche piccolo, per il progetto grande?"
│
├── Se risposta strategica → riconoscimento breve e chiusura
│   "Bene. Questo conta. A domani."
│
├── Se "non ho voglia / sono bloccata" → apertura Scenario C
│   "Questo blocco è più stanchezza, paura,
│    o confusione su dove andare?"
│   ├── Stanchezza → normalizza, proponi azione minima domani
│   ├── Paura → esplora cosa spaventa, proponi passo da 20 minuti
│   └── Confusione → riporta agli obiettivi grandi, chiedi cosa conta
│
└── Chiudi sempre con: "Qualcosa da parcheggiare prima di chiudere?"
```

### Messaggio libero (qualsiasi ora)

```
Il bot classifica: aggiornamento / nuova idea / blocco / domanda

├── Se nuova idea:
│   "Salvata nel Parcheggio. Vale la pena valutarla subito
│    o aspettiamo la review di domenica?"
│   → Se urgente: 3 domande di allineamento agli obiettivi
│   → Se non urgente: conferma breve + chiusura
│
└── Se blocco improvviso → apertura Scenario C immediata
```

### Domenica (revisione settimanale)

```
Report in 3 dati: azioni strategiche / ore Oltre la Bottega / idee in parcheggio

Una domanda: "Vuoi cambiare qualcosa per la settimana che viene?"

Review Parcheggio: "Hai X idee in attesa. Le guardi?"
Per ciascuna: [Sviluppa questa settimana] [Rimanda] [Elimina]
```

---

## Elementi tecnici e di UX da tenere presenti

| Elemento | Perché funziona | Come applicarlo |
|---|---|---|
| **Pulsanti inline** | Zero attrito, specie la sera | Usarli per risposte sì/no e scelte semplici nel check-in |
| **Una domanda alla volta** | Riduce il senso di peso | Mai mandare un elenco. Sempre una sola |
| **Streak** | Crea attaccamento positivo alla continuità | Contare i giorni consecutivi di lavoro strategico |
| **Conferma immediata** | Riduce l'ansia da "ho perso l'idea" | Ogni parcheggio → risposta breve di conferma |
| **Pattern recognition** | Trasforma il bot in specchio | Da implementare dopo 4+ settimane di dati |
| **Frase di ancoraggio** | Riporta allo scopo originale | Nei momenti di bassa motivazione, ricordare perché si è iniziato |
| **Continuità tra sessioni** | Fa sentire l'utente ascoltato | Il bot riprende esplicitamente quello che ha detto ieri/la settimana scorsa |
| **Normalizzazione senza compiacenza** | Non giudica, non elargisce lodi vuote | "Settimane operative capitano. Il problema è quando è sempre così." |
| **Domanda che ribalta la prospettiva** | Sblocca l'auto-sabotaggio senza dare consigli | "Cosa diresti a un'altra imprenditrice nella tua stessa situazione?" |
| **Cattura, poi valuta** | Evita decisioni nel momento di carica emotiva | Le idee si salvano subito, si valutano nel momento dedicato |

---

*Questo documento è la base di ricerca per le specifiche definitive di La Rotta. Aggiornare man mano che emergono nuovi riferimenti o decisioni di design.*
