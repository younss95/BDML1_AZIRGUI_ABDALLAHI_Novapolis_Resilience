"""Benchmarks des performances des algorithmes de graphes."""
import time
import os
import random
import matplotlib.pyplot as plt
from typing import Callable, Any, List
from loguru import logger

from novapolis.donnees.csv_loader import charger_jeu
from novapolis.graphes import parcours, chemins, arbre
from novapolis.generateur import generer_jeu_de_donnees


def mesurer_temps(fonction: Callable, *args: Any, iterations: int = 5, **kwargs: Any) -> float:
    """Mesure le temps d'exécution moyen d'une fonction sur plusieurs itérations."""
    temps_liste = []
    for _ in range(iterations):
        debut = time.perf_counter()
        fonction(*args, **kwargs)
        temps_liste.append(time.perf_counter() - debut)
    return sum(temps_liste) / len(temps_liste)


def generer_tailles(max_sommets: int) -> List[int]:
    """Génère les paliers de sommets dynamiquement selon la limite définie."""
    tailles = []
    courant = 100
    while courant <= max_sommets:
        tailles.append(courant)
        if courant < 1000:
            if courant == 100:
                courant = 250
            elif courant == 250:
                courant = 500
            elif courant == 500:
                courant = 1000
        elif courant < 10000:
            courant += 500
        elif courant < 20000:
            courant += 5000
        elif courant < 50000:
            courant += 10000
        else:
            courant += 25000
            
    if tailles and tailles[-1] != max_sommets and max_sommets >= 100:
        tailles.append(max_sommets)
    return sorted(list(set(tailles)))


def generer_tailles_fw(max_sommets: int) -> List[int]:
    """Génère les paliers spécifiques et réduits pour Floyd-Warshall."""
    tailles = []
    courant = 20
    while courant <= max_sommets:
        tailles.append(courant)
        courant += 20
        
    if tailles and tailles[-1] != max_sommets and max_sommets >= 20:
        tailles.append(max_sommets)
    return sorted(list(set(tailles)))


def executer_benchmarks(dossier_sortie: str = "resultats", max_sommets: int = 1000, max_fw: int = 100) -> None:
    """Exécute tous les benchmarks, collecte les métriques et génère les graphiques."""
    os.makedirs(dossier_sortie, exist_ok=True)
    logger.info("Début des Benchmarks...")
    
    random.seed(42)

    tailles = generer_tailles(max_sommets)
    degre_moyen = 5

    temps_dijkstra = []
    temps_bellman = []
    temps_kruskal = []
    temps_prim = []
    temps_bfs = []
    temps_scc = []
    temps_cc = []

    logger.info(f"Tailles sélectionnées pour les parcours et arbres : {tailles}")

    for taille in tailles:
        dossier_jeu = os.path.join(dossier_sortie, f"bench_{taille}")
        # Le nombre de demandes importe peu pour les benchmarks de graphes bruts, on fixe à 10
        generer_jeu_de_donnees(dossier_jeu, taille, 10, degre_moyen, seed=42)
        sites, routes, fibre, _ = charger_jeu(dossier_jeu)

        source = list(sites.keys())[0]

        logger.info(f"Évaluation sur graphe de {taille} sommets...")
        t_dij = mesurer_temps(chemins.dijkstra, routes, source)
        temps_dijkstra.append(t_dij)

        t_bel = mesurer_temps(chemins.bellman_ford, routes, source)
        temps_bellman.append(t_bel)

        t_kru = mesurer_temps(arbre.kruskal, fibre)
        temps_kruskal.append(t_kru)

        t_pri = mesurer_temps(arbre.prim, fibre)
        temps_prim.append(t_pri)

        t_bfs = mesurer_temps(parcours.parcours_largeur, routes, [source])
        temps_bfs.append(t_bfs)
        
        t_scc = mesurer_temps(parcours.composantes_fortement_connexes, routes)
        temps_scc.append(t_scc)
        
        t_cc = mesurer_temps(parcours.composantes_connexes, fibre)
        temps_cc.append(t_cc)

    plt.figure(figsize=(10, 6))
    plt.plot(tailles, temps_dijkstra, label="Dijkstra O((V+E)logV)", marker="o")
    plt.plot(tailles, temps_bellman, label="Bellman-Ford O(V*E)", marker="s")
    plt.plot(tailles, temps_bfs, label="BFS O(V+E)", marker="^")
    plt.xlabel("Nombre de sommets (V)")
    plt.ylabel("Temps moyen (secondes)")
    plt.title("Performance des algorithmes de chemins")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(dossier_sortie, "bench_chemins.png"))
    plt.close()

    plt.figure(figsize=(10, 6))
    plt.plot(tailles, temps_kruskal, label="Kruskal O(E log E)", marker="o")
    plt.plot(tailles, temps_prim, label="Prim O(E log V)", marker="s")
    plt.xlabel("Nombre de sommets (V)")
    plt.ylabel("Temps moyen (secondes)")
    plt.title("Performance des arbres couvrants minimaux")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(dossier_sortie, "bench_arbres.png"))
    plt.close()
    
    plt.figure(figsize=(10, 6))
    plt.plot(tailles, temps_scc, label="Composantes Fortement Connexes (Kosaraju)", marker="o", color="purple")
    plt.plot(tailles, temps_cc, label="Composantes Connexes (DFS)", marker="s", color="orange")
    plt.xlabel("Nombre de sommets (V)")
    plt.ylabel("Temps moyen (secondes)")
    plt.title("Analyse de la connexité (Orienté vs Non Orienté)")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(dossier_sortie, "bench_connexite.png"))
    plt.close()

    tailles_fw = generer_tailles_fw(max_fw)
    temps_fw = []
    temps_apsp_dijkstra = []
    
    logger.info(f"Tailles sélectionnées pour Floyd-Warshall : {tailles_fw}")
    
    for taille in tailles_fw:
        dossier_jeu = os.path.join(dossier_sortie, f"bench_fw_{taille}")
        generer_jeu_de_donnees(dossier_jeu, taille, 2, degre_moyen, seed=42)
        _, routes, _, _ = charger_jeu(dossier_jeu)

        logger.info(f"Évaluation Floyd-Warshall sur {taille} sommets...")
        t_fw = mesurer_temps(chemins.floyd_warshall, routes, iterations=3)
        temps_fw.append(t_fw)
        
        def executer_apsp_dijkstra(graphe_oriente):
            for noeud in graphe_oriente.noeuds():
                chemins.dijkstra(graphe_oriente, noeud)
                
        t_apsp = mesurer_temps(executer_apsp_dijkstra, routes, iterations=3)
        temps_apsp_dijkstra.append(t_apsp)

    plt.figure(figsize=(10, 6))
    plt.plot(tailles_fw, temps_fw, label="Floyd-Warshall O(V^3)", color="red", marker="D")
    plt.plot(tailles_fw, temps_apsp_dijkstra, label="V * Dijkstra O(V*(V+E)logV)", color="blue", marker="X")
    plt.xlabel("Nombre de sommets (V)")
    plt.ylabel("Temps moyen (secondes)")
    plt.title("Plus courts chemins entre toutes paires (APSP)")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(dossier_sortie, "bench_apsp.png"))
    plt.close()
    
    niveaux_densite = [2, 5, 10, 20, 50]
    temps_kruskal_densite = []
    temps_prim_densite = []
    sommets_fixes = min(200, max_sommets)
    
    logger.info(f"Évaluation de l'impact de la densité sur {sommets_fixes} sommets...")
    for densite in niveaux_densite:
        dossier_jeu = os.path.join(dossier_sortie, f"bench_densite_{densite}")
        generer_jeu_de_donnees(dossier_jeu, sommets_fixes, 2, densite, seed=42)
        _, _, fibre_graphe, _ = charger_jeu(dossier_jeu)
        
        t_k_dens = mesurer_temps(arbre.kruskal, fibre_graphe)
        temps_kruskal_densite.append(t_k_dens)
        
        t_p_dens = mesurer_temps(arbre.prim, fibre_graphe)
        temps_prim_densite.append(t_p_dens)

    plt.figure(figsize=(10, 6))
    plt.plot(niveaux_densite, temps_kruskal_densite, label="Kruskal O(E log E)", color="green", marker="o")
    plt.plot(niveaux_densite, temps_prim_densite, label="Prim O(E log V)", color="brown", marker="s")
    plt.xlabel("Degré moyen (Densité des arêtes)")
    plt.ylabel("Temps moyen (secondes)")
    plt.title(f"Impact de la densité du graphe sur le calcul de l'Arbre Couvrant (V={sommets_fixes})")
    plt.legend()
    plt.grid(True)
    plt.savefig(os.path.join(dossier_sortie, "bench_densite.png"))
    plt.close()

    logger.success("Les graphiques ont été sauvegardés avec succès.")
