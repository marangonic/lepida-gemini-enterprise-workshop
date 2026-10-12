#!/usr/bin/env python3
"""
Configura e pubblica automaticamente il Chat Agent Multi-Livello (con Gemini 3.8 Flash)
e le 3 Skills nell'App Gemini Enterprise (`lepida-comuni-er-app`):
1. Abilita le feature `no-code-agent-builder` (Chat Agent) e `skills` sull'Engine Gemini Enterprise.
2. Crea e condivide (`ALL_USERS`) le 3 Skills operative nella sezione `Skills` della Web App:
   - `Simulazione Punteggio Bando Fibra 10 Gbps`
   - `Checklist Migrazione Cloud e Sicurezza ACN`
   - `Generatore Bozza Determina Dirigenziale PA`
3. Crea, pubblica (`:deployLowCode`) e condivide (`ALL_USERS`) il Chat Agent Multi-Livello
   `Consulente Digitale Comuni ER e Servizi Lepida` con modello `Gemini 3.8 Flash` (`gemini-3.8-flash`):
   - Livello 0 (`SequentialAgentNode`): Pipeline a 2 fasi (Fase 1 -> Fase 2)
   - Livello 1 (Coordinatori Tematici Blu con `gemini-3.8-flash`):
     * `Fase 1 - Istruttoria Bandi e Cloud`
     * `Fase 2 - Atti PA e Benchmark Comuni`
   - Livello 2 (Sub-Agents Specialisti Viola con `gemini-3.8-flash`):
     * Sotto Fase 1: `Specialista Bando Fibra 10 Gbps`, `Specialista Cloud PA e Sicurezza ACN`
     * Sotto Fase 2: `Redattore Determine e Convenzioni PA`, `Analista TARI e Benchmark Comuni ER`
4. (Opzionale, se è presente un Reasoning Engine ADK) Registra anche l'Agente ADK senza duplicati.
"""

import argparse
import json
import os
import subprocess
import urllib.error
import urllib.parse
import urllib.request


REQUIRED_ENGINE_FEATURES = {
    "agent-gallery": "FEATURE_STATE_ON",
    "no-code-agent-builder": "FEATURE_STATE_ON",
    "prompt-gallery": "FEATURE_STATE_ON",
    "model-selector": "FEATURE_STATE_ON",
    "agent-sharing": "FEATURE_STATE_ON",
    "agent-sharing-without-admin-approval": "FEATURE_STATE_ON",
    "skills": "FEATURE_STATE_ON",
    "skill-sharing": "FEATURE_STATE_ON",
    "skill-sharing-without-admin-approval": "FEATURE_STATE_ON",
    "workflow-agents": "FEATURE_STATE_ON",
    "workflow-agent-sharing": "FEATURE_STATE_ON",
    "workflow-agent-sharing-without-admin-approval": "FEATURE_STATE_ON",
}


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


def _detect_project_number(project_id: str) -> str:
    res = subprocess.run(
        ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def get_token() -> str:
    res = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def api_request(method: str, url: str, token: str, project_id: str, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-Goog-User-Project", project_id)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def discover_reasoning_engine_optional(project_id: str, token: str, region: str = "us-central1") -> str:
    url = f"https://{region}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{region}/reasoningEngines"
    status, resp = api_request("GET", url, token, project_id)
    if status != 200 or not isinstance(resp, dict):
        return ""
    engines = resp.get("reasoningEngines", [])
    if not engines:
        return ""
    engines.sort(key=lambda x: x.get("createTime", ""), reverse=True)
    return engines[0].get("name", "")


def discover_ge_engine_id(project_id: str, token: str) -> str:
    url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines"
    status, resp = api_request("GET", url, token, project_id)
    if status != 200 or not isinstance(resp, dict):
        raise RuntimeError(f"Impossibile elencare gli Engine Gemini Enterprise ({status}): {resp}")
    engines = resp.get("engines", [])
    for eng in engines:
        name = eng.get("name", "")
        disp = eng.get("displayName", "")
        if "lepida" in name.lower() or "lepida" in disp.lower():
            return name.split("/")[-1]
    if engines:
        return engines[0]["name"].split("/")[-1]
    raise RuntimeError("Nessuna App Gemini Enterprise trovata. Esegui prima `python3 setup_ge_datastore.py`.")


def ensure_engine_features(project_id: str, engine_id: str, token: str):
    eng_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/collections/default_collection/engines/{engine_id}"
    st, eng = api_request("GET", eng_url, token, project_id)
    feats = dict(eng.get("features", {})) if st == 200 and isinstance(eng, dict) else {}
    feats.update(REQUIRED_ENGINE_FEATURES)
    st_p, _ = api_request("PATCH", f"{eng_url}?updateMask=features", token, project_id, {"features": feats})
    print(f"  -> Feature Chat Agent (`no-code-agent-builder`) e `skills` attive su `{engine_id}` (HTTP {st_p}).")


def main():
    parser = argparse.ArgumentParser(description="Pubblica il Chat Agent Multi-Livello (Gemini 3.8 Flash) e le 3 Skills su Gemini Enterprise.")
    parser.add_argument("--reasoning-engine", default=os.environ.get("REASONING_ENGINE_RES", ""))
    parser.add_argument("--no-adk", action="store_true", help="Non registrare l'Agente ADK")
    parser.add_argument("--adk-only", action="store_true", help="Registra solo l'Agente ADK")
    args = parser.parse_args()

    project_id = _detect_project_id()
    project_number = _detect_project_number(project_id)
    token = get_token()

    engine_id = discover_ge_engine_id(project_id, token)
    print(f"[Info] Project: {project_id} ({project_number}) | Engine ID: {engine_id}")

    # 1. Abilita le feature Chat Agent e Skills sull'Engine
    ensure_engine_features(project_id, engine_id, token)

    agents_url = (
        f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}"
        f"/locations/global/collections/default_collection/engines/{engine_id}"
        f"/assistants/default_assistant/agents"
    )

    st_list, resp_list = api_request("GET", agents_url, token, project_id)
    existing_agents = resp_list.get("agents", []) if st_list == 200 and isinstance(resp_list, dict) else []

    # 2. Se esiste un Reasoning Engine ADK (e non è stato passato --no-adk), registralo senza duplicati
    adk_agent_resource = ""
    reasoning_engine = "" if args.no_adk else (args.reasoning_engine.strip() or discover_reasoning_engine_optional(project_id, token))
    if reasoning_engine:
        for ag in existing_agents:
            ag_name = ag.get("name", "")
            disp = ag.get("displayName", "")
            if "adkAgentDefinition" in ag or disp == "Assistente Bandi e Pratiche Lepida":
                api_request("DELETE", f"https://discoveryengine.googleapis.com/v1alpha/{ag_name}", token, project_id)
        adk_body = {
            "displayName": "Assistente Bandi e Pratiche Lepida",
            "description": (
                "Agente ADK su Vertex AI Agent Engine per interrogare i Bandi Regionali, "
                "verificare o inserire pratiche degli Enti su BigQuery e calcolare i cofinanziamenti."
            ),
            "adkAgentDefinition": {
                "toolSettings": {
                    "toolDescription": (
                        "Interroga i bandi regionali, controlla o inserisce le pratiche dei Comuni/Enti "
                        "su BigQuery e calcola il cofinanziamento regionale."
                    )
                },
                "provisionedReasoningEngine": {
                    "reasoningEngine": reasoning_engine,
                },
            },
            "sharingConfig": {"scope": "ALL_USERS"},
        }
        st_adk, resp_adk = api_request("POST", agents_url, token, project_id, adk_body)
        if st_adk == 200 and isinstance(resp_adk, dict):
            adk_agent_resource = resp_adk.get("name", "")
            print(f"  -> [ADK Agent] Registrato `Assistente Bandi e Pratiche Lepida` ({adk_agent_resource}).")

    if args.adk_only:
        return

    # 3. Crea e abilita le 3 Skills operative nella sezione Skills (/r/skills)
    skills_defs = [
        {
            "displayName": "Simulazione Punteggio Bando Fibra 10 Gbps",
            "description": "Calcola la pre-valutazione e il punteggio sul Bando Fibra 10 Gbps per le Scuole secondo i 4 criteri regionali (Max 100 punti).",
            "instruction": (
                "Quando l'utente chiede di simulare o calcolare il punteggio per il Bando Fibra 10 Gbps Scuole, "
                "recupera i criteri dal documento '02_Linee_Guida_Bandi_Digitalizzazione_Comuni_2026.html' e '01_Catalogo_Servizi_Listino_Lepida_2026.html' nel Data Store e presenta sempre:\n"
                "1. Verifica della soglia minima di ammissibilità (70/100 punti per APPROVATA, 60-69 per INTEGRAZIONE_RICHIESTA entro 15 gg);\n"
                "2. Calcolo delle premialità cumulative (+5% Comune Montano/Area Interna, +5% Unione di Comuni >=3, +5% Comune <15.000 abitanti) col tetto massimo inderogabile del 95% a fondo perduto;\n"
                "3. Tabella con Valore Progetto, Contributo Regionale a Fondo Perduto, Quota a carico dell'Ente e le 3 Tranche (40% Anticipo, 30% SAL, 30% Saldo)."
            ),
        },
        {
            "displayName": "Checklist Migrazione Cloud e Sicurezza ACN",
            "description": "Genera il piano operativo di migrazione al Datacenter Lepida, adeguamento SOC/CSIRT NIS2 e conformità AI Act.",
            "instruction": (
                "Quando l'utente chiede come migrare un applicativo comunale o adeguarsi alle direttive ACN/NIS2 e AI Act con Lepida, "
                "consulta i documenti '01_Catalogo_Servizi_Listino_Lepida_2026.html', '04_Comune_Modena_Piattaforma_Cybersecurity_SOC_NIS2.html' e '10_Regolamento_Governance_AI_Act_Comuni_ER_2026.html' e produci:\n"
                "1. I riferimenti ai 4 Data Center Regionali certificati ACN (Bologna, Ferrara, Modena, Parma) con SLA 99,98%, RPO 15 min e RTO 1 ora;\n"
                "2. I tempi tassativi di notifica CSIRT Italia NIS2 (Early Warning 24h, Notifica 72h, Relazione Finale 30 gg) e presa in carico SOC Lepida entro 15 min;\n"
                "3. I presidi obbligatori AI Act UE 2024/1689 (sorveglianza umana Human-in-the-Loop del RUP, trasparenza art. 50, Model Armor/DLP e log retention 24 mesi in Region UE)."
            ),
        },
        {
            "displayName": "Generatore Bozza Determina Dirigenziale PA",
            "description": "Redige una bozza strutturata di Determina Dirigenziale di affidamento in-house a Lepida ScpA nelle 6 sezioni ufficiali.",
            "instruction": (
                "Quando l'utente chiede di preparare o redigere una bozza di Determina Dirigenziale per l'adesione a un bando o servizio Lepida, "
                "utilizza obbligatoriamente le 6 SEZIONI del modello ufficiale '08_Template_Determina_Dirigenziale_Affidamento_InHouse_Lepida.html' (MOD-DET-INHOUSE-LEPIDA-2026):\n"
                "- SEZIONE 1: Intestazione dell'Ente, Settore e individuazione del RUP (art. 15 D.Lgs. 36/2023);\n"
                "- SEZIONE 2: Premesse di Fatto e di Diritto (L.R. 11/2004, controllo analogo congiunto su Lepida ScpA);\n"
                "- SEZIONE 3: Motivazione di Congruità Economica (art. 7 comma 2 D.Lgs. 36/2023, canone e SLA dal Catalogo Lepida, risparmio >22% vs Consip/MEPA);\n"
                "- SEZIONE 4: Quadro Economico e Piano Finanziario nelle 3 tranche (40% / 30% / 30%);\n"
                "- SEZIONE 5: Clausole Obbligatorie di Conformità ACN, NIS2, GDPR e AI Act UE 2024/1689;\n"
                "- SEZIONE 6: Dispositivo della Determina (esenzione CIG ordinario per in-house e tracciabilità tramite CUP)."
            ),
        },
    ]

    for s in skills_defs:
        for ag in existing_agents:
            if ag.get("displayName") == s["displayName"]:
                api_request("DELETE", f"https://discoveryengine.googleapis.com/v1alpha/{ag['name']}", token, project_id)
        skill_payload = {
            "displayName": s["displayName"],
            "description": s["description"],
            "skillAgentDefinition": {"instruction": s["instruction"]},
            "sharingConfig": {"scope": "ALL_USERS"},
        }
        st_sk, resp_sk = api_request("POST", agents_url, token, project_id, skill_payload)
        if st_sk == 200 and isinstance(resp_sk, dict):
            sk_name = resp_sk["name"]
            api_request("POST", f"https://discoveryengine.googleapis.com/v1alpha/{sk_name}:requestAgentReview", token, project_id, {})
            api_request(
                "PATCH",
                f"https://discoveryengine.googleapis.com/v1alpha/{sk_name}?updateMask=sharingConfig",
                token,
                project_id,
                {"sharingConfig": {"scope": "ALL_USERS"}},
            )
            print(f"  -> [Skill] Creata e abilitata `{s['displayName']}`.")

    # 4. Crea, deploya (:deployLowCode) e condivide il Chat Agent Multi-Livello con Gemini 3.8 Flash
    chat_display_name = "Consulente Digitale Comuni ER e Servizi Lepida"
    for ag in existing_agents:
        if "Consulente Digitale Comuni ER" in ag.get("displayName", ""):
            api_request("DELETE", f"https://discoveryengine.googleapis.com/v1alpha/{ag['name']}", token, project_id)

    ds_resource = f"projects/{project_number}/locations/global/collections/default_collection/dataStores/lepida-comuni-er-ds"
    ds_spec = {"specs": [{"dataStore": ds_resource}]}

    phase2_sub_agents = ["spec_determine_pa", "spec_benchmark_comuni"]
    if adk_agent_resource:
        phase2_sub_agents.append("ref_adk_bigquery")

    nodes = [
        {
            "id": "root_agent",
            "displayName": chat_display_name,
            "sequentialAgentNode": {
                "description": "Orchestratore sequenziale multi-livello: Fase 1 Istruttoria Tecnica Bandi & Cloud -> Fase 2 Atti PA & Benchmark Comuni ER.",
                "subAgentIds": ["coord_bandi_infra", "coord_atti_comuni"],
            },
        },
        {
            "id": "coord_bandi_infra",
            "displayName": "Fase 1 - Istruttoria Bandi e Cloud",
            "llmAgentNode": {
                "model": "gemini-3.8-flash",
                "description": "Coordinatore di 1° livello (Gemini 3.8 Flash) per l'analisi dei Bandi Regionali 2026, del Catalogo Lepida e della Sicurezza Cloud ACN/NIS2.",
                "instruction": (
                    "Sei il Coordinatore Tecnico Bandi e Infrastruttura Lepida.\n"
                    "Delega e coordina i tuoi due sub-agenti specialisti:\n"
                    "- 'Specialista Bando Fibra 10 Gbps' per la verifica di ammissibilità (>=70 pt), premialità cumulative (tetto 95%) e calcolo delle 3 tranche (40%/30%/30%);\n"
                    "- 'Specialista Cloud PA e Sicurezza ACN' per il listino e gli SLA del Catalogo Lepida 2026, i 4 Data Center Regionali e le regole SOC/NIS2 e AI Act."
                ),
                "subAgentIds": ["spec_bando_fibra", "spec_cloud_acn"],
                "dataStoreSpecs": ds_spec,
            },
        },
        {
            "id": "spec_bando_fibra",
            "displayName": "Specialista Bando Fibra 10 Gbps",
            "llmAgentNode": {
                "model": "gemini-3.8-flash",
                "description": "Sub-agent di 2° livello (Gemini 3.8 Flash): calcolo punteggi, premialità (cap 95%) e 3 tranche dei Bandi Lepida 2026.",
                "instruction": (
                    "Consulta '01_Catalogo_Servizi_Listino_Lepida_2026.html' e '02_Linee_Guida_Bandi_Digitalizzazione_Comuni_2026.html' e calcola sempre:\n"
                    "1. Esito ammissibilità (>=70/100 APPROVATA, 60-69 INTEGRAZIONE_RICHIESTA entro 15 gg);\n"
                    "2. Quota base bando + premialità cumulative (+5% Montano, +5% Unione >=3 Comuni, +5% <15.000 ab.) applicando il tetto massimo del 95%;\n"
                    "3. Tabella finanziaria con Contributo Regionale, Quota Ente e le 3 Tranche (40% Anticipo, 30% SAL, 30% Saldo)."
                ),
                "subAgentIds": [],
                "dataStoreSpecs": ds_spec,
            },
        },
        {
            "id": "spec_cloud_acn",
            "displayName": "Specialista Cloud PA e Sicurezza ACN",
            "llmAgentNode": {
                "model": "gemini-3.8-flash",
                "description": "Sub-agent di 2° livello (Gemini 3.8 Flash): Catalogo Servizi Lepida 2026, Data Center Regionali, SOC NIS2 e AI Act.",
                "instruction": (
                    "Consulta '01_Catalogo_Servizi_Listino_Lepida_2026.html', '04_Comune_Modena_Piattaforma_Cybersecurity_SOC_NIS2.html' e '10_Regolamento_Governance_AI_Act_Comuni_ER_2026.html' "
                    "per fornire i canoni annui e gli SLA dei 5 servizi a catalogo Lepida, i 4 poli Data Center Regionali, i tempi di notifica CSIRT NIS2 (24h/72h/30gg) e i presidi AI Act."
                ),
                "subAgentIds": [],
                "dataStoreSpecs": ds_spec,
            },
        },
        {
            "id": "coord_atti_comuni",
            "displayName": "Fase 2 - Atti PA e Benchmark Comuni",
            "llmAgentNode": {
                "model": "gemini-3.8-flash",
                "description": "Coordinatore di 1° livello (Gemini 3.8 Flash) che coordina la redazione di Determine In-House in 6 sezioni e il Benchmark tra i Comuni ER.",
                "instruction": (
                    "Sei il Coordinatore Amministrativo per gli Atti PA e il Benchmark dei Comuni dell'Emilia-Romagna.\n"
                    "Delega e coordina i tuoi sub-agenti specialisti:\n"
                    "- 'Redattore Determine e Convenzioni PA' per redigere bozze di Determine Dirigenziali in-house nelle 6 sezioni ufficiali del modello MOD-DET-INHOUSE-LEPIDA-2026;\n"
                    "- 'Analista TARI e Benchmark Comuni ER' per il Regolamento TARI Bologna, soglie LoRaWAN Ravenna, stato pratiche e Benchmark comparativo dei Comuni ER.\n"
                    "Presenta sempre una risposta finale completa e ben formattata in italiano citando i documenti fonte."
                ),
                "subAgentIds": phase2_sub_agents,
                "dataStoreSpecs": ds_spec,
            },
        },
        {
            "id": "spec_determine_pa",
            "displayName": "Redattore Determine e Convenzioni PA",
            "llmAgentNode": {
                "model": "gemini-3.8-flash",
                "description": "Sub-agent di 2° livello (Gemini 3.8 Flash): redazione Determine Dirigenziali In-House Lepida in 6 sezioni (MOD-DET-INHOUSE-LEPIDA-2026).",
                "instruction": (
                    "Consulta '08_Template_Determina_Dirigenziale_Affidamento_InHouse_Lepida.html', '01_Catalogo_Servizi_Listino_Lepida_2026.html' e '10_Regolamento_Governance_AI_Act_Comuni_ER_2026.html' "
                    "per redigere Determine Dirigenziali complete nelle 6 sezioni obbligatorie (Intestazione e RUP, Premesse L.R. 11/2004, Congruità Economica art. 7 c. 2 D.Lgs. 36/2023, Quadro Economico 3 tranche, Clausole ACN/GDPR/AI Act, Dispositivo con CUP)."
                ),
                "subAgentIds": [],
                "dataStoreSpecs": ds_spec,
            },
        },
        {
            "id": "spec_benchmark_comuni",
            "displayName": "Analista TARI e Benchmark Comuni ER",
            "llmAgentNode": {
                "model": "gemini-3.8-flash",
                "description": "Sub-agent di 2° livello (Gemini 3.8 Flash): TARI Bologna, IoT Ravenna, criticità pratiche NIS2 Ferrara e Benchmark Comuni ER.",
                "instruction": (
                    "Consulta i documenti comunali ('03_Comune_Bologna_Delibera_Sportello_AI_Urp.html', '04_Comune_Modena_Piattaforma_Cybersecurity_SOC_NIS2.html', "
                    "'05_Comuni_Ravenna_Rimini_IoT_Idrogeologico_Turismo.html', '06_Comuni_Ferrara_Parma_Banda_Ultra_Larga_Scuole_Sanita.html', "
                    "'07_Unioni_Comuni_Montani_Appennino_Servizi_Associati_SIA.html', '09_FAQ_Cittadini_Imprese_Tributi_TARI_Anagrafe_SUAP.html') "
                    "per costruire tabelle comparative tra gli Enti e indicare come sanare le pratiche in stato INTEGRAZIONE_RICHIESTA (es. Allegato Tecnico B2 entro 15 gg per Ferrara)."
                ),
                "subAgentIds": [],
                "dataStoreSpecs": ds_spec,
            },
        },
    ]

    if adk_agent_resource:
        nodes.append(
            {
                "id": "ref_adk_bigquery",
                "displayName": "Assistente Bandi e Pratiche Lepida (ADK)",
                "referencedAdkAgentNode": {
                    "sourceAgent": adk_agent_resource,
                    "sourceAgentName": adk_agent_resource,
                },
            }
        )

    starter_prompts = [
        {"text": "Esegui la SKILL 1: calcola contributo (tetto 95%) e 3 tranche per l'Unione Appennino Bolognese (11 Comuni montani <15k ab.) su progetto Fibra 10G da 140.000 EUR (punteggio 88/100)."},
        {"text": "Esegui la SKILL 2: redigi nelle 6 sezioni ufficiali la Determina Dirigenziale in-house per il Comune di Rimini (RUP Ing. Marco Verdi) sul Bando AI Sportello da 110.000 EUR."},
        {"text": "Esegui la SKILL 3: genera la tabella comparativa di Benchmark tra Bologna, Modena, Ravenna, Rimini, Ferrara, Parma e Unione Appennino Bolognese."},
    ]
    chat_payload = {
        "displayName": chat_display_name,
        "description": "Assistente Multi-Agent Gerarchico e Sequenziale (Gemini 3.8 Flash) specializzato nei servizi Lepida ScpA, bandi regionali 2026, sicurezza ACN/NIS2 e Comuni ER.",
        "starterPrompts": starter_prompts,
        "lowCodeAgentDefinition": {
            "draftDisplayName": chat_display_name,
            "draftDescription": "Assistente Multi-Agent Gerarchico e Sequenziale (Gemini 3.8 Flash) specializzato nei servizi Lepida ScpA, bandi regionali 2026, sicurezza ACN/NIS2 e Comuni ER.",
            "draftStarterPrompts": starter_prompts,
            "rootAgentId": "root_agent",
            "nodes": nodes,
            "deployedRootAgentId": "root_agent",
            "deployedNodes": nodes,
        },
        "sharingConfig": {"scope": "ALL_USERS"},
    }
    st_ch, resp_ch = api_request("POST", agents_url, token, project_id, chat_payload)
    if st_ch == 200 and isinstance(resp_ch, dict):
        ch_name = resp_ch["name"]
        api_request("POST", f"https://discoveryengine.googleapis.com/v1alpha/{ch_name}:deployLowCode", token, project_id, {"name": ch_name})
        api_request("POST", f"https://discoveryengine.googleapis.com/v1alpha/{ch_name}:requestAgentReview", token, project_id, {})
        api_request(
            "PATCH",
            f"https://discoveryengine.googleapis.com/v1alpha/{ch_name}?updateMask=sharingConfig",
            token,
            project_id,
            {"sharingConfig": {"scope": "ALL_USERS"}},
        )
        print(f"  -> [Chat Agent Multi-Livello (Gemini 3.8 Flash)] Creato, deployato e condiviso `{chat_display_name}` ({ch_name}).")


if __name__ == "__main__":
    main()
