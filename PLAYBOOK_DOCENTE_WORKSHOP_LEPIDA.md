# Playbook Docente & Regia Tecnica — Workshop Gemini Enterprise & Agentic AI (Lepida ScpA)

> [!IMPORTANT]
> **Scopo del Playbook (Uso Esclusivo Docente — Postazione #26)**
> Questo documento contiene la regia operativa, i comandi di automazione per i **26 laboratori Qwiklabs** (25 partecipanti + 1 docente), la traccia guidata della tua **Demo Live su `adk web`** e **tutti gli esempi di prompt e risultati reali verificati end-to-end** nell'ambiente Qwiklabs `qwiklabs-gcp-00-436de4629ca8`.

---

## 1. Architettura dei 26 Ambienti Qwiklabs e Punti Automatizzati vs Manuali

Ogni partecipante (`#01..#25`) e il docente (`#26`) accedono manualmente al proprio laboratorio Qwiklabs dedicato (`qwiklabs-gcp-XX-YYYYYYYYYYYY`).

| Attività del Workshop | Modalità per i 25 Partecipanti | Modalità per il Docente (Lab #26) |
| :--- | :--- | :--- |
| **0. Login Qwiklabs & Accettazione ToS** | **Manuale** (con le proprie credenziali `student-XX@...`) | **Manuale** (o via skill `qwiklabs-login` in fase di test) |
| **1. Creazione Bucket GCS Univoco & Upload 10 Documenti Comuni ER / Lepida** | **100% Automatico** (`gs://${PROJECT_ID}-lepida-comuni-er/documenti_pa/`) tramite comando One-Click | **100% Automatico** (`bootstrap_lepida_lab.sh --instructor`) |
| **2. Creazione & Indicizzazione Istantanea Connettore GCS (`lepida-comuni-er-ds`)** | **100% Automatico** (indicizzazione sincrona in 2 secondi + sync batch GCS) | **100% Automatico** |
| **3. Creazione Dataset BigQuery (`lepida_territorio`) & Deploy Agente ADK (`cloud_search_agent`) su Agent Engine + Telemetria + Agent Registry (A2A)** | **Opzionale (`--with-adk`)** (`deploy_adk_agent.py` + ruoli IAM `cloudtrace.agent`, `telemetry.tracesWriter`, `logging.logWriter`) | **100% Automatico** (`./setup.sh --with-adk` + `./setup_and_run_cloudshell.sh` per `adk web`) |
| **4. Modulo 1 — Creazione Gemini Enterprise App + Collegamento Connettore GCS + Ricerca** | **Guidato da UI** (Console grafica Gemini Enterprise, zero CLI) | Mostrato a schermo + verificato con risultati nel Playbook |
| **5. Modulo 2 — Creazione Chat Agent No-Code in Gemini Enterprise** | **Guidato da UI** (`Agents -> + Create agent` nella Web App) | Mostrato a schermo + prompt pronti |
| **6. Modulo 3 — Configurazione e Test delle 3 Skills dentro l'Agente Gemini Enterprise** | **Guidato da UI** (copia-incolla delle 3 Skills nelle istruzioni dell'agente e test in chat) | Mostrato a schermo + risultati verificati nel Playbook |
| **7. Modulo 4 — Demo Live `adk web` (`cloud_search_agent`), Agent Engine Playground, Telemetria & Agent Registry (A2A)** | **Guida dedicata:** [`README_DEMO_ADK_AGENT_PLATFORM.md`](./README_DEMO_ADK_AGENT_PLATFORM.md) | **Demo Live Docente su `adk web`** (`--port 8080 --allow_origins "*"`), **Playground** e **Agent Registry (A2A)** |

---

## 2. Il Comando Automatico "One-Click Bullet-Proof" (Cosa Fa Dietro le Quinte)

### A. Comando per i 25 Partecipanti e per la tua Postazione Docente (#26)
- **Per i 25 Partecipanti (incollano 1 sola riga in Cloud Shell `>_`):**
  ```bash
  mkdir -p ~/lepida_workshop && cd ~/lepida_workshop && gcloud storage cp gs://lepida-workshop/lepida_workshop_kit.tar.gz . && tar -xzf lepida_workshop_kit.tar.gz && chmod +x bootstrap_lepida_lab.sh && ./bootstrap_lepida_lab.sh
  ```
- **Per la tua Postazione Docente (#26 — prepara anche MCP Toolbox per `adk web`):**
  ```bash
  mkdir -p ~/lepida_workshop && cd ~/lepida_workshop && gcloud storage cp gs://lepida-workshop/lepida_workshop_kit.tar.gz . && tar -xzf lepida_workshop_kit.tar.gz && chmod +x bootstrap_lepida_lab.sh && ./bootstrap_lepida_lab.sh --instructor
  ```

### B. Perché il Connettore GCS (`lepida-comuni-er-ds`) è Subito Coerente con la Ricerca (Zero Attesa di Indicizzazione)
Un problema classico dei workshop su Discovery Engine / Gemini Enterprise è che il job batch `documents:import` da Cloud Storage impiega **15–25 minuti** sui progetti Qwiklabs appena creati.
Lo script [setup_ge_datastore.py](file:///usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/setup_ge_datastore.py) risolve questo problema alla radice con una **doppia operazione automatica**:
1. Crea il bucket univoco `gs://${PROJECT_ID}-lepida-comuni-er` e carica i 10 file HTML in `documenti_pa/`.
2. Indicizza **sincronamente in 2 secondi** tutti i 10 documenti nel branch `0` di `lepida-comuni-er-ds` (includendo il metadato `source_uri: gs://${PROJECT_ID}-lepida-comuni-er/documenti_pa/...`) **e contemporaneamente** avvia il connettore batch GCS `documents:import`.
   - **Risultato verificato nel lab `qwiklabs-gcp-00-436de4629ca8`:** tutti i 10 documenti restituiscono `HTTP 200` in meno di 3 secondi e sono **immediatamente ricercabili** con `SEMANTIC_SEARCH` non appena l'utente collega il Data Store!

### C. Comando "Paracadute" (`--auto-ui`) se un Partecipante si Blocca nella Console GCP
Se uno dei 25 partecipanti resta indietro nella creazione dell'App o nella registrazione dell'agente ADK, fagli eseguire in Cloud Shell:
```bash
cd ~/lepida_workshop && ./bootstrap_lepida_lab.sh --auto-ui
```
*(Nota importante verificata nel lab: la licenza trial di 30 giorni `free_trial_gemini` viene allocata automaticamente da Google Cloud quando l'utente clicca per la prima volta su **Create** nel form grafico di creazione dell'App in `console.cloud.google.com/gemini-enterprise/create-app`).*

---

## 3. Modulo 1 — Creazione Gemini Enterprise App, Connettore GCS e Risultati di Ricerca Verificati

### Passaggi che svolgono gli utenti (e cosa verificare a schermo):
1. Aprono il link diretto stampato a fine setup: `https://console.cloud.google.com/gemini-enterprise/apps?project=<PROJECT_ID>`
2. Cliccano su **Create your first app** (o **Create app**):
   - **App name:** `Lepida & Comuni ER Assistant`
   - **Location:** `global (Global)`
   - **Advanced options -> Company name:** `Lepida ScpA`
   - Cliccano su **Create** *(questo attiva automaticamente la licenza `free_trial_gemini` sul `default_user_store`)*.
3. Nel menu di sinistra cliccano su **Connected data stores** -> **Add existing data stores** -> spuntano la casella **`Corpus Documentale Lepida e Comuni Emilia-Romagna 2026`** (`lepida-comuni-er-ds`) -> cliccano **Connect**.
4. Nel menu di sinistra cliccano su **Integration** -> confermano **Use Google Identity** -> cliccano sul link della **Web App**.

---

### Esempio Reale Verificato — Ricerca Grounded Multi-Documento sul Connettore GCS

**Prompt di test da mostrare/far provare nella barra principale della Web App di Gemini Enterprise:**
```text
Secondo il Catalogo Servizi e Listino Ufficiale Lepida 2026 e i documenti dei Comuni dell'Emilia-Romagna nel Data Store:
1) Quali sono i canoni annui e gli SLA dei 5 servizi a catalogo Lepida (SRV-FIBRA-10G, SRV-CLOUD-ACN, SRV-SOC-NIS2, SRV-AI-SPORTELLO, SRV-IOT-LORAWAN)?
2) Quali sono le scadenze e le riduzioni/esenzioni TARI 2026 del Comune di Bologna?
3) Quali sono le 4 soglie idrometriche LoRaWAN del Comune di Ravenna e i tempi di notifica incidenti NIS2 al CSIRT del Comune di Modena?
```

**Risultato Reale Verificato nel Lab (`qwiklabs-gcp-00-436de4629ca8`):**

> #### 1. Servizi a Catalogo Lepida 2026: Canoni e SLA
> | Codice Servizio | Nome Servizio Lepida | Canone Annuo In-House (IVA Esente/Esclusa) | SLA Garantito / Ripristino |
> | :--- | :--- | :--- | :--- |
> | **`SRV-FIBRA-10G`** | Rilegamento in Fibra Ottica Dedicata 10 Gbps | **4.200 EUR / anno** per sede *(Attivazione una tantum: 8.500 EUR)* | Disponibilità **99,95%** – Ripristino guasto bloccante entro **4 ore** |
> | **`SRV-CLOUD-ACN`** | Ambiente Cloud Qualificato ACN (IaaS / PaaS / Kubernetes) | **9.500 EUR / anno** *(Pacchetto Base fino a 32 vCPU, 128 GB RAM, 5 TB NVMe + Backup immutabile)* | Disponibilità **99,98%** – RPO **15 minuti**, RTO **1 ora** |
> | **`SRV-SOC-NIS2`** | SOC / CERT Regionale Federato e Conformità NIS2 | **6.800 EUR / anno** *(Comuni ≤ 25.000 ab.)* / **14.500 EUR / anno** *(Comuni > 25.000 ab. o Unioni)* | Presa in carico allarmi critici entro **15 minuti** (24x7) |
> | **`SRV-AI-SPORTELLO`** | Piattaforma Gemini Enterprise & Agentic AI per Sportelli PA | **5.400 EUR / anno** per Ente *(fino a 30 postazioni URP/RUP e Sportello Cittadino)* | Disponibilità **99,90%** – Log conservati per **24 mesi** |
> | **`SRV-IOT-LORAWAN`** | Rete Regionale IoT LoRaWAN & Cruscotto Sensoristica | **120 EUR / anno** per Gateway + **18 EUR / anno** per sensore attivo | Disponibilità **99,50%** – Allerta webhook in tempo reale (**< 5 secondi**) |
>
> #### 2. TARI 2026 – Comune di Bologna: Scadenze, Riduzioni ed Esenzioni
> - **Scadenze di pagamento:** **1ª Rata (40%)** entro il **30 aprile 2026**; **2ª Rata (40%)** entro il **30 settembre 2026**; **3ª Rata (Saldo 20%)** entro il **2 dicembre 2026** (oppure soluzione unica entro il 30 aprile 2026 via PagoPA/App IO).
> - **Riduzioni ed Esenzioni:** **-30%** per ISEE ≤ 15.000 EUR; **-65%** per ISEE ≤ 8.500 EUR o disabilità grave (L. 104/92 art. 3 c. 3); **Esenzione 100% per 24 mesi** per Start-up innovative e imprese giovanili under 35; **-15%** per compostaggio domestico certificato.
>
> #### 3. Soglie Idrometriche LoRaWAN (Ravenna) e Notifica Incidenti NIS2 (Modena)
> - **Soglie Idrometriche Ravenna (45 sensori su fiumi Lamone, Montone, Ronco):**
>   - **Ordinario (Verde):** `< 1,80 m` (campionamento ogni 15 min)
>   - **Pre-Allerta (Gialla):** `1,80 m – 2,39 m` (ogni 5 min -> notifica Polizia Locale e Protezione Civile)
>   - **Allerta Arancione:** `2,40 m – 2,99 m` (ogni 60 sec -> apertura pre-COC e allerta Consorzio di Bonifica)
>   - **Allerta Rossa (Critica):** `≥ 3,00 m` (tempo reale ogni 30 sec -> invio allerta pubblica su App IO e pannelli stradali)
> - **Tempi Tassativi Notifica CSIRT Italia NIS2 (Comune di Modena / Unione Terre d'Argine):**
>   - **Pre-allarme (Early Warning):** entro **24 ore**
>   - **Notifica Completa dell'Incidente:** entro **72 ore**
>   - **Relazione Finale (Root Cause Analysis):** entro **30 giorni**

---

## 4. Modulo 2 & Modulo 3 — Creazione Chat Agent Multi-Livello (`Gemini 3.8 Flash`) e Utilizzo delle 3 Skills in Gemini Enterprise

Nella Web App di Gemini Enterprise, i partecipanti cliccano su **Agents -> + New agent -> Chat agent -> Build manually** e configurano l'agente:
- **Agent Name:** `Consulente Digitale Comuni ER e Servizi Lepida`
- **Model (Modello obbligatorio per tutti i nodi):** **`Gemini 3.8 Flash`** (`gemini-3.8-flash`)
- **Description / Goal:** `Assistente Multi-Agent Gerarchico e Sequenziale specializzato nei servizi Lepida ScpA, bandi regionali PR FESR, sicurezza ACN e Comuni ER.`
- **Knowledge / Data Store collegato:** `Corpus Documentale Lepida e Comuni Emilia-Romagna 2026` (`lepida-comuni-er-ds`)
- **Architettura Multi-Livello sul Canvas `Flow` (tutti i nodi LLM con `Gemini 3.8 Flash`):**
  - **Livello 0 (`SequentialAgentNode`):** collega in sequenza orizzontale i 2 Coordinatori Blu (`Fase 1 -> Fase 2`).
  - **Livello 1 (Coordinatori Blu):**
    1. `Fase 1 - Istruttoria Bandi e Cloud`
    2. `Fase 2 - Atti PA e Benchmark Comuni`
  - **Livello 2 (Sub-Agents Viola + ADK Agent):**
    - Sotto Fase 1: `Specialista Bando Fibra 10 Gbps` + `Specialista Cloud PA e Sicurezza ACN`
    - Sotto Fase 2: `Redattore Determine e Convenzioni PA` + `Analista TARI e Benchmark Comuni ER` + `Cloud Search & Sizing ADK Agent` (`referencedAdkAgentNode`).

### Come Funzionano le "Skills" in Gemini Enterprise (`/r/skills` + `Instructions`)
I partecipanti utilizzano le **3 Skills** sia dalla sezione dedicata **`Skills`** nel menu laterale sinistro della Web App (`/r/skills`), sia nel campo **Instructions** del Chat Agent (`[SKILL 1: VALUTAZIONE E SIMULAZIONE BANDO COMUNALE]`, `[SKILL 2: REDAZIONE DETERMINA DIRIGENZIALE IN-HOUSE LEPIDA]`, `[SKILL 3: BENCHMARK PROGETTI COMUNI ER]`). Ogni Skill definisce:
1. **Trigger di attivazione** (in linguaggio naturale o tramite `/NomeSkill`)
2. **Fonti GCS obbligatorie da consultare**
3. **Regole di calcolo / controllo normativo**
4. **Formato di output standardizzato**

---

### Risultati Reali Verificati nel Lab per le 3 Skills

#### Test Skill 1 — Valutazione Ammissibilità, Premialità Cumulative (Cap 95%) e 3 Tranche

**Prompt inviato all'agente:**
```text
Esegui la [SKILL 1: VALUTAZIONE E SIMULAZIONE BANDO COMUNALE]: L'Unione dei Comuni dell'Appennino Bolognese (11 Comuni montani, sotto i 15.000 abitanti) presenta un progetto da 140.000 EUR sul Bando Fibra 10 Gbps (BANDO-ER-2026-01, quota base 85%) con punteggio tecnico 88/100. Verifica se supera la soglia minima dei 70 punti, indica le premialità applicando il tetto massimo del 95%, calcola il contributo regionale a fondo perduto, la quota residua a carico dell'Unione e gli importi delle 3 tranche (40% anticipo, 30% SAL, 30% saldo).
```

**Risultato Reale Verificato (`qwiklabs-gcp-00-436de4629ca8`):**
> - **Esito Ammissibilità:** Punteggio **88/100** ≥ soglia minima **70/100** -> **PRATICA AMMISSIBILE E APPROVATA**.
> - **Calcolo Premialità Cumulative:**
>   - Quota Base `BANDO-ER-2026-01`: **85%**
>   - Premialità Comuni Montani / Aree Interne: **+5%**
>   - Premialità Unione di Comuni (≥ 3 Comuni): **+5%**
>   - Premialità Comuni < 15.000 abitanti: **+5%**
>   - Somma teorica: `85% + 15% = 100%` -> **Applicato Tetto Massimo Regionale del 95%**.
> - **Quadro Finanziario (su 140.000,00 EUR):**
>   | Voce di Bilancio | Aliquota (%) | Importo (EUR) | Note |
>   | :--- | :---: | :---: | :--- |
>   | **Contributo Regionale a Fondo Perduto** | **95%** | **133.000,00 €** | Coperto da Regione / Lepida |
>   | **Quota Residua a Carico dell'Unione** | **5%** | **7.000,00 €** | ~636,36 € per ciascuno degli 11 Comuni |
>   | **Valore Totale del Progetto** | **100%** | **140.000,00 €** | Servizio `SRV-FIBRA-10G` |
> - **Piano di Erogazione in 3 Tranche:**
>   1. **1ª Tranche — Anticipo (40%):** **53.200,00 €** *(entro 30 gg da determina e codice CUP)*
>   2. **2ª Tranche — SAL Intermedio (30%):** **39.900,00 €** *(al 50% delle attività di posa)*
>   3. **3ª Tranche — Saldo Finale (30%):** **39.900,00 €** *(a collaudo positivo e rendicontazione fatture)*

---

#### Test Skill 2 — Redazione Automatica Bozza Determina Dirigenziale In-House Lepida (6 Sezioni)

**Prompt inviato all'agente:**
```text
Esegui la [SKILL 2: REDAZIONE DETERMINA DIRIGENZIALE IN-HOUSE LEPIDA]: Redigi nelle 6 sezioni obbligatorie del modello MOD-DET-INHOUSE-LEPIDA-2026 la Determina Dirigenziale per il Comune di Rimini (RUP: Ing. Marco Verdi) per l'adesione al Bando BANDO-ER-2026-02 (importo progetto 110.000 EUR, quota base 80%) e l'affidamento in-house a Lepida ScpA del servizio SRV-AI-SPORTELLO.
```

**Risultato Reale Verificato (`qwiklabs-gcp-00-436de4629ca8`):**
L'agente genera l'atto amministrativo completo nelle **6 sezioni ufficiali** incrociando `Doc 08` (Modello Determina), `Doc 01` (Listino Lepida) e `Doc 10` (Governance AI Act):
- **Sezione 1 (Intestazione e RUP):** Comune di Rimini, RUP Ing. Marco Verdi (art. 15 D.Lgs. 36/2023), adesione `BANDO-ER-2026-02` e affidamento in-house `SRV-AI-SPORTELLO`.
- **Sezione 2 (Premesse di Fatto e di Diritto):** richiamo alla L.R. Emilia-Romagna 11/2004, controllo analogo congiunto su Lepida ScpA e Linee Guida `LG-LEPIDA-2026-REV4`.
- **Sezione 3 (Congruità Economica art. 7 c. 2 D.Lgs. 36/2023):** attestazione canone `SRV-AI-SPORTELLO` di **5.400 EUR/anno** con SLA **99,90%** (inferiore di oltre il 22% rispetto ai benchmark Consip/MEPA).
- **Sezione 4 (Quadro Economico e 3 Tranche):** Progetto da **110.000,00 EUR** -> **88.000,00 EUR (80%)** a fondo perduto (Anticipo 40% = **35.200 €**, SAL 30% = **26.400 €**, Saldo 30% = **26.400 €**) e **22.000,00 EUR (20%)** a carico del Comune di Rimini.
- **Sezione 5 (Clausole Obbligatorie ACN, GDPR e AI Act UE 2024/1689):** obbligo *Human-in-the-Loop* del RUP (art. 14 AI Act), informativa trasparente al cittadino (art. 50 AI Act), filtri Model Armor / Cloud DLP e conservazione log per **24 mesi** in Region UE.
- **Sezione 6 (Dispositivo):** approvazione quadro economico, affidamento in-house esente da CIG ordinario (tracciato tramite **CUP**) e trasmissione a Lepida per l'erogazione della 1ª Tranche (40%).

---

#### Test Skill 3 — Benchmark & Riuso Soluzioni tra i Comuni dell'Emilia-Romagna

**Prompt inviato all'agente:**
```text
Esegui la [SKILL 3: BENCHMARK PROGETTI COMUNI ER]: Costruisci una tabella comparativa con Ente, Codice Pratica, Bando, Importo, Punteggio, Stato e Risultati/SLA per i Comuni di Bologna, Modena, Ravenna, Rimini, Ferrara, Parma e Unione Appennino Bolognese, e indica quale documento ed entro quanti giorni il Comune di Ferrara deve inviare per sbloccare la pratica PRAT-2026-106.
```

**Risultato Reale Verificato (`qwiklabs-gcp-00-436de4629ca8`):**
L'agente estrae da tutti i documenti comunali (`Doc 03–07`) la tabella comparativa completa e segnala per il **Comune di Ferrara (`PRAT-2026-106`, punteggio 64/100, stato `INTEGRAZIONE_RICHIESTA`)** che il CISO deve trasmettere entro **15 giorni solari** l'**Allegato Tecnico B2** con l'inventario degli asset critici NIS2 e il piano di federazione SIEM col SOC Lepida per superare la soglia di 70/100 e sbloccare il cofinanziamento del 90%.

---

## 5. Modulo 4 — Traccia della Demo Live ADK (`cloud_search_agent`): Cloud Shell (`adk web`), Agent Engine, Observability & Agent Registry (A2A)

> 👉 **Guida Tecnica Completa Passo-Passo:** consulta **[`README_DEMO_ADK_AGENT_PLATFORM.md`](./README_DEMO_ADK_AGENT_PLATFORM.md)**.

### Parte A — Traccia per la Tua Demo Live su `adk web` in Cloud Shell (15–20 min)

1. Nella tua Cloud Shell avvia `adk web` tramite lo script dedicato:
   ```bash
   cd ~/lepida_workshop
   ./setup_and_run_cloudshell.sh
   ```
2. Apri **Web Preview -> Preview on port 8080** e mostra alla sala:
   - In alto a sinistra la selezione di **`cloud_search_agent`** (*"Cloud Search & Sizing ADK Agent"*).
   - I **4 Tool standard ADK** definiti in `cloud_search_agent/tools.py`:
     1. `search_cloud_knowledge` (`FunctionTool` + `ToolContext.state["search_history"]`)
     2. `google_web_search_specialist` (`AgentTool` che incapsula un sub-agent con `google_search` Grounding)
     3. `calculate_agent_sizing` (`FunctionTool` con calcolo prezzi mensili in USD: **Prezzo Mese List `$/mo`**, **Prezzo Mese 1Y CUD `$/mo`**, **Prezzo Mese 3Y CUD `$/mo`**)
     4. `get_session_telemetry_status` (`FunctionTool` che legge lo stato di telemetria e la cronologia delle ricerche della sessione)
3. Incolla dal vivo in `adk web` (o nel **Playground di Agent Engine**) questi prompt dimostrativi mostrando i pannelli **`Events`**, **`State`** e **`Trace`**:

   - **Demo Prompt 1 (Knowledge Base Search + Session State):**
     ```text
     Cerca nella knowledge base come attivare observability, Cloud Trace e Cloud Logging su un agente ADK deployato su Vertex AI Agent Engine e quali ruoli IAM servono.
     ```
   - **Demo Prompt 2 (Calcolo Sizing e Tabella Prezzi Mensili USD List / 1Y CUD / 3Y CUD):**
     ```text
     Calcola il costo mensile in USD (Prezzo Mese List, 1Y CUD e 3Y CUD) per un agente ADK in produzione con 4.000 richieste al giorno, 1.500 token di input medi, 600 token di output medi, 2 vCPU e 4 GiB di RAM.
     ```
   - **Demo Prompt 3 (Ricerca Web Live con Google Search Grounding tramite `AgentTool`):**
     ```text
     Usa la ricerca web per trovare le ultime novità e caratteristiche principali di Google Agent Development Kit (ADK) e del protocollo Agent2Agent (A2A).
     ```
   - **Demo Prompt 4 (Verifica Stato Sessione e Telemetria OpenTelemetry):**
     ```text
     Mostrami l'ora corrente in Italia, lo stato della telemetria OpenTelemetry e il riepilogo di tutte le ricerche che ho effettuato in questa sessione.
     ```

---

### Parte B — Deploy su Agent Platform Deployment (Agent Engine) e Registrazione A2A in Agent Registry

1. Esegui il deploy e la registrazione automatica con:
   ```bash
   cd ~/lepida_workshop
   python3 deploy_adk_agent.py
   ```
2. Mostra nella Console Google Cloud:
   - **Agent Engine Playground & Telemetry:** il toggle **Telemetry** attivo, gli span in **Cloud Trace Explorer** (`invocation` -> `agent_run` -> `call_llm` / `execute_tool`) e i log strutturati in **Cloud Logging**.
   - **Agent Platform -> Agent Registry:** la scheda **`Cloud Search & Sizing ADK Agent`** con protocollo **`A2A` (`0.3.0`)**, endpoint `/a2a`, le 3 **Skills** e il **Code Snippet A2A**.

---

## 6. Note Tecniche Fondamentali Verificate sul Campo (Dietro le Quinte dello Script)

1. **Abilitazione Automatica di `Chat agent` (`no-code-agent-builder`) e `Skills` (`skills`) sull'Engine:**
   - Su una nuova App Gemini Enterprise, i flag `no-code-agent-builder` (*"Build agents without writing code"*) e `skills` (*"Create and use skills"*) hanno stato predefinito `FEATURE_STATE_OFF` (motivo per cui, senza abilitarli, nella Web App compariva solo `+ Workflow` e mancavano sia `Chat agent` sia la voce `Skills` nel menu laterale).
   - Lo script `setup_ge_datastore.py` e `register_ge_agent.py` eseguono automaticamente `PATCH .../engines/<ENGINE_ID>?updateMask=features` attivando:
     - `no-code-agent-builder: FEATURE_STATE_ON`
     - `skills: FEATURE_STATE_ON`
     - `skill-sharing: FEATURE_STATE_ON`
     - `skill-sharing-without-admin-approval: FEATURE_STATE_ON`
     - `agent-sharing: FEATURE_STATE_ON`
     - `agent-sharing-without-admin-approval: FEATURE_STATE_ON`
2. **Prevenzione Automatica dei Duplicati ADK (`register_ge_agent.py`):**
   - `register_ge_agent.py` verifica sempre gli agenti esistenti sull'Engine e rimuove eventuali registrazioni ADK precedenti prima di registrare `Cloud Search & Sizing ADK Agent`, garantendo che sotto *From your organization* compaia sempre **1 solo Agente ADK**.
3. **Pubblicazione Automatica di Chat Agent (`:deployLowCode`) e Skills (`:requestAgentReview`):**
   - In modalità `--solution` (o lanciando `python3 register_ge_agent.py`), lo script crea e pubblica automaticamente anche il Chat Agent **`Consulente Digitale Comuni ER e Servizi Lepida`** (`lowCodeAgentDefinition` + `:deployLowCode` + `:requestAgentReview` + `ALL_USERS`) e le **3 Skills** nella sezione `Skills` della Web App.

