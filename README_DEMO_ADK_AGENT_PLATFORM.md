# Guida Completa Demo ADK (`cloud_search_agent`) — Cloud Shell (`adk web`), Agent Platform Deployment, Observability & Agent Registry (A2A)

> **Riferimento al Repository Principale:** [Torna al README principale (`README.md`)](./README.md)

Questa guida descrive passo-passo l'architettura, il codice e tutti i comandi per eseguire la demo dell'agente **Google Agent Development Kit (ADK)** denominato **`cloud_search_agent`** (**"Cloud Search & Sizing ADK Agent"**):
1. **Esecuzione interattiva in Google Cloud Shell** tramite **`adk web`** (porta `8080`).
2. **Definizione dei Tool con standard ufficiale Google ADK** (`FunctionTool`, `ToolContext`, `AgentTool` con `google_search`).
3. **Deploy su Agent Platform Deployment (Vertex AI Agent Engine)** con supporto nativo al **Playground**.
4. **Attivazione completa di Observability, Telemetria OpenTelemetry, Cloud Trace e Cloud Logging**.
5. **Registrazione in Agent Platform -> Agent Registry** (`us-central1` e `global`) con configurazione **A2A (`A2A_AGENT` / `A2A_AGENT_CARD` / `spec.agentCard`)**.
6. **5 Scenari ed Esempi Pronti di Test End-to-End**.

---

## 1. Architettura e Struttura dei File della Demo ADK

```text
lepida-gemini-enterprise-workshop/
├── cloud_search_agent/                # Package Python dell'agente ADK (scoperto da `adk web`)
│   ├── __init__.py                    # Esporta `agent`
│   ├── agent.py                       # Definizione di `root_agent` (Gemini 2.5 Flash) + tool + callback
│   ├── tools.py                       # 4 Tool definiti con standard ADK (FunctionTool, ToolContext, AgentTool)
│   ├── callbacks.py                   # 6 Callback di Observability & Cloud Logging
│   └── requirements.txt               # Dipendenze runtime per Agent Engine + OpenTelemetry
├── setup_and_run_cloudshell.sh        # Script 1-click per avviare `adk web` in Cloud Shell (porta 8080)
├── deploy_adk_agent.py                # Deploy su Agent Engine + Telemetria + Registrazione A2A in Agent Registry
├── deploy_agent.py                    # Alias di `deploy_adk_agent.py`
├── test_remote_agent.py               # Suite di test end-to-end sull'agente deployato (genera Trace e Log)
└── requirements.txt                   # Dipendenze Python complete del progetto
```

### I 4 Tool definiti secondo lo Standard ADK (`cloud_search_agent/tools.py`)

| Nome Tool | Tipo ADK Standard | Descrizione Funzionale |
| :--- | :--- | :--- |
| **`search_cloud_knowledge`** | `FunctionTool(func=search_cloud_knowledge)` + `ToolContext` | Cerca nella Knowledge Base tecnica di Google Cloud (ADK, `adk web`, Vertex AI Agent Engine, Cloud Trace, Agent Registry, Model Armor) e salva ogni ricerca in `tool_context.state["search_history"]`. |
| **`google_web_search_specialist`** | `AgentTool(agent=web_search_subagent)` con `google_search` | Sub-agent ADK specializzato che utilizza il tool nativo `google_search` (Google Search Grounding) per ricerche live sul web. Incapsulare `google_search` in un `AgentTool` consente di mantenere attivo l'*Automatic Function Calling (AFC)* insieme ai `FunctionTool` personalizzati. |
| **`calculate_agent_sizing`** | `FunctionTool(func=calculate_agent_sizing)` + `ToolContext` | Calcola il dimensionamento e la stima economica mensile in dollari (**Prezzo Mese List `$/mo`**, **Prezzo Mese 1Y CUD `$/mo`**, **Prezzo Mese 3Y CUD `$/mo`**) per il runtime Agent Engine (vCPU + RAM) e i token di Gemini 2.5 Flash. |
| **`get_session_telemetry_status`** | `FunctionTool(func=get_session_telemetry_status)` + `ToolContext` | Restituisce data e ora corrente in Italia (`Europe/Rome`), progetto/regione GCP, stato di Cloud Trace/Logging e la cronologia delle ricerche memorizzate in `tool_context.state`. |

### Le 6 Callback di Observability & Cloud Logging (`cloud_search_agent/callbacks.py`)
L'agente configura tutti i punti di aggancio (`hooks`) previsti dallo standard ADK per emettere log strutturati su **Cloud Logging** ad ogni fase del ciclo di vita:
- `before_agent_callback=before_agent_log` (inizializza il timestamp del turno e `search_history` nello stato della sessione)
- `after_agent_callback=after_agent_log` (calcola e registra in millisecondi la latenza totale del turno `[ADK-AGENT-END]`)
- `before_model_callback=log_query_to_model` (registra il prompt inviato al modello `[ADK-LLM-REQUEST]`)
- `after_model_callback=log_model_response` (registra la risposta testuale o le function call `[ADK-LLM-TOOL-CALL]`)
- `before_tool_callback=before_tool_log` (registra l'avvio del tool e gli argomenti `[ADK-TOOL-START]`)
- `after_tool_callback=after_tool_log` (registra l'esito del tool `[ADK-TOOL-END]`)

---

## 2. Passo 1 — Eseguire l'Agente in Google Cloud Shell con `adk web`

1. Apri **Google Cloud Shell** sul tuo progetto GCP (es. `rootprj-377111` o progetto Qwiklabs).
2. Clona il repository (se non già presente) e avvia lo script di esecuzione locale:
   ```bash
   git clone https://github.com/marangonic/lepida-gemini-enterprise-workshop.git ~/lepida_workshop
   cd ~/lepida_workshop
   ./setup_and_run_cloudshell.sh
   ```
   *(In alternativa, se hai già l'ambiente `.venv` attivo)*:
   ```bash
   cd ~/lepida_workshop
   source .venv/bin/activate
   export GOOGLE_GENAI_USE_VERTEXAI=TRUE
   export GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)
   export GOOGLE_CLOUD_LOCATION=us-central1
   adk web --port 8080 --allow_origins "*"
   ```
   > [!IMPORTANT]
   > In Google Cloud Shell è fondamentale passare `--allow_origins "*"` a `adk web` per evitare errori `403 Forbidden` sul caricamento dei moduli ES6 attraverso il proxy di Cloud Shell Web Preview.

3. Clicca sull'icona **Web Preview** in alto a destra nella barra della Cloud Shell $\rightarrow$ **Preview on port 8080**.
4. Nel menu a tendina in alto a sinistra dell'interfaccia `adk web`, seleziona **`cloud_search_agent`** e inizia a chattare ispezionando in tempo reale le schede **Events**, **State** e **Trace**.

---

## 3. Passo 2 — Attivazione API e Permessi IAM per Observability, Telemetria e Agent Registry

Prima di effettuare il deploy su **Agent Platform Deployment (Vertex AI Agent Engine)**, abilita le API necessarie e assegna i ruoli IAM al **Reasoning Engine Service Agent** (`service-<PROJECT_NUMBER>@gcp-sa-aiplatform-re.iam.gserviceaccount.com`):

```bash
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")

# 1. Abilita le API per Agent Engine, Cloud Trace, OpenTelemetry, Cloud Logging e Agent Registry
gcloud services enable \
  aiplatform.googleapis.com \
  cloudtrace.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  telemetry.googleapis.com \
  agentregistry.googleapis.com \
  apphub.googleapis.com \
  storage.googleapis.com \
  --project="${PROJECT_ID}"

# 2. Assegna i ruoli IAM di Observability & Runtime al Service Agent di Agent Engine
RE_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
for ROLE in \
  roles/aiplatform.user \
  roles/cloudtrace.agent \
  roles/telemetry.tracesWriter \
  roles/logging.logWriter \
  roles/monitoring.metricWriter \
  roles/serviceusage.serviceUsageConsumer \
  roles/storage.objectViewer; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${RE_SA}" \
    --role="${ROLE}" \
    --condition=None \
    --quiet
done
```

---

## 4. Passo 3 — Deploy su Agent Platform Deployment (Vertex AI Agent Engine) con Telemetria & Playground

Lo script [`deploy_adk_agent.py`](./deploy_adk_agent.py) incapsula `root_agent` in `AdkApp(agent=root_agent, enable_tracing=True)` e imposta le variabili d'ambiente che attivano l'interruttore **Telemetry: ON** nella Console di Agent Engine, l'esportazione degli span OpenTelemetry verso **Cloud Trace** (`telemetry.googleapis.com`) e la cattura dei payload di prompt/risposta:
- `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY="true"`
- `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT="true"`
- `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS="true"`

Per lanciare il deploy e la registrazione automatica in Agent Registry:

```bash
cd ~/lepida_workshop
source .venv/bin/activate
python3 deploy_adk_agent.py
```

 *(Oppure tramite lo script unificato del workshop: `./setup.sh --with-adk`)*.

Al termine del deploy (~3-4 minuti):
- Il Resource Name dell'agente viene salvato in `deployment_metadata.json` e `DEPLOYED_AGENT_RESOURCE.txt` (es. su `rootprj-377111`: `projects/482813436426/locations/us-central1/reasoningEngines/1325967317510651904`).
- Puoi aprire direttamente il **Playground di Agent Engine** in Console:
  `https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/<ENGINE_ID>/playground?project=<PROJECT_ID>`
  *(Su `rootprj-377111`: [Apri Playground `1325967317510651904`](https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/us-central1/agent-engines/1325967317510651904/playground?project=rootprj-377111))*.

---

## 5. Passo 4 — Registrazione in Agent Platform -> Agent Registry e Configurazione A2A

Lo script [`deploy_adk_agent.py`](./deploy_adk_agent.py) configura automaticamente **due livelli di integrazione** con **Agent Registry** (`agentregistry.googleapis.com`):

1. **Iniezione di `a2a_agent_card` nello `spec` del Reasoning Engine (`spec.agentCard`)**:
   - Inietta il JSON della `AgentCard` nel campo `a2a_agent_card` del metodo `async_create_session` (`PATCH /v1beta1/.../reasoningEngines/<ENGINE_ID>?updateMask=spec.class_methods`).
   - Questo popola `spec.agentCard` direttamente sulla risorsa Reasoning Engine mantenendo tutti i 14 metodi ADK (`stream_query`, `async_stream_query`, `create_session`, ecc.) necessari al funzionamento del **Playground**.
2. **Registrazione del Servizio A2A (`cloud-search-adk-agent`) in Agent Registry (`us-central1` e `global`)**:
   - Crea/aggiorna il servizio `cloud-search-adk-agent` con `--agent-spec-type=a2a-agent-card`, protocollo **`A2A_AGENT` (`0.3.0`)**, endpoint `/a2a` (`https://us-central1-aiplatform.googleapis.com/v1beta1/projects/<PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<ENGINE_ID>/a2a`) e le **3 Skills A2A** (`cloud_knowledge_search`, `google_web_search`, `cloud_sizing_calculator`).

### Come visualizzare e verificare la configurazione A2A

#### A. Da Google Cloud Console (UI Grafica)
1. Apri [**Agent Registry in Google Cloud Console**](https://console.cloud.google.com/vertex-ai/agents/agent-registry).
2. Clicca sulla voce **`Cloud Search & Sizing ADK Agent`** con protocollo **`A2A`**:
   - Nella tabella **Protocols** vedrai l'URI `.../reasoningEngines/<ENGINE_ID>/a2a`, Type **`A2A`** e Version **`0.3.0`**.
   - Nella tabella **Skills** vedrai le 3 skill complete di tag ed esempi.
   - Sotto **Skills** comparirà automaticamente lo snippet di codice client A2A (**A2A Code Snippet**).

#### B. Da Cloud Shell tramite `gcloud alpha agent-registry`
```bash
export PROJECT_ID=$(gcloud config get-value project)

# 1. Elenca gli agenti registrati in us-central1 e global
gcloud alpha agent-registry agents list --location=us-central1 --project="${PROJECT_ID}"
gcloud alpha agent-registry agents list --location=global --project="${PROJECT_ID}"

# 2. Mostra il dettaglio completo del Servizio A2A e della AgentCard
gcloud alpha agent-registry services describe cloud-search-adk-agent \
  --location=us-central1 \
  --project="${PROJECT_ID}"
```

#### C. Da Cloud Shell tramite `curl` (Ispezione `spec.agentCard` e chiamata `:streamQuery`)
```bash
export ENGINE_RES=$(cat DEPLOYED_AGENT_RESOURCE.txt)

# 1. Mostra lo spec.agentCard salvato direttamente sul Reasoning Engine
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://us-central1-aiplatform.googleapis.com/v1beta1/${ENGINE_RES}" \
  | jq '.spec.agentCard'

# 2. Invoca via HTTP POST l'endpoint di streaming :streamQuery del Reasoning Engine
curl -s -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1/${ENGINE_RES}:streamQuery" \
  -d '{
    "class_method": "stream_query",
    "input": {
      "user_id": "demo-user-argolis",
      "message": "Cerca nella knowledge base come funziona Agent Registry e mostrami le best practice"
    }
  }'
```

---

## 6. Passo 5 — Esempi Pronti su cui Testare l'Agente (in `adk web`, nel Playground o da CLI)

Puoi eseguire automaticamente tutti i test da terminale (generando tracce in **Cloud Trace** e log in **Cloud Logging**) con:

```bash
cd ~/lepida_workshop
source .venv/bin/activate
python3 test_remote_agent.py
```

Oppure copiare e incollare manualmente questi **5 prompt** in **`adk web`** (porta `8080`) o nel **Playground di Agent Engine**:

### Esempio 1 — Ricerca nella Knowledge Base Tecnica (`search_cloud_knowledge` — `FunctionTool` + `ToolContext`)
```text
Cerca nella knowledge base come attivare observability, Cloud Trace e Cloud Logging su un agente ADK deployato su Vertex AI Agent Engine e quali ruoli IAM servono.
```
* **Cosa verificare:** invocazione del tool `search_cloud_knowledge(query='...', category='observability')`, risposta strutturata con i ruoli IAM (`roles/cloudtrace.agent`, `roles/telemetry.tracesWriter`, `roles/logging.logWriter`) e salvataggio della query in `state["search_history"]`.

### Esempio 2 — Ricerca Web Live con Google Search (`google_web_search_specialist` — `AgentTool` + `google_search`)
```text
Usa la ricerca web per trovare le ultime novità e caratteristiche principali di Google Agent Development Kit (ADK) e del protocollo Agent2Agent (A2A).
```
* **Cosa verificare:** delega da `root_agent` al sub-agent `google_web_search_specialist` tramite `AgentTool`, esecuzione del grounding live con `google_search` e sintesi in italiano.

### Esempio 3 — Calcolo Sizing e Prezzi Mensili USD (`calculate_agent_sizing` — `FunctionTool`)
```text
Calcola il costo mensile in USD (Prezzo Mese List, 1Y CUD e 3Y CUD) per un agente ADK in produzione con 4.000 richieste al giorno, 1.500 token di input medi, 600 token di output medi, 2 vCPU e 4 GiB di RAM.
```
* **Cosa verificare:** invocazione di `calculate_agent_sizing` e generazione della tabella Markdown:
  | Prezzo Mese List (`$/mo`) | Prezzo Mese 1Y CUD (`$/mo`) | Prezzo Mese 3Y CUD (`$/mo`) |
  | :--- | :--- | :--- |
  | **385.84** | **319.92** | **269.19** |

### Esempio 4 — Invocazione Multi-Tool in Parallelo nello Stesso Turno
```text
Cerca nella knowledge base le best practice di deploy su Agent Engine e calcola contemporaneamente la stima mensile in USD per 10.000 richieste/giorno (2.000 token input, 800 token output) su un'istanza da 4 vCPU e 8 GiB di RAM.
```
* **Cosa verificare:** in **Cloud Trace Explorer** e nel tab **Trace** di `adk web` vedrai due span `execute_tool` distinti (`search_cloud_knowledge` + `calculate_agent_sizing`) all'interno della stessa invocazione.

### Esempio 5 — Verifica dello Stato della Sessione e della Telemetria (`get_session_telemetry_status`)
```text
Mostrami l'ora corrente in Italia, lo stato della telemetria OpenTelemetry e il riepilogo di tutte le ricerche che ho effettuato in questa sessione.
```
* **Cosa verificare:** lettura da `tool_context.state["search_history"]` delle ricerche eseguite nei turni precedenti della sessione corrente e conferma dello stato attivo di Cloud Trace e Cloud Logging.

---

## 7. Come Ispezionare le Tracce e i Log Generati dai Test

- **Cloud Trace Explorer:**
  `https://console.cloud.google.com/traces/explorer?project=<PROJECT_ID>`
  *(Vedrai la gerarchia degli span OpenTelemetry: `invocation` $\rightarrow$ `agent_run [cloud_search_agent]` $\rightarrow$ `call_llm` $\rightarrow$ `execute_tool`)*.
- **Cloud Logging (Logs Explorer):**
  ```bash
  gcloud logging read 'resource.type="aiplatform.googleapis.com/ReasoningEngine"' \
    --project=$(gcloud config get-value project) \
    --limit=20 \
    --format="table(timestamp, textPayload)"
  ```
  *(Vedrai i log strutturati emessi dalle callback: `[ADK-AGENT-START]`, `[ADK-LLM-REQUEST]`, `[ADK-LLM-TOOL-CALL]`, `[ADK-TOOL-START]`, `[ADK-TOOL-END]`, `[ADK-LLM-RESPONSE]`, `[ADK-AGENT-END]`)*.
