# Guida Operativa Partecipanti — Workshop Gemini Enterprise per Lepida ScpA e i Comuni dell'Emilia-Romagna

> **Benvenuti!** In questo laboratorio pratico utilizzerete **Google Cloud Gemini Enterprise** per costruire un **Chat Agent No-Code** alimentato dal modello **`Gemini 3.8 Flash`** e dotarlo di **Skills operative** capaci di interrogare i documenti ufficiali di **Lepida ScpA** e dei **Comuni dell'Emilia-Romagna** (Catalogo Servizi e Listino 2026, Bandi Regionali PR FESR, Piani Cybersecurity NIS2, Regolamenti TARI, Piani Smart City IoT e Modelli di Determina Dirigenziale In-House).

---

## PASSO PRELIMINARE (Automatico, 30 Secondi) — Scarica ed Esegui la Preparazione dell'Ambiente

Tutta l'infrastruttura tecnica del tuo laboratorio personale (il tuo **Bucket Cloud Storage univoco**, i **10 documenti pubblici della PA**, il **Connettore di ricerca indicizzato** e l'**App Gemini Enterprise** già pronta) viene creata **in automatico con un solo comando**.

1. Nella barra blu in alto a destra della Console Google Cloud, clicca sull'icona **`>_`** (**Activate Cloud Shell**).
2. Se compare una finestra di conferma nella parte bassa dello schermo, clicca sul pulsante blu **Continue** (Continua) o **Authorize** (Autorizza).
3. Copia il comando seguente, incollalo nel terminale nero in basso (`Ctrl+V` oppure `Cmd+V` su Mac) e premi **INVIO**:

```bash
git clone https://github.com/marangonic/lepida-gemini-enterprise-workshop.git ~/lepida_workshop && ~/lepida_workshop/setup.sh
```

> [!TIP]
> **Cosa fa questo comando in ~30 secondi?**
> - Crea il tuo **Bucket Cloud Storage univoco** (`gs://<TUO_PROJECT_ID>-lepida-comuni-er`) e carica i **10 documenti ufficiali** di Lepida e dei Comuni dell'Emilia-Romagna.
> - Crea e indicizza istantaneamente il Connettore **`Corpus Documentale Lepida e Comuni Emilia-Romagna 2026`** (`lepida-comuni-er-ds`).
> - Crea la tua App Gemini Enterprise (**`Lepida & Comuni ER Assistant`**) abilitando automaticamente il costruttore **Chat Agent** e le **Skills**.
> - Al termine stampa a schermo il **link diretto cliccabile (`1️⃣ CLICCA QUI PER APRIRE DIRETTAMENTE LA WEB APP DI GEMINI ENTERPRISE`)**.

4. **Clicca sul link `https://vertexaisearch.cloud.google.com/home/cid/...`** stampato alla fine dello script (se appare il messaggio di benvenuto *"Welcome to Gemini Enterprise!"*, clicca su **Get started**). Sei subito pronto per il **Modulo 2**!

---

## MODULO 2 — Creare il Proprio Chat Agent No-Code in Gemini Enterprise (30 min)

In questo modulo costruiamo direttamente dentro la Web App di **Gemini Enterprise** un **Agente Conversazionale Specializzato** (*Chat Agent*) dedicato ai RUP e agli operatori dei Comuni dell'Emilia-Romagna, utilizzando il modello **`Gemini 3.8 Flash`**.

### 2.1 Creazione Guidata del Chat Agent
1. All'interno della **Web App di Gemini Enterprise**, guarda il menu laterale a sinistra e clicca su **Agents** (oppure direttamente su **+ New agent** nella barra laterale).
2. Clicca sul pulsante blu in alto a destra **+ New agent** e dal menu a tendina seleziona **Chat agent** (si aprirà la schermata *"Launch powerful chat agents with unmatched speed and simplicity"*).
3. Clicca sul link blu **Build manually** accanto alla scritta *"Want to skip this step and build manually?"*.
4. Nell'editor del tuo Chat Agent, configura i campi principali nel pannello dei dettagli:

   - **Name (Nome dell'Agente):**
     ```text
     Consulente Digitale Comuni ER e Servizi Lepida
     ```
   - **Model (Modello LLM):**
     Seleziona **`Gemini 3.8 Flash`** (`gemini-3.8-flash`, segnalato anche dal banner in alto *"✦ NEW: Try Gemini 3.8 Flash"*).
   - **Description (Descrizione breve):**
     ```text
     Assistente ufficiale per i RUP e i referenti dei Comuni dell'Emilia-Romagna: supporta l'analisi dei Bandi Lepida 2026, il calcolo dei cofinanziamenti, la redazione di Determine In-House e il confronto tra progetti comunali.
     ```
   - **Knowledge / Data Stores (Fonti di conoscenza / Connettori):**
     Assicurati che sia selezionato e collegato il connettore **`Corpus Documentale Lepida e Comuni Emilia-Romagna 2026`** (`lepida-comuni-er-ds`).

---

### 2.2 Strutturare il Chat Agent su Più Livelli di Sub-Agents (Canvas `Flow`)
Nella scheda **`Flow`** al centro dello schermo puoi progettare un'architettura **Multi-Agent a più livelli** (impostando sempre il modello **`Gemini 3.8 Flash`** su ciascun nodo):

1. Passando il mouse sul nodo principale blu (**`Consulente Digitale Comuni ER e Servizi Lepida`**), clicca sull'icona **`+`** in basso per aggiungere dei **Sub-Agents specializzati** (Card Viola) dedicati ai diversi ambiti amministrativi e tecnici:
   - **Sub-Agent 1 — `Specialista Bandi e Cloud Lepida`**:
     - *Model:* **`Gemini 3.8 Flash`**
     - *Description:* `Analizza i Bandi Regionali 2026, le premialità col tetto del 95%, i canoni del Catalogo Lepida e i requisiti Cloud ACN / NIS2.`
     - *Data Store:* `Corpus Documentale Lepida e Comuni Emilia-Romagna 2026`
   - **Sub-Agent 2 — `Specialista Atti PA e Benchmark Comuni`**:
     - *Model:* **`Gemini 3.8 Flash`**
     - *Description:* `Redige bozze di Determine Dirigenziali In-House in 6 sezioni e confronta i progetti e regolamenti dei Comuni dell'Emilia-Romagna.`
     - *Data Store:* `Corpus Documentale Lepida e Comuni Emilia-Romagna 2026`
2. Puoi anche usare la chat assistita a sinistra del canvas (*"Ask to make changes"*) scrivendo direttamente in italiano:
   ```text
   Aggiungi due sub-agenti con modello Gemini 3.8 Flash collegati al Data Store: il primo chiamato "Specialista Bandi e Cloud Lepida" per calcolare i punteggi e i contributi dei bandi, e il secondo chiamato "Specialista Atti PA e Benchmark Comuni" per redigere le Determine Dirigenziali e confrontare i Comuni dell'Emilia-Romagna.
   ```

---

### 2.3 Test Rapido del Chat Agent (Verifica del Grounding sul Connettore Cloud Storage)
Prima di passare alle Skills del Modulo 3, clicca su **Update** (o **Create**) in alto a destra, apri la scheda **Preview** e fai subito una prima domanda al tuo Chat Agent per verificare che interroghi correttamente i documenti del tuo Data Store Cloud Storage:

```text
Quali sono i 4 Bandi Regionali 2026 gestiti con il supporto di Lepida, quali sono le rispettive percentuali di contributo a fondo perduto, qual è il punteggio minimo per l'approvazione e come funzionano le premialità aggiuntive?
```

**Risultato atteso (estratto automaticamente dal `Doc 02` — Linee Guida Bandi 2026):**
- **`BANDO-ER-2026-01`** (*Scuole e Municipi 10 Gbps*): fondo perduto base **`85%`** (dotazione `4.500.000 €`).
- **`BANDO-ER-2026-02`** (*AI Generativa & Sportelli Digitali Comuni*): fondo perduto base **`80%`** (dotazione `3.200.000 €`).
- **`BANDO-ER-2026-03`** (*Cybersecurity NIS2 & SOC Territoriale*): fondo perduto base **`90%`** (dotazione `2.800.000 €`).
- **`BANDO-ER-2026-04`** (*Smart City, Sensoristica IoT & Gemello Digitale*): fondo perduto base **`75%`** (dotazione `5.000.000 €`).
- **Soglie punteggio tecnico:** **`>= 70/100`** Approvata | **`60–69/100`** Integrazione richiesta entro 15 gg | **`< 60/100`** Non ammessa.
- **Premialità cumulative:** **`+5%`** Comune Montano/Area Interna, **`+5%`** Unione di Comuni ($\ge 3$ Comuni), **`+5%`** Comune $< 15.000$ abitanti, con **tetto massimo inderogabile del `95%`**.

---

## MODULO 3 — Creare e Utilizzare le "Skills" in Gemini Enterprise (45 min)

Una **Skill** all'interno di **Gemini Enterprise** è una competenza operativa strutturata e riutilizzabile che insegna all'agente **come eseguire un processo amministrativo o tecnico complesso** (quali documenti del Data Store incrociare, quali regole matematiche o normative applicare e quale formato di output restituire).

In Gemini Enterprise puoi definire e utilizzare le **Skills** in **due modalità complementari**:

---

### 3.1 Parte A — Creare una Skill Modulare nella Sezione `Skills` della Web App
1. Nel menu laterale sinistro della Web App di Gemini Enterprise, clicca sulla voce **`Skills`**.
2. Clicca sul pulsante **`+`** in alto nella colonna `Skills` per creare una nuova Skill riutilizzabile a livello di organizzazione.
   > [!IMPORTANT]
   > Il nome della Skill (*Display Name*) può contenere lettere maiuscole/minuscole, numeri, spazi e trattini (massimo 64 caratteri), ma **non deve contenere caratteri speciali come `&`**.

3. Crea le seguenti **3 Skills ufficiali del Workshop** (oppure verifica quelle già presenti e condividile cliccando su **Share**):

   - **Skill 1 — `Simulazione Punteggio Bando Fibra 10 Gbps`**
     - *Description:* `Calcola l'ammissibilità (>=70 pt), le premialità cumulative (tetto 95%) e le 3 tranche di erogazione sui Bandi Lepida 2026.`
     - *Instruction (`SKILL.md`):*
       ```text
       Quando l'utente chiede di valutare un progetto per un Bando Lepida 2026 o calcolare il contributo:
       1. Consulta il "Catalogo Servizi e Listino Lepida 2026" (Doc 01) e le "Linee Guida Bandi 2026" (Doc 02).
       2. Verifica se il punteggio tecnico stimato è >= 70/100 (APPROVATA), tra 60 e 69 (INTEGRAZIONE_RICHIESTA entro 15 gg) o < 60 (NON AMMESSA).
       3. Partendo dalla quota base del bando (80% AI/Cloud, 85% Fibra, 90% NIS2, 75% IoT), somma le premialità cumulative (+5% Comune Montano/Area Interna, +5% Unione >= 3 Comuni, +5% Comune < 15.000 abitanti) applicando SEMPRE il tetto massimo inderogabile del 95% a fondo perduto.
       4. Presenta una tabella con Valore Progetto, Aliquota Applicata (%), Contributo Regionale a Fondo Perduto (€), Quota a Carico dell'Ente (€) e le 3 Tranche (40% Anticipo, 30% SAL, 30% Saldo).
       ```

   - **Skill 2 — `Generatore Bozza Determina Dirigenziale PA`**
     - *Description:* `Redige una bozza strutturata di Determina Dirigenziale di affidamento in-house a Lepida ScpA nelle 6 sezioni ufficiali.`
     - *Instruction (`SKILL.md`):*
       ```text
       Quando l'utente chiede di generare una bozza di Determina Dirigenziale per un Ente:
       Utilizza obbligatoriamente tutte le 6 SEZIONI del Modello Ufficiale "MOD-DET-INHOUSE-LEPIDA-2026" (Doc 08):
       - SEZIONE 1: Intestazione dell'Ente, Settore e individuazione del RUP (art. 15 D.Lgs. 36/2023)
       - SEZIONE 2: Premesse di Fatto e di Diritto (L.R. 11/2004, controllo analogo congiunto su Lepida ScpA)
       - SEZIONE 3: Motivazione di Congruità Economica (art. 7 comma 2 D.Lgs. 36/2023, canone annuo e SLA dal Catalogo Doc 01 e risparmio >22% vs Consip/MEPA)
       - SEZIONE 4: Quadro Economico e Piano Finanziario nelle 3 tranche (40% / 30% / 30%)
       - SEZIONE 5: Clausole Obbligatorie di Conformità ACN, NIS2, GDPR e AI Act UE 2024/1689 (Doc 10: Human-in-the-Loop del RUP, trasparenza art. 50, Model Armor/DLP e log per 24 mesi in Region UE)
       - SEZIONE 6: Dispositivo della Determina (esenzione CIG ordinario per in-house e tracciabilità tramite CUP).
       ```

   - **Skill 3 — `Checklist Migrazione Cloud e Sicurezza ACN`**
     - *Description:* `Genera il piano operativo di migrazione al Datacenter Lepida, adeguamento SOC/CSIRT NIS2 e benchmark progetti Comuni ER.`
     - *Instruction (`SKILL.md`):*
       ```text
       Quando l'utente chiede un piano di migrazione Cloud ACN/NIS2 o un confronto tra i Comuni dell'Emilia-Romagna:
       1. Riporta i canoni e gli SLA dei 4 Data Center Regionali certificati ACN (Bologna, Ferrara, Modena, Parma), i tempi di notifica CSIRT NIS2 (Early Warning 24h, Notifica 72h, Relazione 30 gg) e la presa in carico SOC Lepida entro 15 minuti.
       2. Costruisci una Tabella Comparativa tra i Comuni ER (Bologna, Modena, Ravenna, Rimini, Ferrara, Parma, Unione Appennino Bolognese) con Ente, Codice Pratica, Bando, Importo (€), Punteggio, Stato e azioni correttive (es. Allegato Tecnico B2 entro 15 gg per Ferrara).
       ```

---

### 3.2 Parte B — Inserire le 3 Skills nel campo `Instructions` del tuo Chat Agent
1. Torna in **Agents**, apri il tuo Chat Agent **`Consulente Digitale Comuni ER e Servizi Lepida`** e nel campo **Instructions (Istruzioni)** copia e incolla integralmente il blocco seguente:

```text
Rispondi sempre in italiano con tono istituzionale, chiaro e strutturato, citando sempre i documenti ufficiali presenti nel Data Store Cloud Storage.
Disponi di 3 SKILLS OPERATIVE specializzate che devi eseguire rigorosamente quando richiesto dall'utente:

=== [SKILL 1: VALUTAZIONE E SIMULAZIONE BANDO COMUNALE] ===
Quando l'utente chiede di valutare un progetto per un Bando Lepida 2026 o calcolare il contributo:
1. Consulta il "Catalogo Servizi e Listino Lepida 2026" (Doc 01) e le "Linee Guida Bandi 2026" (Doc 02).
2. Verifica se il punteggio tecnico stimato è >= 70/100 (APPROVATA), tra 60 e 69 (INTEGRAZIONE_RICHIESTA entro 15 gg) o < 60 (NON AMMESSA).
3. Partendo dalla quota base del bando (80% AI/Cloud, 85% Fibra, 90% NIS2, 75% IoT), somma le premialità cumulative:
   - +5% se Comune Montano / Area Interna
   - +5% se Unione di Comuni (almeno 3 Comuni)
   - +5% se Comune sotto i 15.000 abitanti
   applicando SEMPRE il tetto massimo inderogabile del 95% a fondo perduto.
4. Presenta una tabella con: Valore Progetto, Aliquota Applicata (%), Contributo Regionale a Fondo Perduto (€), Quota a Carico dell'Ente (€) e il dettaglio delle 3 Tranche di erogazione:
   - 1ª Tranche Anticipo (40% del contributo regionale, entro 30 gg da determina e CUP)
   - 2ª Tranche SAL Intermedio (30% del contributo regionale, al 50% attività)
   - 3ª Tranche Saldo Finale (30% del contributo regionale, a collaudo e rendicontazione).

=== [SKILL 2: REDAZIONE DETERMINA DIRIGENZIALE IN-HOUSE LEPIDA] ===
Quando l'utente chiede di generare una bozza di Determina Dirigenziale per un Ente:
1. Utilizza obbligatoriamente tutte le 6 SEZIONI del Modello Ufficiale "MOD-DET-INHOUSE-LEPIDA-2026" (Doc 08):
   - SEZIONE 1: Intestazione dell'Ente, Settore e individuazione del RUP (art. 15 D.Lgs. 36/2023)
   - SEZIONE 2: Premesse di Fatto e di Diritto (L.R. 11/2004, controllo analogo congiunto su Lepida ScpA)
   - SEZIONE 3: Motivazione di Congruità Economica (art. 7 comma 2 D.Lgs. 36/2023), riportando il canone annuo esatto e lo SLA del servizio dal Catalogo CAT-LEPIDA-2026-V1 (Doc 01) e il risparmio >22% rispetto a Consip/MEPA
   - SEZIONE 4: Quadro Economico e Piano Finanziario nelle 3 tranche (40% / 30% / 30%)
   - SEZIONE 5: Clausole Obbligatorie di Conformità ACN, NIS2, GDPR e AI Act UE 2024/1689 (Doc 10: sorveglianza umana Human-in-the-Loop del RUP, trasparenza art. 50, Model Armor/DLP e conservazione log per 24 mesi in Region UE)
   - SEZIONE 6: Dispositivo della Determina (esenzione CIG ordinario per affidamento in-house e tracciabilità tramite CUP).

=== [SKILL 3: BENCHMARK PROGETTI COMUNI ER] ===
Quando l'utente chiede un confronto tra le esperienze dei Comuni dell'Emilia-Romagna:
1. Analizza i documenti comunali presenti nel Data Store (Doc 03 Bologna, Doc 04 Modena, Doc 05 Ravenna e Rimini, Doc 06 Ferrara e Parma, Doc 07 Unioni Montane).
2. Costruisci una Tabella Comparativa con: Ente, Codice Pratica, Bando, Importo (€), Punteggio Tecnico, Stato Pratica e Risultati/SLA ottenuti.
3. Evidenzia eventuali criticità istruttorie (es. Allegato Tecnico B2 entro 15 gg per sbloccare pratiche NIS2 in stato INTEGRAZIONE_RICHIESTA) e suggerisci come riusare il progetto.
```

2. Clicca sul pulsante blu **Update** (o **Create**) in alto a destra per pubblicare il tuo Chat Agent!

---

### 3.3 Parte C — Esecuzione e Verifica dei 3 Test Pratici nel Chat Agent

Passa alla scheda **Preview** (oppure apri il tuo agente **`Consulente Digitale Comuni ER e Servizi Lepida`** dalla galleria **Agents**) ed esegui i 3 test seguenti:

#### Test 1 — Esecuzione della `SKILL 1` (Istruttoria Bando, Tetto 95% e 3 Tranche)
Incolla nella chat dell'agente:
```text
Esegui la [SKILL 1: VALUTAZIONE E SIMULAZIONE BANDO COMUNALE]: L'Unione dei Comuni dell'Appennino Bolognese (11 Comuni montani, sotto i 15.000 abitanti) presenta un progetto da 140.000 EUR sul Bando Fibra 10 Gbps (BANDO-ER-2026-01, quota base 85%) con punteggio tecnico 88/100. Verifica se supera la soglia minima dei 70 punti, indica le premialità applicando il tetto massimo del 95%, calcola il contributo regionale a fondo perduto, la quota residua a carico dell'Unione e gli importi delle 3 tranche (40% anticipo, 30% SAL, 30% saldo).
```
**Risultato atteso:**
- Pratica **AMMISSIBILE E APPROVATA** (`88/100 >= 70/100`).
- Somma teorica `85% + 5% (Montano) + 5% (Unione) + 5% (<15k ab.) = 100%` $\rightarrow$ applicato il **tetto massimo del 95%**.
- **Contributo a fondo perduto:** **133.000,00 EUR (95%)** | **Quota a carico dell'Unione:** **7.000,00 EUR (5%)** (~636,36 € a Comune).
- **3 Tranche:** Anticipo 40% = **53.200,00 €**, SAL 30% = **39.900,00 €**, Saldo 30% = **39.900,00 €**.

---

#### Test 2 — Esecuzione della `SKILL 2` (Redazione Bozza Determina Dirigenziale In-House in 6 Sezioni)
Incolla nella chat dell'agente:
```text
Esegui la [SKILL 2: REDAZIONE DETERMINA DIRIGENZIALE IN-HOUSE LEPIDA]: Redigi nelle 6 sezioni obbligatorie del modello MOD-DET-INHOUSE-LEPIDA-2026 la Determina Dirigenziale per il Comune di Rimini (RUP: Ing. Marco Verdi) per l'adesione al Bando BANDO-ER-2026-02 (importo progetto 110.000 EUR, quota base 80%) e l'affidamento in-house a Lepida ScpA del servizio SRV-AI-SPORTELLO.
```
**Risultato atteso:**
- Bozza completa di Determina Dirigenziale strutturata nelle **6 sezioni ufficiali**, con il canone esatto di **`5.400 EUR/anno`** e SLA **`99,90%`** estratti dal Catalogo Lepida (`Doc 01`), il quadro economico (**`88.000 EUR`** fondo perduto in 3 tranche da `35.200 € / 26.400 € / 26.400 €` + **`22.000 EUR`** quota Comune) e le clausole obbligatorie **AI Act** (*Human-in-the-Loop* del RUP e conservazione log per **24 mesi** dal `Doc 10`).

---

#### Test 3 — Esecuzione della `SKILL 3` (Benchmark Comparativo tra i Comuni dell'Emilia-Romagna)
Incolla nella chat dell'agente:
```text
Esegui la [SKILL 3: BENCHMARK PROGETTI COMUNI ER]: Costruisci una tabella comparativa con Ente, Codice Pratica, Bando, Importo, Punteggio, Stato e Risultati/SLA per i Comuni di Bologna, Modena, Ravenna, Rimini, Ferrara, Parma e Unione Appennino Bolognese, e indica quale documento ed entro quanti giorni il Comune di Ferrara deve inviare per sbloccare la pratica PRAT-2026-106.
```
**Risultato atteso:**
- Tabella comparativa completa dei 7 Enti e indicazione precisa che il **Comune di Ferrara (`PRAT-2026-106`, punteggio 64/100)** deve trasmettere entro **15 giorni solari** l'**Allegato Tecnico B2** con l'inventario degli asset critici NIS2 e il piano di federazione SIEM col SOC Lepida.

---

> [!NOTE]
> **Hai bisogno di caricare subito la Soluzione Completa già pronta?**
> Se in qualsiasi momento vuoi generare automaticamente il Chat Agent Multi-Livello completo (con modello `Gemini 3.8 Flash` e i 4 Sub-Agents) e le 3 Skills nella tua Web App, ti basta incollare in Cloud Shell:
> ```bash
> ~/lepida_workshop/setup.sh --solution
> ```
