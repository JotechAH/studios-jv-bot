"""
Ajoute une liste de nouveaux studios dans la feuille "Nouveau", en respectant les colonnes
déjà présentes, en dédupliquant sur le nom, et en retriant l'ensemble par ordre alphabétique.

Une seule lecture + une seule écriture par exécution (aucun transfert du fichier entier :
uniquement les valeurs de la feuille "Nouveau" transitent par l'API).

Usage :
    python scripts/add_studios.py '[{"Nom du studio": "Exemple Studio", "Ville": "Lyon", ...}]'
    # ou en lisant stdin :
    echo '[...]' | python scripts/add_studios.py

Chaque élément de la liste est un dict dont les clés doivent correspondre (insensible à la
casse/espaces) aux en-têtes de colonnes déjà présents dans la feuille "Nouveau". Une clé qui
ne correspond à aucune colonne existante est ignorée silencieusement — vérifie les en-têtes
réels avant d'appeler ce script si besoin (get_all_values sur la feuille suffit, pas besoin
d'un outil séparé).
"""

import json
import sys

from sheet_client import open_sheet, extend_native_table

NAME_HEADER_CANDIDATES = {"nom", "nom du studio", "studio"}


def normalize(value: str) -> str:
    return (value or "").strip().lower()


def find_name_column(header: list[str]) -> int:
    for i, h in enumerate(header):
        if normalize(h) in NAME_HEADER_CANDIDATES:
            return i
    return 0  # à défaut, on suppose que la première colonne est le nom


def main() -> None:
    if len(sys.argv) > 1:
        new_studios = json.loads(sys.argv[1])
    else:
        new_studios = json.load(sys.stdin)

    sh = open_sheet()
    ws = sh.worksheet("Nouveau")
    values = ws.get_all_values()
    if not values:
        raise RuntimeError('La feuille "Nouveau" est vide — pas d\'en-tête trouvé.')

    header = values[0]
    rows = values[1:]
    name_col = find_name_column(header)

    existing_names = {normalize(r[name_col]) for r in rows if len(r) > name_col}

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

        rows.append(new_row)
        existing_names.add(normalize(nom))
        added.append(nom)

    if not added:
        print(json.dumps({"added": [], "total_rows": len(rows)}, ensure_ascii=False))
        return

    rows.sort(key=lambda r: normalize(r[name_col]) if len(r) > name_col else "")

    ws.resize(rows=len(rows) + 1)
    ws.update("A2", rows, value_input_option="USER_ENTERED")
    extend_native_table(sh, ws, total_data_rows=len(rows))

    print(json.dumps({"added": added, "total_rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
