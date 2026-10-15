# Playbook Docente & Regia Tecnica — Workshop Lepida ScpA & Comuni dell'Emilia-Romagna (Moduli 2 & 3)

> **Obiettivo del Workshop per i 27 Utenti (26 Partecipanti + 1 Docente):** far svolgere ai partecipanti **esclusivamente i due laboratori ad alto valore aggiunto** dentro la Web App di **Gemini Enterprise** (**Modulo 2 — Creare il Proprio Chat Agent No-Code con `Gemini 3.8 Flash`** e **Modulo 3 — Creare e Utilizzare le "Skills"**), mentre tutta la preparazione infrastrutturale (**Bucket GCS garantito univoco per ciascuno dei 27 utenti/ambienti**, 10 documenti della PA, Connettore GCS indicizzato in 2 secondi, attivazione licenza Free Trial, creazione dell'App Gemini Enterprise e sblocco delle feature `Chat agent` e `Skills`) avviene in **~60 secondi** scaricando ed eseguendo un singolo comando dal repository GitHub.

---

## 1. Repository GitHub Ufficiale, Univocità dei 27 Bucket GCS e Comandi Rapidi

Tutti gli script e i dataset sono pubblicati e pronti da scaricare dal repository GitHub:
- **Repository:** `https://github.com/marangonic/lepida-gemini-enterprise-workshop`

### Come è garantita l'univocità dei 27 Bucket GCS e dei 27 Connettori (Zero Valori Statici)
In Google Cloud Storage i nomi dei bucket sono **univoci a livello globale mondiale**. Se i 27 utenti provassero a creare un bucket con un nome fisso (es. `gs://lepida-comuni-er`), solo il primo utente ci riuscirebbe e gli altri 26 riceverebbero `409 Conflict: Bucket already exists`.
Per questo motivo gli script (`setup.sh`, `setup_workshop_data.py` e `setup_ge_datastore.py`) **non contengono alcun nome di bucket statico**:
1. All'avvio, lo script rileva dinamicamente il **`PROJECT_ID` univoco del singolo laboratorio Qwiklabs** (`gcloud config get-value project`, es. `qwiklabs-gcp-02-e71aeab0dc46`).
2. Costruisce dinamicamente il nome del bucket come:
   ```text
   gs://${PROJECT_ID}-lepida-comuni-er
   ```
3. Poiché Qwiklabs assegna a ciascuno dei **27 utenti** un progetto isolato con un suffisso esadecimale univoco di 12 caratteri:
   - **Utente #1:** crea `gs://qwiklabs-gcp-00-436de4629ca8-lepida-comuni-er` → collegato al suo connettore `lepida-comuni-er-ds`
   - **Utente #2:** crea `gs://qwiklabs-gcp-02-e71aeab0dc46-lepida-comuni-er` → collegato al suo connettore `lepida-comuni-er-ds`
   - **...**
   - **Utente #27:** crea `gs://qwiklabs-gcp-04-9f8e7d6c5b4a-lepida-comuni-er` → collegato al suo connettore `lepida-comuni-er-ds`
4. Subito dopo, `setup_ge_datastore.py` legge la stessa variabile `BUCKET_NAME = f"{PROJECT_ID}-lepida-comuni-er"` e configura automaticamente il connettore `lepida-comuni-er-ds` puntando a `gs://${PROJECT_ID}-lepida-comuni-er/documenti_pa/*.html`. *(Inoltre, se mai due utenti dovessero operare dentro lo stesso progetto GCP, basta esportare `export LEPIDA_BUCKET_NAME="${PROJECT_ID}-lepida-utente-01"` e sia il bucket sia il connettore useranno quel nome).*

### A. Comando Unico per i Partecipanti (~60 secondi)
Ogni partecipante apre **Cloud Shell** (`>_`) nel proprio ambiente Qwiklabs e incolla:
```bash
git clone https://github.com/marangonic/lepida-gemini-enterprise-workshop.git ~/lepida_workshop && ~/lepida_workshop/setup.sh
```
**Cosa esegue automaticamente in ~60 secondi (`setup.sh`):**
1. Abilita le API (`discoveryengine.googleapis.com`, `storage.googleapis.com`, `aiplatform.googleapis.com`, `bigquery.googleapis.com`, `logging.googleapis.com`).
2. Crea il **Bucket Cloud Storage univoco per quel singolo utente** `gs://<PROJECT_ID>-lepida-comuni-er` e carica i **10 documenti HTML pubblici** di Lepida e dei Comuni dell'Emilia-Romagna (`setup_workshop_data.py`).
3. Attiva via API la licenza a 30 giorni **`free_trial_gemini`** (`enableLicenseAutoRegister: true` su `default_user_store`) e configura **Google Identity** (`IDP_TYPE_GSUITE` su `locations/global/aclConfig`).
4. Crea il Data Store **`lepida-comuni-er-ds`** (*"Corpus Documentale Lepida e Comuni Emilia-Romagna 2026"*) collegato al bucket univoco `gs://<PROJECT_ID>-lepida-comuni-er/documenti_pa/*.html` e **indicizza in modo sincrono in 2 secondi** tutti i 10 documenti (`branches/0/documents` + job `gcsSource`).
5. Crea l'App Gemini Enterprise **`Lepida & Comuni ER Assistant`** (`lepida-comuni-er-app`) già collegata al Data Store `lepida-comuni-er-ds` e abilita subito i feature flag:
   - `no-code-agent-builder: FEATURE_STATE_ON` (sblocca `+ New agent -> Chat agent`)
   - `skills: FEATURE_STATE_ON`, `skill-sharing: FEATURE_STATE_ON`, `skill-sharing-without-admin-approval: FEATURE_STATE_ON` (sblocca la sezione `Skills` nel menu laterale)
   - `agent-sharing: FEATURE_STATE_ON`, `agent-sharing-without-admin-approval: FEATURE_STATE_ON`
6. Recupera il `configId` (`cid`) della Web App e stampa a schermo il **link diretto cliccabile (`https://vertexaisearch.cloud.google.com/home/cid/<CID>`)** così l'utente entra direttamente nella Web App senza dover configurare nulla nella Console GCP!

---

### B. Comando "Soluzione Pronta / Paracadute" (~10 secondi)
Se tu (o un partecipante rimasto indietro) vuoi pubblicare automaticamente nella Web App anche il **Chat Agent Multi-Livello completo (con `Gemini 3.8 Flash` e i 4 Sub-Agents)** e le **3 Skills**:
```bash
~/lepida_workshop/setup.sh --solution
```

### C. Comando Completo Postazione Docente #27 (con Demo ADK `cloud_search_agent` su `adk web`, Vertex AI Agent Engine, Telemetria & Agent Registry A2A)
Se sulla tua postazione docente (#27) vuoi mostrare anche l'Agente ADK Pro-Code **`cloud_search_agent`** (*"Cloud Search & Sizing ADK Agent"*) su `adk web`, deployarlo su **Agent Platform Deployment (Vertex AI Agent Engine)** con **Cloud Trace, Cloud Logging, OpenTelemetry e Playground** e registrarlo con **Agent Card A2A** in **Agent Registry** (vedi la guida completa in **[`README_DEMO_ADK_AGENT_PLATFORM.md`](./README_DEMO_ADK_AGENT_PLATFORM.md)**):
```bash
git clone https://github.com/marangonic/lepida-gemini-enterprise-workshop.git ~/lepida_workshop && ~/lepida_workshop/setup.sh --with-adk
```
E per lanciare `adk web` in Cloud Shell Web Preview (porta 8080):
```bash
cd ~/lepida_workshop
./setup_and_run_cloudshell.sh
```

---

## 2. Verifica Live Eseguita sul Laboratorio `qwiklabs-gcp-02-e71aeab0dc46`

L'intero flusso è stato appena eseguito e validato sul tuo ambiente Qwiklabs live:
- **Account:** `student-02-5178b3508fe9@qwiklabs.net`
- **Project ID:** `qwiklabs-gcp-02-e71aeab0dc46` (Project Number: `248119123873`)
- **Bucket Univoco Creato:** `gs://qwiklabs-gcp-02-e71aeab0dc46-lepida-comuni-er/documenti_pa/` (10 documenti HTML caricati)
- **Data Store Indicizzato:** `lepida-comuni-er-ds` (*"Corpus Documentale Lepida e Comuni Emilia-Romagna 2026"*)
- **App Gemini Enterprise Creata:** `Lepida & Comuni ER Assistant` (`lepida-comuni-er-app`)
- **Link Diretto Web App Attiva:** **`https://vertexaisearch.cloud.google.com/home/cid/7ae8a434-2318-4858-82c5-2194e1881041`**
- **Chat Agent Multi-Livello (`Gemini 3.8 Flash`) Pubblicato:** `Consulente Digitale Comuni ER e Servizi Lepida` (`agents/5439338955828520489`)
- **3 Skills Abilitate in `/r/skills`:**
  1. `Simulazione Punteggio Bando Fibra 10 Gbps`
  2. `Checklist Migrazione Cloud e Sicurezza ACN`
  3. `Generatore Bozza Determina Dirigenziale PA`

---

## 3. Regia Didattica del Modulo 2 — Creare il Proprio Chat Agent No-Code in Gemini Enterprise (30 min)

### Cosa fanno i partecipanti nella Web App
1. Aprono il link diretto alla Web App stampato da `setup.sh` (`https://vertexaisearch.cloud.google.com/home/cid/...`).
2. Cliccano nel menu a sinistra su **Agents** $\rightarrow$ pulsante in alto a destra **+ New agent** $\rightarrow$ **Chat agent** $\rightarrow$ **Build manually**.
3. Compilano:
   - **Name:** `Consulente Digitale Comuni ER e Servizi Lepida`
   - **Model:** **`Gemini 3.8 Flash`** (`gemini-3.8-flash`)
   - **Description:** `Assistente ufficiale per i RUP e i referenti dei Comuni dell'Emilia-Romagna: supporta l'analisi dei Bandi Lepida 2026, il calcolo dei cofinanziamenti, la redazione di Determine In-House e il confronto tra progetti comunali.`
   - **Knowledge / Data Store:** selezionano **`Corpus Documentale Lepida e Comuni Emilia-Romagna 2026`** (`lepida-comuni-er-ds`).
4. **Architettura Multi-Livello di Sub-Agents sul Canvas `Flow`:**
   - Mostri come dal pulsante **`+`** sotto il nodo blu (o tramite il pannello conversazionale a sinistra *"Ask to make changes"*) si possono aggiungere più livelli di **Sub-Agents specializzati** (Card Viola), tutti configurati con **`Gemini 3.8 Flash`**:
     - **Fase 1 (`Fase 1 - Istruttoria Bandi e Cloud`)** $\rightarrow$ governa `Specialista Bando Fibra 10 Gbps` e `Specialista Cloud PA e Sicurezza ACN`.
     - **Fase 2 (`Fase 2 - Atti PA e Benchmark Comuni`)** $\rightarrow$ governa `Redattore Determine e Convenzioni PA` e `Analista TARI e Benchmark Comuni ER`.

---

## 4. Regia Didattica del Modulo 3 — Creare e Utilizzare le "Skills" in Gemini Enterprise (45 min)

### Parte A — Creazione delle Skills nella sezione `Skills` (`/r/skills`)
1. Fai cliccare ai partecipanti sulla voce **`Skills`** nel menu laterale sinistro della Web App e poi sul pulsante **`+`**.
2. Ricorda alla sala la regola di validazione sui nomi delle Skills: **non usare il carattere `&`** nel nome della Skill (solo lettere, numeri, spazi e trattini, max 64 caratteri):
   - `Simulazione Punteggio Bando Fibra 10 Gbps`
   - `Generatore Bozza Determina Dirigenziale PA`
   - `Checklist Migrazione Cloud e Sicurezza ACN`
3. Mostra come ogni Skill genera un file strutturato `SKILL.md` condivisibile con tutta l'organizzazione tramite il pulsante **Share** e utilizzabile direttamente con **New chat** o `/NomeSkill`.

### Parte B — Inserimento delle 3 Skills nelle `Instructions` del Chat Agent e Risultati Verificati dei 3 Test

I partecipanti incollano il blocco delle 3 Skills nel campo **Instructions** del proprio Chat Agent, cliccano su **Update** in alto a destra e testano i 3 scenari reali nella scheda **Preview** (o nella chat dell'agente):

#### Test 1 — `SKILL 1: VALUTAZIONE E SIMULAZIONE BANDO COMUNALE`
**Prompt:**
```text
Esegui la [SKILL 1: VALUTAZIONE E SIMULAZIONE BANDO COMUNALE]: L'Unione dei Comuni dell'Appennino Bolognese (11 Comuni montani, sotto i 15.000 abitanti) presenta un progetto da 140.000 EUR sul Bando Fibra 10 Gbps (BANDO-ER-2026-01, quota base 85%) con punteggio tecnico 88/100. Verifica se supera la soglia minima dei 70 punti, indica le premialità applicando il tetto massimo del 95%, calcola il contributo regionale a fondo perduto, la quota residua a carico dell'Unione e gli importi delle 3 tranche (40% anticipo, 30% SAL, 30% saldo).
```
**Risultato Verificato:**
- **Esito Ammissibilità:** Punteggio **88/100** $\ge$ soglia minima **70/100** $\rightarrow$ **PRATICA AMMISSIBILE E APPROVATA**.
- **Calcolo Premialità Cumulative:** Quota Base **85%** + Montano **+5%** + Unione **+5%** + `<15.000 ab.` **+5%** = `100%` teorico $\rightarrow$ **Applicato Tetto Massimo Regionale del 95%**.
- **Quadro Finanziario (su 140.000,00 EUR):**
  - **Contributo Regionale a Fondo Perduto (95%):** **133.000,00 €**
  - **Quota Residua a Carico dell'Unione (5%):** **7.000,00 €** (~636,36 € per ciascuno degli 11 Comuni)
  - **3 Tranche:** 1ª Tranche Anticipo (40%) = **53.200,00 €** | 2ª Tranche SAL (30%) = **39.900,00 €** | 3ª Tranche Saldo (30%) = **39.900,00 €**.

---

#### Test 2 — `SKILL 2: REDAZIONE DETERMINA DIRIGENZIALE IN-HOUSE LEPIDA`
**Prompt:**
```text
Esegui la [SKILL 2: REDAZIONE DETERMINA DIRIGENZIALE IN-HOUSE LEPIDA]: Redigi nelle 6 sezioni obbligatorie del modello MOD-DET-INHOUSE-LEPIDA-2026 la Determina Dirigenziale per il Comune di Rimini (RUP: Ing. Marco Verdi) per l'adesione al Bando BANDO-ER-2026-02 (importo progetto 110.000 EUR, quota base 80%) e l'affidamento in-house a Lepida ScpA del servizio SRV-AI-SPORTELLO.
```
**Risultato Verificato:**
- Genera l'atto amministrativo completo nelle **6 sezioni ufficiali** (`MOD-DET-INHOUSE-LEPIDA-2026` - `Doc 08`):
  1. **Intestazione e RUP:** Comune di Rimini, RUP Ing. Marco Verdi (art. 15 D.Lgs. 36/2023).
  2. **Premesse di Fatto e di Diritto:** L.R. Emilia-Romagna 11/2004 e controllo analogo congiunto su Lepida ScpA.
  3. **Congruità Economica (art. 7 c. 2 D.Lgs. 36/2023):** canone `SRV-AI-SPORTELLO` di **5.400 EUR/anno** con SLA **99,90%** (`Doc 01`), inferiore di oltre il 22% rispetto ai benchmark Consip/MEPA.
  4. **Quadro Economico e 3 Tranche:** Progetto da **110.000,00 EUR** $\rightarrow$ **88.000,00 EUR (80%)** a fondo perduto (Anticipo 40% = **35.200 €**, SAL 30% = **26.400 €**, Saldo 30% = **26.400 €**) e **22.000,00 EUR (20%)** a carico del Comune di Rimini.
  5. **Clausole Obbligatorie ACN, GDPR e AI Act UE 2024/1689 (`Doc 10`):** sorveglianza umana *Human-in-the-Loop* del RUP (art. 14 AI Act), informativa trasparente al cittadino (art. 50 AI Act), Model Armor / Cloud DLP e conservazione log per **24 mesi** in Region UE.
  6. **Dispositivo:** affidamento in-house esente da CIG ordinario e tracciato tramite **CUP**.

---

#### Test 3 — `SKILL 3: BENCHMARK PROGETTI COMUNI ER`
**Prompt:**
```text
Esegui la [SKILL 3: BENCHMARK PROGETTI COMUNI ER]: Costruisci una tabella comparativa con Ente, Codice Pratica, Bando, Importo, Punteggio, Stato e Risultati/SLA per i Comuni di Bologna, Modena, Ravenna, Rimini, Ferrara, Parma e Unione Appennino Bolognese, e indica quale documento ed entro quanti giorni il Comune di Ferrara deve inviare per sbloccare la pratica PRAT-2026-106.
```
**Risultato Verificato:**
- Tabella comparativa completa estratta dai documenti comunali (`Doc 03–07`) e segnalazione puntuale per il **Comune di Ferrara (`PRAT-2026-106`, punteggio 64/100, stato `INTEGRAZIONE_RICHIESTA`)**: invio entro **15 giorni solari** dell'**Allegato Tecnico B2** con l'inventario degli asset critici NIS2 e il piano di federazione SIEM col SOC Lepida per superare la soglia di 70/100 e sbloccare il cofinanziamento del 90%.
