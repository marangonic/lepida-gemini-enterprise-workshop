#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-rootprj-377111}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"

echo "=================================================================="
echo " Setup & Avvio Locale in Cloud Shell di 'cloud_search_agent' (ADK)"
echo " Progetto: ${PROJECT_ID} | Regione: ${REGION}"
echo "=================================================================="

gcloud config set project "${PROJECT_ID}"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

pip install --upgrade pip -q
pip install -r requirements.txt -q

export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="${PROJECT_ID}"
export GOOGLE_CLOUD_LOCATION="${REGION}"
export GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
export ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=true

echo ""
echo "✅ Avvio di ADK Web UI sulla porta 8080..."
echo "👉 In Cloud Shell clicca su 'Web Preview' -> 'Preview on port 8080'"
echo "   e seleziona l'agente 'cloud_search_agent' dal menu in alto a sinistra."
echo ""

adk web --port 8080 --allow_origins "*"
