# 02 — Page 1 : Configuration du système

Onglet « 1. Configuration ». Il remplit le projet décrit dans `03_Modele_de_donnees.md`.

## Barre d'outils (en haut de la fenêtre, visible sur les 2 pages)

| Bouton | Action |
|---|---|
| **Nouveau** | Demande confirmation si des modifications ne sont pas enregistrées, puis charge un projet vide : système par défaut, une seule radio `CA` de rôle base (`ip_octet` 100, MAINV DI8 actif), clé générée par `M.generer_cle()`. |
| **Ouvrir…** | Filtre `Projet ELPRO (*.elpro.json)`. Charge le JSON dans les formulaires. |
| **Enregistrer** / **Enregistrer sous…** | Écrit le projet en JSON (`ensure_ascii=False, indent=2`). Le fichier se termine **toujours** par `.elpro.json` : après la boîte de dialogue, si le chemin finit par `.json` sans `.elpro.json`, remplacer `.json` par `.elpro.json` ; s'il n'a pas d'extension, ajouter `.elpro.json`. Nom proposé : `M.nom_fichier(nom_projet) + '.elpro.json'`. |
| **Importer un .cdb…** | Filtre `CConfig (*.cdb)`. Appelle `M.importer_cdb(chemin)`. Si `M.ProjetProtege` est levée : message « Projet protégé par mot de passe : dans CConfig, enregistrer une copie sans protection ». Sinon, charger le projet retourné et afficher la liste des avertissements dans une boîte d'information. |

Le titre de la fenêtre affiche `ELPRO Config — <nom du fichier>` avec `*` si non enregistré.

## Disposition de la page

```
┌───────────────────────────── Système ─────────────────────────────┐
│ Nom du projet [_____________]   System Name [____________]          │
│ Clé de chiffrement [________________________] [Générer] [👁]        │
│ Puissance générale [34 ▲▼] dBm                                      │
│ Propriétaire [______] Contact [______] Localisation [______]        │
│ Description [_______________________________________________]       │
├──────────────── Radios ─────────────────┬──── Radio sélectionnée ───┤
│ #  Nom      Rôle     IP    Amont  Pér.  │ (formulaire de la radio)  │
│ 1  CA       Base     .100   —      3    │                           │
│ 2  SM1      Remote   .101   CA     2    │ ── Périphériques ──       │
│ …                                       │ Type  Nom  Câblage  [✎][✕]│
│ [+ Ajouter] [Supprimer] [▲] [▼]          │ [+ Ajouter un périph.]    │
└─────────────────────────────────────────┴───────────────────────────┘
                                             [  Générer la configuration  ]
```

### Bloc « Système »

Un champ par clé de `systeme`. La clé est masquée par défaut (bouton œil pour l'afficher) ; « Générer » la remplace après confirmation (« Toutes les radios devront être reprogrammées. Continuer ? »).

### Liste des radios (tableau)

Colonnes : `#`, `Nom`, `Rôle`, `IP` (`192.168.1.x`), `Amont`, `Nb périphériques`. Lecture seule ; la sélection d'une ligne affiche son formulaire à droite.

| Bouton | Action |
|---|---|
| + Ajouter | Ajoute une radio en fin de liste : nom `RADIO<n>`, rôle remote, amont = la base, `ip_octet` = plus petit libre ≥ 101, MAINV DI8 actif, aucun périphérique. Refusé au-delà de 17 radios. |
| Supprimer | Confirmation. Interdit sur la base. Si d'autres radios avaient celle-ci comme amont, leur amont devient la base. |
| ▲ / ▼ | Déplace la radio. La base reste toujours en position 1 (boutons grisés pour elle et pour la position 2 avec ▲). |

### Formulaire « Radio sélectionnée »

| Libellé | Contrôle | Clé |
|---|---|---|
| Nom | champ texte (20 car. max) | `nom` |
| Rôle | liste : Base / Repeater / Remote. « Base » n'est proposé que pour la radio n° 1, qui ne peut pas changer de rôle. **Passage en Repeater** : `ip_octet` devient le plus petit nombre libre ≥ 120. **Passage de Repeater à Remote** : `ip_octet` devient le plus petit nombre libre ≥ 101. L'utilisateur peut ensuite modifier l'IP à la main | `role` |
| Amont | liste des radios de rôle Base ou Repeater (sauf elle-même). Masqué pour la base | `amont` |
| Adresse IP | `192.168.1.` + champ numérique 100–254 | `ip_octet` |
| Puissance | case « Utiliser la puissance générale » (cochée = `null`) + champ 10–40 | `puissance_dbm` |
| Titre de page web | champ texte | `titre_page` |
| Description | champ texte | `description` |
| Présence secteur (MAINV) | case + liste DI1–DI8 (défaut DI8) | `mainv` |
| Inverser toutes les entrées | case | `inversion_entrees` |
| Inverser toutes les sorties | case | `inversion_sorties` |

**Renommage** : le nom est appliqué quand l'utilisateur quitte le champ ou appuie sur Entrée (`editingFinished`), **pas à chaque frappe**. À ce moment :
1. si le nouveau nom est vide ou déjà pris par une autre radio, remettre l'ancien nom et afficher « Nom vide ou déjà utilisé » ;
2. sinon, remplacer l'`amont` de toutes les radios qui référençaient l'ancien nom ;
3. rafraîchir **tout** le tableau des radios (colonne Amont des autres lignes comprise) et la liste Amont du formulaire.

### Périphériques de la radio

Tableau : `Type` (libellé), `Nom`, `Câblage` (ex. `DI3-DI5`, `DO1/DO2`, `AI1 — seuil 12 mA`), boutons Modifier / Supprimer.

« + Ajouter un périphérique » ouvre une boîte de dialogue :

1. Liste **Type** (libellés de la table de `03_Modele_de_donnees.md`). Pour la base, le type Radar n'est pas proposé.
2. Champ **Nom** prérempli : `CABLE<n>`, `LIDAR`, `F<n>` (n = numéro du feu sur tout le site), `SIRENE`, `FLASH`, `CAM`, `SPOT`, `RADAR<n>`, `DO<n>`, `DI<n>`…
3. Champs de câblage selon le type :

| Type | Champs affichés |
|---|---|
| CABLE, ALARME_BT, ENTREE | Entrée : liste DI1–DI8 |
| LIDAR3 | Première entrée : DI1–DI6 ; les 3 entrées suivantes sont proposées (modifiables une par une) |
| LIDAR6 | Première entrée : DI1–DI3 ; idem pour 6 entrées |
| FEU | Sortie rouge, Sortie orange, Sortie verte (avec choix « aucune ») : listes DO1–DO8 |
| SIRENE, FLASH, SIRENE_FLASH, CAMERA, SPOT, SORTIE | Sortie : DO1–DO8 |
| CAMERA_SPOT | Sortie caméra, Sortie spot : DO1–DO8 |
| RADAR | Entrée analogique : AI1–AI4 ; Seuil haut (mA, 4,1–19,9, pas 0,1) ; Hystérésis (mA, défaut 0,8) ; Variation déclenchant un envoi (mA, défaut 0,8) ; Intervalle minimal entre envois (s, défaut 10) |

Dans les listes DI/DO/AI, les entrées déjà prises par un autre périphérique (ou par MAINV) apparaissent grisées avec le nom de l'occupant entre parenthèses.

4. OK → ajoute l'élément à `peripheriques` ; Annuler → rien.

### Bouton « Générer la configuration »

1. `erreurs = M.valider(projet)`.
2. Si la liste n'est pas vide : boîte « Configuration incomplète » listant les erreurs (une par ligne), rester en page 1.
3. Sinon : `plan = M.calculer_plan(projet)`, garder `plan` en mémoire, remplir la page 2, basculer sur l'onglet 2.

### Validation en direct (confort)

À chaque modification, appeler `M.valider(projet)` et afficher le nombre d'erreurs dans la barre d'état (« 3 erreurs — cliquer pour voir »). Ne bloque aucune saisie.
