# Passation — ELPRO Config

Document de reprise pour le nouveau programmeur. À lire en entier avant toute modification, puis à garder dans `docs/PASSATION.md`.

---

## 1. En une minute

**ELPRO Config** est une application Windows de Geoazimut SàRL. Elle génère, à partir d'une saisie simple, la configuration standardisée des radios **ELPRO 415U-2-C4** d'un site d'alarme : une centrale d'alarme (« base ») et ses stations (remotes et repeaters). Elle produit le fichier `.cdb` à ouvrir dans le logiciel ELPRO **CConfig**, qui programme les radios, ainsi que la logique IO Plus de la base, un compte rendu PDF et la liste d'adresses Excel.

| Élément | Valeur |
|---|---|
| Dépôt | `lucapancottigz/elpro-config` (**public**) |
| Dernière version publiée | **1.3.0** (moteur de règles v1.8) |
| Langage / interface | Python 3.11+ / PySide6 |
| Distribution | Installateur Inno Setup publié dans les Releases GitHub |
| Licence | Propriétaire : « © 2026 Geoazimut SàRL. Tous droits réservés. », geoazimut.com (fichier `LICENSE`) |
| Application sœur | **ELPRO Logs** (dépôt `elpro-logs`) : elle lit les `.elpro.json` produits ici |

---

## 2. Qui fait quoi

| Rôle | Responsabilité |
|---|---|
| **Luca** (Geoazimut, propriétaire) | Exprime les besoins, teste sur Windows et sur les vraies radios, fusionne les PR, publie les releases. Il n'est pas à l'aise avec GitHub : il lui faut des **commandes PowerShell exactes, une par une**, avec le résultat attendu après chacune. |
| **Ingénieur** (session Claude séparée) | Écrit et teste le **moteur de règles** (`engine/`), les tests du moteur et les spécifications. Il livre des **compléments** (zip : fichiers moteur, tests, `COMPLEMENT_Vx.md`) et rédige les procédures de test de Luca. |
| **Programmeur** (toi) | Interface, intégration des compléments, documentation `docs/`, empaquetage (`build.bat`, installateur), **une PR par version**. Tu n'as accès qu'à ce dépôt. |

Circuit d'une version : besoin de Luca → complément de l'ingénieur → ta PR sur une branche `claude/...` → tests de Luca sous Windows → fusion et release par Luca.

---

## 3. Règles de travail (non négociables)

1. **Ne modifie pas `engine/elpro_engine.py`, `engine/views.py`, `resources/`, `examples/` ni `tests/`.** Leurs règles ont été validées sur de vraies radios. Si quelque chose y semble faux, **arrête-toi et signale-le** : la correction passe par l'ingénieur. Dans `export_excel.py` et `export_pdf.py`, seule la mise en forme peut changer.
2. **Aucune règle métier dans l'interface.** Elle saisit, appelle le moteur, affiche. Les messages d'erreur viennent de `elpro_engine.valider()`.
3. **Aucune donnée réelle dans le dépôt**, qui est public : ni nom de client ou de site, ni clé de chiffrement, ni plan IP réel, ni `.elpro.json` ou `.cdb` de site. Seuls les exemples fictifs (`demo_site_A`, `demo_site_B`) y figurent.
4. **Noms de fichiers et dossiers de code en anglais** ; **commentaires, docstrings, documentation et interface en français**.
5. **Les fichiers produits pour l'utilisateur gardent des noms français** : `_Compte_rendu.pdf`, `_Adresses.xlsx`, `IOPlus_<radio>_V<x.y>_DESACTIVE.sconf`, `.elpro.json`. Les accents sont retirés des noms de fichiers.
6. Avant toute livraison : `.\venv\Scripts\python.exe -m unittest discover -s tests -v` doit afficher **`Ran 22 tests … OK`**. `build.bat` le vérifie aussi.
7. Installateur : ne change ni l'**`AppId`** ni **`AppPublisher` = `GeoAzimut`**, sinon une mise à jour s'installe à côté de l'ancienne version au lieu de la remplacer.
8. Mentions de copyright présentes partout : fenêtre « À propos », barre d'état, propriétés de l'exécutable, installateur (page de licence), PDF et Excel.

---

## 4. Architecture

```
elpro-config/
├─ app.py, version.py (APP_VERSION), build.bat
├─ ui/                    ← interface (main_window, page_config, page_result, dialogs, …)
├─ engine/
│  ├─ elpro_engine.py     ← moteur de règles (NE PAS MODIFIER)
│  ├─ views.py            ← données prêtes à afficher (NE PAS MODIFIER)
│  ├─ export_excel.py, export_pdf.py   ← mise en forme seulement
├─ resources/             ← gabarits XML validés dans CConfig, police du PDF, icône
├─ examples/              ← demo_site_A/B.json + expected_*.json
├─ tests/                 ← tests du moteur (22)
├─ installer/             ← elpro_config.iss (Inno Setup, UTF-8 avec BOM) + génération de la ressource de version
└─ docs/                  ← 00_LISEZMOI … 05_Recette (dossier de réalisation)
```

Les noms exacts peuvent différer légèrement ; le dépôt fait foi.

**Fonctions du moteur appelées par l'interface :**

```python
import elpro_engine as M, views as V, export_excel as XL, export_pdf as PDF
projet = M.normaliser_projet(projet)              # à l'ouverture d'un .elpro.json (anciens formats)
erreurs = M.valider(projet)                        # [] = valide
projet, niveau = M.preparer_generation(projet)     # incrémente la version de config si nécessaire
plan = M.calculer_plan(projet)
M.ecrire_cdb(plan, chemin); M.ecrire_sconf(lignes, chemin)
V.vue_page2(plan); XL.ecrire_excel(...); PDF.ecrire_pdf(...)
projet, avertissements = M.importer_cdb(chemin)    # M.ProjetProtege si le .cdb est protégé
M.base_nom_fichier(plan)                           # préfixe des fichiers exportés, avec _V<x.y>
plan['avertissements']                             # ex. RSSI retirés du tableau de bord de la base
```

Ces signatures sont indicatives : `docs/01_Architecture.md` et le code font foi.

**Les deux pages de l'application :**
- **Page 1 (Configuration)** : système, liste des radios, radio sélectionnée, périphériques, bouton « Générer ».
- **Page 2 (Visualisation)** : arbre présenté comme dans CConfig, en lecture seule, avec les exports `.cdb`, `.sconf`, PDF et Excel.

Toute modification en page 1 efface le plan et grise les exports.

---

## 5. Le standard radio, en bref

`docs/` décrit tout le standard en détail. L'essentiel à connaître :

**Topologie et communication**
- **Topologie :** une base, la centrale d'alarme, et jusqu'à 17 radios, remotes et repeaters, en mode Fixed Links. Réseau local 192.168.1.0/24, base en `.100`.
- **Polling :** la base interroge chaque remote dans des créneaux de **22 s**. Un cycle dure T = nombre de créneaux × 22 s.
- **IO Plus de la base :** pour chaque remote, comflag = (toutes ses lectures ont échoué) OU (l'envoi des commandes a échoué). Le `.sconf` (tar.gz contenant `Logic.conf` et `Logic.version`) est **toujours livré désactivé** (`Enabled 0`) : Luca l'active à la main.
- **Fail-safe :** commandes 401 × 50.

**Plan de registres de la base**
- Détections : 150nn.
- Comflags : 151xx, où xx est le numéro de la radio (01 = base).
- Échecs : 152xx (BATTV), 153xx (RSSI), 154xx (détections), 155xx (commandes), 156xx (MAINV), 157xx (radar). Ces registres sont utilisés par les mappings et l'IO Plus, mais **ne figurent pas dans la liste des registres** affichée.
- MAINV (secteur) : 105xx.
- Tension batterie : 305xx, avec 8192 = 0 V et 49152 = 40 V.
- RSSI : 351xx, avec la valeur 0..150 = 0..−150 dBm.
- Radars : 352nn, valeur brute de 16384 (4 mA) à 49152 (20 mA).
- Commandes :

| Registres | Commande |
|---|---|
| 401–410 | feu rouge |
| 411–420 | feu orange clignotant |
| 421–430 | feu orange fixe |
| 431–440 | autres signalisations (sirène, flash, caméra…) |
| 441–450 | feu vert |

**Périphériques**
- **Feu :** 4 sorties, avec les clés JSON `do_rouge` (obligatoire), `do_orange_cli` et `do_orange_fixe` (au moins un orange), `do_vert`. L'ancien `do_orange` est converti en `do_orange_cli` par `normaliser_projet`.
- **Radar :** échelle facultative `mesure_4ma`, `mesure_20ma` et `unite` (cm par défaut). Les seuils sont stockés en mA.
- **Base :** elle accepte n'importe quel périphérique. Un radar sur la base est copié en local (30000 + AI) vers 352nn.

**Noms et tableau de bord**
- **Noms des registres et du tableau de bord :** **16 caractères au maximum** et uniques (`nom_court`). Au-delà, la radio affiche « DIn1 » ou « DOut5 » à la place du nom.
- **Tableau de bord de la base :** toutes les alarmes et tous les radars, une commande de chaque type, tous les BATTV, MAINV, RSSI et comflags. Il est limité à **50 éléments** : au-delà, les RSSI sont retirés et un avertissement est ajouté.

**Version de configuration** (dans le `.elpro.json`)
- Une modification **majeure** fait passer de X.Y à X+1.0 : radio ajoutée, retirée ou déplacée, périphérique ajouté, retiré ou de type changé, MAINV activé ou désactivé.
- Toute autre modification est **mineure** : X.Y+1.
- La version est incrémentée à la génération ; la première génération reste en 1.0.
- Tous les fichiers produits portent `_V<x.y>` dans leur nom.

**Pièges des fichiers `.cdb`**
- Encodage **UTF-16 LE avec BOM, fins de ligne CRLF**.
- Un fichier protégé contient `<DBE>…` à la place des unités : refuser l'import et demander à l'utilisateur une copie non protégée.
- La partie « modèle » du fichier fait foi, pas l'image `E2Config`.
- Les champs modifiés portent les marqueurs `d="C"` ou `d="D"`.

---

## 6. Construire, tester, publier

**Environnement Windows de Luca**
- Les dépôts sont dans `Documents\Git\` (et non `GitHub`).
- Le lanceur `py` et `python` ne sont **pas** dans le PATH. Python 3.12 est installé dans `%LOCALAPPDATA%\Programs\Python\Python312\`.
- `build.bat` suppose un `venv` existant. Quand c'est nécessaire, donne à Luca la commande complète : `& "<chemin>\python.exe" -m venv venv`, puis `.\venv\Scripts\python.exe -m pip install -r requirements.txt`.
- `build.bat` enchaîne les tests du moteur, la recette automatique de l'interface, PyInstaller (`--onedir`), Inno Setup et `SHA256SUMS.txt`. Il produit dans `dist\` : `ELPRO_Config_Setup_<version>.exe`, `ELPRO_Config_Setup.exe` et `SHA256SUMS.txt`.
- Le message Qt `This plugin does not support propagateSizeHints()`, émis pendant la recette hors écran, est **sans gravité**.

**Publication par Luca** : l'ingénieur lui fournit une procédure `Test_Vx.y.md` qui enchaîne :
1. `gh pr checkout N`, puis `.\build.bat` ;
2. les tests sous Windows ;
3. `gh pr merge N --merge`, puis `git checkout main`, `git pull` et un nouveau `.\build.bat` ;
4. l'extraction de la section `## [x.y.z]` du `CHANGELOG.md` ;
5. `gh release create vx.y.z` avec les 3 fichiers, puis `--latest` ;
6. la vérification de l'empreinte du lien `releases/latest/download/ELPRO_Config_Setup.exe`.

**À chaque version :**
- `version.py` ;
- une section `## [x.y.z]` dans `CHANGELOG.md`, dont le texte devient les notes de release ;
- la mise à jour de `docs/` et du README ;
- une PR dont la description résume les changements, les tests passés et **ce qui reste à tester sous Windows**.

---

## 7. Historique

| Version | Contenu principal |
|---|---|
| 1.0.0 | Première version publique : saisie, plan, exports, import `.cdb`, installateur, copyright |
| 1.1.0 | Version de configuration (majeure/mineure) dans les noms de fichiers, feu à 4 sorties, accents retirés des noms de fichiers, tout périphérique accepté sur la base |
| 1.2.0 | Registres d'échec retirés de la liste des registres, renumérotation des commandes (vert en 441–450) |
| 1.3.0 | Noms de 16 caractères au maximum, radar en unité physique (cm), tableau de bord de la base limité à 50 éléments |

`CHANGELOG.md` fait foi.

---

## 8. Chantiers ouverts

1. **Générer directement le XML de chaque radio**, au lieu du `.cdb` pour CConfig. C'est en attente d'une radio de banc chez Luca. CConfig n'est pas fiable : il lui arrive d'annoncer « programmé » alors que la radio ne l'est pas. L'export XML d'une radio (racine `<group name="E2Config">`) contient toute sa configuration :
   - réseau et identification ;
   - noms des E/S (`IOUsrCfg`) et mappings (`ELPROMesh`) ;
   - `FailSafe` et tableau de bord (`HMI`) ;
   - IO Plus (`Logic`) et **log** (`DataLog`).

   Il reste à faire, par l'ingénieur :
   - obtenir l'export d'une remote et d'un repeater ;
   - vérifier sur radio de banc que la radio accepte le rechargement de son propre XML ;
   - écrire le générateur.

   Bonus prévu : une **vérification**, qui compare l'export lu sur la radio au XML attendu.
2. **Activer automatiquement le log de la centrale (DataLog).** Il n'est configurable ni dans le `.cdb` ni dans CConfig, mais il figure dans le XML de la radio. C'est lié au point 1. Liste standard actuelle, configurée à la main : 16 entrées, **Scan Rate 30, Records per File 2880** (voir `docs/` d'ELPRO Logs).
3. Remontée des « 15501 » et autres registres d'échec de la base dans l'interface : aucun besoin exprimé pour l'instant.

---

## 9. Pour démarrer

1. Clone le dépôt et lis `docs/00_LISEZMOI.md` à `docs/05_Recette.md`, puis `CHANGELOG.md`.
2. Crée le venv et lance les tests : `Ran 22 tests … OK`.
3. Lance l'application et ouvre `examples/demo_site_B.json`, puis Générer : la page 2 se remplit.
4. Attends le prochain complément de l'ingénieur. Ne prends pas d'initiative sur les règles radio.
