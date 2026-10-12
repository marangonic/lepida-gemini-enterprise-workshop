"""
HANDS-ON 1 — STEP 2: Connessione ai Dati con MCP Toolbox for Databases
Agente ADK connesso al server locale MCP Toolbox (`tools.yaml`) su porta 5000.
"""

import os
import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from toolbox_core import ToolboxSyncClient

from .agent_step1_base import get_current_time, calcola_cofinanziamento_pa

load_dotenv()

RETRY_OPTIONS = types.HttpRetryOptions(initial_delay=1, max_delay=3, attempts=30)

# Connessione al server MCP Toolbox for Databases (avviato con ./toolbox --tools-file tools.yaml)
TOOLBOX_URL = os.getenv("MCP_TOOLBOX_URL", "http://127.0.0.1:5000")
toolbox_client = ToolboxSyncClient(TOOLBOX_URL)
mcp_tools = toolbox_client.load_toolset("lepida_data_toolset")

root_agent = Agent(
    model=Gemini(model=os.getenv("MODEL", "gemini-2.5-flash"), retry_options=RETRY_OPTIONS),
    name="lepida_agent",
    description=(
        "Assistente Digitale Lepida ScpA connesso ai dati regionali tramite MCP Toolbox for Databases."
    ),
    instruction="""
        Sei l'Assistente Digitale di Lepida ScpA per il supporto ai Responsabili Unici di Progetto (RUP)
        dei Comuni, delle Unioni di Comuni e delle AUSL dell'Emilia-Romagna.
        Rispondi sempre in italiano in modo chiaro, preciso e ben formattato.

        Hai accesso ai seguenti strumenti:
        1. Tool MCP Toolbox (`cerca_bandi_regionali`, `verifica_pratiche_ente`, `riepilogo_pratiche_per_provincia`)
           per interrogare in tempo reale i bandi e lo stato delle pratiche istruttorie sul database BigQuery `lepida_territorio`.
        2. `calcola_cofinanziamento_pa` per simulare il contributo regionale e le premialità territoriali (+5% montano, +5% Unione, +5% <15k abitanti).
        3. `get_current_time` per conoscere la data e l'ora corrente.
    """,
    tools=[*mcp_tools, get_current_time, calcola_cofinanziamento_pa],
)
