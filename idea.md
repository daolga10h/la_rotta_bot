# La rotta

## Idea generale
La rotta è un assistente AI pensato per l'imprenditrice che ha molte idee, poco tempo e il rischio di perdersi tra attività secondarie. Il suo ruolo non è solo ricordare cose da fare, ma aiutare a restare fedele ai propri obiettivi principali, evitando dispersioni e mantenendo una direzione chiara.

Il nome richiama il senso del progetto: dare una rotta precisa, correggere la traiettoria quando serve e riportare sulla strada giusta — anche quando manca la voglia o ci sono dubbi.

---

## Scope
**MVP:** strumento personale per uso proprio. Una sola utente, architettura semplice.
**Futuro:** possibile integrazione con il sistema "Oltre la Bottega" per essere offerto ad altri imprenditori simili.

---

## 1. COSA FA
La rotta:
- aiuta a scegliere uno o due obiettivi prioritari per ogni periodo;
- distingue il lavoro **operativo** (mandare avanti il negozio ogni giorno) dal lavoro **strategico** (avvicinarsi agli obiettivi grandi);
- intercetta quando l'operativo sta divorando lo strategico;
- crea un "Parcheggio delle opportunità" dove mettere da parte idee e proposte non urgenti, senza perderle e senza inseguirle subito;
- monitora se ci si sta allontanando dalla direzione scelta;
- fa un check-in la mattina ogni giorno alle 7:30 con una sola domanda;
- risponde attivamente quando c'è mancanza di voglia o dubbi — non si limita a registrare la risposta, entra nella conversazione e aiuta a sbloccarsi.

Il bot non è un semplice promemoria: è un coach operativo che risponde a come stai, non solo a cosa hai fatto.

---

## 2. PER CHI È (PERSONA SPECIFICA)
**Utente primaria:** imprenditrice con bottega artigianale fisica. Gestisce il negozio da sola o con marito, con ordini che arrivano da canali diversi (WhatsApp, email, telefono, di persona). Ha obiettivi grandi che rischiano di restare sempre in secondo piano perché l'operativo assorbe tutto.

**Il problema specifico:** non è che non sa cosa fare. Sa benissimo cosa vorrebbe fare. Il problema è che alla fine della giornata ha lavorato molto ma sulle cose urgenti e quotidiane, non su quelle importanti e strategiche. Si "svurgola" — si nasconde dietro le piccole cose operative — e procrastina sulle grandi.

**Obiettivi attuali (gerarchia):**
1. Portare il negozio a livello premium e prepararlo alla vendita *(priorità assoluta)*
2. Lavorare su "Oltre la Bottega" in parallelo — almeno 6 ore a settimana *(priorità alta)*
3. Comprare casa a Marta, avere più tempo libero per sé *(obiettivi di fondo)*

**Caratteristica chiave:** le vengono continuamente nuove idee. Non sa se possano aiutarla a raggiungere gli obbiettivi principali, non vuole perderle, ma sa che inseguirle subito la porta fuori rotta.

---

## 3. DA DOVE PRENDE LE INFORMAZIONI
L'assistente si basa su:
- obiettivi dichiarati dall'utente durante l'onboarding;
- aggiornamenti quotidiani tramite il check-in la mattina dopo;
- messaggi spontanei inviati durante il giorno (nuove idee, blocchi, aggiornamenti);
- risposte alle domande del bot.

Le informazioni devono essere semplici da dare. L'utente è spesso in negozio, con i clienti. Non può fermarsi a compilare form o rispondere a domande lunghe. **Una domanda alla volta, sempre.**

---

## 4. DOVE OPERA
Telegram. Canale principale scelto per velocità e immediatezza — già usato, nessuna app nuova da installare.

Il bot invia:
- check-in serale alle 21.30 (una domanda);
- promemoria per proteggere le ore dedicate a "Oltre la Bottega";
- richiami quando gli obiettivi strategici non vengono toccati per troppo tempo;
- valutazione rapida ma approfondita se l'idea possa aiutare a raggiungere gli obbiettivi o meno;
- conferma rapida quando un'idea viene parcheggiata.

---

## 5. COSA RESTITUISCE ALL'UTENTE
- chiarezza su quale obiettivo strategico lavorare oggi;
- distinzione netta tra lavoro operativo e lavoro strategico;
- un posto sicuro dove mettere le idee senza perderle e senza inseguirle;
- risposta attiva quando non c'è voglia o ci sono dubbi — non giudizio, ma sblocco;
- traccia di quante volte a settimana si è lavorato sugli obiettivi grandi;
- protezione attiva delle 6 ore settimanali per "Oltre la Bottega".

---

## 6. ARCHITETTURA MVP

### 6.1 Canale principale
Telegram — interfaccia principale e unica per l'MVP.

### 6.2 Motore di conversazione
Layer AI che interpreta i messaggi dell'utente, capisce il contesto (sta aggiornando? sta parcheggiando un'idea? sta chiedendo aiuto?) e risponde in modo coerente con gli obiettivi memorizzati.

### 6.3 Logica di priorità
Integrata nel motore di conversazione, non come modulo separato. Distingue tra:
- lavoro operativo (necessario ma non strategico);
- lavoro strategico (avvicina agli obiettivi grandi);
- idee nuove (da valutare o da parcheggiare);
- blocchi e dubbi (da gestire attivamente).

### 6.4 Memoria del contesto
Storage strutturato con due livelli:
- **Profilo stabile:** obiettivi, gerarchia, preferenze, ore target per Oltre la Bottega
- **Storia compressa:** riassunto periodico degli aggiornamenti, non log raw di ogni messaggio

Quando gli obiettivi cambiano, si crea una nuova versione — non si sovrascrive la storia.

### 6.5 Reminder e scheduler
- Check-in serale fisso alle 21:30
- Alert settimanale se le 6 ore per "Oltre la Bottega" non sono state fatte
- Nessun reminder invasivo durante il giorno a meno che non sia richiesto

### 6.6 Logging interno
Ogni interazione viene loggata per permettere al team di capire cosa funziona. Non è una feature per l'utente — è infrastruttura interna di sviluppo.

---

## 7. STRUTTURA DEL PRODOTTO

### 7.1 Onboarding
- chi sei e cosa fai;
- quali sono i tuoi 2-3 obiettivi principali adesso;
- qual è la gerarchia tra di loro;
- quante ore a settimana vuoi dedicare a ciascuno;
- a che ora vuoi il check-in.

Breve, conversazionale. Il bot fa una domanda alla volta.

### 7.2 Piano quotidiano (mattina — opzionale)
Il bot può inviare un breve messaggio mattutino con la priorità strategica del giorno alle 7.30. Non obbligatorio nell'MVP — da valutare dopo i primi giorni di utilizzo.

### 7.3 Parcheggio delle opportunità
Quando arriva un'idea nuova, l'utente la manda al bot. Il bot la salva, conferma con un messaggio breve. Fa una valutazione se l'idea è utile al raggiungimento degli obbiettivi. Se non è utile non ne parla più fino alla revisione settimanale. L'idea non si perde, ma non distrae. Se si avvia una conversazione per capire come può essere sfruttata.

Regole del parcheggio:
- massimo 10 idee contemporaneamente;
- ogni settimana il bot propone di rivedere il parcheggio (promuovere, eliminare, tenere);
- le idee più vecchie di 30 giorni vengono segnalate per eliminazione.

### 7.4 Check-in serale alle 21.30 — tre scenari

**Scenario A — "Sì, ho lavorato su X"**
Il bot registra, fa un breve riconoscimento, chiude. Niente domande aggiuntive a meno che l'utente non voglia aggiungere qualcosa.

**Scenario B — "No, non ho avuto tempo / è successo altro"**
Il bot non giudica. Chiede: cosa potrebbe bloccare anche domani? Propone un'azione minima concreta per il giorno dopo.

**Scenario C — "Non ho voglia / ho dubbi"**
Qui il bot apre uno spazio. Non registra e passa oltre. Chiede cosa sta generando il dubbio o la mancanza di voglia — è su un aspetto specifico o è stanchezza generale? Poi risponde in modo concreto: una domanda utile, un'azione minima da 20 minuti, oppure il permesso di fermarsi senza senso di colpa se serve.

### 7.5 Revisione settimanale
Una volta a settimana (giorno e ora da definire durante l'onboarding) il bot invia un breve riepilogo:
- quante volte è stato fatto lavoro strategico;
- stato delle ore per "Oltre la Bottega";
- idee nel parcheggio da rivedere.

Non è un report complesso. Sono tre righe e una domanda: vuoi cambiare qualcosa per la settimana che viene?

---

## 8. DECISIONI GIÀ PRESE

| Decisione | Risposta |
|---|---|
| A chi serve | A me per prima — uso personale nell'MVP |
| Problema principale | Operativo che divora lo strategico + procrastinazione + mancanza di voglia/dubbi |
| Coach o tool | Entrambi: tool per il tracciamento, coach per i momenti di blocco |
| Tipo di memoria | Ibrida: profilo strutturato + riassunti compressi della storia |
| Canale | Telegram |
| Check-in | Ogni sera alle 21:30, una domanda sola |
| Integrazioni MVP | Nessuna integrazione esterna — solo Telegram |
| MVP vs feature future | MVP: onboarding + check-in serale + parcheggio idee + protezione ore Oltre la Bottega |

---

## 9. COSA NON ENTRA NELL'MVP
- Fallback umano: rimandato — zero casi d'uso concreti per ora
- Analytics per l'utente: è infrastruttura interna, non feature
- Integrazioni con agenda, task manager, CRM: tutte rimandato a versioni successive
- Multi-utente: rimandato a dopo la validazione personale

---

## Versione sintetica del concept
La rotta è un assistente AI su Telegram che aiuta l'imprenditrice a non perdere di vista gli obiettivi strategici grandi mentre gestisce il caos operativo quotidiano. Fa un check-in ogni sera alle 21.30, risponde ai momenti di dubbio e mancanza di voglia, protegge il tempo per i progetti importanti e parcheggia le idee nuove senza farle perdere e senza inseguirle subito.
