# studios-jv-bot

Skill Claude Code pour la recherche d'emploi 3D jeux vidéo en France : trouve de nouveaux
studios et alimente automatiquement un Google Sheet, sans jamais faire transiter le fichier
entier — uniquement des appels ciblés à l'API Google Sheets.

## Installation locale

```bash
pip install -r requirements.txt
```

Variables d'environnement nécessaires (à mettre dans un `.env` local, jamais commité — voir
`.gitignore`) :

```bash
export SPREADSHEET_ID="1bG6pRCc4dYuZrzDVgK4QkwpJtf0vEGuNB7jd7NA1RIM"
export GOOGLE_SERVICE_ACCOUNT_FILE="/chemin/vers/ta-cle-de-compte-de-service.json"
```

(En local tu peux utiliser le fichier `.json` téléchargé depuis Google Cloud Console
directement — ne le mets jamais dans ce dépôt.)

Test rapide :

```bash
python -c "from scripts.sheet_client import open_sheet; print(open_sheet().worksheet('Nouveau').get_all_values()[0])"
```
Si ça affiche la ligne d'en-tête de ta feuille "Nouveau", tout est branché.

## Utilisation avec Claude Code (local)

Ouvre ce dossier avec Claude Code (`claude` dans le terminal, à la racine du dépôt) et
demande directement, par exemple :

> Trouve 5 nouveaux studios de jeux vidéo 3D en France qui ne sont pas déjà dans mon tableau,
> ajoute-les, puis fais-moi un rapport.

Claude Code trouvera automatiquement le skill dans `.claude/skills/studios-3d-jeuxvideo-fr/`.

## Utilisation en routine cloud (programmée, ex. tous les lundis)

1. Va sur `claude.ai/code/routines`.
2. Crée une routine pointant sur ce dépôt GitHub (`studios-jv-bot`).
3. Dans les paramètres de la routine (ou dans les secrets du dépôt GitHub, selon l'interface
   proposée), ajoute les mêmes variables qu'en local :
   - `SPREADSHEET_ID`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` → colle ici le **contenu complet** du fichier `.json` de la
     clé (pas un chemin de fichier, cette fois — le script lit `GOOGLE_SERVICE_ACCOUNT_JSON`
     en priorité s'il est présent).
4. Programme la fréquence voulue (ex. hebdomadaire, le lundi).
5. Prompt suggéré pour la routine :

   > Cherche des nouveaux studios de jeux vidéo 3D en France non présents dans la feuille
   > "Nouveau" du Google Sheet (AFJV, Jobs in Games, LinkedIn, annuaires régionaux),
   > ajoute-les, puis donne un rapport court de ce qui a été ajouté.

6. Claude Code exécutera cette routine dans un environnement cloud isolé, en utilisant le
   skill de ce dépôt — pas besoin d'avoir ton PC allumé.

## Sécurité

- Le fichier `.json` de la clé de compte de service et le `.env` local ne doivent **jamais**
  être commités (déjà exclus par `.gitignore`).
- Le compte de service n'a accès qu'aux fichiers Google explicitement partagés avec son
  adresse email (`...@...iam.gserviceaccount.com`) — c'est le cas pour ton fichier Sheet,
  partagé en "Éditeur".
