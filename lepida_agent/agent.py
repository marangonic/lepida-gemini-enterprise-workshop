"""
Agente ADK completo per Lepida ScpA ("Assistente Digitale Servizi Territoriali e Bandi Regionali").
- Supporta il caricamento dinamico dei tool da MCP Toolbox for Databases (se MCP_TOOLBOX_URL è impostato in locale per la demo `adk web`)
- Integra i tool nativi Python (`esegui_query_bigquery`, `calcola_cofinanziamento_pa`, `get_current_time`)
  che istanziano il client BigQuery a runtime sul progetto reale (`PROJECT_ID`), evitando qualsiasi
  leakage delle credenziali della VM Cloud Shell durante il deploy su Vertex AI Agent Engine.
"""

import datetime
import logging
import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

import google.auth
from google.cloud import bigquery
import google.cloud.logging
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from .callback_logging import log_query_to_model, log_model_response

load_dotenv()

_, adc_project = google.auth.default()
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("DEVSHELL_PROJECT_ID") or adc_project or ""
MODEL_NAME = os.getenv("MODEL", "gemini-2.5-flash")

try:
    cloud_logging_client = google.cloud.logging.Client(project=PROJECT_ID)
    cloud_logging_client.setup_logging()
except Exception:
    pass

RETRY_OPTIONS = types.HttpRetryOptions(initial_delay=1, max_delay=3, attempts=30)


def get_current_time() -> dict:
    """
    Restituisce la data e l'ora corrente nel fuso orario italiano (Europe/Rome).
    Utile per verificare le scadenze dei bandi e compilare la data_presentazione di nuove pratiche.
    """
    now = datetime.datetime.now(ZoneInfo("Europe/Rome"))
    return {"current_time": now.strftime("%Y-%m-%d %H:%M:%S"), "current_date": now.strftime("%Y-%m-%d")}


def calcola_cofinanziamento_pa(
    importo_progetto_eur: float,
    quota_base_pct: int,
    comune_montano: bool = False,
    unione_comuni: bool = False,
    sotto_15000_abitanti: bool = False,
) -> dict:
    """
    Calcola la percentuale effettiva di cofinanziamento regionale a fondo perduto
    e la quota residua a carico dell'Ente pubblico secondo le Linee Guida Lepida 2026.

    Args:
        importo_progetto_eur: Costo complessivo del progetto presentato dall'Ente in Euro.
        quota_base_pct: Percentuale base prevista dal bando (es. 80, 85, 90).
        comune_montano: True se l'Ente è situato in zona montana o area interna (+5%).
        unione_comuni: True se la domanda è presentata in forma associata da un'Unione di Comuni (+5%).
        sotto_15000_abitanti: True se il Comune ha meno di 15.000 abitanti (+5%).

    Returns:
        Dizionario con il dettaglio del calcolo finanziario e delle 3 tranche (40%, 30%, 30%).
    """
    bonus_pct = 0
    if comune_montano:
        bonus_pct += 5
    if unione_comuni:
        bonus_pct += 5
    if sotto_15000_abitanti:
        bonus_pct += 5

    quota_finale_pct = min(95, quota_base_pct + bonus_pct)
    contributo_regionale_eur = round(importo_progetto_eur * (quota_finale_pct / 100.0), 2)
    quota_ente_eur = round(importo_progetto_eur - contributo_regionale_eur, 2)

    return {
        "importo_progetto_eur": importo_progetto_eur,
        "quota_base_pct": quota_base_pct,
        "bonus_premialita_pct": bonus_pct,
        "quota_finale_applicata_pct": quota_finale_pct,
        "contributo_regionale_fondo_perduto_eur": contributo_regionale_eur,
        "quota_co_finanziamento_a_carico_ente_eur": quota_ente_eur,
        "tranche_1_anticipo_40pct_eur": round(contributo_regionale_eur * 0.40, 2),
        "tranche_2_sal_30pct_eur": round(contributo_regionale_eur * 0.30, 2),
        "tranche_3_saldo_30pct_eur": round(contributo_regionale_eur * 0.30, 2),
    }


def esegui_query_bigquery(query_sql: str) -> dict:
    """
    Esegue una query SQL (SELECT o INSERT/UPDATE) sul dataset BigQuery `lepida_territorio`
    del progetto GCP corrente e restituisce le righe risultanti o l'esito dell'operazione.

    Args:
        query_sql: Query SQL standard BigQuery (es. SELECT ... FROM `lepida_territorio.bandi_regionali`
                   oppure INSERT INTO `lepida_territorio.pratiche_enti` ...).
    """
    creds, runtime_proj = google.auth.default()
    target_project = PROJECT_ID or runtime_proj
    if hasattr(creds, "with_quota_project") and target_project:
        creds = creds.with_quota_project(target_project)
    client = bigquery.Client(project=target_project, credentials=creds)
    job = client.query(query_sql)
    result = job.result()
    rows = [dict(row.items()) for row in result]
    for r in rows:
        for k, v in list(r.items()):
            if isinstance(v, (datetime.date, datetime.datetime)):
                r[k] = v.isoformat()
    return {
        "status": "SUCCESS",
        "project_id": target_project,
        "row_count": len(rows),
        "num_dml_affected_rows": job.num_dml_affected_rows,
        "rows": rows,
    }


agent_tools = [esegui_query_bigquery, get_current_time, calcola_cofinanziamento_pa]
mcp_url = os.getenv("MCP_TOOLBOX_URL")
if mcp_url:
    try:
        from toolbox_core import ToolboxSyncClient
        tb_client = ToolboxSyncClient(mcp_url)
        agent_tools.extend(tb_client.load_toolset("lepida_data_toolset"))
    except Exception as e:
        logging.warning("MCP Toolbox non raggiungibile su %s (%s), uso esegui_query_bigquery.", mcp_url, e)


root_agent = Agent(
    model=Gemini(model=MODEL_NAME, retry_options=RETRY_OPTIONS),
    name="lepida_agent",
    description=(
        "Assistente Digitale di Lepida ScpA per l'analisi dei Bandi Regionali, "
        "la verifica e l'inserimento delle pratiche degli Enti su BigQuery e il calcolo dei cofinanziamenti."
    ),
    instruction=f"""
        Sei l'Assistente Digitale ufficiale di Lepida ScpA per i Servizi Territoriali e i Bandi Regionali
        dell'Emilia-Romagna. Rispondi sempre in italiano in modo chiaro, accurato e ben strutturato
        (utilizzando elenchi puntati o tabelle Markdown quando mostri più record).

        Quando interroghi o aggiorni i dati su BigQuery tramite `esegui_query_bigquery`, utilizza SEMPRE:
        - Progetto GCP: `{PROJECT_ID}`
        - Dataset BigQuery: `lepida_territorio`
        - Tabelle disponibili nel dataset `{PROJECT_ID}.lepida_territorio`:
          1. `bandi_regionali`: contiene l'elenco dei bandi regionali gestiti da Lepida
             (`id_bando`, `titolo`, `ambito`, `budget_totale_eur`, `contributo_massimo_eur`,
             `quota_cofinanziamento_base_pct`, `stato`, `data_scadenza`, `ente_gestore`, `descrizione`).
          2. `pratiche_enti`: contiene le domande e pratiche presentate da Comuni, Unioni e AUSL
             (`id_pratica`, `id_bando`, `ente_richiedente`, `provincia`, `importo_richiesto_eur`,
             `punteggio_tecnico`, `stato_pratica`, `data_presentazione`, `referente_email`, `note_istruttore`).

        Quando l'utente chiede di simulare o calcolare il contributo a fondo perduto per un Ente,
        usa sempre il tool `calcola_cofinanziamento_pa`.
        Quando l'utente chiede di registrare una nuova pratica nella tabella `pratiche_enti`,
        verifica prima la data odierna con `get_current_time` se non specificata ed esegui una query
        SQL `INSERT INTO \`{PROJECT_ID}.lepida_territorio.pratiche_enti\`` tramite `esegui_query_bigquery`.
    """,
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    tools=agent_tools,
)
