"""
Client d'accès à Google Sheets via un compte de service.

Auth (l'une des deux, dans cet ordre de priorité) :
- GOOGLE_SERVICE_ACCOUNT_JSON : le contenu JSON complet de la clé, en une variable
  d'environnement (c'est ce qu'on utilise dans l'environnement cloud Claude Code / les
  routines).
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


def main_sheet_name() -> str:
    """
    Nom de la feuille principale (liste des studios). Configurable via
    STUDIOS_SHEET_NAME pour ne pas avoir à toucher au code si tu renommes la feuille sur
    ton Drive — mets à jour cette variable d'environnement à la place.
    """
    return os.environ.get("STUDIOS_SHEET_NAME", "Liste")


NAME_HEADER_CANDIDATES = {"nom", "nom du studio", "studio"}


def normalize(value: str) -> str:
    return (value or "").strip().lower()


def find_name_column(header: list) -> int:
    for i, h in enumerate(header):
        if normalize(h) in NAME_HEADER_CANDIDATES:
            return i
    return 0  # à défaut, on suppose que la première colonne est le nom


def col_letter(index: int) -> str:
    letters = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def formula_arg_separator(sh: gspread.Spreadsheet) -> str:
    """
    Google Sheets attend un séparateur d'arguments de formule qui dépend de la locale du
    classeur : virgule "," pour les locales anglophones, point-virgule ";" pour la plupart
    des locales européennes (dont fr_FR) — sinon erreur "Formula parse error" à l'écriture
    via l'API, même si la formule est syntaxiquement correcte en anglais.
    """
    meta = sh.fetch_sheet_metadata()
    locale = meta.get("properties", {}).get("locale", "en_US")
    return "," if locale.lower().startswith("en") else ";"


def get_native_table(sh: gspread.Spreadsheet, sheet_id: int) -> dict | None:
    """
    Retourne l'objet "Table" natif (Insert > Table dans Sheets) défini sur la feuille
    d'id `sheet_id`, s'il y en a un. Retourne None si la feuille n'a pas de Table native
    (juste des cellules avec un format tableau manuel, par exemple).
    """
    meta = sh.fetch_sheet_metadata()
    for sheet in meta.get("sheets", []):
        if sheet.get("properties", {}).get("sheetId") == sheet_id:
            tables = sheet.get("tables", [])
            return tables[0] if tables else None
    return None


def extend_native_table(sh: gspread.Spreadsheet, ws: gspread.Worksheet, total_data_rows: int, header_rows: int = 1) -> bool:
    """
    Si la feuille `ws` a une Table native Google Sheets, étend sa plage pour couvrir
    `header_rows` lignes d'en-tête + `total_data_rows` lignes de données à partir de la
    ligne de départ actuelle de la table. Ne fait rien (retourne False) s'il n'y a pas de
    Table native — dans ce cas les nouvelles lignes restent de simples cellules, ce qui est
    normal si l'utilisateur n'a jamais créé de Table sur cette feuille.
    """
    table = get_native_table(sh, ws.id)
    if not table:
        return False

    current_range = table["range"]
    new_range = dict(current_range)
    new_range["endRowIndex"] = current_range["startRowIndex"] + header_rows + total_data_rows

    sh.batch_update(
        {
            "requests": [
                {
                    "updateTable": {
                        "table": {"tableId": table["tableId"], "range": new_range},
                        "fields": "range",
                    }
                }
            ]
        }
    )
    return True
