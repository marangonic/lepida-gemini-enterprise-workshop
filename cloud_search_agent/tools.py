"""
Definizione dei Tool secondo lo standard ufficiale Google ADK (Agent Development Kit):
1. `search_cloud_knowledge_tool` (`FunctionTool`): ricerca nel catalogo di architetture,
   documentazione e best practice di Google Cloud, ADK, Agent Engine e Agent Registry,
   salvando la cronologia delle ricerche nello stato della sessione (`tool_context.state`).
2. `google_web_search_tool` (`AgentTool` con `google_search`): sub-agent ADK dedicato
   alla ricerca live sul web tramite Google Search Grounding (incapsulato in `AgentTool`
   per coesistere con i `FunctionTool` personalizzati mantenendo l'Automatic Function Calling).
3. `calculate_agent_sizing_tool` (`FunctionTool`): calcola il sizing e la stima economica
   mensile in USD (`Prezzo Mese List $/mo`, `Prezzo Mese 1Y CUD $/mo`, `Prezzo Mese 3Y CUD $/mo`)
   per un workload Agent Engine + Gemini 2.5.
4. `get_session_telemetry_status_tool` (`FunctionTool`): restituisce data/ora corrente
   (Europe/Rome), stato di telemetria/tracing e riepilogo delle ricerche salvate nella sessione.
"""

import datetime
import os
from typing import Dict, List
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools import AgentTool, FunctionTool, ToolContext, google_search
from google.genai import types

RETRY_OPTIONS = types.HttpRetryOptions(initial_delay=1, max_delay=3, attempts=10)
MODEL_NAME = os.getenv("MODEL", "gemini-2.5-flash")

KNOWLEDGE_BASE: List[Dict[str, str]] = [
    {
        "id": "KB-ADK-001",
        "topic": "Agent Development Kit (ADK) & adk web",
        "category": "adk",
        "summary": (
            "Google ADK è il framework open-source code-first per sviluppare, testare "
            "e orchestrare agenti AI multi-agente in Python. In Cloud Shell si avvia la UI "
            "interattiva locale con `adk web --port 8080 --allow_origins \"*\"` per ispezionare "
            "eventi, stato della sessione, chiamate ai tool e trace in tempo reale."
        ),
        "best_practice": (
            "Definire i tool con FunctionTool(func=...), usare type hint espliciti, "
            "docstring Google-style (Args/Returns) e restituire sempre un dizionario JSON-serializzabile."
        ),
        "doc_url": "https://google.github.io/adk-docs/",
    },
    {
        "id": "KB-AE-002",
        "topic": "Agent Platform Deployment (Vertex AI Agent Engine)",
        "category": "deployment",
        "summary": (
            "Vertex AI Agent Engine (Reasoning Engine) è il runtime completamente gestito "
            "di Agent Platform per il deploy di agenti ADK in produzione con auto-scaling, "
            "gestione nativa delle sessioni (VertexAiSessionService), Memory Bank e Playground integrato."
        ),
        "best_practice": (
            "Incapsulare `root_agent` in `AdkApp(agent=root_agent, enable_tracing=True)` "
            "e distribuire con `vertexai.agent_engines.create(..., env_vars={'GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY': 'true'})`."
        ),
        "doc_url": "https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview",
    },
    {
        "id": "KB-OBS-003",
        "topic": "Observability, Cloud Trace & Cloud Logging per Agenti ADK",
        "category": "observability",
        "summary": (
            "ADK emette span OpenTelemetry gerarchici (`invocation` -> `agent_run` -> "
            "`call_llm` / `execute_tool`) verso Cloud Trace (`telemetry.googleapis.com`) e "
            "log strutturati verso Cloud Logging. Consente di monitorare latenza, token, "
            "payload dei tool ed errori direttamente nella console di Agent Engine e in Trace Explorer."
        ),
        "best_practice": (
            "Abilitare `enable_tracing=True` in AdkApp, impostare `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` "
            "e assegnare al Reasoning Engine Service Agent i ruoli `roles/cloudtrace.agent`, "
            "`roles/telemetry.tracesWriter` e `roles/logging.logWriter`."
        ),
        "doc_url": "https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/manage/tracing",
    },
    {
        "id": "KB-REG-004",
        "topic": "Agent Platform - Agent Registry",
        "category": "registry",
        "summary": (
            "Agent Registry (`agentregistry.googleapis.com`) è il catalogo centralizzato di "
            "governance e discovery per Agenti (ADK/A2A), Server MCP, Endpoint e Skills su Google Cloud. "
            "Scopre automaticamente i Reasoning Engine deployati e permette di registrare "
            "servizi agentici con Agent Card A2A standard."
        ),
        "best_practice": (
            "Verificare la registrazione con `gcloud alpha agent-registry agents list` "
            "e registrare servizi custom/A2A con `gcloud alpha agent-registry services create`."
        ),
        "doc_url": "https://cloud.google.com/agent-registry/overview",
    },
    {
        "id": "KB-SEC-005",
        "topic": "Sicurezza Agentica: Model Armor, IAM & VPC-SC",
        "category": "security",
        "summary": (
            "Protezione degli agenti in produzione tramite Model Armor (prompt injection, "
            "jailbreak, DLP dati sensibili), least-privilege IAM sul Service Account dell'agente "
            "e perimetri VPC Service Controls."
        ),
        "best_practice": (
            "Separare i permessi dei tool usando callback `before_tool_callback` per validare "
            "gli input e tracciare ogni azione nel log di audit."
        ),
        "doc_url": "https://cloud.google.com/security-command-center/docs/model-armor-overview",
    },
]


def search_cloud_knowledge(
    query: str,
    category: str,
    tool_context: ToolContext,
) -> dict:
    """Cerca informazioni tecniche, pattern architetturali e best practice nella Knowledge Base di Google Cloud e ADK.

    Args:
        query: Parole chiave o argomento da cercare (es. 'adk web', 'tracing', 'agent registry', 'deploy', 'security').
        category: Categoria di filtro ('all', 'adk', 'deployment', 'observability', 'registry', 'security').

    Returns:
        Dizionario con lo stato della ricerca, il numero di risultati e le schede tecniche trovate.
    """
    q_lower = query.strip().lower()
    cat_lower = category.strip().lower() if category else "all"
    tokens = [t for t in q_lower.replace(",", " ").split() if len(t) > 1]

    matches = []
    for item in KNOWLEDGE_BASE:
        if cat_lower not in ("all", "", "*") and item["category"] != cat_lower:
            continue
        haystack = f"{item['topic']} {item['category']} {item['summary']} {item['best_practice']}".lower()
        if not tokens or any(tok in haystack for tok in tokens):
            matches.append(item)

    if not matches:
        matches = KNOWLEDGE_BASE[:3]

    history = list(tool_context.state.get("search_history", []))
    history.append(
        {
            "query": query,
            "category": cat_lower,
            "results_count": len(matches),
            "timestamp": datetime.datetime.now(ZoneInfo("Europe/Rome")).strftime("%Y-%m-%d %H:%M:%S"),
        }
    )
    tool_context.state["search_history"] = history
    tool_context.state["last_search_query"] = query

    return {
        "status": "success",
        "query": query,
        "category": cat_lower,
        "match_count": len(matches),
        "results": matches,
    }


def calculate_agent_sizing(
    daily_requests: int,
    avg_input_tokens: int,
    avg_output_tokens: int,
    vcpu_count: int,
    memory_gib: int,
    tool_context: ToolContext,
) -> dict:
    """Calcola la stima di costo mensile in USD ($/mo) per un agente ADK su Vertex AI Agent Engine e Gemini 2.5 Flash.

    Args:
        daily_requests: Numero medio di richieste/conversazioni giornaliere inviate all'agente.
        avg_input_tokens: Numero medio di token di input per richiesta (es. 1500).
        avg_output_tokens: Numero medio di token di output per richiesta (es. 600).
        vcpu_count: Numero di vCPU allocate all'istanza Agent Engine (es. 2 o 4).
        memory_gib: Memoria RAM in GiB allocata all'istanza Agent Engine (es. 4 o 8).

    Returns:
        Dizionario con il dettaglio dei costi mensili in USD (Prezzo Mese List $/mo, 1Y CUD $/mo, 3Y CUD $/mo).
    """
    monthly_requests = max(1, daily_requests) * 30
    monthly_input_m = (monthly_requests * max(100, avg_input_tokens)) / 1_000_000.0
    monthly_output_m = (monthly_requests * max(50, avg_output_tokens)) / 1_000_000.0

    # Stima indicativa Gemini 2.5 Flash + Agent Engine Runtime (730 ore/mese)
    hours_per_month = 730.0
    runtime_vcpu_list = round(max(1, vcpu_count) * hours_per_month * 0.086, 2)
    runtime_mem_list = round(max(1, memory_gib) * hours_per_month * 0.009, 2)
    llm_tokens_list = round((monthly_input_m * 0.30) + (monthly_output_m * 2.50), 2)

    total_list_usd = round(runtime_vcpu_list + runtime_mem_list + llm_tokens_list, 2)
    total_1y_cud_usd = round((runtime_vcpu_list + runtime_mem_list) * 0.72 + llm_tokens_list * 0.90, 2)
    total_3y_cud_usd = round((runtime_vcpu_list + runtime_mem_list) * 0.54 + llm_tokens_list * 0.80, 2)

    estimate = {
        "status": "success",
        "currency": "USD",
        "monthly_requests": monthly_requests,
        "monthly_input_millions_tokens": round(monthly_input_m, 3),
        "monthly_output_millions_tokens": round(monthly_output_m, 3),
        "sizing": {"vcpu": vcpu_count, "memory_gib": memory_gib, "hours_per_month": 730},
        "prezzo_mese_list_usd": total_list_usd,
        "prezzo_mese_1y_cud_usd": total_1y_cud_usd,
        "prezzo_mese_3y_cud_usd": total_3y_cud_usd,
        "breakdown_list_usd": {
            "agent_engine_vcpu_usd_mo": runtime_vcpu_list,
            "agent_engine_memory_usd_mo": runtime_mem_list,
            "gemini_2_5_flash_tokens_usd_mo": llm_tokens_list,
        },
    }
    tool_context.state["last_sizing_estimate"] = estimate
    return estimate


def get_session_telemetry_status(tool_context: ToolContext) -> dict:
    """Restituisce data/ora corrente, configurazione di telemetria/tracing e cronologia della sessione corrente.

    Returns:
        Dizionario con data/ora italiana, progetto GCP, stato di Cloud Trace/Logging e ricerche effettuate.
    """
    now = datetime.datetime.now(ZoneInfo("Europe/Rome"))
    return {
        "status": "success",
        "current_datetime_rome": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "gcp_project": os.getenv("GOOGLE_CLOUD_PROJECT", "rootprj-377111"),
        "gcp_location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        "telemetry": {
            "cloud_trace_enabled": True,
            "cloud_logging_enabled": True,
            "agent_engine_telemetry_env": os.getenv("GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "true"),
            "capture_message_content": os.getenv("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS", "true"),
        },
        "session_state_summary": {
            "total_turns": tool_context.state.get("total_turns", 1),
            "last_search_query": tool_context.state.get("last_search_query"),
            "search_history": tool_context.state.get("search_history", []),
            "has_sizing_estimate": "last_sizing_estimate" in tool_context.state,
        },
    }


# Sub-Agent ADK dedicato a Google Search Grounding incapsulato come AgentTool standard ADK
web_search_subagent = Agent(
    name="google_web_search_specialist",
    model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
    description=(
        "Esegue ricerche live su Internet tramite Google Search per trovare notizie attuali, "
        "eventi, documentazione aggiornata, meteo o informazioni pubbliche sul web."
    ),
    instruction=(
        "Sei uno specialista di ricerca web. Usa SEMPRE il tool `google_search` per cercare "
        "informazioni aggiornate e verificate su Internet e rispondi in italiano sintetizzando "
        "i fatti principali e le fonti trovate."
    ),
    tools=[google_search],
)

# Esportazione dei Tool secondo lo standard ADK (FunctionTool e AgentTool)
search_cloud_knowledge_tool = FunctionTool(func=search_cloud_knowledge)
calculate_agent_sizing_tool = FunctionTool(func=calculate_agent_sizing)
get_session_telemetry_status_tool = FunctionTool(func=get_session_telemetry_status)
google_web_search_tool = AgentTool(agent=web_search_subagent)

ALL_AGENT_TOOLS = [
    search_cloud_knowledge_tool,
    google_web_search_tool,
    calculate_agent_sizing_tool,
    get_session_telemetry_status_tool,
]
