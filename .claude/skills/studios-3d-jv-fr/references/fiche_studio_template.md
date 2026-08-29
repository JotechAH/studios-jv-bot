# Structure d'une fiche studio (lignes de la colonne A, une par ligne de la liste "lines")

```
<Nom du studio>
Ville / région : ...
Site web : ...
Dernière mise à jour de cette fiche : <date du jour>

JEUX SORTIS
- <Titre> (<année>, <plateformes>)
- ...

À VENIR / ACTUALITÉS RÉCENTES
- annonces de sorties, recrutements en cours, levées de fonds, rachats, fermetures...
- dater chaque info si possible (ex: "juin 2026 — ...")

STACK TECHNIQUE
- moteur(s) : Unreal / Unity / moteur maison / ...
- outils 3D mentionnés (offres d'emploi, interviews) : Blender, Maya, ZBrush, Substance...

DIRECTION ARTISTIQUE
- style visuel dominant (réaliste, stylisé, low-poly, cartoon...)
- univers / références (utile pour calibrer un portfolio à leur présenter)

CULTURE / ÉQUIPE
- taille approximative de l'équipe
- ambiance / valeurs affichées publiquement
- avis glanés (Glassdoor, Indeed, témoignages) — à formuler avec prudence, ce sont des
  opinions individuelles, pas des faits vérifiés

SOURCES
- <nom du site> — <URL>
- <nom du site> — <URL>
```

Passe cette structure comme liste de chaînes (une par ligne) dans le champ `"lines"` du JSON
donné à `scripts/add_fiche.py`.

Règles :
- Une info non trouvée = ligne absente ou "Non trouvé", jamais une supposition présentée
  comme un fait.
- Toujours dater les actualités quand la source le permet.
- La section SOURCES est obligatoire dès qu'une info a été utilisée dans la fiche.
