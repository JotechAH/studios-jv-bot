"""
Répare en masse les liens hypertexte entre la feuille principale (ex: "Liste") et les
fiches studio existantes, après qu'un bug d'add_studios.py ait effacé des formules
=HYPERLINK(...) lors d'un tri (corrigé depuis). Ne touche à aucun contenu des fiches
elles-mêmes — seulement à la cellule du nom dans la feuille principale.

Pour chaque onglet du classeur qui n'est ni "Template" ni la feuille principale, cherche la
ligne correspondante (par nom, insensible à la casse/espaces) et pose le lien s'il n'y est
pas déjà. Une seule lecture + une seule écriture groupée.

Usage :
    python scripts/relink_all_fiches.py
"""

import json

from sheet_client import col_letter, find_name_column, formula_arg_separator, main_sheet_name, normalize, open_sheet
from template_map import TEMPLATE_SHEET_NAME


def main() -> None:
    sh = open_sheet()
    main_name = main_sheet_name()
    reserved = {TEMPLATE_SHEET_NAME, main_name}

    ws_main = sh.worksheet(main_name)
    display_values = ws_main.get_all_values()
    formula_values = ws_main.get_all_values(value_render_option="FORMULA")
    header = display_values[0] if display_values else []
    name_col = find_name_column(header)
    sep = formula_arg_separator(sh)

    row_by_name = {}
    for i, row in enumerate(display_values[1:], start=2):
        if len(row) > name_col and row[name_col].strip():
            row_by_name[normalize(row[name_col])] = i

    updates = []
    relinked = []
    already_ok = 0
    no_matching_row = []

    for ws in sh.worksheets():
        if ws.title in reserved:
            continue
        target_row = row_by_name.get(normalize(ws.title))
        if not target_row:
            no_matching_row.append(ws.title)
            continue

        current = formula_values[target_row - 1] if target_row - 1 < len(formula_values) else []
        current_cell = current[name_col] if len(current) > name_col else ""
        if str(current_cell).strip().upper().startswith("=HYPERLINK("):
            already_ok += 1
            continue

        formula = f'=HYPERLINK("#gid={ws.id}"{sep} "{ws.title}")'
        coord = f"{col_letter(name_col)}{target_row}"
        updates.append({"range": coord, "values": [[formula]]})
        relinked.append(ws.title)

    if updates:
        ws_main.batch_update(updates, value_input_option="USER_ENTERED")

    print(
        json.dumps(
            {
                "relinked": relinked,
                "relinked_count": len(relinked),
                "already_ok": already_ok,
                "tabs_without_matching_row_in_liste": no_matching_row,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
