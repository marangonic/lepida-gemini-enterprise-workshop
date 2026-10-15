"""
Callback di Observability, Telemetria e Cloud Logging per l'agente ADK.
Traccia in modo strutturato su Cloud Logging e OpenTelemetry spans:
- Avvio/fine invocazione agente (before_agent_callback / after_agent_callback)
- Prompt inviati al modello LLM e risposte/tool call (before_model_callback / after_model_callback)
- Esecuzione dei singoli tool ADK con argomenti ed esito (before_tool_callback / after_tool_callback)
"""

import logging
import time
from typing import Any, Dict, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger("adk_observability")
logger.setLevel(logging.INFO)


def before_agent_log(callback_context: CallbackContext) -> Optional[Any]:
    """Inizializza lo stato di telemetria della sessione e registra l'inizio del turno."""
    state = callback_context.state
    state["turn_start_ts"] = time.time()
    state["total_turns"] = state.get("total_turns", 0) + 1
    if "search_history" not in state:
        state["search_history"] = []
    logger.info(
        "[ADK-AGENT-START] agent=%s invocation_id=%s turn=%s",
        callback_context.agent_name,
        getattr(callback_context, "invocation_id", "n/a"),
        state["total_turns"],
    )
    return None


def after_agent_log(callback_context: CallbackContext) -> Optional[Any]:
    """Registra la durata complessiva del turno dell'agente."""
    state = callback_context.state
    start_ts = state.get("turn_start_ts")
    elapsed_ms = round((time.time() - start_ts) * 1000, 2) if start_ts else 0.0
    logger.info(
        "[ADK-AGENT-END] agent=%s invocation_id=%s elapsed_ms=%s",
        callback_context.agent_name,
        getattr(callback_context, "invocation_id", "n/a"),
        elapsed_ms,
    )
    return None


def log_query_to_model(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Registra l'ultimo messaggio utente inviato al modello Gemini."""
    if llm_request.contents and llm_request.contents[-1].role == "user":
        for part in llm_request.contents[-1].parts:
            if getattr(part, "text", None):
                logger.info(
                    "[ADK-LLM-REQUEST] agent=%s prompt=%s",
                    callback_context.agent_name,
                    part.text[:500],
                )
    return None


def log_model_response(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Registra la risposta testuale o le function call generate dal modello Gemini."""
    if llm_response.content and llm_response.content.parts:
        for part in llm_response.content.parts:
            if getattr(part, "text", None):
                logger.info(
                    "[ADK-LLM-RESPONSE] agent=%s text=%s",
                    callback_context.agent_name,
                    part.text[:500],
                )
            elif getattr(part, "function_call", None):
                logger.info(
                    "[ADK-LLM-TOOL-CALL] agent=%s tool_name=%s args=%s",
                    callback_context.agent_name,
                    part.function_call.name,
                    dict(part.function_call.args) if part.function_call.args else {},
                )
    return None


def before_tool_log(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict[str, Any]]:
    """Registra l'invocazione di un tool ADK prima della sua esecuzione."""
    logger.info(
        "[ADK-TOOL-START] agent=%s tool=%s args=%s",
        tool_context.agent_name,
        tool.name,
        args,
    )
    return None


def after_tool_log(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext,
    tool_response: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Registra il risultato restituito da un tool ADK."""
    logger.info(
        "[ADK-TOOL-END] agent=%s tool=%s status=%s",
        tool_context.agent_name,
        tool.name,
        tool_response.get("status", "completed") if isinstance(tool_response, dict) else "ok",
    )
    return None
