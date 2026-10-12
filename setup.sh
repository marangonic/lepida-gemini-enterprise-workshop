#!/usr/bin/env bash
# ==============================================================================
# ONE-CLICK BULLET-PROOF SETUP — WORKSHOP LEPIDA & COMUNI EMILIA-ROMAGNA
# Focus Partecipanti:
#   - MODULO 2: Creare il Proprio Chat Agent No-Code in Gemini Enterprise (30 min)
#   - MODULO 3: Creare e Utilizzare le "Skills" in Gemini Enterprise (45 min)
#
# Cosa automatizza in ~25 secondi per ciascuno dei 26 ambienti Qwiklabs:
#   [Passo 1/3] Abilitazione API Google Cloud (Gemini Enterprise, Storage, Vertex AI, BigQuery)
#   [Passo 2/3] Creazione Bucket GCS Univoco (gs://<PROJECT_ID>-lepida-comuni-er)
#               + Upload dei 10 Documenti Pubblici Lepida & Comuni ER
#               + Creazione Dataset BigQuery (lepida_territorio)
#   [Passo 3/3] Attivazione Licenza Gemini Enterprise (free_trial_gemini) + Google Identity,
#               Creazione e Indicizzazione Istantanea (2s) del Connettore GCS (lepida-comuni-er-ds),
#               Creazione automatica della Gemini Enterprise App ("Lepida & Comuni ER Assistant")
#               con Chat Agent (no-code-agent-builder) e Skills già sbloccati,
#               e stampa del LINK DIRETTO alla Web App di Gemini Enterprise!
#
# Opzioni aggiuntive (per il Docente o per caricare la soluzione già pronta):
#   --solution / --auto-ui : Crea e pubblica automaticamente anche il Chat Agent Multi-Livello
#                            (con modello Gemini 3.8 Flash) e le 3 Skills nella Web App
#   --instructor           : Esegue anche il deploy dell'Agente ADK + MCP Toolbox (:5000) + Soluzione
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

INSTRUCTOR_MODE=false
SOLUTION_MODE=false
for arg in "$@"; do
  case "$arg" in
    --instructor|--full-deploy)
      INSTRUCTOR_MODE=true
      SOLUTION_MODE=true
      ;;
    --solution|--auto-ui)
      SOLUTION_MODE=true
      ;;
  esac
done

export PATH="$HOME/.local/bin:$PATH"
export PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
if [[ -z "${PROJECT_ID}" ]]; then
  echo "[ERRORE] Nessun progetto Google Cloud rilevato. Esegui: gcloud config set project <PROJECT_ID>"
  exit 1
fi
export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
export PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")"
export LEPIDA_BUCKET_NAME="${LEPIDA_BUCKET_NAME:-${PROJECT_ID}-lepida-comuni-er}"

echo ""
echo "================================================================================"
echo " 🚀 AVVIO SETUP AUTOMATICO WORKSHOP LEPIDA — GEMINI ENTERPRISE (MODULI 2 & 3)"
echo "    Progetto Qwiklabs : ${PROJECT_ID} (Numero: ${PROJECT_NUMBER})"
echo "    Bucket GCS Univoco: gs://${LEPIDA_BUCKET_NAME}"
echo "================================================================================"
echo ""

# [Passo 1/3] Abilitazione API
echo "⏳ [Passo 1/3] Attivazione dei servizi Google Cloud..."
gcloud services enable \
  discoveryengine.googleapis.com \
  storage.googleapis.com \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  logging.googleapis.com \
  --project="${PROJECT_ID}" --quiet
echo "✅ [Passo 1/3] Servizi Google Cloud attivati."
echo ""

# [Passo 2/3] Creazione Bucket GCS Univoco + 10 Documenti + BigQuery
echo "⏳ [Passo 2/3] Creazione Bucket GCS univoco (gs://${LEPIDA_BUCKET_NAME}) e caricamento dei 10 documenti..."
python3 setup_workshop_data.py
echo "✅ [Passo 2/3] Bucket GCS univoco e 10 documenti dei Comuni ER / Lepida pronti."
echo ""

# [Passo 3/3] Attivazione Licenza, Connettore GCS e App Gemini Enterprise con Chat Agent & Skills sbloccati
echo "⏳ [Passo 3/3] Creazione Connettore GCS (lepida-comuni-er-ds) e App Gemini Enterprise (Lepida & Comuni ER Assistant)..."
python3 setup_ge_datastore.py --create-app --wait
echo "✅ [Passo 3/3] App Gemini Enterprise e Connettore GCS pronti e indicizzati!"
echo ""

if [[ "${INSTRUCTOR_MODE}" == "true" ]]; then
  echo "⏳ [Modalità Docente] Preparazione MCP Toolbox (:5000) e deploy Agente ADK su Vertex AI Agent Engine..."
  if [[ -f "tools.yaml.template" ]]; then
    envsubst '${PROJECT_ID}' < tools.yaml.template > tools.yaml
  fi
  cat <<EOF > lepida_agent/.env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
GOOGLE_CLOUD_LOCATION=global
MODEL=gemini-2.5-flash
EOF
  pip install --quiet --upgrade -r requirements.txt
  if [[ ! -x "./toolbox" ]]; then
    curl -s -L -o toolbox https://storage.googleapis.com/genai-toolbox/v0.16.0/linux/amd64/toolbox
    chmod +x toolbox
  fi
  if ! ss -tulpn 2>/dev/null | grep -q ":5000 "; then
    nohup ./toolbox --tools-file tools.yaml --port 5000 </dev/null >/tmp/toolbox.log 2>&1 &
    sleep 2
  fi
  unset MCP_TOOLBOX_URL
  python3 deploy_adk_agent.py
  RE_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
  for ROLE in "roles/bigquery.user" "roles/bigquery.dataEditor" "roles/serviceusage.serviceUsageConsumer"; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${RE_SA}" \
      --role="${ROLE}" \
      --quiet >/dev/null
  done
fi

if [[ "${SOLUTION_MODE}" == "true" ]]; then
  echo "⏳ [Modalità Soluzione] Pubblicazione automatica del Chat Agent Multi-Livello (Gemini 3.8 Flash) e delle 3 Skills..."
  python3 register_ge_agent.py
  echo "✅ [Modalità Soluzione] Chat Agent Multi-Livello (Gemini 3.8 Flash) e 3 Skills pubblicati nella Web App!"
  echo ""
fi

WEB_APP_URL="$(cat "${SCRIPT_DIR}/WEB_APP_URL.txt" 2>/dev/null || echo "https://console.cloud.google.com/gemini-enterprise/apps?project=${PROJECT_ID}")"

echo "================================================================================"
echo " 🎉 CONFIGURAZIONE COMPLETATA! TUTTO PRONTO PER I MODULI 2 E 3"
echo "================================================================================"
echo ""
echo " 🌐 1️⃣  CLICCA QUI PER APRIRE DIRETTAMENTE LA WEB APP DI GEMINI ENTERPRISE:"
echo "        ${WEB_APP_URL}"
echo ""
echo " 🏛️ 2️⃣  CONSOLE GOOGLE CLOUD — GEMINI ENTERPRISE (opzionale):"
echo "        https://console.cloud.google.com/gemini-enterprise/apps?project=${PROJECT_ID}"
echo ""
echo " 📂 3️⃣  IL TUO BUCKET GCS UNIVOCO E IL CONNETTORE GIÀ COLLEGATO:"
echo "        Bucket     : gs://${LEPIDA_BUCKET_NAME}/documenti_pa/"
echo "        Data Store : Corpus Documentale Lepida e Comuni Emilia-Romagna 2026 (lepida-comuni-er-ds)"
echo ""
echo " 🤖 4️⃣  ORA PUOI INIZIARE SUBITO NELLA WEB APP:"
echo "        - MODULO 2 (30 min): Crea il tuo Chat Agent No-Code con modello 'Gemini 3.8 Flash'"
echo "        - MODULO 3 (45 min): Crea e utilizza le 3 Skills in Gemini Enterprise"
echo "================================================================================"
