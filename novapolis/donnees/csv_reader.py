"""Module de lecture des fichiers CSV."""
import csv

def lire_fichier_csv(chemin):
    """Lit un fichier CSV et retourne une liste de dictionnaires."""
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def extraire_nombre(valeur, nom, fichier, ligne, erreurs, negatif_ok=False):
    """Convertit une valeur en float et vérifie qu'elle est valide."""
    try:
        x = float(valeur)
    except (TypeError, ValueError):
        erreurs.append(f"{fichier} ligne {ligne} : '{nom}' non numérique ({valeur!r})")
        return None
    if x < 0 and not negatif_ok:
        erreurs.append(f"{fichier} ligne {ligne} : '{nom}' négatif ({x})")
        return None
    return x
