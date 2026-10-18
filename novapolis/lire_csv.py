"""Lecture et validation des CSV. Les erreurs sont collectées avec un message explicite."""
import csv
import os

STATUTS_ROUTE = {"ouvert", "ferme", "travaux"}
STATUTS_FIBRE = {"disponible", "interdit"}


class ValidationError(Exception):
    pass


def _lire(chemin):
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _nombre(valeur, nom, fichier, ligne, erreurs, negatif_ok=False):
    try:
        x = float(valeur)
    except (TypeError, ValueError):
        erreurs.append(f"{fichier} ligne {ligne} : '{nom}' non numérique ({valeur!r})")
        return None
    if x < 0 and not negatif_ok:
        erreurs.append(f"{fichier} ligne {ligne} : '{nom}' négatif ({x})")
        return None
    return x


def charger_sites(dossier, erreurs):
    sites = {}
    for i, r in enumerate(_lire(os.path.join(dossier, "sites.csv")), start=2):
        if r["id"] in sites:
            erreurs.append(f"sites.csv ligne {i} : identifiant dupliqué '{r['id']}'")
            continue
        sites[r["id"]] = r
    return sites


def charger_routes(dossier, sites, erreurs, pointe=False):
    """Retourne un Graph orienté. Les arcs 'ferme' sont conservés avec leur statut."""
    from .graphe import Graph
    g = Graph(oriente=True)
    for s in sites:
        g.add_node(s)
    col = "temps_pointe" if pointe else "temps_normal"
    for i, r in enumerate(_lire(os.path.join(dossier, "routes.csv")), start=2):
        ok = True
        for k in ("u", "v"):
            if r[k] not in sites:
                erreurs.append(f"routes.csv ligne {i} : le site '{r[k]}' n'existe pas dans sites.csv")
                ok = False
        if r["statut"] not in STATUTS_ROUTE:
            erreurs.append(f"routes.csv ligne {i} : statut inconnu '{r['statut']}'")
            ok = False
        t = _nombre(r[col], col, "routes.csv", i, erreurs)
        if ok and t is not None:
            g.add_edge(r["u"], r["v"], t, r["statut"])
    return g


def charger_fibre(dossier, sites, erreurs):
    from .graphe import Graph
    g = Graph(oriente=False)
    for s in sites:
        g.add_node(s)
    for i, r in enumerate(_lire(os.path.join(dossier, "fibre.csv")), start=2):
        ok = True
        for k in ("u", "v"):
            if r[k] not in sites:
                erreurs.append(f"fibre.csv ligne {i} : le site '{r[k]}' n'existe pas dans sites.csv")
                ok = False
        if r["statut"] not in STATUTS_FIBRE:
            erreurs.append(f"fibre.csv ligne {i} : statut inconnu '{r['statut']}'")
            ok = False
        c = _nombre(r["cost"], "cost", "fibre.csv", i, erreurs)
        if ok and c is not None:
            g.add_edge(r["u"], r["v"], c, r["statut"])
    return g


def charger_demandes(dossier, sites, erreurs):
    demandes, ids = [], set()
    for i, r in enumerate(_lire(os.path.join(dossier, "demandes.csv")), start=2):
        if r["id"] in ids:
            erreurs.append(f"demandes.csv ligne {i} : identifiant dupliqué '{r['id']}'")
            continue
        ids.add(r["id"])
        if r["origine"] not in sites:
            erreurs.append(f"demandes.csv ligne {i} : le site '{r['origine']}' n'existe pas dans sites.csv")
            continue
        demandes.append(r)
    return demandes


def charger_jeu(dossier):
    """Charge et valide un jeu complet. Lève ValidationError si des erreurs existent."""
    erreurs = []
    sites = charger_sites(dossier, erreurs)
    routes = charger_routes(dossier, sites, erreurs)
    fibre = charger_fibre(dossier, sites, erreurs)
    demandes = charger_demandes(dossier, sites, erreurs)
    if erreurs:
        raise ValidationError("\n".join(erreurs))
    return sites, routes, fibre, demandes
