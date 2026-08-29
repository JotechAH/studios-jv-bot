"""
Liste les studios de la feuille principale qui n'ont PAS encore de fiche liée (la cellule de
leur nom n'est pas une formule =HYPERLINK(...)), jusqu'à une limite donnée. Prévu pour
alimenter une routine "fiches studios" en lot raisonnable plutôt que de tout traiter d'un coup.

Une seule lecture, aucune écriture (aucun transfert du fichier entier).

Usage :
    python scripts/list_missing_fiches.py            # 5 par défaut
    python scripts/list_missing_fiches.py 10         # jusqu'à 10
"""

import json
import sys

from sheet_client import find_name_column, main_sheet_name, open_sheet

DEFAULT_LIMIT = 5


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_LIMIT

    sh = open_sheet()
    ws = sh.worksheet(main_sheet_name())

    display_values = ws.get_all_values()
    if not display_values:
        print(json.dumps([]))
        return

    formula_values = ws.get_all_values(value_render_option="FORMULA")

    header = display_values[0]
    name_col = find_name_column(header)

    missing = []
    for i in range(1, len(display_values)):
        row = display_values[i]
        if len(row) <= name_col or not row[name_col].strip():
            continue
        formula_row = formula_values[i] if i < len(formula_values) else []
        cell_formula = formula_row[name_col] if len(formula_row) > name_col else ""
        already_linked = str(cell_formula).strip().upper().startswith("=HYPERLINK(")
        if not already_linked:
            missing.append(row[name_col].strip())
        if len(missing) >= limit:
            break

    print(json.dumps(missing, ensure_ascii=False))


if __name__ == "__main__":
    main()
