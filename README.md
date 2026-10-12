# Workshop Lepida ScpA & Comuni dell'Emilia-Romagna — Gemini Enterprise (Moduli 2 & 3)

Repository ufficiale del Workshop pratico su **Google Cloud Gemini Enterprise** dedicato a **Lepida ScpA** e ai **Comuni dell'Emilia-Romagna**.

---

## 🚀 Avvio Rapido in Google Cloud Shell (1 Solo Comando — 30 Secondi)

Apri **Google Cloud Shell** (icona **`>_`** in alto a destra nella Console Google Cloud) e incolla questo singolo comando:

```bash
git clone https://github.com/marangonic/lepida-gemini-enterprise-workshop.git ~/lepida_workshop && ~/lepida_workshop/setup.sh
```

### Cosa prepara automaticamente `setup.sh` (Modalità Partecipante):
1. **Attivazione API Google Cloud** (`discoveryengine`, `storage`, `aiplatform`, `bigquery`, `logging`).
2. **Creazione del Bucket Cloud Storage Univoco** (`gs://<PROJECT_ID>-lepida-comuni-er`) e caricamento dei **10 Documenti Pubblici Ufficiali** di Lepida e dei Comuni dell'Emilia-Romagna (`setup_workshop_data.py`).
3. **Attivazione automatica della Licenza Gemini Enterprise (`free_trial_gemini`)**, configurazione di **Google Identity**, creazione e **indicizzazione istantanea (in 2 secondi)** del Connettore Cloud Storage **`lepida-comuni-er-ds`** (*"Corpus Documentale Lepida e Comuni Emilia-Romagna 2026"*).
4. **Creazione automatica dell'App Gemini Enterprise** (**`Lepida & Comuni ER Assistant`** / `lepida-comuni-er-app`) già collegata al Data Store e con le funzionalità **Chat Agent (`no-code-agent-builder`)** e **Skills (`skills`)** già sbloccate.
5. **Stampa a schermo del Link Diretto alla Web App di Gemini Enterprise** (`https://vertexaisearch.cloud.google.com/home/cid/...`), pronto da cliccare per svolgere i due laboratori:
   - **MODULO 2 (30 min):** Creare il Proprio Chat Agent No-Code in Gemini Enterprise (con modello **`Gemini 3.8 Flash`** e architettura Multi-Livello di Sub-Agents).
   - **MODULO 3 (45 min):** Creare e Utilizzare le **"Skills"** in Gemini Enterprise.

---

## 🛠️ Opzioni Avanzate (Per il Docente o per Caricare la Soluzione Completa)

- **Caricare automaticamente la Soluzione Completa (Chat Agent Multi-Livello con `Gemini 3.8 Flash` + 3 Skills già pubblicati nella Web App):**
  ```bash
  ~/lepida_workshop/setup.sh --solution
  ```
- **Modalità Docente Completa (include anche MCP Toolbox + Deploy Agente ADK su Vertex AI Agent Engine):**
  ```bash
  ~/lepida_workshop/setup.sh --instructor
  ```
