# 05 — Recette

## A. Tests automatiques (à chaque modification)

```
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Résultat attendu : `Ran 62 tests … OK` (moteur v2.4 : `test_engine.py`, plus `test_updater.py` pour la mise à jour automatique). Ces tests vérifient le moteur sur deux sites de démonstration (`demo_site_A`, `demo_site_B`) : résultats identiques aux fichiers `expected_*.json`, format des fichiers, cohérence IO Plus, grille de polling, comportement du radar, validation, clé, import, version de configuration, feu à 4 sorties, radar sur la base, accents, liste des registres sans registres d'échec, noms de 15 caractères, échelle du radar, tableau de bord de la base, textes avec `\`, maximum de 100 registres de détection, entrée déplacée = modification majeure, PDF avec `<…>` dans le nom, entrées et sorties analogiques génériques, XML des radios, option IO Plus activé, étalonnage et alarme radio d'une entrée analogique, entrées en tension AI1-AI4 et conversion des fichiers au format 1.

## B. Recette de l'interface (avant livraison)

Cocher chaque ligne. Tout « non » bloque la livraison.

### Page 1
- [ ] Ouvrir `examples/demo_site_A.json` : 6 radios, champs conformes au fichier.
- [ ] « Enregistrer sous » puis comparer au fichier d'origine : contenu JSON identique (ordre des clés libre).
- [ ] Nouveau → une base `CA` seule, clé de 24 caractères générée.
- [ ] Ajouter une 18e radio : refusé avec message.
- [ ] Mettre deux périphériques sur DI1 : l'entrée occupée est grisée dans la liste ; si on force via un JSON, « Générer » affiche l'erreur du moteur.
- [ ] Radar proposé sur une remote, absent pour la base.
- [ ] Renommer une radio servant d'amont : les radios en aval suivent.
- [ ] Supprimer un repeater : ses radios aval passent sur la base.
- [ ] Projet invalide → « Générer » liste les erreurs et reste en page 1.

### Page 2
- [ ] demo_site_A généré : arbre `Demo Site A / IP Address List / Units / A-BASE / Mappings…` ; `Mappings` de A-BASE = 16 lectures + 5 scatters ; cycle de polling 440 s dans le nœud racine.
- [ ] Modifier un champ en page 1 → page 2 vidée, boutons grisés.
- [ ] Les 5 boutons créent leurs fichiers (dont un XML par radio) ; demo_site_A → 1 `.sconf` (base) ; demo_site_B → 2 `.sconf` (B-BASE et B-SM3).
- [ ] Fichier Excel ouvert dans Excel puis export relancé → message d'erreur propre, pas de plantage.

### Import
- [ ] Importer le `.cdb` généré depuis demo_site_A : mêmes radios, rôles, IP, amonts, clé ; message « Les périphériques ne sont pas importés… ».
- [ ] Importer un `.cdb` protégé par mot de passe → message dédié.

### Validation dans les outils ELPRO (faite par GeoAzimut)
- [ ] Les `.cdb` de demo_site_A et de demo_site_B s'ouvrent dans CConfig sans erreur ; noms, IP, modes, amonts, mappings visibles.
- [ ] Un `.sconf` s'importe dans la page IOPlusLogic d'une radio (System Tools → Write Configuration File) et apparaît **non activé**.

### Exécutable
- [ ] L'icône (logo GeoAzimut sur tuile foncée) apparaît sur le fichier `ELPRO Config.exe` dans l'Explorateur, dans la barre de titre et dans la barre des tâches.
- [ ] `dist\ELPRO Config\ELPRO Config.exe` démarre sur un PC Windows **sans Python installé**.
- [ ] Les 5 exports fonctionnent depuis l'exécutable (gabarits, dont `radio_template.xml`, et police trouvés).
- [ ] Windows réglé en français : la date « CfgVersion » du `.cdb` reste au format `6-Oct-2026 8:00:42 AM`.

## Version de configuration et feu à 4 sorties (moteur v1.5)

- [ ] Ouvrir `examples/demo_site_A.json` : « Version de configuration : V1.0 ». Générer : V1.0 (première génération), fichiers proposés `Demo_Site_A_V1.0.cdb`, `Demo_Site_A_V1.0_Compte_rendu.pdf`, `Demo_Site_A_V1.0_Adresses.xlsx`, `IOPlus_A-BASE_V1.0_DESACTIVE.sconf`.
- [ ] Changer l'IP d'une radio, générer : V1.1, barre d'état « Configuration générée — version V1.1 (modification mineure) », titre avec `*`.
- [ ] Supprimer un périphérique, générer : V2.0 (majeure).
- [ ] Générer à nouveau sans rien changer : reste V2.0 (aucune modification).
- [ ] Enregistrer, fermer, rouvrir : la version affichée est V2.0 ; générer sans modification : V2.0.
- [ ] Feu : la fenêtre propose Rouge, Orange clignotant, Orange fixe, Vert. Rouge seul → refusé ; rouge + orange fixe → accepté.
- [ ] `demo_site_B`, radio B-F3 : registres 403 (rouge), 413 (orange clignotant), 423 (orange fixe), 443 (vert) ; autres signalisations à partir de 431.
- [ ] Liste des registres (page 2, PDF, Excel) : aucun registre d'échec 152xx–157xx ni 15501 ; les comflags 151xx sont présents.
- [ ] Ouvrir un ancien projet (avec `do_orange`) : l'orange apparaît en « Orange clignotant », le titre affiche `*`, et l'enregistrement écrit `do_orange_cli`.

## Noms courts et échelle du radar (moteur v1.7)

- [ ] Tous les noms de registres (I/O Register Name Configuration) et de tags du tableau de bord font 15 caractères au plus (constaté sur radio : un tag de 16 caractères est remplacé par DIn1, DOut5…). Sur la radio, le tableau de bord n'affiche plus de « DIn1 », « DOut5 »…
- [ ] Radar avec échelle 0–1000 cm, seuil 500 cm : tableau de bord en cm, alarme haute à 500 cm ; dans le JSON, `seuil_haut_ma` = 12.0.
- [ ] Tableau de bord de la base : toutes les alarmes, une seule commande par genre (1 feu rouge, 1 orange clignotant…), tous les BATTV, MAINV, RSSI et comflags ; au plus 50 éléments.
- [ ] `demo_site_B` (57 éléments) : les RSSI sont retirés du tableau de bord de la base et une boîte « Configuration générée avec des remarques » s'affiche.

## Corrections de la relecture (moteur v1.9)

- [ ] Description du système `Armoire A\B`, propriétaire `C:\new` : export `.cdb` sans erreur ; réimport : textes identiques.
- [ ] 16 remotes avec chacune un câble (DI1) et un Lidar 6 (DI2–DI7) : « Générer » refuse avec le message « … maximum 100 … ».
- [ ] Sur une remote, déplacer un câble de DI1 à une DI libre plus haute, générer : version **majeure** (X+1.0).
- [ ] Changer la sortie d'une sirène (ex. DO3 → DO5), générer : version **mineure**.
- [ ] Nom de projet `Site <A> & Co` : le PDF s'exporte et affiche le nom tel quel.

## Entrée et sortie analogiques (moteur v2.0)

- [ ] Remote : **Entrée analogique** AI2, courant, échelle 0–10 bar : page 2, registre 35301 « Mesure analogique » avec `16384 = 0 bar, 49152 = 10 bar` ; tableau de bord de la base (groupe Mesures) en bar.
- [ ] Base : **Entrée analogique** AI4, **tension**, échelle 0–48 V : registre 3530x ; en mode Tension, AI1 à AI4 sont proposées (AI4 : « Valeur à 5 V »).
- [ ] Une AI prise par un radar est grisée pour l'entrée analogique, et inversement.
- [ ] Remote : **Sortie analogique** AO1 : registre 45001 « Consigne sortie analogique » ; câblage : ligne AO1 ; checklist : « écrire 16384 puis 49152 dans 45001 ».
- [ ] Ajouter une entrée ou une sortie analogique à un projet existant : version **majeure** ; changer seulement l'échelle : **mineure**.
- [ ] Ouvrir un projet existant sans E/S analogique et générer : fichiers identiques à la 1.4.0 (hors date et version).

## XML des radios et option IO Plus (moteur v2.1)

- [ ] `demo_site_B`, Générer, « Générer les XML des radios » : 9 fichiers `Demo_Site_B_V1.0_<radio>.xml`.
- [ ] Ouvrir `…_B-BASE.xml` dans un éditeur : `DeviceName` = B-BASE, groupe `DataLog` avec 16 lignes, groupe `Logic` avec `Enabled` = 0 ; `…_B-SM1.xml` : pas de groupe `DataLog`.
- [ ] Cocher « IO Plus activé » : confirmation demandée ; Non → case décochée. Oui → Générer : version mineure ; `.sconf` nommés `_ACTIVE` ; dans `…_B-BASE.xml`, `Logic/Enabled` = 1 ; page 2 et PDF indiquent « livré activé ».
- [ ] Décocher, Générer : version mineure ; `.sconf` `_DESACTIVE`.
- [ ] Ouvrir un projet existant (sans l'option) et générer : « aucune modification ».
- [ ] Charger un XML dans une radio de banc par sa page web : configuration complète, IO Plus dans l'état choisi ; sur la base, régler Scan Rate 30 et Records per File 2880.

## Noms limités à 15 caractères (moteur v2.2)

- [ ] `examples\demo_site_B.json`, Générer : page 2, registre 411 nommé `B-BAS_F1_OR_CLI` ; aucun nom de registre ou de tag de plus de 15 caractères.
- [ ] Ajouter un périphérique : le nom est limité à 15 caractères à la saisie.

## Réglages avancés d'une entrée analogique (moteur v2.3)

- [ ] `demo_site_A`, A-BASE : Entrée analogique `BATT_CAM`, Tension, AI4, Réglages avancés : Étalonnage 8192 / 30720 / 0 / 25, unité V ; Alarme de la radio 11,4 / 14,6, fenêtre décochée. « Span calculé : 901,12 ». OK.
- [ ] Générer : registre 35301 « AI4 tension, étalonnage : 8192 = 0 V, 30720 = 25 V » ; tableau de bord en V avec alarmes 14,6 / 11,4.
- [ ] `.cdb` dans CConfig, A-BASE, E/S AI4 (0-5V) : nom `BATT_CAM`, Zero 8192, Span 901.12, seuils 11.4 / 14.6.
- [ ] XML de A-BASE : ligne AIn `BATT_CAM | 8192 | 901.12 | 5 | 11.4 | 14.6 | 0 | 0`.
- [ ] Cocher Étalonnage grise l'Échelle ; rouvrir le périphérique : réglages relus et groupe déplié.
- [ ] Changer seulement un seuil, Générer : version mineure.
- [ ] Projets existants sans ces réglages : « aucune modification ».

## Entrées en tension corrigées (moteur v2.4)

- [ ] Entrée analogique, mode Tension : AI1 à AI4 proposées ; libellés 0 V / 20 V pour AI1-AI2, 0 V / 5 V pour AI3-AI4 ; Étalonnage grisé sur AI1/AI2.
- [ ] `demo_site_A`, A-BASE : Tension AI2 `BATT_CAM` : registre 35301 « AI2 0-20 V : 8192 = 0 V, 49152 = 20 V » ; XML de A-BASE, ligne AIn `BATT_CAM | 8192 | 2048 | …`.
- [ ] Toutes les radios, `.cdb` dans CConfig : E/S AI1 (0-20V) et AI2 (0-20V) Span 2048.
- [ ] Ouvrir un fichier de la 1.6.0 avec une entrée « AI4 tension » : message de conversion ; l'entrée est en AI2, sans étalonnage ; Générer : version mineure ; registres identiques.
- [ ] Projets existants sans entrée en tension : « aucune modification ».

## Mise à jour automatique (1.7.0, moteur v2.4)

Contrôlé sans réseau par `tests\ui_acceptance.py` (`U.chercher`, `U.telecharger` et `U.lancer_installation` remplacés) :
- [ ] À propos : bouton « Rechercher les mises à jour… » à gauche de « Licence » ; il ferme l'À propos et lance la recherche.
- [ ] Recherche manuelle à jour : « ELPRO Config est à jour (version 1.7.0). » ; erreur : avertissement avec le texte de l'erreur.
- [ ] Version 9.9.9 : fenêtre « Mise à jour disponible », « ELPRO Config 9.9.9 est disponible », notes affichées.
- [ ] « Ignorer cette version » : la vérification automatique ne la propose plus, la recherche manuelle si.
- [ ] Vérification automatique faite il y a moins de 24 h : GitHub n'est pas interrogé ; en erreur : rien d'affiché, nouvel essai au démarrage suivant.
- [ ] « Installer et redémarrer » : `lancer_installation` appelé une fois, après la fermeture normale.
- [ ] Projet modifié, « Annuler » à « Enregistrer les modifications ? » : rien n'est lancé, la fenêtre reste ouverte.
- [ ] Lancement de l'installateur impossible : avertissement, la fenêtre reste ouverte.
- [ ] `ELPRO Config.exe --verifier` : ligne « OK module de mise à jour et certificats HTTPS ».

À vérifier sous Windows avec le réseau, une fois la 1.7.0 publiée (variable d'environnement `ELPRO_VERSION_SIMULEE`, ex. `1.6.1` : l'application se compare aux releases comme si elle était dans cette version) :
- [ ] Au démarrage : fenêtre « Mise à jour disponible » ; « Installer et redémarrer » : barre de progression en Mo, autorisation Windows (UAC), installation silencieuse, ELPRO Config redémarre seul.
- [ ] Refus de l'UAC : l'application se ferme, rien n'est installé ; la relancer à la main.
