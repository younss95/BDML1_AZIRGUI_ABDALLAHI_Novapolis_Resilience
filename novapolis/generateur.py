# novapolis/generateur.py
"""Générateur de données synthétiques pour les expériences."""
import csv
import os
import random
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger

TYPES_SITES = ["caserne", "hopital", "ecole", "telecom", "quartier"]


def creer_dossiers(chemin_dossier: str) -> None:
    """Crée le dossier cible s'il n'existe pas."""
    os.makedirs(chemin_dossier, exist_ok=True)


def generer_sites(nb_sites: int) -> List[Dict[str, Any]]:
    """Génère une liste de sites aléatoires avec des pondérations de types réalistes."""
    sites = []
    for i in range(1, nb_sites + 1):
        type_s = random.choices(
            TYPES_SITES,
            weights=[5, 5, 10, 10, 70],
            k=1
        )[0]
        sites.append({
            "id": f"S{i}",
            "nom": f"Site_{i}",
            "type": type_s,
            "longitude": f"{random.uniform(2.0, 3.0):.4f}",
            "latitude": f"{random.uniform(48.0, 49.0):.4f}"
        })
    return sites


def generer_routes(
    sites: List[Dict[str, Any]], 
    degre_moyen: int, 
    poids_negatifs: bool = False, 
    circuit_absorbant: bool = False
) -> Tuple[List[Dict[str, Any]], Optional[List[str]]]:
    """Génère le graphe routier orienté selon un degré sortant moyen et implémente d'éventuels circuits négatifs."""
    routes = []
    ids_sites = [s["id"] for s in sites]
    circuit = None

    for origine in ids_sites:
        nb_aretes = degre_moyen
        cibles = random.sample(ids_sites, k=min(nb_aretes, len(ids_sites) - 1))
        for destination in cibles:
            if origine == destination:
                continue
            
            t_normal = random.uniform(2.0, 20.0)
            if poids_negatifs and random.random() < 0.1:
                t_normal = -random.uniform(0.1, 5.0)
                
            if t_normal > 0:
                t_pointe = t_normal * random.uniform(1.2, 3.0)
            else:
                t_pointe = t_normal * 0.8
                
            routes.append({
                "u": origine,
                "v": destination,
                "temps_normal": f"{t_normal:.2f}",
                "temps_pointe": f"{t_pointe:.2f}",
                "statut": "ouvert"
            })
            
    if circuit_absorbant and len(ids_sites) >= 3:
        cycle_nodes = random.sample(ids_sites, 3)
        u, v, w = cycle_nodes
        
        routes = [r for r in routes if not (r["u"] in cycle_nodes and r["v"] in cycle_nodes)]
        
        routes.append({"u": u, "v": v, "temps_normal": "1.00", "temps_pointe": "2.00", "statut": "ouvert"})
        routes.append({"u": v, "v": w, "temps_normal": "1.00", "temps_pointe": "2.00", "statut": "ouvert"})
        routes.append({"u": w, "v": u, "temps_normal": "-5.00", "temps_pointe": "-5.00", "statut": "ouvert"})
        circuit = [u, v, w, u]

    return routes, circuit


def generer_fibre(sites: List[Dict[str, Any]], degre_moyen: int) -> List[Dict[str, Any]]:
    """Génère le graphe non orienté de fibre optique."""
    fibre = []
    ids_sites = [s["id"] for s in sites]
    for i, origine in enumerate(ids_sites):
        nb_aretes = max(1, degre_moyen // 2)
        cibles = random.sample(ids_sites[i + 1:], k=min(nb_aretes, len(ids_sites[i + 1:])))
        for destination in cibles:
            cout = random.uniform(10.0, 100.0)
            fibre.append({
                "u": origine,
                "v": destination,
                "cost": f"{cout:.2f}",
                "statut": "disponible"
            })
    return fibre


def generer_demandes(sites: List[Dict[str, Any]], nb_demandes: int) -> List[Dict[str, Any]]:
    """Génère des demandes d'intervention aléatoires."""
    demandes = []
    ids_sites = [s["id"] for s in sites]
    for i in range(1, nb_demandes + 1):
        demandes.append({
            "id": f"D{i}",
            "origine": random.choice(ids_sites),
            "type": random.choice(["incendie", "medical"]),
            "priorite": random.randint(1, 3)
        })
    return demandes


def sauvegarder_csv(chemin_fichier: str, noms_colonnes: List[str], donnees: List[Dict[str, Any]]) -> None:
    """Sauvegarde une liste de dictionnaires dans un fichier CSV."""
    with open(chemin_fichier, mode="w", newline="", encoding="utf-8") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=noms_colonnes)
        writer.writeheader()
        writer.writerows(donnees)


def generer_jeu_de_donnees(
    dossier_sortie: str, 
    nb_sites: int, 
    nb_demandes: int, 
    degre_moyen: int, 
    seed: int = 42,
    poids_negatifs: bool = False,
    circuit_absorbant: bool = False
) -> Optional[List[str]]:
    """Génère et sauvegarde l'ensemble des fichiers CSV du jeu de données, et retourne l'éventuel circuit absorbant."""
    random.seed(seed)
    creer_dossiers(dossier_sortie)

    logger.info(f"Génération du dataset dans {dossier_sortie} (sites={nb_sites}, seed={seed})")

    sites = generer_sites(nb_sites)
    sauvegarder_csv(os.path.join(dossier_sortie, "sites.csv"), ["id", "nom", "type", "longitude", "latitude"], sites)

    routes, circuit = generer_routes(sites, degre_moyen, poids_negatifs, circuit_absorbant)
    sauvegarder_csv(os.path.join(dossier_sortie, "routes.csv"), ["u", "v", "temps_normal", "temps_pointe", "statut"], routes)

    fibre = generer_fibre(sites, degre_moyen)
    sauvegarder_csv(os.path.join(dossier_sortie, "fibre.csv"), ["u", "v", "cost", "statut"], fibre)

    demandes = generer_demandes(sites, nb_demandes)
    sauvegarder_csv(os.path.join(dossier_sortie, "demandes.csv"), ["id", "origine", "type", "priorite"], demandes)

    sauvegarder_csv(os.path.join(dossier_sortie, "scenarios.csv"), ["scenario", "type_element", "u", "v", "action"], [])

    logger.success("Fichiers générés avec succès.")
    return circuit