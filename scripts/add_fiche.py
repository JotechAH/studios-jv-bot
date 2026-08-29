"""
Crée ou met à jour la feuille dédiée à un studio, et pose (ou rafraîchit) le lien
hypertexte depuis la cellule de son nom dans la feuille principale vers cette feuille.

Usage :
    python scripts/add_fiche.py '{"nom": "Asobo Studio", "lines": ["Asobo Studio", "", "JEUX SORTIS", "- ..."]}'
    # ou en lisant stdin :
    echo '{...}' | python scripts/add_fiche.py

"lines" est une liste de chaînes, une par ligne, écrites en colonne A de la feuille dédiée.
Structure recommandée : voir references/fiche_studio_template.md.
"""

import json
import re
import sys

import gspread
from sheet_client import col_letter, find_name_column, formula_arg_separator, main_sheet_name, normalize, open_sheet

FORBIDDEN_TAB_CHARS = re.compile(r"[\[\]\:\*\?/\\]")


def sanitize_tab_name(name: str) -> str:
    return FORBIDDEN_TAB_CHARS.sub("", name)[:100]


def main() -> None:
    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    studio_name = payload["nom"]
    lines = payload["lines"]

    sh = open_sheet()
    tab_name = sanitize_tab_name(studio_name)

    try:
        ws_studio = sh.worksheet(tab_name)
        ws_studio.clear()
    except gspread.WorksheetNotFound:
        ws_studio = sh.add_worksheet(title=tab_name, rows=max(50, len(lines) + 5), cols=5)

    ws_studio.update("A1", [[line] for line in lines], value_input_option="USER_ENTERED")
    gid = ws_studio.id

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
        formula = f'=HYPERLINK("#gid={gid}"{sep} "{studio_name}")'
        ws_nouveau.update(
            f"{col_letter(name_col)}{target_row}", [[formula]], value_input_option="USER_ENTERED"
        )
        linked = True

    print(
        json.dumps(
            {"studio": studio_name, "tab": tab_name, "linked_in_nouveau": linked},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
