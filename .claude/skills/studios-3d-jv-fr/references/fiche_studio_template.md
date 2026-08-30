# Payload attendu par `add_fiche.py` (gabarit "Template")

Le gabarit vient de l'utilisateur (feuille "Template" du classeur) — ce document liste les
clés exactes qu'il contient, extraites automatiquement de ce gabarit. Si l'utilisateur
modifie "Template" plus tard (ajoute/renomme un champ unique), relance le scan pour mettre ce
document à jour plutôt que de deviner :

```bash
python -c "
from sheet_client import open_sheet
from add_fiche import values_to_cell_dict
from template_map import scan_unique_placeholders
ws = open_sheet().worksheet('Template')
fields = scan_unique_placeholders(values_to_cell_dict(ws.get_all_values()))
for name in sorted(fields): print(name)
"
```

## `nom` (obligatoire)

Nom du studio — sert de nom d'onglet et de texte du lien hypertexte.

## `fields` — champs uniques (clé exacte -> valeur texte)

Une info non trouvée = `"non trouvé"` (le script met déjà cette valeur par défaut si la clé
est absente du payload — inutile de la répéter explicitement, mais ça ne pose pas de
problème si tu le fais).

```
Studio's Name, City, location_Region_Country, website, COUNTRY_MAJUSCULE,
type de studio, nombre de personnes en moyenne, date_de_creation, plateformes, genres,
studio_date_creation, studio_effectif, studio_type, studio_groupe, studio_city,
studio_recruit_3d, update_date,
nombre_de_titre, Art_Direction_infos,
ouverture_3d, stage_alternance_3d, fourchette_salariale, process_entretien, profiles,
nombre_de_projets, info_moteurs, info_softwares_3d, info_softwares_texturing,
info_softwares_procedural,
taille_de_lequipe_art, note_glassdoor_indeed, langue_de_travail, moyenne_danciennete,
à remplir après recherche LinkedIn / interviews,
statut_capitalistique, editeur_partenaires, chiffre_d'affaires,
Site officiel, Fiche AFJV, Jobs in Games, Page carrières, LinkedIn entreprise
```

Certaines cellules combinent plusieurs clés dans un même texte (ex: `"{City}   |
{location_Region_Country}   |   {website}"`, `"Studio {type de studio}"`,
`"~{nombre de personnes en moyenne} personnes"`) — fournis chaque clé séparément dans
`fields`, le script recompose la phrase automatiquement.

## Sections répétées

Chaque clé prend une **liste** ; les emplacements non remplis restent vides (pas de
`"non trouvé"` répété). S'il y a plus d'éléments que d'emplacements dans le gabarit, les
éléments en trop sont **abandonnés** (pas d'insertion automatique de lignes dans ce
gabarit fait main — trop risqué sur une grille à colonnes multiples). Le script signale dans
sa sortie JSON si des éléments ont été abandonnés faute de place ; mentionne-le à
l'utilisateur si `add_fiche.py` le rapporte.

- **`jeux_sortis`** (8 emplacements) : liste de `[titre, année, plateformes, éditeur]`, du
  plus récent au moins récent.
- **`actualites`** (9 emplacements) : liste de chaînes déjà formatées, ex.
  `"2024 — Sortie de Microsoft Flight Simulator 2024"`.
- **`projets_dev`** (8 emplacements) : liste de `[projet, statut]`.
- **`contacts_cles`** (8 emplacements) : liste de `[nom, rôle, canal]`.

## Champs personnels (jamais écrits par le script)

Ces cellules du gabarit ne contiennent aucun `{...}` (texte fixe "à remplir manuellement" /
"non envoyée") — elles sont donc automatiquement ignorées par le scan, sans code dédié à
maintenir : **Priorité**, **Candidature**, **Pourquoi ce studio**, **Points d'attention**,
**Prochaine action**. Ne mets jamais ces informations dans le payload, ça n'aurait aucun
effet de toute façon.

Le logo studio (cellule B3) n'est également jamais touché — l'utilisateur le glisse
manuellement.

## Formatage automatique des champs non trouvés

`add_fiche.py` applique lui-même l'italique + couleur `#98989b` à toute valeur exactement
égale à `"non trouvé"`, et repasse en texte normal (non italique, noir) sinon — y compris au
rafraîchissement, si une info auparavant absente est désormais trouvée. Tu n'as rien à faire
de spécial pour ça côté recherche : écris juste `"non trouvé"` littéralement, le script gère
le style.

## Ordre des sections répétées : du plus récent au plus ancien

Pour `jeux_sortis`, `actualites` et `projets_dev`, fournis toujours la liste triée **du plus
récent en premier**. Ça s'applique aussi bien à la création qu'au rafraîchissement d'une
fiche : si une actualité ou un jeu plus récent est apparu depuis la dernière recherche,
il doit venir en tête de liste — le script ne fait aucun tri lui-même, il écrit dans l'ordre
fourni. En clair : au rafraîchissement, refais la recherche et renvoie la liste complète et
réordonnée (pas seulement les nouveautés), sinon les anciennes infos aux emplacements du bas
ne seront pas remplacées par des plus récentes.

## Valeurs attendues pour le type de studio

Les clés `"type de studio"` et `"studio_type"` (même information, utilisée à deux endroits du
gabarit) doivent utiliser une valeur parmi : `"Indépendant"`, `"AAA"`, `"AA"`, `"A"`. Si le
studio a fermé, mets `"Fermé"` dans ces deux clés à la place — et mentionne-le aussi dans
`actualites` (ex. `"2023 — Fermeture du studio"`) si tu as une date.

## Champ `studio_groupe`

Si le studio est indépendant et n'appartient à aucun groupe, mets `"Aucun"` — jamais
`"non trouvé"` pour un studio confirmé indépendant, ce n'est pas une absence d'info. Si ce
studio indépendant a des partenariats éditoriaux ponctuels (un éditeur qui publie certains de
ses jeux sans en être propriétaire), précise-le entre parenthèses, ex. :
`"Aucun (partenariat éditorial ponctuel avec Focus Entertainment)"`. Si le studio appartient
réellement à un groupe/maison mère, mets le nom du groupe normalement.

## Champs calculés automatiquement par le script (ne pas fournir, ignorés de toute façon)

`add_fiche.py` calcule lui-même ces 3 clés à chaque exécution — inutile de les rechercher ou
de les mettre dans `fields`, toute valeur fournie serait de toute façon écrasée :
- `update_date` : date du jour (création ou dernière modification de la fiche).
- `nombre_de_titre` : nombre de jeux effectivement écrits dans `jeux_sortis` (plafonné aux 8
  emplacements disponibles).
- `nombre_de_projets` : nombre de projets effectivement écrits dans `projets_dev` (plafonné
  aux 8 emplacements disponibles).

## Règles de contenu

- Une info non trouvée = `"non trouvé"`, jamais une supposition présentée comme un fait.
- Toujours dater les actualités quand la source le permet.
- Cite tes sources dans les champs dédiés (`Site officiel`, `Fiche AFJV`, `Jobs in Games`,
  `Page carrières`, `LinkedIn entreprise`) plutôt que dans une section libre.


