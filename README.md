# Novapolis Résilience

Projet d'algorithmique des graphes (EFREI ING-APP1-BDML).
Données de `data/petit` : synthétiques (fictives), écrites à la main.

## Installation
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Utilisation
    python main.py --data data/petit --op validate

## Format des CSV
- sites.csv    : id,nom,type,longitude,latitude
- routes.csv   : u,v,temps_normal,temps_pointe,statut   (statut: ouvert|ferme|travaux)
- fibre.csv    : u,v,cost,statut                         (statut: disponible|interdit)
- demandes.csv : id,origine,type,priorite
- scenarios.csv: scenario,type_element,u,v,action
