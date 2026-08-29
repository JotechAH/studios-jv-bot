"""
Client d'accès à Google Sheets via un compte de service.

Auth (l'une des deux, dans cet ordre de priorité) :
- GOOGLE_SERVICE_ACCOUNT_JSON : le contenu JSON complet de la clé, en une variable
  d'environnement (c'est ce qu'on utilise pour les secrets GitHub / routines cloud).
- GOOGLE_SERVICE_ACCOUNT_FILE : chemin local vers le fichier .json de la clé
  (pratique en local, le fichier ne doit JAMAIS être commité — voir .gitignore).

Requiert aussi SPREADSHEET_ID (l'ID du classeur, visible dans son URL entre /d/ et /edit).
"""

import json
import os

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_client() -> gspread.Client:
    raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw_json:
        info = json.loads(raw_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        key_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")
        if not key_path:
            raise RuntimeError(
                "Définis GOOGLE_SERVICE_ACCOUNT_JSON (contenu JSON) ou "
                "GOOGLE_SERVICE_ACCOUNT_FILE (chemin vers le fichier .json)."
            )
        creds = Credentials.from_service_account_file(key_path, scopes=SCOPES)
    return gspread.authorize(creds)


def open_sheet() -> gspread.Spreadsheet:
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    if not spreadsheet_id:
        raise RuntimeError("Définis la variable d'environnement SPREADSHEET_ID.")
    return get_client().open_by_key(spreadsheet_id)
