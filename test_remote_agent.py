#!/usr/bin/env python3
"""
Script di test end-to-end dell'agente ADK deployato su Agent Platform Deployment (Agent Engine).
Esegue 4 query di test (Knowledge Search, Google Web Search, Calcolo Costi USD e Stato Telemetria)
tramite sessioni gestite e streaming (`async_stream_query` / `stream_query`), generando
automaticamente gli span in Cloud Trace e i log in Cloud Logging.
"""

import json
import os
import vertexai
from vertexai import agent_engines

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "rootprj-377111")
REGION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")


def load_resource_name() -> str:
    if os.path.exists("deployment_metadata.json"):
        with open("deployment_metadata.json", "r", encoding="utf-8") as f:
            return json.load(f)["remote_agent_runtime_id"]
    if os.path.exists("DEPLOYED_AGENT_RESOURCE.txt"):
        with open("DEPLOYED_AGENT_RESOURCE.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    raise FileNotFoundError("Esegui prima `python3 deploy_agent.py`.")


def main():
    resource_name = load_resource_name()
    print(f"Connessione all'Agente ADK su Agent Engine: {resource_name}")
    vertexai.init(project=PROJECT_ID, location=REGION)
    remote_agent = agent_engines.get(resource_name)

    session = remote_agent.create_session(user_id="demo-user-argolis")
    session_id = session["id"] if isinstance(session, dict) else session.id
    print(f"✅ Sessione creata: {session_id}\n")

    test_prompts = [
        (
            "Test 1 - Search Knowledge Base (FunctionTool)",
            "Cerca nella knowledge base come attivare observability, Cloud Trace e Cloud Logging su un agente ADK deployato su Agent Engine.",
        ),
        (
            "Test 2 - Calcolo Sizing & Prezzi Mensili USD (FunctionTool)",
            "Calcola il costo mensile in USD (List, 1Y CUD, 3Y CUD) per un agente ADK con 4.000 richieste al giorno, 1.500 token di input, 600 token di output, 2 vCPU e 4 GiB di RAM.",
        ),
        (
            "Test 3 - Google Web Search Live (AgentTool + google_search)",
            "Usa la ricerca web per dirmi quali sono le principali caratteristiche di Google Agent Development Kit (ADK) e Vertex AI Agent Engine.",
        ),
        (
            "Test 4 - Stato Sessione & Telemetria (FunctionTool + ToolContext)",
            "Mostrami l'ora corrente in Italia, lo stato della telemetria e il riepilogo delle ricerche che ho appena effettuato in questa sessione.",
        ),
    ]

    for title, prompt in test_prompts:
        print("=" * 80)
        print(f"▶ {title}")
        print(f"Prompt: {prompt}")
        print("-" * 80)
        for event in remote_agent.stream_query(
            user_id="demo-user-argolis",
            session_id=session_id,
            message=prompt,
        ):
            if isinstance(event, dict):
                content = event.get("content", {})
                for part in content.get("parts", []):
                    if "function_call" in part:
                        fc = part["function_call"]
                        print(f"  🛠️ [Tool Call] {fc.get('name')}({fc.get('args')})")
                    if "text" in part and part["text"].strip():
                        print(f"\n🤖 Risposta:\n{part['text'].strip()}\n")


if __name__ == "__main__":
    main()
