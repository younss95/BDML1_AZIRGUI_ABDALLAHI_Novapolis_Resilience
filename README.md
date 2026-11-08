# Novapolis Résilience

Outil en ligne de commande (Python) pour analyser le réseau de la métropole de Novapolis :
accessibilité des sites sensibles, itinéraires de secours, extension de la fibre optique
et test de scénarios de crise.

Projet EFREI – Graphes. Binôme : Younes AZIRGUI et EL Housseine ABDALLAHI.

---

## 1. Installation

Python 3.10 ou plus récent.

```bash
git clone https://github.com/younss95/BDML1_AZIRGUI_ABDALLAHI_Novapolis_Resilience.git
cd BDML1_AZIRGUI_ABDALLAHI_Novapolis_Resilience
python3 -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Utilisation

### Mode interactif (recommandé pour la démo)

```bash
python3 -m novapolis.cli.interactive
```

1. Un premier menu permet de naviguer jusqu'au dossier de données voulu (ex. `data/realiste`)
   puis de le choisir avec **✓ VALIDER CE DOSSIER**.
   Ce menu propose aussi **⚙ GÉNÉRER UN DATASET** et **📈 LANCER LES BENCHMARKS**.
2. Un second menu donne accès à la vérification des données et aux 5 modules (voir tableau ci-dessous).

### Mode commande

```bash
# Vérifier un jeu de données
python3 main.py --data data/petit --op validate

# Accessibilité (BFS / DFS)
python3 main.py --data data/petit --op accessibilite

# Résilience : un scénario du fichier scenarios.csv
python3 main.py --data data/realiste --op resilience --scenario fermeture_axe

# Benchmarks (les graphiques sont écrits dans resultats/)
python3 main.py --data resultats --op benchmark --max-sommets 1000 --max-fw 100
```

Pour voir toutes les options : `python3 main.py --help`.

## 3. Les 5 modules

| Module | Contenu | Algorithmes |
|---|---|---|
| 1 – Accessibilité | Quels sites peuvent atteindre quels autres ? Cycles, composantes | BFS, DFS, détection de cycle, Kosaraju |
| 2 – Itinéraires | Plus court chemin entre un site et une demande, selon le critère choisi | Dijkstra, Bellman-Ford |
| 3 – Circuits absorbants | Détection des cycles de poids négatif | Bellman-Ford (propagation de −∞) |
| 4 – Fibre optique | Réseau de fibre de coût minimum, réparation après une panne | Kruskal (Union-Find), Prim |
| 5 – Résilience et expériences | Scénarios de crise, indicateurs, benchmarks | Tous les précédents |

Floyd-Warshall est utilisé pour la comparaison de performances (benchmarks).

## 4. Jeux de données

| Dossier | Sites | Origine |
|---|---|---|
| `data/petit` | 7 | Écrit à la main (sert aux tests et aux exemples du rapport) |
| `data/realiste` | 120 | Généré (graine 42) |
| `data/genere` | 1000 | Généré (graine 42) |
| `data/osm_creteil` | 1115 | Données réelles de Créteil, © contributeurs OpenStreetMap (licence ODbL) |

Chaque dossier contient : `sites.csv`, `routes.csv`, `fibre.csv`, `demandes.csv`
et, si besoin, `scenarios.csv`.

Les données OSM ne sont pas reproduites à l'identique si on relance l'extraction
(la carte OpenStreetMap évolue). `osm_creteil` n'a pas de `scenarios.csv`.

### Générer un jeu de données

```bash
python3 main.py --data x --op generate --sites 120 --dossier realiste
```

⚠️ Attention : régénérer `data/realiste` écrase son `scenarios.csv`.
Pour le retrouver : `git checkout data/realiste/scenarios.csv`.

### Extraire des données réelles (OpenStreetMap)

Nécessite internet.

```bash
python3 tools/extract_donnees_reelles.py --lieu "Créteil, France" --sortie data/osm_creteil --demandes 50
```

## 5. Format des scénarios

Fichier `scenarios.csv` : `scenario,type_element,u,v,action`

- Route : `fermer` ou `ouvrir`
- Fibre : `supprimer` ou `interdire`

Exemple (`data/realiste`) : `fermeture_axe` ferme la route S62→S112 ;
`panne_fibre` supprime le tronçon de fibre S25–S54.

## 6. Structure du code

```
main.py                    point d'entrée en ligne de commande
novapolis/
  graphes/                 graphe, parcours (BFS/DFS), chemins, arbre couvrant, scénarios
  donnees/                 lecture et validation des fichiers CSV
  cli/                     menus interactifs et modules
  indicateurs.py           indicateurs de comparaison avant / après
  generateur.py            génération de jeux de données
  benchmarks.py            mesures de temps et graphiques
tools/                     extraction des données OpenStreetMap
tests/                     tests automatiques
data/                      jeux de données
```

## 7. Choix de structures de données

- **Graphe : listes d'adjacence** (dictionnaire de dictionnaires). Les réseaux sont peu denses,
  donc c'est plus léger qu'une matrice et on parcourt directement les voisins.
- **Routes** : graphe orienté. **Fibre** : graphe non orienté.
- **File (`deque`)** pour le BFS, **pile** pour le DFS, **tas (`heapq`)** pour Dijkstra et Prim.
- **Union-Find** (compression de chemin + rang) pour Kruskal.
- Pour tester un scénario, on travaille sur une **copie** du graphe : l'original n'est jamais modifié.

## 8. Tests

```bash
python3 -m pytest
```

24 tests : parcours, circuits absorbants, arbres couvrants, résilience.

## 9. Limites connues

- Les temps de pointe sont lus dans les fichiers mais ne sont pas utilisés dans les calculs.
- Une route « en travaux » est traversable pour le BFS/DFS, mais bloquée pour les plus courts chemins.
- Kruskal trie uniquement selon le coût : en cas d'égalité, le choix des arêtes est arbitraire
  (le coût total, lui, reste identique à Prim).