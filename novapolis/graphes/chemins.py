"""
Algorithmes de calcul de plus courts chemins (Dijkstra, Bellman-Ford, Floyd-Warshall).
Gère la détection des circuits absorbants (cycles de poids négatif).
"""

import heapq
from typing import Dict, List, Tuple, Optional, Set
from .graphe import Graphe

STATUTS_BLOQUES = {"ferme", "interdit", "travaux"}


def dijkstra(graphe: Graphe, source: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """
    Algorithme de Dijkstra pour les plus courts chemins avec poids non négatifs.
    Retourne les distances minimales et les prédécesseurs.
    """
    distances = {noeud: float('inf') for noeud in graphe.noeuds()}
    predecesseurs: Dict[str, Optional[str]] = {noeud: None for noeud in graphe.noeuds()}
    
    distances[source] = 0.0
    file_priorite = [(0.0, source)]
    visites: Set[str] = set()
    
    while file_priorite:
        dist_u, u = heapq.heappop(file_priorite)
        
        if u in visites:
            continue
        visites.add(u)
        
        for v, arete in graphe.adjacences[u].items():
            if arete.statut in STATUTS_BLOQUES:
                continue
                
            nouvelle_distance = dist_u + arete.poids
            if nouvelle_distance < distances[v]:
                distances[v] = nouvelle_distance
                predecesseurs[v] = u
                heapq.heappush(file_priorite, (nouvelle_distance, v))
                
    return distances, predecesseurs


def bellman_ford(graphe: Graphe, source: str) -> Tuple[Dict[str, float], Dict[str, Optional[str]], bool]:
    """
    Algorithme de Bellman-Ford gérant les poids négatifs.
    Retourne les distances, les prédécesseurs, et un booléen indiquant la présence d'un
    circuit absorbant ACCESSIBLE depuis la source.
    """
    distances = {noeud: float('inf') for noeud in graphe.noeuds()}
    predecesseurs: Dict[str, Optional[str]] = {noeud: None for noeud in graphe.noeuds()}
    distances[source] = 0.0
    noeuds = graphe.noeuds()

    for _ in range(len(noeuds) - 1):
        changement = False
        for u in noeuds:
            if distances[u] == float('inf'):
                continue
            for v, arete in graphe.adjacences[u].items():
                if arete.statut in STATUTS_BLOQUES:
                    continue
                if distances[u] + arete.poids < distances[v]:
                    distances[v] = distances[u] + arete.poids
                    predecesseurs[v] = u
                    changement = True
        if not changement:
            break

    # Passage de vérification : un sommet qui s'améliore encore est "instable"
    sommets_instables = set()
    for u in noeuds:
        if distances[u] == float('inf'):
            continue
        for v, arete in graphe.adjacences[u].items():
            if arete.statut in STATUTS_BLOQUES:
                continue
            if distances[u] + arete.poids < distances[v]:
                sommets_instables.add(v)

    cycle_absorbant = bool(sommets_instables)

    # Propagation de -inf : tout sommet atteignable depuis un sommet instable
    pile = list(sommets_instables)
    while pile:
        u = pile.pop()
        if distances[u] == float('-inf'):
            continue
        distances[u] = float('-inf')
        for v, arete in graphe.adjacences[u].items():
            if arete.statut not in STATUTS_BLOQUES and distances[v] != float('-inf'):
                pile.append(v)

    return distances, predecesseurs, cycle_absorbant


def floyd_warshall(graphe: Graphe) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, Optional[str]]], List[str]]:
    """
    Algorithme de Floyd-Warshall pour les plus courts chemins entre toutes paires de sommets.
    Retourne les matrices de distances, de prédécesseurs, et la liste des sommets impliqués dans un cycle absorbant.
    """
    noeuds = graphe.noeuds()
    distances = {u: {v: float('inf') for v in noeuds} for u in noeuds}
    predecesseurs: Dict[str, Dict[str, Optional[str]]] = {u: {v: None for v in noeuds} for u in noeuds}
    
    for u in noeuds:
        distances[u][u] = 0.0
        for v, arete in graphe.adjacences[u].items():
            if arete.statut not in STATUTS_BLOQUES:
                distances[u][v] = arete.poids
                predecesseurs[u][v] = u
                
    for k in noeuds:
        for i in noeuds:
            for j in noeuds:
                if distances[i][k] != float('inf') and distances[k][j] != float('inf'):
                    nouvelle_distance = distances[i][k] + distances[k][j]
                    if nouvelle_distance < distances[i][j]:
                        distances[i][j] = nouvelle_distance
                        predecesseurs[i][j] = predecesseurs[k][j]

    noeuds_dans_cycle_negatif = [u for u in noeuds if distances[u][u] < 0]

    # Les trajets qui traversent un circuit absorbant n'ont pas de distance finie : -inf
    for k in noeuds_dans_cycle_negatif:
        for i in noeuds:
            if distances[i][k] == float('inf'):
                continue
            for j in noeuds:
                if distances[k][j] != float('inf'):
                    distances[i][j] = float('-inf')

    return distances, predecesseurs, noeuds_dans_cycle_negatif


def reconstruire_chemin(predecesseurs: Dict[str, Optional[str]], source: str, cible: str) -> Optional[List[str]]:
    """
    Reconstruit l'itinéraire de la source vers la cible à partir du dictionnaire des prédécesseurs.
    Retourne la liste des sommets visités ou None si la cible est inaccessible, ou si les
    prédécesseurs forment une boucle (signe d'un circuit absorbant : pas de chemin défini).
    """
    if cible == source:
        return [source]

    if cible not in predecesseurs or predecesseurs[cible] is None:
        return None

    chemin = []
    deja_vus = set()
    noeud_courant = cible
    while noeud_courant is not None:
        if noeud_courant in deja_vus:
            return None
        deja_vus.add(noeud_courant)
        chemin.append(noeud_courant)
        noeud_courant = predecesseurs[noeud_courant]

    return chemin[::-1]
