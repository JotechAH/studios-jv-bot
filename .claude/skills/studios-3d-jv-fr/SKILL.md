---
name: studios-3d-jeuxvideo-fr
description: >
  Aide à la recherche d'emploi en 3D dans le secteur du jeu vidéo en France, en s'appuyant
  sur un Google Sheet ("Nouveau"/nom configurable via STUDIOS_SHEET_NAME = liste des studios,
  une feuille dédiée par studio = fiche
  détaillée), accédé via l'API Google Sheets (gspread) avec un compte de service — pas de
  téléchargement/upload de fichier. Utiliser ce skill dès que l'utilisateur demande de :
  trouver / chercher / ajouter de nouveaux studios de jeux vidéo (3D, art, animation) en
  France ; mettre à jour, compléter ou trier le tableau de studios ; faire une recherche /
  fiche / topo sur un studio précis (actus, stack technique, direction artistique, jeux
  sortis, culture). Se déclenche même sans mention explicite de "Google Sheet" ou "studio" —
  par exemple "trouve-moi d'autres boîtes de jeux vidéo" ou "renseigne-toi sur Asobo" doivent
  aussi déclencher ce skill. S'applique aussi aux exécutions programmées (routines).
---

# Studios 3D Jeux Vidéo FR — recherche d'emploi (édition directe via l'API Sheets)

Ce skill gère un classeur Google Sheets via l'**API Google Sheets** (`gspread` + compte de
service), directement — **jamais** de téléchargement/upload du fichier entier. Chaque
opération ne transfère que les valeurs concernées (quelques lignes ou une feuille), ce qui
évite tout problème de taille ou de consommation excessive de tokens.

Le classeur contient :
- une feuille principale (appelée **"Nouveau"** dans les exemples ci-dessous — le nom réel
  vient de la variable d'environnement `STUDIOS_SHEET_NAME`, "Liste" par défaut ; consulte-la
  plutôt que de supposer un nom) : le tableau principal, une ligne par studio, trié par ordre
  alphabétique, avec le nom du studio en lien hypertexte vers sa fiche dédiée (si elle existe);
- une **feuille par studio** (nommée d'après le studio) : la fiche détaillée créée par ce skill.

## Pré-requis (déjà en place si tu suis le README du dépôt)

- `SPREADSHEET_ID` et l'authentification (`GOOGLE_SERVICE_ACCOUNT_JSON` ou
  `GOOGLE_SERVICE_ACCOUNT_FILE`) sont disponibles en variables d'environnement.
- `pip install -r requirements.txt` a été fait (gspread, google-auth).

Ne jamais demander à l'utilisateur de coller la clé de compte de service en clair dans le
chat — elle est censée être en variable d'environnement/secret, pas dans la conversation.

## Mode A — Découverte de nouveaux studios

Déclencheurs typiques : "trouve-moi d'autres studios", "complète ma liste", "cherche des
boîtes de jeux vidéo en 3D en France", "mets à jour mon tableau".

1. **Lis l'état actuel** avec un petit script Python (`scripts/sheet_client.py` +
   `ws.get_all_values()` sur la feuille "Nouveau") pour connaître les studios déjà présents et
   les colonnes existantes. **Respecte la structure existante** — n'invente pas de nouvelles
   colonnes sans le dire à l'utilisateur.

2. **Cherche de nouveaux studios** via recherche web, en croisant plusieurs sources sauf
   indication contraire :
   - AFJV (annuaire studios / société du jeu vidéo)
   - Jobs in Games
   - LinkedIn (recherche d'entreprises "jeu vidéo" + ville/région française)
   - Annuaires régionaux / clusters jeu vidéo français

   Filtre sur des studios pertinents pour un profil **3D** (production 3D/art dans le jeu
   vidéo, cinématique/animation liée au jeu vidéo). Ignore le pur édition/publishing sans
   production interne, sauf indication contraire.

3. **Déduplique** contre la liste lue à l'étape 1 (insensible casse/espaces — le script
   `add_studios.py` le fait déjà, mais évite de proposer des doublons évidents en amont).

4. Si l'utilisateur a demandé un nombre précis de studios (ex: "5 nouveaux studios"),
   confirme-toi que tu en as bien trouvé au moins ce nombre avant d'écrire — sinon annonce
   combien tu as réellement trouvés.

5. **Écris en une seule fois** via :
   ```
   python scripts/add_studios.py '<JSON: liste de dicts {"Nom du studio": ..., ...}>'
   ```
   Le script lit lui-même les en-têtes réels, déduplique, trie alphabétiquement, et fait une
   seule écriture API. Laisse vide ce que tu ignores plutôt que d'inventer une info. Pas de
   lien vers une fiche à ce stade (elle n'existe pas encore — le Mode B s'en charge).

6. Termine par un résumé court (studios ajoutés + sources) — pas la peine de tout redétailler,
   le Sheet fait foi.

## Mode B — Fiche détaillée d'un studio

Déclencheurs typiques : "renseigne-toi sur [Studio]", "fais-moi une fiche sur [Studio]".

1. Si le studio n'est pas encore dans "Nouveau", ajoute-le d'abord (Mode A, étape 5, avec au
   minimum son nom).
2. **Recherche web** sur le studio, en couvrant si possible : jeux sortis, direction
   artistique, recrutement, stack technique, projets en développement, contacts clés,
   actualités récentes, culture/équipe, actionnariat/financement. Cite tes sources dans les
   champs dédiés (site officiel, AFJV, Jobs in Games, page carrières, LinkedIn). N'invente
   rien : une info non trouvée s'écrit `"non trouvé"` littéralement — le script la mettra lui
   -même en italique gris, rien à faire de plus. Les clés exactes attendues, l'ordre
   chronologique attendu pour les listes, et les valeurs autorisées pour le type de studio
   sont dans `references/fiche_studio_template.md` (généré depuis le vrai gabarit "Template"
   du classeur, fait à la main par l'utilisateur — ne pas en inventer d'autres).
3. **Si la fiche existe déjà** (rafraîchissement), refais la recherche complète plutôt que de
   ne chercher que les nouveautés — les listes (jeux sortis, actualités, projets) doivent être
   fournies réordonnées et complètes à chaque appel, du plus récent au plus ancien, sinon une
   actualité plus récente qu'une ancienne déjà en place ne la remplacera pas.
4. **Écris la fiche et pose le lien** en un seul appel :
   ```
   python scripts/add_fiche.py '<JSON : voir references/fiche_studio_template.md>'
   ```
   Ce script crée la fiche si elle n'existe pas (en dupliquant "Template"), ou la rafraîchit
   si elle existe déjà — **et** met à jour le lien hypertexte dans "Nouveau". Il ne touche
   jamais aux champs personnels (priorité, candidature, verdict...) ni au logo : ce sont des
   cellules sans `{...}` dans le gabarit, elles sont ignorées automatiquement, pas besoin de
   précaution particulière de ta part au-delà de ne pas les mettre dans le JSON.
5. Si la sortie JSON du script mentionne `items_dropped_no_room`, préviens l'utilisateur que
   certains éléments (trop de jeux/actus/contacts/projets pour les emplacements disponibles)
   n'ont pas pu être écrits — le gabarit fait main n'a pas de croissance automatique.
6. Résumé court dans le chat (2-3 lignes : ce qui est le plus notable) — la fiche complète vit
   dans le Sheet.

### Pré-requis pour Mode B/C : le gabarit "Template"

La feuille **"Template"** est construite et entretenue à la main par l'utilisateur dans
Google Sheets — ce skill ne la génère ni ne la modifie jamais. Si `add_fiche.py` échoue en
disant qu'elle est introuvable, il n'y a rien à corriger côté script : demande à l'utilisateur
de vérifier le nom de l'onglet dans son classeur.

## Mode C — Rattrapage en lot des fiches manquantes (routine dédiée)

Déclencheurs typiques : "fais des fiches pour les studios qui n'en ont pas encore", "avance
sur les fiches manquantes" — et c'est le mode à utiliser pour une **routine programmée**
séparée de la routine de découverte (Mode A), pour ne pas mélanger recherche de nouveaux
studios et rédaction de fiches dans la même exécution.

1. **Repère les studios sans fiche**, sans deviner — utilise le script dédié qui compare la
   cellule du nom à un lien `=HYPERLINK(...)` :
   ```
   python scripts/list_missing_fiches.py 5
   ```
   L'argument est la taille max du lot (5 par défaut). **Garde ce nombre petit** (3 à 5) sur
   une routine programmée : chaque studio demande plusieurs recherches web, donc un lot trop
   grand allonge beaucoup le temps et le coût d'une exécution.
2. Pour chaque studio renvoyé, applique le Mode B (étapes 2 et 3) — une recherche web puis un
   appel à `add_fiche.py` par studio (c'est normal ici, contrairement au Mode A : chaque fiche
   est un contenu propre qui doit être écrit séparément).
3. Si `list_missing_fiches.py` renvoie une liste vide, dis-le simplement — rien à faire, tous
   les studios déjà présents ont une fiche.
4. Résumé court à la fin : combien de fiches créées, lesquelles, et combien il en reste encore
   à traiter (pas besoin d'un nombre exact — mentionner "quelques-uns" ou une fourchette based
   on la présence continue de studios sans fiche suffit si tu ne veux pas relancer une lecture
   complète juste pour compter).

## Notes générales

- Ne jamais halluciner une donnée studio : chercher, lire le Sheet, ou demander à
  l'utilisateur.
- Un nom de feuille (onglet) Google Sheets a des contraintes (pas de `[ ] : * ? / \`, 100
  caractères max) — `add_fiche.py` nettoie déjà le nom pour le titre d'onglet ; garde le nom
  complet et correct dans `fields["Studio's Name"]` (le contenu de la fiche elle-même).
- Pour une exécution programmée (routine), le prompt doit rester générique et ne pas contenir
  d'info sensible — les identifiants viennent des secrets de l'environnement, pas du prompt.
