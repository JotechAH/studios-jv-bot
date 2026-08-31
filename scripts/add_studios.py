"""
Ajoute une liste de nouveaux studios dans la feuille principale (nom configurable via
STUDIOS_SHEET_NAME, "Liste" par défaut), en respectant les colonnes
déjà présentes, en dédupliquant sur le nom, et en retriant l'ensemble par ordre alphabétique.

Une seule lecture + une seule écriture par exécution (aucun transfert du fichier entier :
uniquement les valeurs de la feuille principale transitent par l'API).

Usage :
    python scripts/add_studios.py '[{"Nom du studio": "Exemple Studio", "Ville": "Lyon", ...}]'
    # ou en lisant stdin :
    echo '[...]' | python scripts/add_studios.py

Chaque élément de la liste est un dict dont les clés doivent correspondre (insensible à la
casse/espaces) aux en-têtes de colonnes déjà présents dans la feuille principale. Une clé qui
ne correspond à aucune colonne existante est ignorée silencieusement — vérifie les en-têtes
réels avant d'appeler ce script si besoin (get_all_values sur la feuille suffit, pas besoin
d'un outil séparé).
"""

import json
import sys

from sheet_client import (
    extend_native_table,
    find_name_column,
    main_sheet_name,
    NAME_HEADER_CANDIDATES,
    normalize,
    open_sheet,
)


def main() -> None:
    if len(sys.argv) > 1:
        new_studios = json.loads(sys.argv[1])
    else:
        new_studios = json.load(sys.stdin)

    sh = open_sheet()
    ws = sh.worksheet(main_sheet_name())

    # Deux lectures : les valeurs affichées (pour trier/dédupliquer sur le nom lisible) et
    # les formules brutes (pour ne jamais perdre un =HYPERLINK(...) existant en réécrivant
    # la feuille — get_all_values() seul renvoie le texte affiché et écraserait les liens).
    display_values = ws.get_all_values()
    if not display_values:
        raise RuntimeError(f'La feuille "{main_sheet_name()}" est vide — pas d\'en-tête trouvé.')
    formula_values = ws.get_all_values(value_render_option="FORMULA")

    header = display_values[0]
    name_col = find_name_column(header)

    # Chaque ligne existante est gardée sous sa forme BRUTE (formule si elle en a une), mais
    # on utilise le nom AFFICHÉ (pas la formule) comme clé de tri/déduplication.
    rows = []  # liste de (nom_affiché, ligne_brute)
    for i in range(1, len(display_values)):
        display_row = display_values[i]
        raw_row = formula_values[i] if i < len(formula_values) else display_row
        name = display_row[name_col] if len(display_row) > name_col else ""
        rows.append((name, raw_row))

    existing_names = {normalize(name) for name, _ in rows}

    added = []
    for studio in new_studios:
        nom = None
        for k, v in studio.items():
            if normalize(k) in NAME_HEADER_CANDIDATES:
                nom = v
                break
        if not nom:
            continue
        if normalize(nom) in existing_names:
            continue

        new_row = [""] * len(header)
        for i, h in enumerate(header):
            for k, v in studio.items():
                if normalize(k) == normalize(h):
                    new_row[i] = v
                    break
        if not new_row[name_col]:
            new_row[name_col] = nom

        rows.append((nom, new_row))
        existing_names.add(normalize(nom))
        added.append(nom)

    if not added:
        print(json.dumps({"added": [], "total_rows": len(rows)}, ensure_ascii=False))
        return

    rows.sort(key=lambda item: normalize(item[0]))
    final_rows = [row for _, row in rows]

    ws.resize(rows=len(final_rows) + 1)
    ws.update("A2", final_rows, value_input_option="USER_ENTERED")
    extend_native_table(sh, ws, total_data_rows=len(final_rows))

    print(json.dumps({"added": added, "total_rows": len(final_rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
