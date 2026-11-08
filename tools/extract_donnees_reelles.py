"""
Outil d'extraction et de conversion des données OpenStreetMap vers le format Novapolis.
Génère les réseaux de routes, sites, et une topologie de fibre basée sur la triangulation de Delaunay.
"""

import os
import csv
import random
import argparse
import math
from typing import List, Dict, Any, Tuple
from loguru import logger
import osmnx as ox
import networkx as nx
from scipy.spatial import Delaunay
import numpy as np
import sys

LIEU_DEFAUT = "Créteil, France"
TYPES_SITES = ["caserne", "hopital", "ecole", "telecom", "quartier"]


def preparer_dossier_extraction(dossier_sortie: str) -> None:
    """Crée le dossier de destination pour les fichiers CSV extraits."""
    os.makedirs(dossier_sortie, exist_ok=True)


def analyser_vitesse_max(attr_vitesse_max: Any) -> float:
    """Analyse l'attribut maxspeed d'OpenStreetMap pour extraire une valeur numérique en km/h."""
    if isinstance(attr_vitesse_max, list):
        attr_vitesse_max = attr_vitesse_max[0]
    
    if isinstance(attr_vitesse_max, str):
        try:
            return float(attr_vitesse_max.replace(" km/h", "").replace(" mph", "").strip())
        except ValueError:
            return 50.0
            
    if isinstance(attr_vitesse_max, (int, float)):
        return float(attr_vitesse_max)
        
    return 50.0


def extraire_graphe_osm(nom_lieu: str) -> nx.MultiDiGraph:
    """Télécharge le graphe routier depuis OpenStreetMap pour la zone spécifiée."""
    logger.info("Extraction OSM")
    logger.info(f"Téléchargement des données pour : {nom_lieu}")
    try:
        graphe = ox.graph_from_place(nom_lieu, network_type="drive", simplify=True)
        return graphe
    except Exception as erreur:
        logger.error(f"Err: Impossible de récupérer les données pour {nom_lieu}. {erreur}")
        raise


def construire_donnees_sites(graphe: nx.MultiDiGraph) -> Tuple[List[Dict[str, Any]], Dict[int, str]]:
    """Convertit les nœuds OpenStreetMap en sites Novapolis et retourne la correspondance des identifiants."""
    sites = []
    correspondance_ids = {}
    
    donnees_noeuds = list(graphe.nodes(data=True))
    
    for index, (id_osm, donnees) in enumerate(donnees_noeuds, start=1):
        id_site = f"S{index}"
        correspondance_ids[id_osm] = id_site
        
        type_site = random.choices(TYPES_SITES, weights=[2, 3, 5, 5, 85], k=1)[0]
        
        sites.append({
            "id": id_site,
            "nom": f"OSM_{id_osm}",
            "type": type_site,
            "longitude": f"{donnees.get('x', 0.0):.6f}",
            "latitude": f"{donnees.get('y', 0.0):.6f}"
        })
        
    return sites, correspondance_ids


def construire_donnees_routes(graphe: nx.MultiDiGraph, correspondance_ids: Dict[int, str]) -> List[Dict[str, Any]]:
    """Convertit les arêtes OpenStreetMap en routes Novapolis avec calcul des temps de parcours."""
    routes = []
    aretes_ajoutees = set()
    
    for noeud_u, noeud_v, cle, donnees in graphe.edges(keys=True, data=True):
        id_src = correspondance_ids.get(noeud_u)
        id_dst = correspondance_ids.get(noeud_v)
        
        if not id_src or not id_dst or id_src == id_dst:
            continue
            
        signature_arete = (id_src, id_dst)
        if signature_arete in aretes_ajoutees:
            continue
            
        longueur_m = donnees.get("length", 100.0)
        vitesse_kmh = analyser_vitesse_max(donnees.get("maxspeed", 50.0))
        
        temps_minutes = (longueur_m / 1000.0) / vitesse_kmh * 60.0
        temps_minutes = max(0.1, temps_minutes)
        
        temps_pointe = temps_minutes * random.uniform(1.2, 3.0)
        
        routes.append({
            "u": id_src,
            "v": id_dst,
            "temps_normal": f"{temps_minutes:.2f}",
            "temps_pointe": f"{temps_pointe:.2f}",
            "statut": "ouvert"
        })
        aretes_ajoutees.add(signature_arete)
        
    return routes


def construire_donnees_fibre(sites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Génère un réseau de fibre optique réaliste basé sur la triangulation de Delaunay des coordonnées."""
    logger.info("Topologie Fibre")
    if len(sites) < 3:
        return []
        
    points = np.array([[float(s["longitude"]), float(s["latitude"])] for s in sites])
    tri_delaunay = Delaunay(points)
    
    aretes_fibre = set()
    
    for simplexe in tri_delaunay.simplices:
        for i in range(3):
            idx_u = simplexe[i]
            idx_v = simplexe[(i + 1) % 3]
            
            if idx_u > idx_v:
                idx_u, idx_v = idx_v, idx_u
                
            aretes_fibre.add((idx_u, idx_v))
            
    donnees_fibre = []
    for idx_u, idx_v in aretes_fibre:
        site_u = sites[idx_u]
        site_v = sites[idx_v]
        
        lon_u, lat_u = float(site_u["longitude"]), float(site_u["latitude"])
        lon_v, lat_v = float(site_v["longitude"]), float(site_v["latitude"])
        
        dist_deg = math.hypot(lon_u - lon_v, lat_u - lat_v)
        cout = dist_deg * 100000.0 
        cout = max(10.0, cout)
        
        donnees_fibre.append({
            "u": site_u["id"],
            "v": site_v["id"],
            "cost": f"{cout:.2f}",
            "statut": "disponible"
        })
        
    return donnees_fibre


def construire_donnees_demandes(sites: List[Dict[str, Any]], nombre_demandes: int) -> List[Dict[str, Any]]:
    """Génère des demandes d'intervention aléatoires sur les sites extraits."""
    demandes = []
    ids_sites = [s["id"] for s in sites]
    
    for index in range(1, nombre_demandes + 1):
        demandes.append({
            "id": f"D{index}",
            "origine": random.choice(ids_sites),
            "type": random.choice(["incendie", "medical"]),
            "priorite": random.randint(1, 3)
        })
        
    return demandes


def ecrire_csv(chemin_fichier: str, noms_colonnes: List[str], lignes: List[Dict[str, Any]]) -> None:
    """Écrit les données formatées dans un fichier CSV."""
    with open(chemin_fichier, mode="w", newline="", encoding="utf-8") as fichier:
        ecrivain = csv.DictWriter(fichier, fieldnames=noms_colonnes)
        ecrivain.writeheader()
        ecrivain.writerows(lignes)


def executer_extraction(nom_lieu: str, dossier_sortie: str, nombre_demandes: int = 50) -> None:
    """Orchestre le téléchargement OSM, la transformation des données et l'écriture des CSV."""
    try:
        graphe = extraire_graphe_osm(nom_lieu)
        preparer_dossier_extraction(dossier_sortie)
        
        sites, correspondance_ids = construire_donnees_sites(graphe)
        ecrire_csv(
            os.path.join(dossier_sortie, "sites.csv"), 
            ["id", "nom", "type", "longitude", "latitude"], 
            sites
        )
        
        routes = construire_donnees_routes(graphe, correspondance_ids)
        ecrire_csv(
            os.path.join(dossier_sortie, "routes.csv"), 
            ["u", "v", "temps_normal", "temps_pointe", "statut"], 
            routes
        )
        
        fibre = construire_donnees_fibre(sites)
        ecrire_csv(
            os.path.join(dossier_sortie, "fibre.csv"), 
            ["u", "v", "cost", "statut"], 
            fibre
        )
        
        demandes = construire_donnees_demandes(sites, nombre_demandes)
        ecrire_csv(
            os.path.join(dossier_sortie, "demandes.csv"), 
            ["id", "origine", "type", "priorite"], 
            demandes
        )
        
        ecrire_csv(
            os.path.join(dossier_sortie, "scenarios.csv"), 
            ["scenario", "type_element", "u", "v", "action"], 
            []
        )
        
        logger.success(f"Opération réussie. Données sauvegardées dans {dossier_sortie}")
        logger.info(f"Résumé : {len(sites)} sites, {len(routes)} routes, {len(fibre)} liaisons fibre.")
        
    except Exception as erreur:
        logger.error(f"Err: L'extraction a échoué. Détails : {erreur}")
        sys.exit(1)


def analyser_arguments() -> argparse.Namespace:
    """Configure et analyse les arguments de ligne de commande."""
    parseur = argparse.ArgumentParser(description="Extracteur OSM pour Novapolis")
    parseur.add_argument("--lieu", type=str, default=LIEU_DEFAUT, help="Nom de la ville ou zone (ex: 'Créteil, France')")
    parseur.add_argument("--sortie", type=str, default="data/osm_extract", help="Dossier de destination")
    parseur.add_argument("--demandes", type=int, default=50, help="Nombre de demandes à générer")
    return parseur.parse_args()


if __name__ == "__main__":
    arguments = analyser_arguments()
    executer_extraction(arguments.lieu, arguments.sortie, arguments.demandes)
