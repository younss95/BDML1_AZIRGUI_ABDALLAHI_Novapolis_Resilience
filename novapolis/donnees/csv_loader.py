"""Module de chargement des entités du domaine depuis les données brutes."""
import os
from .exceptions import ErreurValidation
from .csv_reader import lire_fichier_csv, extraire_nombre
from novapolis.graphes.graphe import Graphe

STATUTS_ROUTE = {"ouvert", "ferme", "travaux"}
STATUTS_FIBRE = {"disponible", "interdit"}
ACTIONS_VALIDES = {"route": {"fermer", "ouvrir"}, "fibre": {"supprimer", "interdire"}}

def charger_sites(dossier, erreurs):
    sites = {}
    for i, r in enumerate(lire_fichier_csv(os.path.join(dossier, "sites.csv")), start=2):
        if r["id"] in sites:
            erreurs.append(f"sites.csv ligne {i} : identifiant dupliqué '{r['id']}'")
            continue
        sites[r["id"]] = r
    return sites

def charger_routes(dossier, sites, erreurs, pointe=False):
    g = Graphe(oriente=True)
    for s in sites:
        g.ajouter_noeud(s)
    col = "temps_pointe" if pointe else "temps_normal"
    for i, r in enumerate(lire_fichier_csv(os.path.join(dossier, "routes.csv")), start=2):
        ok = True
        for k in ("u", "v"):
            if r[k] not in sites:
                erreurs.append(f"routes.csv ligne {i} : le site '{r[k]}' n'existe pas dans sites.csv")
                ok = False
        if r["statut"] not in STATUTS_ROUTE:
            erreurs.append(f"routes.csv ligne {i} : statut inconnu '{r['statut']}'")
            ok = False
        t = extraire_nombre(r[col], col, "routes.csv", i, erreurs)
        if ok and t is not None:
            g.ajouter_arete(r["u"], r["v"], t, r["statut"])
    return g

def charger_fibre(dossier, sites, erreurs):
    g = Graphe(oriente=False)
    for s in sites:
        g.ajouter_noeud(s)
    for i, r in enumerate(lire_fichier_csv(os.path.join(dossier, "fibre.csv")), start=2):
        ok = True
        for k in ("u", "v"):
            if r[k] not in sites:
                erreurs.append(f"fibre.csv ligne {i} : le site '{r[k]}' n'existe pas dans sites.csv")
                ok = False
        if r["statut"] not in STATUTS_FIBRE:
            erreurs.append(f"fibre.csv ligne {i} : statut inconnu '{r['statut']}'")
            ok = False
        c = extraire_nombre(r["cost"], "cost", "fibre.csv", i, erreurs)
        if ok and c is not None:
            g.ajouter_arete(r["u"], r["v"], c, r["statut"])
    return g

def charger_demandes(dossier, sites, erreurs):
    demandes, ids = [], set()
    for i, r in enumerate(lire_fichier_csv(os.path.join(dossier, "demandes.csv")), start=2):
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
    erreurs = []
    sites = charger_sites(dossier, erreurs)
    routes = charger_routes(dossier, sites, erreurs)
    fibre = charger_fibre(dossier, sites, erreurs)
    demandes = charger_demandes(dossier, sites, erreurs)
    if erreurs:
        raise ErreurValidation("\n".join(erreurs))
    return sites, routes, fibre, demandes

def charger_scenarios(dossier, sites):
    chemin = os.path.join(dossier, "scenarios.csv")
    if not os.path.exists(chemin):
        return {}
    erreurs, scenarios = [], {}
    for i, r in enumerate(lire_fichier_csv(chemin), start=2):
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
