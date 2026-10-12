"""
HANDS-ON 1 — STEP 1: Hello ADK & Function Tools Locali
Agente base ADK per i Servizi Territoriali e Bandi Regionali di Lepida ScpA.
"""

import os
import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

load_dotenv()

RETRY_OPTIONS = types.HttpRetryOptions(initial_delay=1, max_delay=3, attempts=30)


def get_current_time() -> dict:
    """
    Restituisce la data e l'ora corrente nel fuso orario italiano (Europe/Rome).
    Utile per verificare se un bando regionale è ancora aperto rispetto alla data odierna.
    """
    now = datetime.datetime.now(ZoneInfo("Europe/Rome"))
    return {"current_time": now.strftime("%Y-%m-%d %H:%M:%S")}


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
        Dizionario con il dettaglio del calcolo finanziario.
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
    }


root_agent = Agent(
    model=Gemini(model=os.getenv("MODEL", "gemini-2.5-flash"), retry_options=RETRY_OPTIONS),
    name="lepida_agent",
    description=(
        "Assistente Digitale per i Servizi Territoriali e i Bandi Regionali di Lepida ScpA."
    ),
    instruction="""
        Sei l'Assistente Digitale di Lepida ScpA per il supporto ai Comuni, alle Unioni di Comuni
        e alle Aziende Sanitarie (AUSL) dell'Emilia-Romagna sui Bandi Regionali di Transizione Digitale.
        Rispondi sempre in lingua italiana con tono professionale, chiaro e strutturato.
        Usa i tool a tua disposizione per verificare la data odierna e per calcolare le quote di
        cofinanziamento regionale e le premialità territoriali.
    """,
    tools=[get_current_time, calcola_cofinanziamento_pa],
)
