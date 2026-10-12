#!/usr/bin/env python3
"""
Script di supporto per HANDS-ON 2 (Parte A):
Genera l'Authorization URI (URL-encoded) necessario per collegare l'agente ADK
deployato su Vertex AI Agent Engine all'interno di Gemini Enterprise con OAuth 2.0.
"""

import sys

# Inserisci qui il Client ID del tuo OAuth 2.0 Web Client creato in Google Auth Platform
# (oppure passalo come primo argomento da riga di comando: python3 construct_auth_uri.py <CLIENT_ID>)
OAUTH_CLIENT_ID = sys.argv[1] if len(sys.argv) > 1 else "YOUR_CLIENT_ID"

SCOPES = ["https://www.googleapis.com/auth/bigquery"]
REDIRECT_URI = "https://vertexaisearch.cloud.google.com/static/oauth/oauth.html"
OTHER_REQUIRED_QUERY_PARAMETERS = (
    "include_granted_scopes=true&response_type=code&access_type=offline&prompt=consent"
)

query_parameters = [
    f"client_id={OAUTH_CLIENT_ID}",
    f"redirect_uri={REDIRECT_URI}",
    OTHER_REQUIRED_QUERY_PARAMETERS,
]
if SCOPES:
    scopes_substring = f"scope={'%20'.join(SCOPES)}"
    query_parameters.append(scopes_substring)

query_parameters_joined = "&".join(query_parameters)
query_parameters_encoded = (
    query_parameters_joined.replace(" ", "%20").replace(":", "%3A").replace("/", "%2F")
)

auth_uri = "https://accounts.google.com/o/oauth2/v2/auth?" + query_parameters_encoded

print("\n=== Token URI (da incollare nel campo Token URI) ===")
print("https://oauth2.googleapis.com/token")
print("\n=== Authorization URI (da incollare nel campo Authorization URI) ===")
print(auth_uri + "\n")
