#!/usr/bin/env python3
"""
Deploy deterministico e indipendente dalla versione CLI di `lepida_agent`
su Vertex AI Agent Engine (`us-central1`) utilizzando `vertexai.agent_engines.create`
con `staging_bucket=gs://<PROJECT_ID>-lepida-comuni-er`.
Salva automaticamente il Resource Name in `IL_MIO_AGENTE_ADK.txt`.
"""

import os
import subprocess
import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

from lepida_agent.agent import root_agent


def _detect_project_id() -> str:
    for env_key in ("GOOGLE_CLOUD_PROJECT", "DEVSHELL_PROJECT_ID", "GCLOUD_PROJECT"):
        val = os.environ.get(env_key, "").strip()
        if val:
            return val
    res = subprocess.run(
        ["gcloud", "config", "get-value", "project"],
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def main():
    os.environ.pop("MCP_TOOLBOX_URL", None)
    project_id = _detect_project_id()
    region = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
    bucket_name = os.environ.get("LEPIDA_BUCKET_NAME", f"{project_id}-lepida-comuni-er").strip()
    staging_bucket = f"gs://{bucket_name}"

    print(f"  -> Inizializzazione Vertex AI ({project_id}, {region}, staging={staging_bucket})...")
    vertexai.init(project=project_id, location=region, staging_bucket=staging_bucket)

    adk_app = AdkApp(agent=root_agent, enable_tracing=True)
    with open("lepida_agent/requirements.txt", "r", encoding="utf-8") as f:
        reqs = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print("  -> Deploy di `Assistente Territoriale Lepida` su Vertex AI Agent Engine in corso...")
    remote_agent = agent_engines.create(
        agent_engine=adk_app,
        display_name="Assistente Territoriale Lepida",
        description="Agente ADK di Lepida ScpA per Bandi Regionali, Pratiche Enti su BigQuery e Calcolo Cofinanziamenti.",
        requirements=reqs,
        extra_packages=["lepida_agent"],
    )
    res_name = remote_agent.resource_name
    with open("IL_MIO_AGENTE_ADK.txt", "w", encoding="utf-8") as out:
        out.write(res_name + "\n")
    print(f"  -> ✅ Reasoning Engine creato con successo: {res_name}")


if __name__ == "__main__":
    main()
