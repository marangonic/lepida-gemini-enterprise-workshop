#!/usr/bin/env python3
"""
Deploy completo di `cloud_search_agent` ("Cloud Search & Sizing ADK Agent")
su Agent Platform Deployment (Vertex AI Agent Engine, `us-central1`):
1. Attiva Cloud Trace, Cloud Logging e OpenTelemetry GenAI Capture (`enable_tracing=True`
   + `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`) e abilita il Playground.
2. Inietta `a2a_agent_card` in `spec.classMethods` (`async_create_session`) sul Reasoning Engine
   per popolare `spec.agentCard` mantenendo tutti i metodi ADK del Playground.
3. Registra e aggiorna l'agente con Agent Card A2A completa (`A2A_AGENT_CARD`, 3 skills,
   esempi, tag ed endpoint `/a2a`) in Agent Platform -> Agent Registry (`global` e `us-central1`).
4. Salva il Resource Name in `deployment_metadata.json`, `DEPLOYED_AGENT_RESOURCE.txt`
   e `IL_MIO_AGENTE_ADK.txt`.
"""

import datetime
import json
import os
import subprocess
import time
import urllib.error
import urllib.request

import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

from cloud_search_agent.agent import root_agent

DISPLAY_NAME = "Cloud Search & Sizing ADK Agent"
SERVICE_ID = "cloud-search-adk-agent"


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
    return res.stdout.strip() or "rootprj-377111"


def _ensure_staging_bucket(project_id: str, region: str) -> str:
    explicit = os.environ.get("STAGING_BUCKET", "").strip()
    if explicit:
        return explicit if explicit.startswith("gs://") else f"gs://{explicit}"
    bucket_name = f"{project_id}-agent-engine-staging"
    bucket_uri = f"gs://{bucket_name}"
    chk = subprocess.run(
        ["gcloud", "storage", "buckets", "describe", bucket_uri, f"--project={project_id}"],
        capture_output=True,
        text=True,
    )
    if chk.returncode != 0:
        subprocess.run(
            [
                "gcloud",
                "storage",
                "buckets",
                "create",
                bucket_uri,
                f"--project={project_id}",
                f"--location={region}",
            ],
            check=False,
        )
    return bucket_uri


def _get_access_token() -> str:
    for cmd in (
        ["gcloud", "auth", "application-default", "print-access-token"],
        ["gcloud", "auth", "print-access-token"],
    ):
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    return ""


def _build_agent_card(a2a_url: str, streaming: bool = True) -> dict:
    return {
        "name": DISPLAY_NAME,
        "description": (
            "Agente ADK di esempio su Agent Engine con tool standard ADK: "
            "search_cloud_knowledge (FunctionTool), google_web_search_specialist (AgentTool + google_search), "
            "calculate_agent_sizing (FunctionTool) e get_session_telemetry_status (FunctionTool)."
        ),
        "version": "1.0.0",
        "protocolVersion": "0.3.0",
        "preferredTransport": "HTTP+JSON",
        "url": a2a_url,
        "defaultInputModes": ["text/plain"],
        "defaultOutputModes": ["application/json", "text/plain"],
        "capabilities": {"streaming": streaming},
        "supportsAuthenticatedExtendedCard": True,
        "skills": [
            {
                "id": "cloud_knowledge_search",
                "name": "Ricerca Knowledge Base Cloud & ADK",
                "description": "Cerca best practice e documentazione su ADK, Agent Engine, Observability e Agent Registry.",
                "tags": ["adk", "search", "cloud", "agent-platform"],
                "examples": [
                    "Cerca nella knowledge base come funziona l'observability e il tracing in ADK.",
                    "Quali sono le best practice per fare il deploy su Vertex AI Agent Engine?",
                ],
            },
            {
                "id": "google_web_search",
                "name": "Ricerca Web Live con Google Search",
                "description": "Esegue ricerche live su Internet tramite Google Search Grounding.",
                "tags": ["google-search", "web", "live"],
                "examples": [
                    "Cerca sul web le ultime novità su Google Cloud ADK e Vertex AI Agent Engine.",
                ],
            },
            {
                "id": "cloud_sizing_calculator",
                "name": "Calcolo Sizing e Costi Mensili USD ($/mo)",
                "description": "Calcola Prezzo Mese List ($/mo), 1Y CUD ($/mo) e 3Y CUD ($/mo) per Agent Engine e Gemini.",
                "tags": ["pricing", "sizing", "usd", "cud"],
                "examples": [
                    "Calcola il costo mensile USD per un agente con 4000 richieste/giorno, 1500 input token, 600 output token, 2 vCPU e 4 GiB RAM.",
                ],
            },
        ],
    }


def _patch_reasoning_engine_a2a_card(project_id: str, region: str, resource_name: str):
    """Inietta `a2a_agent_card` in `async_create_session` per popolare `spec.agentCard`."""
    token = _get_access_token()
    if not token:
        return
    base_url = f"https://{region}-aiplatform.googleapis.com/v1beta1"
    a2a_url = f"{base_url}/{resource_name}/a2a"

    def _api(method: str, url: str, body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("X-Goog-User-Project", project_id)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="replace")

    st, current_re = _api("GET", f"{base_url}/{resource_name}")
    if st != 200 or not isinstance(current_re, dict):
        return
    spec = current_re.get("spec", {})
    class_methods = spec.get("classMethods", [])
    card_dict = _build_agent_card(a2a_url, streaming=False)
    card_json_str = json.dumps(card_dict)

    for cm in class_methods:
        if cm.get("name") == "async_create_session":
            cm["a2a_agent_card"] = card_json_str

    patch_body = {
        "displayName": current_re.get("displayName", DISPLAY_NAME),
        "description": current_re.get("description", card_dict["description"]),
        "spec": {
            "classMethods": class_methods,
            "agentFramework": spec.get("agentFramework", "google-adk"),
        },
    }
    st_p, resp_p = _api(
        "PATCH",
        f"{base_url}/{resource_name}?updateMask=spec.class_methods",
        patch_body,
    )
    if st_p == 200 and isinstance(resp_p, dict) and "name" in resp_p:
        op_name = resp_p["name"]
        for _ in range(30):
            _, op_res = _api("GET", f"{base_url}/{op_name}")
            if isinstance(op_res, dict) and op_res.get("done"):
                print("  -> ✅ `spec.agentCard` popolato sul Reasoning Engine.")
                break
            time.sleep(2)


def register_in_agent_registry(project_id: str, region: str, resource_name: str):
    """Registra il servizio A2A in Agent Registry (`global` e `us-central1`) e verifica l'auto-discovery."""
    a2a_url = f"https://{region}-aiplatform.googleapis.com/v1beta1/{resource_name}/a2a"
    agent_card = _build_agent_card(a2a_url, streaming=True)

    for loc in ("global", region):
        subprocess.run(
            [
                "gcloud",
                "alpha",
                "agent-registry",
                "services",
                "delete",
                SERVICE_ID,
                f"--location={loc}",
                f"--project={project_id}",
                "--quiet",
            ],
            capture_output=True,
            text=True,
        )
        cmd_create = [
            "gcloud",
            "alpha",
            "agent-registry",
            "services",
            "create",
            SERVICE_ID,
            f"--location={loc}",
            f"--project={project_id}",
            f"--display-name={DISPLAY_NAME}",
            "--description=Agente ADK con Search Tool, Google Search Grounding, Sizing USD e Telemetria OpenTelemetry",
            "--agent-spec-type=a2a-agent-card",
            f"--agent-spec-content={json.dumps(agent_card)}",
        ]
        res = subprocess.run(cmd_create, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  -> ✅ Registrato servizio A2A '{SERVICE_ID}' in Agent Registry (location={loc})")
        else:
            print(f"  -> ℹ️ Output Agent Registry ({loc}): {res.stderr.strip()}")

    time.sleep(3)
    print(f"=== 4. Verifica Agenti presenti in Agent Registry ({region}) ===")
    list_res = subprocess.run(
        [
            "gcloud",
            "alpha",
            "agent-registry",
            "agents",
            "list",
            f"--project={project_id}",
            f"--location={region}",
            f'--filter=displayName:"{DISPLAY_NAME}"',
        ],
        capture_output=True,
        text=True,
    )
    print(list_res.stdout or list_res.stderr)


def main():
    project_id = _detect_project_id()
    region = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    staging_bucket = _ensure_staging_bucket(project_id, region)

    print(f"=== 1. Inizializzazione Vertex AI ({project_id} | {region} | {staging_bucket}) ===")
    vertexai.init(project=project_id, location=region, staging_bucket=staging_bucket)

    adk_app = AdkApp(agent=root_agent, enable_tracing=True)
    req_file = "cloud_search_agent/requirements.txt" if os.path.exists("cloud_search_agent/requirements.txt") else "requirements.txt"
    with open(req_file, "r", encoding="utf-8") as f:
        reqs = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    env_vars = {
        "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
        "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
        "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS": "true",
    }

    print(f"=== 2. Deploy di '{DISPLAY_NAME}' su Agent Platform Deployment (Agent Engine) ===")
    remote_agent = agent_engines.create(
        agent_engine=adk_app,
        display_name=DISPLAY_NAME,
        description=(
            "Agente ADK standard con tool di ricerca Knowledge Base (FunctionTool), "
            "Google Search live (AgentTool), calcolo sizing/costi USD e Observability/Telemetria."
        ),
        requirements=reqs,
        extra_packages=["cloud_search_agent"],
        env_vars=env_vars,
    )

    resource_name = remote_agent.resource_name
    engine_id = resource_name.split("/")[-1]
    print(f"  -> ✅ Reasoning Engine creato con successo: {resource_name}")

    metadata = {
        "remote_agent_runtime_id": resource_name,
        "engine_id": engine_id,
        "project_id": project_id,
        "location": region,
        "display_name": DISPLAY_NAME,
        "deployment_target": "agent_runtime",
        "telemetry_enabled": True,
        "tracing_enabled": True,
        "playground_url": (
            f"https://console.cloud.google.com/vertex-ai/agents/agent-engines/"
            f"locations/{region}/agent-engines/{engine_id}/playground?project={project_id}"
        ),
        "a2a_endpoint_url": f"https://{region}-aiplatform.googleapis.com/v1beta1/{resource_name}/a2a",
        "deployment_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    with open("deployment_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    for out_file in ("DEPLOYED_AGENT_RESOURCE.txt", "IL_MIO_AGENTE_ADK.txt"):
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(resource_name + "\n")

    print("=== 3. Configurazione A2A Card & Registrazione in Agent Registry ===")
    _patch_reasoning_engine_a2a_card(project_id, region, resource_name)
    register_in_agent_registry(project_id, region, resource_name)


if __name__ == "__main__":
    main()
