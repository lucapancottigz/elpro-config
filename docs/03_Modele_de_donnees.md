# 03 — Modèle de données (projet)

La page 1 produit et relit **exactement** cette structure (`dict` Python, enregistrée en JSON). Exemples complets : `examples/demo_site_A.json`, `examples/demo_site_B.json`.

## Racine

```json
{ "version": 1, "systeme": { … }, "radios": [ … ] }
```

## `systeme`

| Clé | Type | Obligatoire | Défaut | Règle de saisie |
|---|---|---|---|---|
| `nom_projet` | texte | oui | `""` | Nom du projet CConfig (nom du fichier .cdb) |
| `system_name` | texte | oui | `""` | 1 à 32 caractères `A-Z a-z 0-9 _ -` |
| `cle_chiffrement` | texte | oui | généré | 8 à 63 caractères ASCII visibles, sans espace. Bouton « Générer » → `M.generer_cle()` |
| `puissance_dbm` | entier | oui | `34` | 10 à 40 |
| `proprietaire` | texte | non | `""` | libre |
| `contact` | texte | non | `""` | libre |
| `description` | texte | non | `""` | libre |
| `localisation` | texte | non | `""` | libre |

## `radios` (liste ordonnée)

L'ordre de la liste **compte** : la première radio est obligatoirement la base, l'ordre fixe la numérotation des registres. 17 radios maximum.

| Clé | Type | Obligatoire | Défaut | Règle de saisie |
|---|---|---|---|---|
| `nom` | texte | oui | — | 1 à 20 caractères `A-Z a-z 0-9 _ -`, unique |
| `role` | `"base"` / `"repeater"` / `"remote"` | oui | `"remote"` | une seule base, en première position |
| `amont` | texte | si remote/repeater | — | nom d'une radio de rôle base ou repeater (liste déroulante) |
| `ip_octet` | entier | oui | voir ci-dessous | 100 à 254, unique. IP = 192.168.1.`ip_octet` |
| `puissance_dbm` | entier ou `null` | non | `null` | `null` = puissance générale ; sinon 10 à 40 |
| `titre_page` | texte | non | `""` | titre du tableau de bord web ; vide = nom de la radio |
| `description` | texte | non | `""` | vide = description générale |
| `inversion_entrees` | booléen | non | `false` | inverse toutes les détections (DI) de la radio |
| `inversion_sorties` | booléen | non | `false` | inverse toutes les sorties (DO) de la radio |
| `mainv` | objet | oui | `{"actif": true, "di": 8}` | présence secteur : `{"actif": false}` ou `{"actif": true, "di": 1..8}` |
| `peripheriques` | liste | oui | `[]` | voir ci-dessous |

`ip_octet` par défaut pour une nouvelle radio : `100` pour la base, sinon le plus petit nombre ≥ 101 non utilisé.

## `peripheriques`

Chaque élément a un `type`, un `nom` (1 à 16 caractères `A-Z a-z 0-9 _`, unique dans la radio) et des champs propres au type :

| `type` | Libellé à afficher | Champs | Exemple |
|---|---|---|---|
| `CABLE` | Câble (détection) | `di`: liste de 1 entier | `{"type":"CABLE","nom":"CABLE1","di":[1]}` |
| `LIDAR3` | Lidar 3 sorties | `di`: liste de 3 entiers | `{"type":"LIDAR3","nom":"LIDAR","di":[3,4,5]}` |
| `LIDAR6` | Lidar 6 sorties | `di`: liste de 6 entiers | `{"type":"LIDAR6","nom":"LIDAR","di":[1,2,3,4,5,6]}` |
| `ALARME_BT` | Alarme bouton/BT | `di`: liste de 1 entier | `{"type":"ALARME_BT","nom":"BT_ALARME","di":[1]}` |
| `ENTREE` | Entrée générique | `di`: liste de 1 entier | |
| `RADAR` | Radar (4-20 mA) | `ai`: 1 à 4 ; `seuil_haut_ma` ; `hysteresis_ma` (déf. 0.8) ; `variation_ma` (déf. 0.8) ; `tmin_s` (déf. 10) | `{"type":"RADAR","nom":"RADAR1","ai":1,"seuil_haut_ma":12.0,"hysteresis_ma":0.8,"variation_ma":0.8,"tmin_s":10}` |
| `FEU` | Feu | `do_rouge`, `do_orange` (obligatoires), `do_vert` (entier ou `null`) | `{"type":"FEU","nom":"F1","do_rouge":1,"do_orange":2,"do_vert":null}` |
| `SIRENE` | Sirène | `do` | `{"type":"SIRENE","nom":"SIRENE","do":3}` |
| `FLASH` | Flash | `do` | |
| `SIRENE_FLASH` | Sirène + flash (1 sortie) | `do` | |
| `CAMERA` | Caméra | `do` | |
| `SPOT` | Spot | `do` | |
| `CAMERA_SPOT` | Caméra + spot (1 commande) | `do_camera`, `do_spot` | `{"type":"CAMERA_SPOT","nom":"CAM","do_camera":1,"do_spot":2}` |
| `SORTIE` | Sortie générique | `do` | |

Plages : `di` et `do` de 1 à 8 ; `ai` de 1 à 4 ; une même DI/DO/AI ne peut servir qu'une fois dans la radio (MAINV compris).

Contraintes vérifiées par `M.valider()` (rien à coder côté interface, seulement afficher les messages) :
- radar interdit sur la base ; radars d'une même radio sur des AI consécutives ;
- au plus 10 feux et 10 signalisations autres sur tout le site ;
- seuil radar entre 4 et 20 mA ; hystérésis entre 0,1 et (seuil − 4) ; variation 0,1 à 8 mA ; tmin 1 à 3600 s ;
- pas de boucle dans les amonts.

## Champ ignoré

Toute autre clé est ignorée par le moteur. Ne pas en ajouter.
