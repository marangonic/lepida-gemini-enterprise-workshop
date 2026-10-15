"""
Definizione dell'agente principale `root_agent` con standard Google ADK:
- Modello: `gemini-2.5-flash` su Vertex AI
- Tool ADK standard (`FunctionTool` e `AgentTool` con `google_search`)
- Callback complete di Observability & Cloud Logging (`before_agent`, `after_agent`,
  `before_model`, `after_model`, `before_tool`, `after_tool`)
- Pronto per esecuzione locale in Cloud Shell con `adk web` e per deploy su
  Agent Platform Deployment (Vertex AI Agent Engine) + Agent Registry.
"""

import logging
import os
from dotenv import load_dotenv
import google.auth
import google.cloud.logging
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from .callbacks import (
    after_agent_log,
    after_tool_log,
    before_agent_log,
    before_tool_log,
    log_model_response,
    log_query_to_model,
)
from .tools import ALL_AGENT_TOOLS

load_dotenv()

try:
    _, adc_project = google.auth.default()
except Exception:
    adc_project = None

PROJECT_ID = (
    os.getenv("GOOGLE_CLOUD_PROJECT")
    or os.getenv("DEVSHELL_PROJECT_ID")
    or adc_project
    or "rootprj-377111"
)
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
MODEL_NAME = os.getenv("MODEL", "gemini-2.5-flash")

# Inizializza l'integrazione nativa con Cloud Logging
try:
    cloud_logging_client = google.cloud.logging.Client(project=PROJECT_ID)
    cloud_logging_client.setup_logging(log_level=logging.INFO)
except Exception:
    logging.basicConfig(level=logging.INFO)

RETRY_OPTIONS = types.HttpRetryOptions(initial_delay=1, max_delay=3, attempts=10)

root_agent = Agent(
    name="cloud_search_agent",
    model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
    description=(
        "Agente ADK di esempio per Google Cloud Agent Platform con tool di ricerca "
        "Knowledge Base (FunctionTool), ricerca web live (Google Search AgentTool), "
        "calcolo sizing/costi USD e telemetria/observability OpenTelemetry."
    ),
    instruction="""Sei l'Assistente Cloud & Search di esempio sviluppato con Google Agent Development Kit (ADK)
sul progetto Argolis `rootprj-377111`. Rispondi sempre in italiano in modo chiaro, strutturato e professionale.

Hai a disposizione 4 tool definiti secondo lo standard ADK:
1. `search_cloud_knowledge`: usalo quando l'utente chiede informazioni su ADK, `adk web`,
   Agent Platform Deployment (Vertex AI Agent Engine), Observability/Cloud Trace/Logging,
   Agent Registry o sicurezza (Model Armor). Specifica sempre `query` e `category` ('all', 'adk', 'deployment', 'observability', 'registry', 'security').
2. `google_web_search_specialist`: usalo quando l'utente chiede notizie attuali, informazioni live dal web,
   eventi, meteo o ricerche generiche su Internet tramite Google Search.
3. `calculate_agent_sizing`: usalo quando l'utente chiede una stima dei costi mensili (sempre in USD $/mo
   con Prezzo Mese List, 1Y CUD e 3Y CUD) o il dimensionamento (vCPU, RAM, token) per un agente su Agent Engine.
4. `get_session_telemetry_status`: usalo quando l'utente chiede l'ora attuale, lo stato di telemetria/tracing
   o il riepilogo delle ricerche effettuate nella sessione corrente.

Quando mostri risultati di costo, presenta sempre una tabella Markdown con le colonne:
- **Prezzo Mese List (`$/mo`)**
- **Prezzo Mese 1Y CUD (`$/mo`)**
- **Prezzo Mese 3Y CUD (`$/mo`)**
""",
    tools=ALL_AGENT_TOOLS,
    before_agent_callback=before_agent_log,
    after_agent_callback=after_agent_log,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    before_tool_callback=before_tool_log,
    after_tool_callback=after_tool_log,
)
