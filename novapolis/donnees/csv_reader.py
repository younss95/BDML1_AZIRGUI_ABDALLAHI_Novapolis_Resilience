"""Lecture et validation des CSV. Les erreurs sont collectées avec un message explicite."""
import csv
import os

from .exceptions import ErreurValidation
from novapolis.graphes.graphe import Graphe

STATUTS_ROUTE = {"ouvert", "ferme", "travaux"}
STATUTS_FIBRE = {"disponible", "interdit"}


def _lire(chemin):
    with open(chemin, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _nombre(valeur, nom, fichier, ligne, erreurs, negatif_ok=False):
    """Convertit une valeur en float et vérifie qu'elle est positive si nécessaire."""
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
    """Retourne un dictionnaire {id: données} des sites. Les doublons sont signalés."""
    sites = {}
    for i, r in enumerate(_lire(os.path.join(dossier, "sites.csv")), start=2):
        if r["id"] in sites:
            erreurs.append(f"sites.csv ligne {i} : identifiant dupliqué '{r['id']}'")
            continue
        sites[r["id"]] = r
    return sites


def charger_routes(dossier, sites, erreurs, pointe=False):
    """Retourne un Graphe orienté. Les arcs 'ferme' sont conservés avec leur statut."""
    g = Graphe(oriente=True)
    for s in sites:
        g.ajouter_noeud(s)
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
            g.ajouter_arete(r["u"], r["v"], t, r["statut"])
    return g


def charger_fibre(dossier, sites, erreurs):
    """Retourne un Graphe non orienté. Les arêtes 'interdit' sont conservées avec leur statut."""
    g = Graphe(oriente=False)
    for s in sites:
        g.ajouter_noeud(s)
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
            g.ajouter_arete(r["u"], r["v"], c, r["statut"])
    return g


def charger_demandes(dossier, sites, erreurs):
    """Retourne une liste de demandes. Les doublons et références invalides sont signalés."""
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
    """Charge et valide un jeu complet. Lève ErreurValidation si des erreurs existent."""
    erreurs = []
    sites = charger_sites(dossier, erreurs)
    routes = charger_routes(dossier, sites, erreurs)
    fibre = charger_fibre(dossier, sites, erreurs)
    demandes = charger_demandes(dossier, sites, erreurs)
    if erreurs:
        raise ErreurValidation("\n".join(erreurs))
    return sites, routes, fibre, demandes


ACTIONS_VALIDES = {"route": {"fermer", "ouvrir"}, "fibre": {"supprimer", "interdire"}}


def charger_scenarios(dossier, sites):
    """Lit scenarios.csv et retourne {nom_scenario: [actions]}.
    Retourne {} si le fichier n'existe pas. Lève ErreurValidation si une ligne est invalide."""
    chemin = os.path.join(dossier, "scenarios.csv")
    if not os.path.exists(chemin):
        return {}
    erreurs, scenarios = [], {}
    for i, r in enumerate(_lire(chemin), start=2):
        if not r["scenario"]:
            erreurs.append(f"scenarios.csv ligne {i} : nom de scénario manquant")
            continue
        if r["type_element"] not in ACTIONS_VALIDES:
            erreurs.append(f"scenarios.csv ligne {i} : type_element inconnu '{r['type_element']}' (route ou fibre)")
            continue
        if r["action"] not in ACTIONS_VALIDES[r["type_element"]]:
            erreurs.append(f"scenarios.csv ligne {i} : action '{r['action']}' invalide pour '{r['type_element']}'")
            continue
        ok = True
        for k in ("u", "v"):
            if r[k] not in sites:
                erreurs.append(f"scenarios.csv ligne {i} : le site '{r[k]}' n'existe pas dans sites.csv")
                ok = False
        if ok:
            scenarios.setdefault(r["scenario"], []).append(dict(r))
    if erreurs:
        raise ErreurValidation("\n".join(erreurs))
    return scenarios