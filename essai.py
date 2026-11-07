from novapolis.lire_csv import charger_jeu
from novapolis.plus_courts_chemins import dijkstra, reconstruire_chemin

sites, routes, fibre, demandes = charger_jeu("data/petit")
dist, pred = dijkstra(routes, "S1")
print(dist)
print(pred)
print(reconstruire_chemin(pred, "S3"))
print(reconstruire_chemin(pred, "S6"))
print(reconstruire_chemin(pred, "S7"))