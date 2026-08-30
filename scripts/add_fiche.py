"""
Crée ou met à jour la fiche détaillée d'un studio en écrivant directement dans les cellules
du gabarit "Template" (dupliqué si besoin), aux positions exactes des placeholders {...}.
Pas de génération de mise en page par script — le gabarit vient de l'utilisateur, voir
template_map.py pour la carte des cellules.

Usage :
    python scripts/add_fiche.py '{
      "nom": "Asobo Studio",
      "fields": {
        "Studio'"'"'s Name": "Asobo Studio",
        "City": "Bordeaux", "location_Region_Country": "Nouvelle-Aquitaine, France",
        "website": "asobostudio.com", "COUNTRY_MAJUSCULE": "FRANCE",
        "type de studio": "indépendant", "nombre de personnes en moyenne": "700",
        "date_de_creation": "2002", "plateformes": "PC, Xbox", "genres": "Simulation",
        "studio_date_creation": "2002", "studio_effectif": "≈ 700", "studio_type": "Indépendant",
        "studio_groupe": "non trouvé", "studio_city": "Bordeaux", "studio_recruit_3d": "à vérifier",
        "update_date": "29/08/2026",
        "nombre_de_titre": "6", "Art_Direction_infos": "Réalisme historique...",
        "ouverture_3d": "non trouvé", "stage_alternance_3d": "non trouvé",
        "fourchette_salariale": "non trouvé", "process_entretien": "non trouvé",
        "profiles": "Environment Artist, Character Artist",
        "nombre_de_projets": "2", "info_moteurs": "moteur maison",
        "info_softwares_3d": "3ds Max, Maya, ZBrush",
        "info_softwares_texturing": "Substance Painter", "info_softwares_procedural": "Houdini",
        "taille_de_lequipe_art": "non trouvé", "note_glassdoor_indeed": "non trouvé",
        "langue_de_travail": "Français / anglais", "moyenne_danciennete": "non trouvé",
        "à remplir après recherche LinkedIn / interviews": "non trouvé",
        "statut_capitalistique": "Indépendant", "editeur_partenaires": "non trouvé",
        "chiffre_d'affaires": "non trouvé",
        "Site officiel": "https://asobostudio.com", "Fiche AFJV": "https://afjv.com/...",
        "Jobs in Games": "https://jobs-in-games.com/...", "Page carrières": "...",
        "LinkedIn entreprise": "..."
      },
      "jeux_sortis": [["A Plague Tale: Requiem", "2022", "PC, PS5, XSX", "Focus Entertainment"]],
      "actualites": ["2024 — Sortie de Microsoft Flight Simulator 2024"],
      "projets_dev": [["Projet non annoncé", "non trouvé"]],
      "contacts_cles": [["—", "Art Director", "—"]]
    }'
    # ou en lisant stdin : echo '{...}' | python scripts/add_fiche.py

Voir references/fiche_studio_template.md pour la liste exacte des clés de "fields" (générée
depuis le vrai gabarit) et le détail des sections répétées.
"""

import datetime
import json
import re
import sys

import gspread
from sheet_client import col_letter, find_name_column, formula_arg_separator, main_sheet_name, normalize, open_sheet
from template_map import (
    ACTUALITES_SLOTS,
    CONTACTS_SLOTS,
    JEUX_SORTIS_SLOTS,
    PLACEHOLDER_RE,
    PROJETS_DEV_SLOTS,
    TEMPLATE_SHEET_NAME,
    scan_unique_placeholders,
)

FORBIDDEN_TAB_CHARS = re.compile(r"[\[\]\:\*\?/\\]")
NOT_FOUND_TEXT = "non trouvé"
NOT_FOUND_RGB = {"red": 152 / 255, "green": 152 / 255, "blue": 155 / 255}  # #98989b
NORMAL_RGB = {"red": 0, "green": 0, "blue": 0}


def compute_insert_index(sh, studio_name: str) -> int:
    """
    Détermine l'index d'insertion (0-based, sur l'ensemble du classeur) pour qu'un nouvel
    onglet studio s'intercale au bon endroit : après "Template" et la feuille principale
    (toujours en position 0 et 1), et parmi les onglets studio déjà présents dans l'ordre
    alphabétique — celui-ci les suppose déjà correctement ordonnés (création normale, ou
    correction manuelle de l'utilisateur), on ne les retrie pas, on trouve juste la bonne
    place pour le nouveau.
    """
    all_ws = sh.worksheets()
    target_norm = normalize(studio_name)
    reserved_names = {TEMPLATE_SHEET_NAME, main_sheet_name()}
    for i, w in enumerate(all_ws):
        if w.title in reserved_names:
            continue
        if normalize(w.title) > target_norm:
            return i
    return len(all_ws)


def sanitize_tab_name(name: str) -> str:
    return FORBIDDEN_TAB_CHARS.sub("", name)[:100]


def values_to_cell_dict(values: list) -> dict:
    cells = {}
    for r, row in enumerate(values, start=1):
        for c, val in enumerate(row, start=1):
            if val not in (None, ""):
                cells[f"{col_letter(c - 1)}{r}"] = val
    return cells


def substitute(template_str: str, data: dict) -> str:
    def repl(m):
        key = m.group(1).strip()
        return str(data.get(key, "non trouvé"))

    return PLACEHOLDER_RE.sub(repl, template_str)


def fill_multi_col_slots(slot_coord_groups: list, items: list) -> tuple:
    updates = []
    ncols = len(slot_coord_groups[0])
    for i, coords in enumerate(slot_coord_groups):
        if i < len(items):
            vals = list(items[i])[:ncols]
            vals += [""] * (ncols - len(vals))
        else:
            vals = [""] * ncols
        updates.extend(zip(coords, vals))
    dropped = max(0, len(items) - len(slot_coord_groups))
    return updates, dropped


def fill_single_col_slots(slot_coords: list, items: list) -> tuple:
    updates = [(coord, items[i] if i < len(items) else "") for i, coord in enumerate(slot_coords)]
    dropped = max(0, len(items) - len(slot_coords))
    return updates, dropped


def format_requests_for_updates(sheet_id: int, updates: list) -> list:
    """
    Une cellule à valeur "non trouvé" doit s'afficher en italique gris (#98989b) ; toute
    autre valeur repasse en italique désactivé / texte normal. On ne touche QUE ces deux
    propriétés (fields scopé précisément) pour ne jamais altérer la police ou la taille de
    caractère définies dans le gabarit — donc pas besoin de relire le format d'origine, la
    police/taille du gabarit reste intacte automatiquement.
    """
    requests = []
    for coord, value in updates:
        row, col = gspread.utils.a1_to_rowcol(coord)
        is_not_found = str(value).strip() == NOT_FOUND_TEXT
        requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": row - 1, "endRowIndex": row,
                        "startColumnIndex": col - 1, "endColumnIndex": col,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "italic": is_not_found,
                                "foregroundColor": NOT_FOUND_RGB if is_not_found else NORMAL_RGB,
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat.italic,userEnteredFormat.textFormat.foregroundColor",
                }
            }
        )
    return requests


def main() -> None:
    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    studio_name = payload["nom"]
    fields = payload.get("fields", {})
    jeux_sortis = payload.get("jeux_sortis", [])
    actualites = payload.get("actualites", [])
    projets_dev = payload.get("projets_dev", [])
    contacts_cles = payload.get("contacts_cles", [])

    sh = open_sheet()
    tab_name = sanitize_tab_name(studio_name)

    try:
        ws_studio = sh.worksheet(tab_name)
        existing = True
    except gspread.WorksheetNotFound:
        try:
            template_ws = sh.worksheet(TEMPLATE_SHEET_NAME)
        except gspread.WorksheetNotFound:
            raise RuntimeError(f'Feuille gabarit "{TEMPLATE_SHEET_NAME}" introuvable dans le classeur.')
        insert_index = compute_insert_index(sh, studio_name)
        ws_studio = sh.duplicate_sheet(
            source_sheet_id=template_ws.id, insert_sheet_index=insert_index, new_sheet_name=tab_name
        )
        existing = False

    # Toujours relire les placeholders depuis "Template" (jamais modifié) : marche
    # identiquement à la création et au rafraîchissement, la duplication préserve les
    # positions.
    template_ws = sh.worksheet(TEMPLATE_SHEET_NAME)
    template_cells = values_to_cell_dict(template_ws.get_all_values())
    unique_fields = scan_unique_placeholders(template_cells)

    # Champs calculés par le script, jamais par la recherche — on écrase toute valeur que le
    # payload aurait pu fournir pour ces clés, elles ne doivent pas dépendre de la recherche.
    fields["update_date"] = datetime.date.today().strftime("%d/%m/%Y")
    fields["nombre_de_titre"] = str(min(len(jeux_sortis), len(JEUX_SORTIS_SLOTS)))
    fields["nombre_de_projets"] = str(min(len(projets_dev), len(PROJETS_DEV_SLOTS)))

    updates = []
    seen_coords = set()
    for occurrences in unique_fields.values():
        for coord, template_str in occurrences:
            if coord in seen_coords:
                continue
            seen_coords.add(coord)
            updates.append((coord, substitute(template_str, fields)))

    jeux_updates, dropped_jeux = fill_multi_col_slots(JEUX_SORTIS_SLOTS, jeux_sortis)
    actus_updates, dropped_actus = fill_single_col_slots(ACTUALITES_SLOTS, actualites)
    projets_updates, dropped_projets = fill_multi_col_slots(PROJETS_DEV_SLOTS, projets_dev)
    contacts_updates, dropped_contacts = fill_multi_col_slots(CONTACTS_SLOTS, contacts_cles)
    updates.extend(jeux_updates + actus_updates + projets_updates + contacts_updates)

    body = [{"range": coord, "values": [[val]]} for coord, val in updates]
    ws_studio.batch_update(body, value_input_option="USER_ENTERED")

    format_requests = format_requests_for_updates(ws_studio.id, updates)
    if format_requests:
        sh.batch_update({"requests": format_requests})

    # Lien hypertexte depuis la feuille principale
    ws_nouveau = sh.worksheet(main_sheet_name())
    all_values = ws_nouveau.get_all_values()
    header = all_values[0] if all_values else []
    name_col = find_name_column(header)

    target_row = None
    for r_idx, row in enumerate(all_values[1:], start=2):
        if len(row) > name_col and normalize(row[name_col]) == normalize(studio_name):
            target_row = r_idx
            break

    linked = False
    if target_row:
        sep = formula_arg_separator(sh)
        formula = f'=HYPERLINK("#gid={ws_studio.id}"{sep} "{studio_name}")'
        ws_nouveau.update(
            f"{col_letter(name_col)}{target_row}", [[formula]], value_input_option="USER_ENTERED"
        )
        linked = True

    dropped_total = dropped_jeux + dropped_actus + dropped_projets + dropped_contacts
    print(
        json.dumps(
            {
                "studio": studio_name,
                "tab": tab_name,
                "linked_in_nouveau": linked,
                "was_existing": existing,
                "items_dropped_no_room": {
                    "jeux_sortis": dropped_jeux,
                    "actualites": dropped_actus,
                    "projets_dev": dropped_projets,
                    "contacts_cles": dropped_contacts,
                }
                if dropped_total
                else None,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
