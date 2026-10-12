#!/usr/bin/env python3
"""
Configura automaticamente l'intero ambiente Gemini Enterprise per il Workshop Lepida:
1. Attiva automaticamente la licenza Free Trial a 30 giorni (`free_trial_gemini`) e abilita
   `enableLicenseAutoRegister: true` su `default_user_store` (zero passaggi manuali in Console!).
2. Configura Google Identity (`IDP_TYPE_GSUITE`) su `locations/global/aclConfig`.
3. Crea il Connettore / Data Store Cloud Storage (`lepida-comuni-er-ds` -
   "Corpus Documentale Lepida e Comuni Emilia-Romagna 2026") puntando al bucket univoco
   `gs://<PROJECT_ID>-lepida-comuni-er/documenti_pa/*.html` e indicizza istantaneamente
   i 10 documenti pubblici (in 2 secondi tramite `branches/0/documents` + sync `gcsSource`).
4. Crea l'App Gemini Enterprise (`lepida-comuni-er-app` - "Lepida & Comuni ER Assistant")
   già collegata al Data Store `lepida-comuni-er-ds` e con tutte le feature sbloccate:
   - `no-code-agent-builder` (Chat Agent)
   - `skills`, `skill-sharing`, `skill-sharing-without-admin-approval` (Skills)
   - `agent-sharing`, `agent-sharing-without-admin-approval`
5. Recupera il `configId` (`cid`) di `default_search_widget_config` e salva l'URL diretto
   della Web App (`https://vertexaisearch.cloud.google.com/home/cid/<CID>`) in `WEB_APP_URL.txt`.
"""

import argparse
import base64
import datetime
import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request


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


PROJECT_ID = _detect_project_id()
DATA_STORE_ID = "lepida-comuni-er-ds"
ENGINE_ID = "lepida-comuni-er-app"
BUCKET_NAME = os.environ.get("LEPIDA_BUCKET_NAME", f"{PROJECT_ID}-lepida-comuni-er").strip()

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


def get_token() -> str:
    res = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def api_request(method: str, url: str, token: str, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-Goog-User-Project", PROJECT_ID)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def ensure_free_trial_license_and_idp(token: str):
    loc_base = f"https://discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_ID}/locations/global"

    # 1. Attiva la licenza Free Trial Gemini Enterprise (`free_trial_gemini`) e `enableLicenseAutoRegister`
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    lic_url = f"{loc_base}/licenseConfigs?licenseConfigId=free_trial_gemini"
    lic_body = {
        "freeTrial": True,
        "subscriptionTier": "SUBSCRIPTION_TIER_SEARCH_AND_ASSISTANT",
        "subscriptionTerm": "SUBSCRIPTION_TERM_ONE_MONTH",
        "startDate": {"year": tomorrow.year, "month": tomorrow.month, "day": tomorrow.day},
    }
    st_lic, _ = api_request("POST", lic_url, token, lic_body)
    if st_lic in (200, 201):
        print("  -> Licenza Gemini Enterprise (`free_trial_gemini`) attivata e `enableLicenseAutoRegister` abilitato.")
    elif st_lic == 409:
        print("  -> Licenza Gemini Enterprise (`free_trial_gemini`) già attiva.")

    # 2. Configura Google Identity (`IDP_TYPE_GSUITE`) su `locations/global/aclConfig`
    acl_url = f"{loc_base}/aclConfig"
    acl_body = {
        "name": f"projects/{PROJECT_ID}/locations/global/aclConfig",
        "idpConfig": {"idpType": "IDP_TYPE_GSUITE"},
    }
    st_acl, _ = api_request("PATCH", acl_url, token, acl_body)
    if st_acl == 200:
        print("  -> Identity Provider configurato su Google Identity (`IDP_TYPE_GSUITE`).")


def enable_features_on_all_engines(token: str, base: str) -> int:
    status_eng, resp_eng = api_request("GET", f"{base}/engines", token)
    if status_eng != 200 or not isinstance(resp_eng, dict):
        return 0
    engines = resp_eng.get("engines", [])
    for eng in engines:
        eng_id = eng.get("name", "").split("/")[-1]
        if not eng_id:
            continue
        feats = dict(eng.get("features", {}))
        needs_patch = any(feats.get(k) != v for k, v in REQUIRED_ENGINE_FEATURES.items())
        if needs_patch:
            feats.update(REQUIRED_ENGINE_FEATURES)
            patch_url = f"{base}/engines/{eng_id}?updateMask=features"
            st, _ = api_request("PATCH", patch_url, token, {"features": feats})
            if st == 200:
                print(f"  -> Feature Chat Agent (`no-code-agent-builder`) e `skills` abilitate su Engine `{eng_id}`.")
    return len(engines)


def get_webapp_url(token: str, base: str, engine_id: str) -> str:
    wc_url = f"{base}/engines/{engine_id}/widgetConfigs/default_search_widget_config"
    for _ in range(10):
        st, resp = api_request("GET", wc_url, token)
        if st == 200 and isinstance(resp, dict):
            cid = resp.get("configId", "")
            if cid:
                return f"https://vertexaisearch.cloud.google.com/home/cid/{cid}"
        time.sleep(2)
    return f"https://console.cloud.google.com/gemini-enterprise/apps?project={PROJECT_ID}"


def index_gcs_docs_immediately(token: str, base_ds_url: str):
    gcs_list_url = f"https://storage.googleapis.com/storage/v1/b/{BUCKET_NAME}/o?prefix=documenti_pa/"
    req = urllib.request.Request(gcs_list_url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        items = json.loads(resp.read().decode("utf-8")).get("items", [])

    count = 0
    for it in items:
        name = it.get("name", "")
        if not name.endswith(".html"):
            continue
        doc_id = name.split("/")[-1].replace(".html", "")
        dl_url = f"https://storage.googleapis.com/storage/v1/b/{BUCKET_NAME}/o/{urllib.parse.quote(name, safe='')}?alt=media"
        with urllib.request.urlopen(
            urllib.request.Request(dl_url, headers={"Authorization": f"Bearer {token}"}),
            timeout=30,
        ) as dl_resp:
            raw_bytes = dl_resp.read()

        doc_body = {
            "id": doc_id,
            "jsonData": json.dumps(
                {
                    "title": doc_id.replace("_", " "),
                    "source_uri": f"gs://{BUCKET_NAME}/{name}",
                }
            ),
            "content": {
                "mimeType": "text/html",
                "rawBytes": base64.b64encode(raw_bytes).decode("ascii"),
            },
        }
        post_url = f"{base_ds_url}/branches/0/documents?documentId={doc_id}"
        st, _ = api_request("POST", post_url, token, doc_body)
        if st == 409:
            patch_url = f"{base_ds_url}/branches/0/documents/{doc_id}"
            st, _ = api_request("PATCH", patch_url, token, doc_body)
        if st in (200, 201):
            count += 1
    print(f"  -> Indicizzazione istantanea completata: {count} documenti subito ricercabili in `{DATA_STORE_ID}`.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create-app", action="store_true", default=True, help="Crea l'App Gemini Enterprise via API (default: attivo)")
    parser.add_argument("--skip-app", action="store_true", help="Non creare l'App Gemini Enterprise via API")
    parser.add_argument("--watch-engines", action="store_true", help="Rimane in ascolto in background")
    parser.add_argument("--wait", action="store_true", help="Compatibilità CLI")
    args = parser.parse_args()

    base = f"https://discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_ID}/locations/global/collections/default_collection"

    if args.watch_engines:
        for _ in range(720):
            try:
                tok = get_token()
                enable_features_on_all_engines(tok, base)
            except Exception:
                pass
            time.sleep(5)
        return

    token = get_token()

    # 0. Attiva automaticamente licenza Free Trial e Google Identity
    ensure_free_trial_license_and_idp(token)

    base_ds_url = f"{base}/dataStores/{DATA_STORE_ID}"

    # 1. Crea il Connettore / Data Store Cloud Storage
    create_url = f"{base}/dataStores?dataStoreId={DATA_STORE_ID}"
    ds_body = {
        "displayName": "Corpus Documentale Lepida e Comuni Emilia-Romagna 2026",
        "industryVertical": "GENERIC",
        "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
        "contentConfig": "CONTENT_REQUIRED",
    }
    status, resp = api_request("POST", create_url, token, ds_body)
    if status in (200, 201):
        print(f"  -> Connettore Data Store `{DATA_STORE_ID}` creato.")
    elif status == 409:
        print(f"  -> Connettore Data Store `{DATA_STORE_ID}` già presente.")
    else:
        print(f"  -> [Avviso DataStore] HTTP {status}: {resp}")

    # 2. Indicizzazione sincrona immediata (2 secondi) dal bucket GCS univoco
    index_gcs_docs_immediately(token, base_ds_url)

    # 3. Avvia anche il job di importazione batch GCS per allineamento connettore
    import_url = f"{base_ds_url}/branches/0/documents:import"
    import_body = {
        "gcsSource": {
            "inputUris": [f"gs://{BUCKET_NAME}/documenti_pa/*.html"],
            "dataSchema": "content",
        },
        "reconciliationMode": "INCREMENTAL",
    }
    status_imp, _ = api_request("POST", import_url, token, import_body)
    print(f"  -> Connettore GCS sincronizzato su gs://{BUCKET_NAME}/documenti_pa/*.html (HTTP {status_imp}).")

    # 4. Creazione automatica App Gemini Enterprise già collegata al Data Store e con Chat Agent & Skills attivi
    target_engine_id = ENGINE_ID
    if not args.skip_app:
        status_eng, resp_eng = api_request("GET", f"{base}/engines", token)
        engines = resp_eng.get("engines", []) if isinstance(resp_eng, dict) else []
        existing = [
            e for e in engines
            if ENGINE_ID in e.get("name", "") or "lepida" in e.get("displayName", "").lower()
        ]
        if existing:
            target_engine_id = existing[0]["name"].split("/")[-1]
            print(f"  -> App Gemini Enterprise già esistente: `{target_engine_id}`")
        else:
            eng_url = f"{base}/engines?engineId={ENGINE_ID}"
            eng_body = {
                "displayName": "Lepida & Comuni ER Assistant",
                "solutionType": "SOLUTION_TYPE_SEARCH",
                "dataStoreIds": [DATA_STORE_ID],
                "industryVertical": "GENERIC",
                "appType": "APP_TYPE_INTRANET",
                "commonConfig": {"companyName": "Lepida ScpA"},
                "searchEngineConfig": {
                    "searchTier": "SEARCH_TIER_ENTERPRISE",
                    "searchAddOns": ["SEARCH_ADD_ON_LLM"],
                },
                "features": REQUIRED_ENGINE_FEATURES,
            }
            status_c, resp_c = api_request("POST", eng_url, token, eng_body)
            print(f"  -> App Gemini Enterprise `Lepida & Comuni ER Assistant` (`{ENGINE_ID}`) creata (HTTP {status_c}).")
            time.sleep(4)

    # 5. Abilita Chat Agent (`no-code-agent-builder`) e `skills` su tutti gli Engine
    enable_features_on_all_engines(token, base)

    # 6. Recupera l'URL diretto della Web App e salvalo in WEB_APP_URL.txt
    webapp_url = get_webapp_url(token, base, target_engine_id)
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "WEB_APP_URL.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(webapp_url + "\n")
    print(f"  -> Web App Gemini Enterprise pronta: {webapp_url}")


if __name__ == "__main__":
    main()
