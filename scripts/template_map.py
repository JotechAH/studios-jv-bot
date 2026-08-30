"""
Carte des cellules du gabarit "Template" (construit à la main par l'utilisateur dans Google
Sheets — voir Recherche_Emplois.xlsx). Ce module ne génère plus aucune mise en page : le
gabarit EST la source de vérité, ce module sait seulement où lire/écrire dedans.

Deux catégories de champs :
- Champs "uniques" : un seul placeholder {nom_du_champ} quelque part sur la feuille (parfois
  mélangé à du texte fixe, ex: "Studio {type de studio}"). Détectés automatiquement en
  scannant "Template" à chaque exécution (`scan_unique_placeholders`) — donc si l'utilisateur
  ajoute/renomme un placeholder dans Template, le script s'adapte sans changement de code.
  Exception : les cellules des sections répétées ci-dessous sont exclues du scan, parce
  qu'elles réutilisent le MÊME nom de placeholder plusieurs fois (ex: "{nom_contact}" x8) —
  le nom seul ne suffit pas à les distinguer, il faut leurs positions exactes.
- Sections répétées (jeux sortis, actualités, projets en développement, contacts clés) :
  listées ici en dur avec leurs coordonnées, dans l'ordre où add_fiche.py doit les remplir.

Toute cellule SANS { } (ex: "à remplir manuellement", "non envoyée") est un champ personnel
que l'utilisateur remplit lui-même : elle n'est jamais détectée comme placeholder, donc
jamais réécrite par add_fiche.py — pas besoin de la marquer explicitement quelque part.

Si l'utilisateur restructure "Template" (déplace les tableaux, change le nombre de lignes
réservées aux jeux/actus/contacts/projets), ces 4 listes doivent être mises à jour à la main
pour rester synchronisées — elles ne sont pas déduites automatiquement, contrairement aux
champs uniques.
"""

import re

TEMPLATE_SHEET_NAME = "Template"

PLACEHOLDER_RE = re.compile(r"\{([^}]+)\}")

# (col_titre, col_année, col_plateformes, col_éditeur) par ligne, du plus récent au moins
# récent. 8 emplacements dans le gabarit actuel.
JEUX_SORTIS_SLOTS = [(f"B{r}", f"E{r}", f"F{r}", f"H{r}") for r in range(17, 32, 2)]

# Une seule cellule par actualité ("Date — description" déjà combinés dans la chaîne
# fournie). 9 emplacements.
ACTUALITES_SLOTS = [f"B{r}" for r in range(58, 75, 2)]

# (col_projet, col_statut) par ligne. 8 emplacements.
PROJETS_DEV_SLOTS = [(f"J{r}", f"M{r}") for r in range(38, 53, 2)]

# (col_nom, col_rôle, col_canal) par ligne. 8 emplacements.
CONTACTS_SLOTS = [(f"P{r}", f"Q{r}", f"S{r}") for r in range(38, 53, 2)]


def repeating_cells() -> set:
    """Coordonnées à exclure du scan des champs uniques (déjà gérées ci-dessus)."""
    cells = set(ACTUALITES_SLOTS)
    for group in JEUX_SORTIS_SLOTS + PROJETS_DEV_SLOTS + CONTACTS_SLOTS:
        cells.update(group)
    return cells


def scan_unique_placeholders(cell_values: dict) -> dict:
    """
    cell_values : dict coordonnée -> valeur brute de cellule (construit depuis
    get_all_values() de la feuille "Template").
    Retourne dict nom_de_placeholder -> liste de (coordonnée, texte_gabarit_de_la_cellule).
    """
    excluded = repeating_cells()
    fields: dict = {}
    for coord, value in cell_values.items():
        if not value or coord in excluded:
            continue
        for name in PLACEHOLDER_RE.findall(str(value)):
            fields.setdefault(name.strip(), []).append((coord, value))
    return fields
