# Runbook Fast-Setup: Rilancio Rapido del Workshop Lepida & Demo ADK (`cloud_search_agent`)

Questa guida raccoglie tutti gli script e i passaggi per preparare in pochi secondi il Workshop **Gemini Enterprise** (Moduli 2 & 3) e la **Demo Agente ADK (`cloud_search_agent` — "Cloud Search & Sizing ADK Agent")** su **Google Cloud Shell (`adk web`)**, **Agent Platform Deployment (Vertex AI Agent Engine)** con **Observability/Telemetria OpenTelemetry** e **Agent Registry (A2A)**.

---

## 1. File e Automazioni nel Repository

Tutti gli script rilevano dinamicamente il `PROJECT_ID` (`GOOGLE_CLOUD_PROJECT`, `DEVSHELL_PROJECT_ID` o `gcloud config get-value project`):

- **Setup 1-Click Workshop + Opzione ADK:** [`setup.sh`](./setup.sh) (e [`bootstrap_lepida_lab.sh`](./bootstrap_lepida_lab.sh))
- **Guida Completa Passo-Passo Demo ADK:** [`README_DEMO_ADK_AGENT_PLATFORM.md`](./README_DEMO_ADK_AGENT_PLATFORM.md)
- **Package Agente ADK (`cloud_search_agent`):**
  - [`cloud_search_agent/agent.py`](./cloud_search_agent/agent.py) (`root_agent` con `gemini-2.5-flash`)
  - [`cloud_search_agent/tools.py`](./cloud_search_agent/tools.py) (`search_cloud_knowledge`, `google_web_search_specialist`, `calculate_agent_sizing`, `get_session_telemetry_status`)
  - [`cloud_search_agent/callbacks.py`](./cloud_search_agent/callbacks.py) (6 callback di telemetria e Cloud Logging)
- **Avvio Locale `adk web` in Cloud Shell (porta 8080):** [`setup_and_run_cloudshell.sh`](./setup_and_run_cloudshell.sh)
- **Deploy su Agent Engine + Telemetria + Registrazione A2A in Agent Registry:** [`deploy_adk_agent.py`](./deploy_adk_agent.py)
- **Suite di Test End-to-End sull'Agente Deployato:** [`test_remote_agent.py`](./test_remote_agent.py)
- **Setup Documenti PA & Connettore Gemini Enterprise:** [`setup_workshop_data.py`](./setup_workshop_data.py) e [`setup_ge_datastore.py`](./setup_ge_datastore.py)
- **Pubblicazione Automatica Chat Agent (`Gemini 3.8 Flash`) & 3 Skills:** [`register_ge_agent.py`](./register_ge_agent.py)

---

## 2. Comandi Rapidi da Cloud Shell

### Opzione A — Solo Workshop Partecipanti Gemini Enterprise (~30 secondi)
```bash
git clone https://github.com/marangonic/lepida-gemini-enterprise-workshop.git ~/lepida_workshop && ~/lepida_workshop/setup.sh
```

### Opzione B — Avvio Locale in Cloud Shell della Demo ADK con `adk web` (~30 secondi)
```bash
cd ~/lepida_workshop
./setup_and_run_cloudshell.sh
```
Poi apri **Web Preview -> Preview on port 8080** e seleziona **`cloud_search_agent`**.

### Opzione C — Full Deploy (Gemini Enterprise + Deploy `cloud_search_agent` su Agent Engine + Telemetria + Agent Registry A2A)
```bash
cd ~/lepida_workshop
./setup.sh --with-adk
```
Oppure per eseguire solo il deploy e il test dell'agente ADK:
```bash
cd ~/lepida_workshop
source .venv/bin/activate
python3 deploy_adk_agent.py
python3 test_remote_agent.py
```
