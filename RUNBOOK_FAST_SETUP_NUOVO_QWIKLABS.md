# Runbook Fast-Setup: Rilancio Rapido del Workshop Lepida su un Nuovo Qwiklabs

Questa guida raccoglie tutti gli script e i passaggi salvati per ri-preparare da zero un nuovo ambiente temporaneo **Qwiklabs** (con un nuovo `PROJECT_ID` e un nuovo utente `student-*@qwiklabs.net`) nel minor tempo possibile.

---

## 1. Dove sono salvati i file e le automazioni

Tutti gli asset sono stati resi **completamente dinamici** (nessun `PROJECT_ID` cablato nel codice: viene rilevato automaticamente da `GOOGLE_CLOUD_PROJECT`, `DEVSHELL_PROJECT_ID` o `gcloud config get-value project`) e salvati in tre livelli:

1. **Kit Locale Completo (Sorgenti + Archivio Portabile da 29 KB):**
   - Cartella di lavoro: [/usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/](file:///usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/)
   - Pacchetto compresso pronto all'upload: [lepida_workshop_kit.tar.gz](file:///usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/lepida_workshop_kit.tar.gz)
   - Script master one-shot: [bootstrap_lepida_lab.sh](file:///usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/bootstrap_lepida_lab.sh)
   - Script creazione Data Store + App Gemini Enterprise: [setup_ge_datastore.py](file:///usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/setup_ge_datastore.py)
   - Script registrazione automatica Agente ADK in Gemini Enterprise: [register_ge_agent.py](file:///usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/register_ge_agent.py)
   - Script popolamento BigQuery + Documenti GCS: [setup_workshop_data.py](file:///usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/setup_workshop_data.py)
   - Template MCP Toolbox: [tools.yaml.template](file:///usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/tools.yaml.template)
   - Guida Partecipanti: [GUIDA_PARTECIPANTI_WORKSHOP_LEPIDA.md](file:///usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/GUIDA_PARTECIPANTI_WORKSHOP_LEPIDA.md)

2. **Skill di Automazione per Jetski:**
   - **Login Qwiklabs & ToS:** [qwiklabs-login/SKILL.md](file:///usr/local/google/home/marangonic/.gemini/config/skills/qwiklabs-login/SKILL.md)
   - **Provisioning Completo Workshop Lepida:** [lepida-workshop-setup/SKILL.md](file:///usr/local/google/home/marangonic/.gemini/config/skills/lepida-workshop-setup/SKILL.md)

---

## 2. Modalità 1 — Rilancio Automatico tramite Agente (Zero Comandi Manuali)

Quando avvii un nuovo Qwiklabs, ti basta incollare in chat le 4 informazioni del nuovo lab:
- `student-XX-YYYYYYYYYYYY@qwiklabs.net`
- `<PASSWORD>`
- `qwiklabs-gcp-XX-YYYYYYYYYYYY`
- `<URL_GOOGLE_SSO>`

e chiedere:
- **"Fai il setup base del workshop Lepida sul nuovo Qwiklabs"** *(~90 secondi: prepara BigQuery, GCS, MCP Toolbox sulla porta 5000 e ADK locale per far svolgere il lab o usare `adk web`)*, oppure
- **"Fai il full deploy del workshop Lepida sul nuovo Qwiklabs"** *(~5 minuti: esegue tutto quanto sopra + deploy su Vertex AI Agent Engine + IAM + creazione App Gemini Enterprise + Data Store documentale + pubblicazione dell'agente ADK in Gemini Enterprise)*.

---

## 3. Modalità 2 — Esecuzione Rapida da Terminale / Cloud Shell

Se vuoi lanciare tu stesso il setup dalla tua workstation (dopo il login Qwiklabs in `/tmp/gcloud-qwiklabs`) verso un nuovo progetto `<NUOVO_PROJECT_ID>`:

### Passo A — Caricamento del Kit (`lepida_workshop_kit.tar.gz`) nel nuovo progetto (15 secondi)
```bash
export CLOUDSDK_CONFIG=/tmp/gcloud-qwiklabs
export GOOGLE_CLOUD_PROJECT="<NUOVO_PROJECT_ID>"
gcloud config set project "${GOOGLE_CLOUD_PROJECT}"

# 1. Crea subito bucket GCS, dataset BigQuery lepida_territorio e documenti HTML
python3 /usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/setup_workshop_data.py

# 2. Carica l'archivio del kit (29 KB) sul bucket GCS del lab e scompattalo in Cloud Shell ~/lepida_workshop
gcloud storage cp /usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/lepida_workshop_kit.tar.gz \
  gs://${GOOGLE_CLOUD_PROJECT}-bucket/lepida_workshop/lepida_workshop_kit.tar.gz

gcloud cloud-shell ssh --authorize-session --project="${GOOGLE_CLOUD_PROJECT}" \
  --command="mkdir -p ~/lepida_workshop && gcloud storage cp gs://${GOOGLE_CLOUD_PROJECT}-bucket/lepida_workshop/lepida_workshop_kit.tar.gz /tmp/kit.tar.gz && tar -xzf /tmp/kit.tar.gz -C ~/lepida_workshop && chmod +x ~/lepida_workshop/bootstrap_lepida_lab.sh"
```

### Passo B — Scelta del Livello di Setup in Cloud Shell

#### Opzione 1: Setup Base (per far eseguire il Workshop ai Partecipanti o usare `adk web` — ~90 secondi)
Dentro il terminale di Cloud Shell:
```bash
cd ~/lepida_workshop
./bootstrap_lepida_lab.sh
```
Questo comando:
1. Abilita le API (`aiplatform`, `discoveryengine`, `bigquery`, `storage`, `logging`).
2. Genera `tools.yaml` e `lepida_agent/.env` con il nuovo `PROJECT_ID`.
3. Popola BigQuery (`lepida_territorio.bandi_regionali` e `lepida_territorio.pratiche_enti`) e GCS (`gs://${PROJECT_ID}-bucket/lepida_docs/*.html`).
4. Scarica `./toolbox` v0.16.0 e lo avvia in background sulla porta `5000`.
5. Installa `google-cloud-aiplatform[agent_engines,adk]` e `toolbox-core`.

Subito dopo puoi lanciare `adk web`:
```bash
export MCP_TOOLBOX_URL="http://127.0.0.1:5000"
adk web --port 8080 --allow_origins "*"
```

#### Opzione 2: Full Deploy End-to-End (Demo Completa Pronta fino a Gemini Enterprise — ~5 minuti)
Dentro il terminale di Cloud Shell:
```bash
cd ~/lepida_workshop
./bootstrap_lepida_lab.sh --full-deploy
```
Oltre ai 5 passi del Setup Base, esegue automaticamente:
6. Creazione del Data Store documentale `lepida-normativa-bandi-ds`, importazione dei 3 documenti HTML da GCS e creazione dell'App Gemini Enterprise **`Lepida Workspace Assistant`** ([setup_ge_datastore.py](file:///usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/setup_ge_datastore.py)).
7. Deploy di `lepida_agent` su **Vertex AI Agent Engine** (`us-central1`).
8. Assegnazione dei ruoli `roles/bigquery.user` e `roles/bigquery.dataEditor` al Service Agent `service-<PROJECT_NUMBER>@gcp-sa-aiplatform-re.iam.gserviceaccount.com`.
9. Registrazione automatica dell'agente ADK **`Assistente Bandi e Pratiche Lepida`** dentro Gemini Enterprise con permessi `ALL_USERS` ([register_ge_agent.py](file:///usr/local/google/home/marangonic/.gemini/jetski/scratch/lepida-workshop/register_ge_agent.py)).
