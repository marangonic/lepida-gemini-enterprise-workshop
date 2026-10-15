#!/usr/bin/env python3
"""
Script zero-dependency (compatibile con qualsiasi Python 3.9+ con gcloud autenticato)
di inizializzazione dati per il Workshop Agentic AI & Gemini Enterprise su GCP (Lepida ScpA).

Cosa crea in automatico per ciascuno dei 26 laboratori Qwiklabs:
1. Bucket Cloud Storage con nome GARANTITO UNIVOCO per ciascun utente/progetto:
   `gs://<PROJECT_ID>-lepida-comuni-er` (personalizzabile via `LEPIDA_BUCKET_NAME`)
2. Corpus di 10 Documenti Pubblici realistici (in HTML strutturato) in:
   `gs://<PROJECT_ID>-lepida-comuni-er/documenti_pa/`
   inerenti a Lepida ScpA e ai Comuni dell'Emilia-Romagna (Bologna, Modena, Ravenna,
   Rimini, Ferrara, Parma, Unione Appennino Bolognese, Unione Romagna Forlivese,
   Listino Servizi Lepida, Regole Bandi 2026, Template Determina In-House, FAQ Sportelli, AI Act).
3. Dataset BigQuery `lepida_territorio` con le 2 tabelle:
   - `bandi_regionali` (6 bandi regionali)
   - `pratiche_enti` (10 pratiche presentate dagli Enti)
"""

import json
import os
import subprocess
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
DATASET_ID = "lepida_territorio"
BUCKET_NAME = os.environ.get("LEPIDA_BUCKET_NAME", f"{PROJECT_ID}-lepida-comuni-er").strip()


def get_token() -> str:
    res = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def api_request(method: str, url: str, token: str, body=None, content_type="application/json"):
    data = None
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            data = body.encode("utf-8")
        else:
            data = body
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-Goog-User-Project", PROJECT_ID)
    if data is not None:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return e.code, err_body


def ensure_bq_dataset(token: str):
    print(f"[1/4] Verifica/Creazione Dataset BigQuery: {PROJECT_ID}.{DATASET_ID}")
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT_ID}/datasets"
    body = {
        "datasetReference": {"projectId": PROJECT_ID, "datasetId": DATASET_ID},
        "location": "US",
        "description": "Dataset Territoriale Lepida per Bandi Regionali e Pratiche Enti PA",
    }
    status, resp = api_request("POST", url, token, body)
    if status in (200, 201):
        print("  -> Dataset BigQuery creato con successo.")
    elif status == 409:
        print("  -> Dataset BigQuery già esistente.")
    else:
        raise RuntimeError(f"Errore creazione dataset ({status}): {resp}")


def ensure_bq_table(token: str, table_id: str, schema_fields: list, description: str):
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT_ID}/datasets/{DATASET_ID}/tables"
    del_url = f"{url}/{table_id}"
    api_request("DELETE", del_url, token)

    body = {
        "tableReference": {
            "projectId": PROJECT_ID,
            "datasetId": DATASET_ID,
            "tableId": table_id,
        },
        "schema": {"fields": schema_fields},
        "description": description,
    }
    status, resp = api_request("POST", url, token, body)
    if status not in (200, 201):
        raise RuntimeError(f"Errore creazione tabella {table_id} ({status}): {resp}")


def insert_bq_rows(token: str, table_id: str, rows: list):
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{PROJECT_ID}/datasets/{DATASET_ID}/tables/{table_id}/insertAll"
    body = {"rows": [{"json": r} for r in rows]}
    status, resp = api_request("POST", url, token, body)
    if status != 200 or resp.get("insertErrors"):
        raise RuntimeError(f"Errore popolamento tabella {table_id} ({status}): {resp}")
    print(f"  -> Tabella `{table_id}` popolata con {len(rows)} record.")


def populate_bigquery(token: str):
    print("[2/4] Creazione e popolamento tabelle BigQuery...")
    bandi_schema = [
        {"name": "id_bando", "type": "STRING", "mode": "REQUIRED"},
        {"name": "titolo", "type": "STRING", "mode": "REQUIRED"},
        {"name": "ambito", "type": "STRING", "mode": "REQUIRED"},
        {"name": "budget_totale_eur", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "contributo_massimo_eur", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "quota_cofinanziamento_base_pct", "type": "INTEGER", "mode": "REQUIRED"},
        {"name": "stato", "type": "STRING", "mode": "REQUIRED"},
        {"name": "data_scadenza", "type": "DATE", "mode": "REQUIRED"},
        {"name": "ente_gestore", "type": "STRING", "mode": "REQUIRED"},
        {"name": "descrizione", "type": "STRING", "mode": "REQUIRED"},
    ]
    ensure_bq_table(token, "bandi_regionali", bandi_schema, "Bandi regionali e PNRR gestiti da Lepida")

    bandi_rows = [
        {
            "id_bando": "BANDO-ER-2026-01",
            "titolo": "Potenziamento Rete Lepida in Fibra Ottica per Sedi Comunali e Plessi Scolastici",
            "ambito": "Connettivita BUL",
            "budget_totale_eur": 4500000.0,
            "contributo_massimo_eur": 150000.0,
            "quota_cofinanziamento_base_pct": 85,
            "stato": "APERTO",
            "data_scadenza": "2026-11-30",
            "ente_gestore": "Lepida ScpA - Direzione Reti e Infrastrutture",
            "descrizione": "Finanziamento per il rilegamento in fibra ottica dedicata (10 Gbps) di municipi, biblioteche e plessi scolastici non ancora connessi alla dorsale regionale.",
        },
        {
            "id_bando": "BANDO-ER-2026-02",
            "titolo": "Adozione Agentic AI e Assistenti Digitali per gli Sportelli Comunali",
            "ambito": "AI & Servizi Digitali",
            "budget_totale_eur": 3200000.0,
            "contributo_massimo_eur": 120000.0,
            "quota_cofinanziamento_base_pct": 80,
            "stato": "APERTO",
            "data_scadenza": "2026-12-15",
            "ente_gestore": "Lepida ScpA - Divisione Innovazione e Piattaforme Digitali",
            "descrizione": "Supporto all'introduzione di assistenti conversazionali basati su GenAI e integrazione con banche dati comunali tramite protocollo MCP e Cloud certificato ACN.",
        },
        {
            "id_bando": "BANDO-ER-2026-03",
            "titolo": "Potenziamento SOC Regionale e Adeguamento Direttiva NIS2 per Enti Locali e Sanita",
            "ambito": "Cybersecurity PA",
            "budget_totale_eur": 5000000.0,
            "contributo_massimo_eur": 200000.0,
            "quota_cofinanziamento_base_pct": 90,
            "stato": "APERTO",
            "data_scadenza": "2026-11-15",
            "ente_gestore": "Lepida ScpA - CERT / Cybersecurity Regionale",
            "descrizione": "Interventi di hardening infrastrutturale, monitoraggio EDR/SIEM federato col SOC Lepida e vulnerability assessment per Comuni, Unioni e Aziende Sanitarie.",
        },
        {
            "id_bando": "BANDO-ER-2026-04",
            "titolo": "Sensoristica IoT LoRaWAN per Monitoraggio Idrogeologico e Qualita dell'Aria",
            "ambito": "Smart City & IoT",
            "budget_totale_eur": 2800000.0,
            "contributo_massimo_eur": 90000.0,
            "quota_cofinanziamento_base_pct": 75,
            "stato": "IN_VALUTAZIONE",
            "data_scadenza": "2026-09-30",
            "ente_gestore": "Lepida ScpA - Area Smart Territory & IoT",
            "descrizione": "Installazione di gateway e nodi sensori sulla rete regionale LoRaWAN di Lepida per il monitoraggio in tempo reale di fiumi, frane e traffico urbano.",
        },
        {
            "id_bando": "BANDO-ER-2026-05",
            "titolo": "Migrazione Cloud Qualificato e Consolidamento Datacenter Regionali",
            "ambito": "Cloud PA",
            "budget_totale_eur": 6000000.0,
            "contributo_massimo_eur": 250000.0,
            "quota_cofinanziamento_base_pct": 80,
            "stato": "APERTO",
            "data_scadenza": "2026-12-31",
            "ente_gestore": "Lepida ScpA - Direzione Cloud e Datacenter",
            "descrizione": "Accompagnamento alla migrazione di applicativi legacy verso infrastrutture Cloud qualificate ACN in logica IaaS/PaaS e containerizzazione.",
        },
        {
            "id_bando": "BANDO-ER-2025-09",
            "titolo": "Digitalizzazione Archivi Storici e Fascicolo Informatico del Cittadino",
            "ambito": "Dematerializzazione",
            "budget_totale_eur": 1900000.0,
            "contributo_massimo_eur": 70000.0,
            "quota_cofinanziamento_base_pct": 70,
            "stato": "CHIUSO",
            "data_scadenza": "2026-03-31",
            "ente_gestore": "Lepida ScpA - Polo Archivistico Regionale",
            "descrizione": "Scansione, indicizzazione semantica e conservazione sostitutiva nel Polo Archivistico Regionale (ParER) delle pratiche edilizie e amministrative comunali.",
        },
    ]
    insert_bq_rows(token, "bandi_regionali", bandi_rows)

    pratiche_schema = [
        {"name": "id_pratica", "type": "STRING", "mode": "REQUIRED"},
        {"name": "id_bando", "type": "STRING", "mode": "REQUIRED"},
        {"name": "ente_richiedente", "type": "STRING", "mode": "REQUIRED"},
        {"name": "provincia", "type": "STRING", "mode": "REQUIRED"},
        {"name": "importo_richiesto_eur", "type": "FLOAT", "mode": "REQUIRED"},
        {"name": "punteggio_tecnico", "type": "INTEGER", "mode": "NULLABLE"},
        {"name": "stato_pratica", "type": "STRING", "mode": "REQUIRED"},
        {"name": "data_presentazione", "type": "DATE", "mode": "REQUIRED"},
        {"name": "referente_email", "type": "STRING", "mode": "REQUIRED"},
        {"name": "note_istruttore", "type": "STRING", "mode": "NULLABLE"},
    ]
    ensure_bq_table(token, "pratiche_enti", pratiche_schema, "Pratiche presentate dagli Enti del territorio")

    pratiche_rows = [
        {
            "id_pratica": "PRAT-2026-101",
            "id_bando": "BANDO-ER-2026-02",
            "ente_richiedente": "Comune di Bologna",
            "provincia": "BO",
            "importo_richiesto_eur": 118000.0,
            "punteggio_tecnico": 92,
            "stato_pratica": "APPROVATA",
            "data_presentazione": "2026-09-12",
            "referente_email": "rup.innovazione@comune.bologna.it",
            "note_istruttore": "Progetto pilota assistente AI per sportello tributi e anagrafe. Architettura MCP validata.",
        },
        {
            "id_pratica": "PRAT-2026-102",
            "id_bando": "BANDO-ER-2026-01",
            "ente_richiedente": "Unione dei Comuni dell'Appennino Bolognese",
            "provincia": "BO",
            "importo_richiesto_eur": 145000.0,
            "punteggio_tecnico": 88,
            "stato_pratica": "APPROVATA",
            "data_presentazione": "2026-09-15",
            "referente_email": "sistemi.informativi@unioneappennino.bo.it",
            "note_istruttore": "Rilegamento di 6 plessi scolastici montani. Priorita alta per area interna (+10% premialita).",
        },
        {
            "id_pratica": "PRAT-2026-103",
            "id_bando": "BANDO-ER-2026-03",
            "ente_richiedente": "Comune di Modena",
            "provincia": "MO",
            "importo_richiesto_eur": 185000.0,
            "punteggio_tecnico": 85,
            "stato_pratica": "APPROVATA",
            "data_presentazione": "2026-09-18",
            "referente_email": "ciso@comune.modena.it",
            "note_istruttore": "Integrazione SIEM comunale con SOC Regionale Lepida completata in fase preliminare.",
        },
        {
            "id_pratica": "PRAT-2026-104",
            "id_bando": "BANDO-ER-2026-02",
            "ente_richiedente": "Comune di Parma",
            "provincia": "PR",
            "importo_richiesto_eur": 95000.0,
            "punteggio_tecnico": 78,
            "stato_pratica": "IN_ISTRUTTORIA",
            "data_presentazione": "2026-10-01",
            "referente_email": "transizione.digitale@comune.parma.it",
            "note_istruttore": "In attesa di chiarimenti sul connettore dati verso il sistema protocollo comunale.",
        },
        {
            "id_pratica": "PRAT-2026-105",
            "id_bando": "BANDO-ER-2026-05",
            "ente_richiedente": "AUSL della Romagna",
            "provincia": "RA",
            "importo_richiesto_eur": 248000.0,
            "punteggio_tecnico": 95,
            "stato_pratica": "APPROVATA",
            "data_presentazione": "2026-09-20",
            "referente_email": "direzione.ict@auslromagna.it",
            "note_istruttore": "Migrazione di 14 applicativi dipartimentali sanitari con requisiti di alta affidabilita.",
        },
        {
            "id_pratica": "PRAT-2026-106",
            "id_bando": "BANDO-ER-2026-03",
            "ente_richiedente": "Comune di Ferrara",
            "provincia": "FE",
            "importo_richiesto_eur": 160000.0,
            "punteggio_tecnico": 64,
            "stato_pratica": "INTEGRAZIONE_RICHIESTA",
            "data_presentazione": "2026-09-28",
            "referente_email": "sicurezza.it@comune.fe.it",
            "note_istruttore": "Richiesto allegato tecnico B2 con inventario asset critici NIS2 entro 15 giorni.",
        },
        {
            "id_pratica": "PRAT-2026-107",
            "id_bando": "BANDO-ER-2026-04",
            "ente_richiedente": "Comune di Ravenna",
            "provincia": "RA",
            "importo_richiesto_eur": 88000.0,
            "punteggio_tecnico": 91,
            "stato_pratica": "APPROVATA",
            "data_presentazione": "2026-09-10",
            "referente_email": "ambiente.smartcity@comune.ra.it",
            "note_istruttore": "Rete di 45 sensori idrometrici su canali di bonifica e allerta precoce alluvioni.",
        },
        {
            "id_pratica": "PRAT-2026-108",
            "id_bando": "BANDO-ER-2026-02",
            "ente_richiedente": "Comune di Reggio Emilia",
            "provincia": "RE",
            "importo_richiesto_eur": 112000.0,
            "punteggio_tecnico": 81,
            "stato_pratica": "IN_ISTRUTTORIA",
            "data_presentazione": "2026-10-03",
            "referente_email": "innovazione@comune.re.it",
            "note_istruttore": "Verifica finale del piano di formazione per 40 operatori URP sullo strumento Gemini Enterprise.",
        },
        {
            "id_pratica": "PRAT-2026-109",
            "id_bando": "BANDO-ER-2026-01",
            "ente_richiedente": "Unione dei Comuni della Bassa Romagna",
            "provincia": "RA",
            "importo_richiesto_eur": 132000.0,
            "punteggio_tecnico": None,
            "stato_pratica": "INVIATA",
            "data_presentazione": "2026-10-05",
            "referente_email": "reti@unione.bassaromagna.it",
            "note_istruttore": "Domanda protocollata correttamente, in attesa di assegnazione alla commissione tecnica.",
        },
        {
            "id_pratica": "PRAT-2026-110",
            "id_bando": "BANDO-ER-2026-05",
            "ente_richiedente": "Comune di Piacenza",
            "provincia": "PC",
            "importo_richiesto_eur": 195000.0,
            "punteggio_tecnico": 76,
            "stato_pratica": "IN_ISTRUTTORIA",
            "data_presentazione": "2026-09-29",
            "referente_email": "cloud@comune.piacenza.it",
            "note_istruttore": "Valutazione tecnica del cronoprogramma di dismissione server on-premise in corso.",
        },
    ]
    insert_bq_rows(token, "pratiche_enti", pratiche_rows)


def ensure_gcs_bucket(token: str):
    print(f"[3/4] Verifica/Creazione Bucket Cloud Storage Univoco: gs://{BUCKET_NAME}")
    get_url = f"https://storage.googleapis.com/storage/v1/b/{BUCKET_NAME}"
    status, _ = api_request("GET", get_url, token)
    if status == 200:
        print("  -> Bucket già esistente.")
        return

    create_url = f"https://storage.googleapis.com/storage/v1/b?project={PROJECT_ID}"
    body = {
        "name": BUCKET_NAME,
        "location": "US",
        "storageClass": "STANDARD",
        "iamConfiguration": {"uniformBucketLevelAccess": {"enabled": True}},
    }
    status, resp = api_request("POST", create_url, token, body)
    if status in (200, 201, 409):
        print("  -> Bucket creato con successo.")
    else:
        raise RuntimeError(f"Errore creazione bucket ({status}): {resp}")


def upload_gcs_object(token: str, object_name: str, content: str, content_type: str = "text/html; charset=utf-8"):
    encoded_name = urllib.parse.quote(object_name, safe="")
    url = f"https://storage.googleapis.com/upload/storage/v1/b/{BUCKET_NAME}/o?uploadType=media&name={encoded_name}"
    status, resp = api_request("POST", url, token, content, content_type=content_type)
    if status not in (200, 201):
        raise RuntimeError(f"Errore upload {object_name} ({status}): {resp}")
    print(f"  -> Caricato: gs://{BUCKET_NAME}/{object_name}")


def populate_gcs_docs(token: str):
    print("[4/4] Caricamento dei 10 Documenti Pubblici Lepida & Comuni Emilia-Romagna in GCS...")

    docs = {
        "documenti_pa/01_Catalogo_Servizi_e_Listino_Lepida_Comuni_2026.html": """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Catalogo Servizi e Listino Ufficiale Lepida ScpA per gli Enti Soci 2026</title></head>
<body>
<h1>Catalogo Servizi e Listino Ufficiale Lepida ScpA per gli Enti Soci (Anno 2026)</h1>
<p><strong>Documento Ufficiale:</strong> CAT-LEPIDA-2026-V1 | <strong>Ambito:</strong> Tutti i Comuni, le Unioni di Comuni, le Province e le Aziende Sanitarie (AUSL/AOU) dell'Emilia-Romagna soci di Lepida ScpA.</p>

<h2>1. Tabella Riepilogativa Servizi, Canoni In-House e SLA</h2>
<table border="1">
<tr><th>Codice Servizio</th><th>Nome Servizio Lepida</th><th>Descrizione Tecnica</th><th>Canone Annuo In-House (IVA Esente / Esclusa)</th><th>SLA Garantito / Ripristino</th><th>Bando Regionale Collegato</th></tr>
<tr><td><strong>SRV-FIBRA-10G</strong></td><td>Rilegamento in Fibra Ottica Dedicata 10 Gbps</td><td>Connessione simmetrica 10 Gbps sulla Rete Lepida per Municipi, Scuole, Biblioteche e Sedi AUSL, inclusa manutenzione proattiva 24x7.</td><td>4.200 EUR / anno per sede (Costo una tantum attivazione: 8.500 EUR)</td><td>Disponibilità 99,95% - Ripristino guasto bloccante entro 4 ore</td><td>BANDO-ER-2026-01 (Cofinanziamento base 85%)</td></tr>
<tr><td><strong>SRV-CLOUD-ACN</strong></td><td>Ambiente Cloud Qualificato ACN (IaaS / PaaS / Kubernetes)</td><td>Infrastruttura Cloud sovrana nei Datacenter Regionali Lepida (Bologna, Modena, Parma, Ravenna) qualificata ACN per dati ordinari e critici.</td><td>9.500 EUR / anno (Pacchetto Base Ente fino a 32 vCPU, 128 GB RAM, 5 TB Storage NVMe + Backup immutabile)</td><td>Disponibilità 99,98% - RPO 15 minuti, RTO 1 ora</td><td>BANDO-ER-2026-05 (Cofinanziamento base 80%)</td></tr>
<tr><td><strong>SRV-SOC-NIS2</strong></td><td>SOC / CERT Regionale Federato e Conformità NIS2</td><td>Monitoraggio continuo 24x7x365 degli endpoint (EDR) e dei log (SIEM), Vulnerability Assessment trimestrale e supporto notifica CSIRT Italia.</td><td>6.800 EUR / anno per Comuni fino a 25.000 ab. | 14.500 EUR / anno per Comuni > 25.000 ab. o Unioni</td><td>Presa in carico allarmi critici entro 15 minuti (24x7)</td><td>BANDO-ER-2026-03 (Cofinanziamento base 90%)</td></tr>
<tr><td><strong>SRV-AI-SPORTELLO</strong></td><td>Piattaforma Gemini Enterprise & Agentic AI per Sportelli PA</td><td>Ambiente gestito su Google Cloud (Region Europe) con assistenti conversazionali grounded sui regolamenti comunali, connettori MCP e Model Armor.</td><td>5.400 EUR / anno per Ente (include fino a 30 postazioni operatore URP/RUP e Sportello Cittadino)</td><td>Disponibilità 99,90% - Log conservati 24 mesi</td><td>BANDO-ER-2026-02 (Cofinanziamento base 80%)</td></tr>
<tr><td><strong>SRV-IOT-LORAWAN</strong></td><td>Rete Regionale IoT LoRaWAN & Cruscotto Sensoristica</td><td>Gateway LoRaWAN multisensore per monitoraggio idrogeologico fiumi/frane, qualità dell'aria e parcheggi/ZTL, con ingestione su BigQuery.</td><td>120 EUR / anno per Gateway + 18 EUR / anno per sensore attivo</td><td>Disponibilità 99,50% - Allerta webhook in tempo reale (< 5 sec)</td><td>BANDO-ER-2026-04 (Cofinanziamento base 75%)</td></tr>
</table>

<h2>2. Modalità di Adesione In-House (Art. 7 D.Lgs. 36/2023)</h2>
<p>Essendo Lepida ScpA società in-house providing della Regione Emilia-Romagna e degli Enti Locali soci, l'attivazione dei servizi a catalogo avviene tramite <strong>Determina Dirigenziale di Affidamento In-House</strong> (senza necessità di gara d'appalto pubblica), previa verifica di congruità economica ai sensi dell'art. 7, comma 2 del D.Lgs. 36/2023, già attestata dal Comitato Permanente di Indirizzo e Coordinamento (CPIC).</p>
</body>
</html>""",

        "documenti_pa/02_Bandi_Regionali_Transizione_Digitale_e_Regole_Cofinanziamento_2026.html": """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Linee Guida Bandi Transizione Digitale Emilia-Romagna 2026 e Regole di Cofinanziamento</title></head>
<body>
<h1>Linee Guida Ufficiali Bandi Regionali Transizione Digitale 2026 (Lepida ScpA)</h1>
<p><strong>Documento di Riferimento:</strong> LG-LEPIDA-2026-REV4 | <strong>Validità:</strong> Programmazione Regionale 2026–2027</p>

<h2>1. Soglie di Punteggio Tecnico e Criteri di Valutazione (Max 100 Punti)</h2>
<ul>
  <li><strong>Impatto territoriale e bacino di utenza servito:</strong> fino a 30 punti.</li>
  <li><strong>Adozione di standard aperti, Cloud Qualificato ACN e protocollo MCP:</strong> fino a 35 punti.</li>
  <li><strong>Sostenibilità economica e riuso del software tra più Enti (Catalogo Developers Italia):</strong> fino a 20 punti.</li>
  <li><strong>Piano di formazione per operatori comunali e RUP:</strong> fino a 15 punti.</li>
</ul>
<p><strong>Regola di idoneità:</strong></p>
<ul>
  <li>Punteggio <strong>pari o superiore a 70/100</strong>: pratica <strong>APPROVATA</strong> e ammessa a finanziamento.</li>
  <li>Punteggio compreso tra <strong>60/100 e 69/100</strong>: pratica posta in stato <strong>INTEGRAZIONE_RICHIESTA</strong>. L'Ente ha <strong>15 giorni solari</strong> per inviare la documentazione integrativa (es. Allegato Tecnico B2 per NIS2 o schema connettori dati).</li>
  <li>Punteggio <strong>inferiore a 60/100</strong>: pratica non ammessa.</li>
</ul>

<h2>2. Regole di Cofinanziamento e Premialità Cumulative (Tetto Massimo 95%)</h2>
<p>Alla quota base di fondo perduto prevista da ciascun bando (80% per AI/Cloud, 85% per Fibra BUL, 90% per Cybersecurity NIS2, 75% per IoT) si sommano le seguenti <strong>premialità territoriali cumulative</strong> fino a un tetto massimo complessivo del <strong>95%</strong>:</p>
<ol>
  <li><strong>Comuni Montani e Aree Interne dell'Appennino Emiliano-Romagnolo:</strong> <strong>+5%</strong> di contributo a fondo perduto.</li>
  <li><strong>Unioni di Comuni (domande presentate in forma associata per almeno 3 Comuni):</strong> <strong>+5%</strong> di contributo a fondo perduto.</li>
  <li><strong>Piccoli Comuni con popolazione residente inferiore a 15.000 abitanti:</strong> <strong>+5%</strong> di contributo a fondo perduto.</li>
</ol>
<p><em>Esempio di calcolo:</em> Un'Unione di Comuni situata in territorio montano (+5% Unione + 5% Montano = +10%) che partecipa a un bando con quota base 80% ottiene il <strong>90% a fondo perduto</strong>; se presenta domanda su un bando con quota base 90%, applicando il tetto massimo ottiene il <strong>95% a fondo perduto</strong> (resta solo il 5% a carico del bilancio dell'Ente).</p>

<h2>3. Modalità di Erogazione del Contributo in 3 Tranche</h2>
<ul>
  <li><strong>1ª Tranche — Anticipo del 40%:</strong> erogato entro <strong>30 giorni</strong> dalla determina di approvazione della pratica e comunicazione del codice CUP.</li>
  <li><strong>2ª Tranche — SAL Intermedio del 30%:</strong> erogato al raggiungimento del <strong>50% delle attività progettuali</strong> (attestato dal verbale di rilascio dell'ambiente di staging o posa infrastrutturale).</li>
  <li><strong>3ª Tranche — Saldo Finale del 30%:</strong> erogato a seguito del <strong>collaudo tecnico positivo</strong>, pubblicazione in produzione e rendicontazione delle fatture elettroniche sul portale Lepida.</li>
</ul>
</body>
</html>""",

        "documenti_pa/03_Comune_di_Bologna_Piano_Sportelli_Digitali_e_Regolamento_TARI_SUAP_2026.html": """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Comune di Bologna - Piano Sportelli Digitali AI di Quartiere e Regolamento TARI / SUAP 2026</title></head>
<body>
<h1>Comune di Bologna — Piano Sportelli Digitali Polifunzionali e Regole TARI / SUAP 2026</h1>
<p><strong>Ente:</strong> Comune di Bologna (Provincia di BO) | <strong>Delibera Giunta:</strong> DG-BO-2026-142 | <strong>Pratica Lepida Collegata:</strong> PRAT-2026-101 (BANDO-ER-2026-02, Importo: 118.000 EUR, Punteggio: 92/100, Stato: APPROVATA)</p>

<h2>1. Architettura dello Sportello Polifunzionale AI nei 6 Quartieri di Bologna</h2>
<p>Il Comune di Bologna ha attivato il progetto pilota <em>"Bologna Sportello Facile AI"</em> basato su <strong>Gemini Enterprise</strong> e <strong>Vertex AI Agent Engine</strong> in tutti i 6 Quartieri cittadini (<strong>Borgo Panigale-Reno, Navile, Porto-Saragozza, San Donato-San Vitale, Santo Stefano, Savena</strong>).</p>
<ul>
  <li><strong>Integrazione Knowledge Base & Tool ADK:</strong> l'assistente interroga in tempo reale i regolamenti comunali su Cloud Storage e i tool ADK standard (FunctionTool & AgentTool) su Vertex AI Agent Engine.</li>
  <li><strong>Riduzione Tempi di Attesa:</strong> riduzione del tempo medio di risposta allo sportello da 18 minuti a 4 minuti (-77%).</li>
</ul>

<h2>2. Regolamento TARI 2026 del Comune di Bologna (Scadenze e Agevolazioni)</h2>
<ul>
  <li><strong>Scadenze di pagamento TARI 2026:</strong>
    <ul>
      <li><strong>1ª Rata (Acconto 40%):</strong> entro il <strong>30 aprile 2026</strong></li>
      <li><strong>2ª Rata (Acconto 40%):</strong> entro il <strong>30 settembre 2026</strong></li>
      <li><strong>3ª Rata (Saldo 20% con conguaglio PEF):</strong> entro il <strong>2 dicembre 2026</strong></li>
      <li><strong>Pagamento in soluzione unica:</strong> entro il <strong>30 aprile 2026</strong> tramite avviso PagoPA o App IO.</li>
    </ul>
  </li>
  <li><strong>Esenzioni e Riduzioni TARI 2026 a Bologna:</strong>
    <ul>
      <li><strong>Nuclei familiari con ISEE fino a 15.000 EUR:</strong> riduzione automatica del <strong>30%</strong> sulla quota variabile.</li>
      <li><strong>Nuclei familiari con ISEE fino a 8.500 EUR o presenza di disabilità grave (L. 104/92 art. 3 c. 3):</strong> riduzione del <strong>65%</strong>.</li>
      <li><strong>Start-up innovative e nuove imprese giovanili (under 35) insediate a Bologna:</strong> <strong>esenzione del 100% della TARI per i primi 24 mesi</strong> dall'apertura della sede operativa.</li>
      <li><strong>Compostaggio domestico certificato (zone collinari e giardini privati):</strong> riduzione del <strong>15%</strong> sulla quota variabile.</li>
    </ul>
  </li>
</ul>

<h2>3. Tempi Procedimentali SUAP (Sportello Unico Attività Produttive) Bologna</h2>
<ul>
  <li><strong>SCIA di avvio esercizio commerciale di vicinato (fino a 250 mq):</strong> efficacia immediata alla ricevuta telematica SUAP; controllo formale entro <strong>30 giorni</strong>.</li>
  <li><strong>Autorizzazione occupazione suolo pubblico per dehors stagionali:</strong> termine massimo del procedimento <strong>30 giorni solari</strong> (ridotto a <strong>15 giorni</strong> per rinnovi senza modifiche).</li>
  <li><strong>Procedimento unico con Conferenza di Servizi asincrona (AUSL, ARPAE, Vigili del Fuoco):</strong> conclusione entro <strong>45 giorni</strong>.</li>
</ul>
</body>
</html>""",

        "documenti_pa/04_Comune_di_Modena_e_Unione_Terre_d_Argine_Piano_Cybersecurity_NIS2.html": """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Comune di Modena e Unione Terre d'Argine - Piano di Adeguamento Direttiva NIS2 e SOC Lepida</title></head>
<body>
<h1>Piano Operativo di Cybersecurity e Adeguamento Direttiva NIS2 (D.Lgs. 138/2024)</h1>
<p><strong>Enti Capofila:</strong> Comune di Modena e Unione delle Terre d'Argine (Carpi, Campogalliano, Novi di Modena, Soliera) | <strong>Pratica Collegata:</strong> PRAT-2026-103 (BANDO-ER-2026-03, Importo: 185.000 EUR, Punteggio: 85/100, Stato: APPROVATA)</p>

<h2>1. Misure Tecniche Obbligatorie per la Conformità NIS2 negli Enti Locali</h2>
<p>In attuazione della Direttiva UE 2022/2555 (NIS2) recepita con D.Lgs. 138/2024 e delle determinazioni ACN, il Comune di Modena e l'Unione delle Terre d'Argine hanno adottato il seguente standard minimo (riutilizzabile da tutti i Comuni dell'Emilia-Romagna):</p>
<ol>
  <li><strong>Federazione SIEM ed EDR col SOC Regionale Lepida (Servizio SRV-SOC-NIS2):</strong> invio in tempo reale dei log di autenticazione Active Directory/Google Workspace, firewall perimetrali e server anagrafe/tributi al SOC Lepida (operativo 24x7x365).</li>
  <li><strong>Autenticazione Multifattore (MFA) Obbligatoria:</strong> MFA phishing-resistant obbligatoria per il 100% degli amministratori di sistema, dei RUP e degli accessi VPN/remoti dei dipendenti comunali.</li>
  <li><strong>Strategia di Backup Immutabile 3-2-1:</strong> 3 copie dei dati, su 2 supporti distinti, di cui 1 copia immutabile (Object Lock WORM per 90 giorni) ospitata nel Datacenter Regionale Lepida di Bologna/Parma.</li>
  <li><strong>Allegato Tecnico B2 (Inventario Asset Critici NIS2):</strong> documento obbligatorio per l'approvazione dei finanziamenti sul Bando `BANDO-ER-2026-03` (la cui assenza comporta lo stato `INTEGRAZIONE_RICHIESTA`, come avvenuto per la pratica `PRAT-2026-106` del Comune di Ferrara).</li>
</ol>

<h2>2. Procedura e Tempistiche Tassative di Notifica Incidenti al CSIRT Italia (ACN)</h2>
<ul>
  <li><strong>Fase 1 — Pre-allarme (Early Warning):</strong> entro e non oltre <strong>24 ore</strong> dal momento in cui l'Ente viene a conoscenza di un incidente significativo, tramite il supporto del CERT Lepida.</li>
  <li><strong>Fase 2 — Notifica Completa dell'Incidente:</strong> entro e non oltre <strong>72 ore</strong> dal rilevamento, con valutazione della gravità, indicatori di compromissione (IoC) e impatto sui servizi comunali.</li>
  <li><strong>Fase 3 — Relazione Finale:</strong> entro <strong>30 giorni</strong> dalla notifica dell'incidente, con analisi della causa radice (Root Cause Analysis) e misure correttive implementate.</li>
</ul>
</body>
</html>""",

        "documenti_pa/05_Comune_di_Ravenna_e_Rimini_Progetto_Smart_City_Monitoraggio_Idrogeologico_e_Turismo.html": """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Comuni di Ravenna e Rimini - Smart City, Monitoraggio Idrogeologico LoRaWAN e Flussi Turistici</title></head>
<body>
<h1>Progetto Smart Territory Romagna: Monitoraggio Idrogeologico LoRaWAN e Mobilità Intelligente (Ravenna e Rimini)</h1>
<p><strong>Enti:</strong> Comune di Ravenna (`PRAT-2026-107`, Bando IoT `BANDO-ER-2026-04`, 88.000 EUR, Punteggio 91/100, APPROVATA) e Comune di Rimini (`PRAT-2026-111`, Bando AI `BANDO-ER-2026-02`, 110.000 EUR, Punteggio 89/100, APPROVATA).</p>

<h2>1. Rete di Monitoraggio Idrogeologico e Allerta Precoce Alluvioni (Comune di Ravenna e Bassa Romagna)</h2>
<p>Sulla rete regionale <strong>IoT LoRaWAN di Lepida</strong> sono stati installati <strong>45 sensori idrometrici ultrasonici e piezometrici</strong> lungo i fiumi Lamone, Montone, Ronco e i principali canali di bonifica del territorio ravennate:</p>
<table border="1">
<tr><th>Livello di Allerta</th><th>Soglia Idrometrica Rilevata</th><th>Frequenza Campionamento</th><th>Azione Automatica del Sistema</th></tr>
<tr><td><strong>Ordinario (Verde)</strong></td><td>Inferiore a 1,80 metri</td><td>Ogni 15 minuti</td><td>Archiviazione storica sul dataset BigQuery territoriale.</td></tr>
<tr><td><strong>Pre-Allerta (Gialla)</strong></td><td>Da 1,80 m a 2,39 metri</td><td>Ogni 5 minuti</td><td>Notifica automatica alla Centrale Operativa Polizia Locale e Protezione Civile Comunale.</td></tr>
<tr><td><strong>Allerta Arancione</strong></td><td>Da 2,40 m a 2,99 metri</td><td>Ogni 60 secondi</td><td>Apertura automatica pre-COC e allerta ai referenti tecnici comunali e Consorzio di Bonifica.</td></tr>
<tr><td><strong>Allerta Rossa (Critica)</strong></td><td>Pari o superiore a 3,00 metri</td><td>Tempo reale continuo (30 sec)</td><td>Predisposizione messaggio di allerta pubblica per i cittadini residenti nelle zone fluviali tramite App IO e pannelli a messaggio variabile.</td></tr>
</table>

<h2>2. Sportello AI Multilingua Turismo e Tributi Soggiorno (Comune di Rimini)</h2>
<p>Il Comune di Rimini ha implementato con `PRAT-2026-111` uno sportello digitale assistito da <strong>Gemini Enterprise</strong> per le strutture ricettive (oltre 1.200 hotel e B&B) e per i turisti:</p>
<ul>
  <li><strong>Imposta di Soggiorno Rimini 2026:</strong> dichiarazione telematica mensile entro il giorno 16 del mese successivo; tariffe da 1,50 EUR/notte (strutture 2 stelle) a 4,00 EUR/notte (strutture 4 e 5 stelle) fino a un massimo di 7 pernottamenti consecutivi.</li>
  <li><strong>Permessi ZTL e Carico/Scarico Fornitori Hotel:</strong> rilascio pass digitale temporaneo in 5 minuti tramite verifica automatica targa su piattaforma comunale connessa a Lepida.</li>
</ul>
</body>
</html>""",

        "documenti_pa/06_Comune_di_Ferrara_e_Parma_Digitalizzazione_Edilizia_SUE_e_Telemedicina_AUSL.html": """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Comuni di Ferrara e Parma - Digitalizzazione Archivi Edilizia SUE e Telemedicina Territoriale AUSL</title></head>
<body>
<h1>Digitalizzazione Pratiche Edilizie SUE (Ferrara) e Connettività Telemedicina Case della Comunità (Parma)</h1>

<h2>1. Comune di Ferrara — Stato Pratica NIS2 e Dematerializzazione Sportello Unico Edilizia (SUE)</h2>
<ul>
  <li><strong>Stato Pratica Cybersecurity (`PRAT-2026-106` su `BANDO-ER-2026-03`):</strong> il Comune di Ferrara ha presentato una richiesta da <strong>160.000 EUR</strong> ottenendo in prima seduta un punteggio di <strong>64/100</strong> (stato: <strong>INTEGRAZIONE_RICHIESTA</strong>). Per superare la soglia minima di 70/100 e sbloccare il cofinanziamento del 90%, il CISO del Comune deve trasmettere entro <strong>15 giorni solari</strong> l'<strong>Allegato Tecnico B2</strong> con l'inventario completo degli asset critici NIS2 e il piano di federazione SIEM col SOC Lepida.</li>
  <li><strong>Archivio Digitale SUE (Sportello Unico Edilizia):</strong> digitalizzate oltre 45.000 pratiche edilizie storiche (CILA, SCIA, Permessi di Costruire e Condoni 1985/1994/2003) conservate nel Polo Archivistico Regionale (ParER) di Lepida.
    <ul>
      <li><strong>Tempi di Accesso agli Atti Edilizi (Legge 241/90):</strong> grazie alla ricerca semantica con Gemini Enterprise sugli archivi indicizzati, il tempo medio di evasione delle richieste di accesso agli atti per compravendite immobiliari e bonus edilizi è sceso da <strong>30 giorni a 3 giorni lavorativi</strong>.</li>
      <li><strong>Diritti di Segreteria SUE Ferrara 2026:</strong> 50 EUR per accesso agli atti digitale (gratuito se la pratica è già interamente nativo-digitale post-2020); 120 EUR per CILA; 250 EUR per SCIA edilizia.</li>
    </ul>
  </li>
</ul>

<h2>2. Comune di Parma e AUSL — Sportello AI (`PRAT-2026-104`) e Telemedicina nelle Case della Comunità</h2>
<ul>
  <li><strong>Pratica Comune di Parma (`PRAT-2026-104` su `BANDO-ER-2026-02`):</strong> importo richiesto <strong>95.000 EUR</strong>, punteggio tecnico <strong>78/100</strong> (sopra soglia 70/100), attualmente in stato <strong>IN_ISTRUTTORIA</strong> in attesa della sola specifica tecnica del connettore verso il protocollo informatico comunale.</li>
  <li><strong>Rete 10 Gbps per le Case della Comunità:</strong> rilegate sulla dorsale in fibra ottica Lepida 14 Case della Comunità tra Parma e provincia (Fidenza, Borgotaro, Langhirano, Colorno) per garantire servizi di telecardiologia, teledermatologia e consultazione immediata del Fascicolo Sanitario Elettronico (FSE 2.0).</li>
</ul>
</body>
</html>""",

        "documenti_pa/07_Unione_Comuni_Appennino_Bolognese_e_Romagna_Forlivese_Servizi_Associati_Montani.html": """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Unioni Montane (Appennino Bolognese e Romagna Forlivese) - Servizi ICT Associati e Scuole Digitali</title></head>
<body>
<h1>Gestione Associata dei Servizi ICT e Sportelli Digitali nei Comuni Montani dell'Emilia-Romagna</h1>
<p><strong>Enti Attuatori:</strong></p>
<ul>
  <li><strong>Unione dei Comuni dell'Appennino Bolognese (Provincia di BO):</strong> comprende 11 Comuni montani tra cui Vergato, Castiglione dei Pepoli, Marzabotto, Gaggio Montano, Grizzana Morandi, Monzuno, San Benedetto Val di Sambro, Camugnano, Lizzano in Belvedere, Castel d'Aiano, Castel di Casio. Pratica `PRAT-2026-102` su `BANDO-ER-2026-01` (145.000 EUR, Punteggio 88/100, <strong>APPROVATA</strong>).</li>
  <li><strong>Unione dei Comuni della Romagna Forlivese (Provincia di FC):</strong> comprende 15 Comuni tra cui Santa Sofia, Bagno di Romagna, Galeata, Premilcuore, Civitella di Romagna, Meldola, Predappio, Portico e San Benedetto, Rocca San Casciano, Tredozio, Modigliana, Castrocaro Terme, Dovadola, Forlimpopoli, Bertinoro.</li>
</ul>

<h2>1. Vantaggio Finanziario Massimizzato per le Unioni Montane (Premialità 95%)</h2>
<p>Presentando domanda come <strong>Unione di Comuni (+5%)</strong> situata in <strong>Territorio Montano / Area Interna (+5%)</strong> e includendo <strong>Comuni sotto i 15.000 abitanti (+5%)</strong>, le Unioni Montane ottengono fino a <strong>+15% di premialità</strong>, raggiungendo il <strong>tetto massimo del 95% di contributo regionale a fondo perduto</strong> su tutti i bandi Lepida 2026!</p>
<ul>
  <li>Su un progetto da <strong>145.000 EUR</strong> (come `PRAT-2026-102` dell'Appennino Bolognese sul bando Fibra con base 85%), la quota applicata sale al <strong>95%</strong>: la Regione/Lepida copre <strong>137.750 EUR a fondo perduto</strong> e l'Unione versa solo <strong>7.250 EUR</strong> totali (meno di 700 EUR per singolo Comune!).</li>
</ul>

<h2>2. Modello "Sportello Digitale Assistito di Montagna"</h2>
<p>Per contrastare il divario digitale della popolazione anziana residente nelle frazioni appenniniche, le Unioni hanno attivato <strong>12 Sportelli Digitali Assistiti</strong> presso i municipi e le biblioteche comunali:</p>
<ul>
  <li>Gli operatori di sportello usano l'agente <strong>Gemini Enterprise</strong> per compilare in 3 minuti pratiche di esenzione ticket sanitario, bonus trasporti montani, iscrizione trasporto scolastico e rilascio identità digitale SPID/LepidaID.</li>
  <li>Rilegati in fibra ottica simmetrica a <strong>10 Gbps</strong> 6 plessi scolastici montani nell'Appennino Bolognese e 4 municipi collinari nella Romagna Forlivese.</li>
</ul>
</body>
</html>""",

        "documenti_pa/08_Modello_Determina_Dirigenziale_e_Capitolato_Adesione_Servizi_Lepida.html": """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Modello Ufficiale Determina Dirigenziale di Affidamento In-House a Lepida ScpA (Art. 7 D.Lgs. 36/2023)</title></head>
<body>
<h1>Schema Ufficiale di Determina Dirigenziale per Affidamento In-House a Lepida ScpA e Adesione ai Bandi 2026</h1>
<p><strong>Codice Template:</strong> MOD-DET-INHOUSE-LEPIDA-2026 | <strong>Riferimento Normativo:</strong> Art. 7 D.Lgs. 36/2023 (Codice dei Contratti Pubblici), L.R. Emilia-Romagna n. 11/2004, CAD (D.Lgs. 82/2005).</p>

<h2>Struttura Obbligatoria in 6 Sezioni (da usare per la redazione di Determine Dirigenziali)</h2>

<h3>SEZIONE 1 — INTESTAZIONE DELL'ENTE E INDIVIDUAZIONE DEL RUP</h3>
<ul>
  <li><strong>Ente Adottante:</strong> [Indicare Nome Comune / Unione di Comuni e Provincia]</li>
  <li><strong>Settore / Direzione:</strong> Settore Innovazione Tecnologica, Transizione Digitale e Sistemi Informativi</li>
  <li><strong>Responsabile Unico del Progetto (RUP) ai sensi dell'art. 15 D.Lgs. 36/2023:</strong> [Nome/Ruolo RUP]</li>
  <li><strong>Oggetto:</strong> Approvazione progetto esecutivo, adesione al Bando Regionale Lepida [Codice Bando] e contestuale affidamento in-house a Lepida ScpA dei servizi [Codici Servizio da Catalogo CAT-LEPIDA-2026-V1].</li>
</ul>

<h3>SEZIONE 2 — PREMESSE DI FATTO E DI DIRITTO</h3>
<ul>
  <li>Richiamata la Legge Regionale Emilia-Romagna n. 11/2004 che individua in <strong>Lepida ScpA</strong> lo strumento operativo in-house della Regione e degli Enti Locali soci per lo sviluppo delle infrastrutture di telecomunicazione, dei servizi Cloud qualificati ACN e dell'innovazione digitale;</li>
  <li>Dato atto che l'Ente è socio di Lepida ScpA ed esercita su di essa, congiuntamente agli altri Enti soci, il controllo analogo congiunto;</li>
  <li>Visto il Bando Regionale [Codice e Titolo Bando] gestito da Lepida ScpA e le relative Linee Guida `LG-LEPIDA-2026-REV4`.</li>
</ul>

<h3>SEZIONE 3 — MOTIVAZIONE DI CONGRUITÀ ECONOMICA E VANTAGGI PER LA COLLETTIVITÀ (ART. 7 COMMA 2 D.LGS. 36/2023)</h3>
<ul>
  <li>Attestato che i canoni del Listino Ufficiale Lepida 2026 (`CAT-LEPIDA-2026-V1`) risultano inferiori di oltre il 22% rispetto ai benchmark di mercato Consip/MEPA a parità di SLA (99,95%–99,98%) e includono l'integrazione nativa con la Rete Lepida, il SOC Regionale NIS2 e il Datacenter Qualificato ACN;</li>
  <li>Rilevato che il progetto garantisce il riuso delle soluzioni già validate dai Comuni dell'Emilia-Romagna.</li>
</ul>

<h3>SEZIONE 4 — QUADRO ECONOMICO, PREMIALITÀ E PIANO FINANZIARIO IN 3 TRANCHE</h3>
<ul>
  <li><strong>Importo Complessivo del Progetto:</strong> [Importo Totale in EUR]</li>
  <li><strong>Quota Base Bando:</strong> [X]% + <strong>Premialità Territoriali Applicate:</strong> [+5% Montano / +5% Unione / +5% <15.000 ab.] = <strong>Quota Finale a Fondo Perduto: [Y]%</strong> (max 95%)</li>
  <li><strong>Contributo Regionale a Fondo Perduto:</strong> [Importo Contributo EUR] (erogato in 3 tranche: 40% Anticipo a 30 gg da CUP, 30% SAL Intermedio al 50% attività, 30% Saldo Finale a collaudo)</li>
  <li><strong>Quota Residua di Cofinanziamento a Carico del Bilancio dell'Ente:</strong> [Importo Quota Ente EUR] imputata sul Capitolo ICT del Bilancio Pluriennale 2026–2028.</li>
</ul>

<h3>SEZIONE 5 — CLAUSOLE OBBLIGATORIE DI CONFORMITÀ (ACN, NIS2, GDPR E AI ACT UE 2024/1689)</h3>
<ul>
  <li>Qualora il progetto preveda soluzioni di Intelligenza Artificiale (`SRV-AI-SPORTELLO`), è fatto obbligo di rispettare il principio di sorveglianza umana (<em>Human-in-the-Loop</em>), l'informativa trasparente agli utenti, l'anonimizzazione PII tramite Cloud DLP/Model Armor e la conservazione dei log di audit per 24 mesi in Region UE (`europe-west8` Milano o `europe-west1`).</li>
</ul>

<h3>SEZIONE 6 — DISPOSITIVO DELLA DETERMINA</h3>
<ol>
  <li>Di approvare il progetto e il relativo Quadro Economico;</li>
  <li>Di affidare in modalità in-house providing a Lepida ScpA l'attivazione dei servizi [Codici Servizio];</li>
  <li>Di dare atto che l'affidamento in-house è esente da CIG ordinario (soggetto a tracciabilità tramite codice <strong>CUP</strong> di progetto);</li>
  <li>Di trasmettere il presente atto a Lepida ScpA per l'istruttoria e l'erogazione della 1ª Tranche di anticipo (40%).</li>
</ol>
</body>
</html>""",

        "documenti_pa/09_Prontuario_FAQ_Cittadini_e_Imprese_Sportelli_Comunali_Emilia_Romagna.html": """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Prontuario Ufficiale FAQ Sportelli Comunali Emilia-Romagna (Anagrafe, URP, Tributi, Scuola, Edilizia)</title></head>
<body>
<h1>Prontuario Ufficiale Procedure e FAQ per gli Sportelli Polifunzionali dei Comuni dell'Emilia-Romagna</h1>
<p><strong>Documento:</strong> FAQ-URP-ER-2026 | <strong>Destinatari:</strong> Operatori URP, Anagrafe, Tributi e Assistenti Digitali Gemini Enterprise.</p>

<h2>1. Anagrafe e Stato Civile</h2>
<ul>
  <li><strong>Cambio di Residenza in Tempo Reale (ANPR):</strong> la dichiarazione si presenta online sul portale ANPR (con SPID/CIE) o allo sportello. L'ufficiale d'anagrafe registra la variazione entro <strong>2 giorni lavorativi</strong> dalla ricezione, con effetti giuridici immediati dalla data di presentazione. La Polizia Locale ha <strong>45 giorni</strong> per effettuare gli accertamenti dimora abituale (silenzio-assenso trascorsi i 45 giorni).</li>
  <li><strong>Rilascio Carta d'Identità Elettronica (CIE):</strong>
    <ul>
      <li><strong>Costo:</strong> <strong>22,21 EUR</strong> per primo rilascio o rinnovo alla scadenza naturale (a partire da 180 giorni prima della scadenza); <strong>27,37 EUR</strong> in caso di duplicato per smarrimento, furto o deterioramento.</li>
      <li><strong>Tempi di consegna:</strong> spedizione da parte del Poligrafico dello Stato entro <strong>6 giorni lavorativi</strong> presso il domicilio indicato dal cittadino o in Municipio.</li>
      <li><strong>Validità:</strong> 3 anni per minori di 3 anni; 5 anni per minori tra 3 e 18 anni; 10 anni per maggiorenni (con scadenza nel giorno del compleanno).</li>
    </ul>
  </li>
</ul>

<h2>2. Servizi Educativi e Scolastici</h2>
<ul>
  <li><strong>Iscrizione Nidi d'Infanzia Comunali e Misura Regionale "Al Nido con la Regione":</strong>
    <ul>
      <li>Apertura bando annuale: dal <strong>1° aprile al 15 maggio</strong> di ogni anno, esclusivamente online con credenziali SPID/CIE/LepidaID.</li>
      <li><strong>Abbattimento Rette (Misura Regionale Emilia-Romagna):</strong> per le famiglie con <strong>ISEE fino a 26.000 EUR</strong> residenti nei Comuni normali (e fino a <strong>40.000 EUR</strong> nei Comuni montani e delle aree interne!) è previsto l'azzeramento o la riduzione fino al <strong>100% della retta mensile del nido</strong> grazie ai fondi FSE+ regionali.</li>
    </ul>
  </li>
</ul>

<h2>3. Tributi Comunali, Passi Carrabili e Occupazione Suolo Pubblico</h2>
<ul>
  <li><strong>Autorizzazione Passo Carrabile:</strong> domanda in bollo da 16,00 EUR tramite portale telematico comunale, rilascio concessione e cartello numerato entro <strong>30 giorni</strong> (costo cartello: 25,00 EUR).</li>
  <li><strong>Esenzione Canone Unico Patrimoniale per Cantieri Edilizi PNRR e Riqualificazione Energetica:</strong> nei Comuni capoluogo dell'Emilia-Romagna che hanno aderito al protocollo regionale è prevista una riduzione del <strong>50% del canone di occupazione suolo pubblico</strong> per i primi 60 giorni di ponteggio.</li>
</ul>
</body>
</html>""",

        "documenti_pa/10_Linee_Guida_Governance_AI_Atto_Europeo_IA_e_Checklist_Conformita_PA.html": """<!DOCTYPE html>
<html lang="it">
<head><meta charset="utf-8"><title>Linee Guida Governance Intelligenza Artificiale nella PA (AI Act UE 2024/1689) e Checklist RUP</title></head>
<body>
<h1>Linee Guida per la Governance dell'Intelligenza Artificiale negli Enti dell'Emilia-Romagna (AI Act UE 2024/1689)</h1>
<p><strong>Codice Documento:</strong> GOV-AI-PA-2026 | <strong>Autorità:</strong> Comitato Regionale Transizione Digitale & DPO Lepida ScpA.</p>

<h2>1. I 5 Principi Inderogabili per l'Adozione di Agenti AI nei Comuni e nelle AUSL</h2>
<ol>
  <li><strong>Sorveglianza Umana Obbligatoria (<em>Human-in-the-Loop</em> — Art. 14 AI Act):</strong> nessun agente AI può adottare in via autonoma e definitiva un provvedimento amministrativo, un diniego di beneficio economico o una sanzione. L'agente predispone l'istruttoria, il calcolo o la bozza di determina, che deve sempre essere verificata e sottoscritta digitalmente dal <strong>Responsabile Unico del Progetto (RUP)</strong> o dal Dirigente competente.</li>
  <li><strong>Obbligo di Trasparenza verso l'Utente (Art. 50 AI Act):</strong> ogni interfaccia di sportello rivolta a cittadini o imprese deve dichiarare esplicitamente all'avvio della sessione: <em>"Stai interagendo con l'Assistente Digitale basato su Intelligenza Artificiale dell'Ente, alimentato da fonti ufficiali certificate"</em>.</li>
  <li><strong>Verificabilità delle Fonti e Grounding:</strong> per prevenire allucinazioni su norme, scadenze o aliquote tributarie, gli agenti devono operare con <strong>Grounding vincolato ai Data Store ufficiali</strong> (Cloud Storage / BigQuery) mostrando sempre le citazioni ai documenti comunali o regionali utilizzati.</li>
  <li><strong>Protezione dei Dati Personali (GDPR) e Residenza in Unione Europea:</strong>
    <ul>
      <li>Tutti i dati e i log devono risiedere in <strong>Region dell'Unione Europea</strong> (es. `europe-west8` Milano o `europe-west1` Belgio).</li>
      <li>I dati inviati ai modelli su Vertex AI / Gemini Enterprise <strong>non vengono mai utilizzati per l'addestramento dei modelli fondazionali</strong>.</li>
      <li>È obbligatorio attivare i filtri <strong>Model Armor</strong> contro prompt injection e <strong>Cloud DLP</strong> per il mascheramento di codici fiscali, IBAN e dati sanitari.</li>
    </ul>
  </li>
  <li><strong>Tracciabilità e Conservazione dei Log di Audit per 24 Mesi:</strong> ogni interazione, invocazione di tool ADK tracciata via OpenTelemetry (Cloud Trace) e versione del documento citato deve essere tracciata in Cloud Logging per un periodo minimo di <strong>24 mesi</strong> ai fini di verifica ispettiva e accesso civico.</li>
</ol>
</body>
</html>""",
    }

    for obj_name, html_content in docs.items():
        upload_gcs_object(token, obj_name, html_content)


def main():
    print("==================================================================")
    print(f" Inizializzazione Dati Workshop Lepida su progetto: {PROJECT_ID}")
    print(f" Bucket GCS Univoco: gs://{BUCKET_NAME}")
    print("==================================================================")
    token = get_token()
    ensure_bq_dataset(token)
    populate_bigquery(token)
    ensure_gcs_bucket(token)
    populate_gcs_docs(token)
    print("\n✅ Setup Dati completato con successo!")
    print(f"   - Dataset BigQuery : {PROJECT_ID}.{DATASET_ID} (tabelle: bandi_regionali, pratiche_enti)")
    print(f"   - Bucket GCS Univoco: gs://{BUCKET_NAME}/documenti_pa/ (10 documenti HTML caricati)")


if __name__ == "__main__":
    main()
