"""
Algorithmes de parcours de graphes (BFS, DFS) et d'analyse de connexité.
"""

from collections import deque
from typing import List, Dict, Set, Tuple, Optional
from .graphe import Graphe

STATUTS_BLOQUES = {"ferme", "interdit"}


def voisins_accessibles(graphe: Graphe, u: str) -> List[str]:
    """Retourne les voisins atteignables depuis u en ignorant les arcs bloqués."""
    return [
        v for v, arete in graphe.adjacences[u].items() 
        if arete.statut not in STATUTS_BLOQUES
    ]


def parcours_largeur(graphe: Graphe, sources: List[str] | str) -> Tuple[Dict[str, int], Dict[str, Optional[str]]]:
    """
    Parcours en largeur (BFS) multi-sources.
    Retourne les distances (nombre minimal d'arcs) et les prédécesseurs.
    """
    if isinstance(sources, str):
        sources = [sources]
        
    distances = {}
    predecesseurs = {}
    file_attente = deque()
    
    for source in sources:
        distances[source] = 0
        predecesseurs[source] = None
        file_attente.append(source)
        
    while file_attente:
        noeud_courant = file_attente.popleft()
        for voisin in voisins_accessibles(graphe, noeud_courant):
            if voisin not in distances:
                distances[voisin] = distances[noeud_courant] + 1
                predecesseurs[voisin] = noeud_courant
                file_attente.append(voisin)
                
    return distances, predecesseurs


def parcours_profondeur(graphe: Graphe, sources: List[str] | str) -> Set[str]:
    """
    Parcours en profondeur (DFS) itératif.
    Retourne l'ensemble des sommets atteints.
    """
    if isinstance(sources, str):
        sources = [sources]
        
    sommets_visites = set()
    pile = list(sources)
    
    while pile:
        noeud = pile.pop()
        if noeud in sommets_visites:
            continue
        sommets_visites.add(noeud)
        
        for voisin in voisins_accessibles(graphe, noeud):
            if voisin not in sommets_visites:
                pile.append(voisin)
                
    return sommets_visites


def chemin_minimum_arcs(graphe: Graphe, source: str, cible: str) -> Optional[List[str]]:
    """Retourne l'itinéraire minimisant le nombre d'arcs ou None si inaccessible."""
    distances, predecesseurs = parcours_largeur(graphe, source)
    if cible not in distances:
        return None
        
    chemin = []
    noeud_courant = cible
    while noeud_courant is not None:
        chemin.append(noeud_courant)
        noeud_courant = predecesseurs[noeud_courant]
        
    return chemin[::-1]


def detecter_cycle_oriente(graphe: Graphe) -> Optional[List[str]]:
    """Détecte un cycle dans un graphe orienté. Retourne la liste des sommets ou None."""
    NON_VISITE, EN_COURS, TERMINE = 0, 1, 2
    etats = {noeud: NON_VISITE for noeud in graphe.noeuds()}
    parents = {}
    
    for sommet in graphe.noeuds():
        if etats[sommet] != NON_VISITE:
            continue
            
        etats[sommet] = EN_COURS
        parents[sommet] = None
        pile = [(sommet, iter(voisins_accessibles(graphe, sommet)))]
        
        while pile:
            noeud_courant, iterateur = pile[-1]
            try:
                voisin = next(iterateur)
                if etats[voisin] == EN_COURS:
                    # Cycle détecté
                    cycle = [voisin]
                    noeud_remontee = noeud_courant
                    while noeud_remontee != voisin:
                        cycle.append(noeud_remontee)
                        noeud_remontee = parents[noeud_remontee]
                    cycle.append(voisin)
                    return cycle[::-1]
                    
                if etats[voisin] == NON_VISITE:
                    etats[voisin] = EN_COURS
                    parents[voisin] = noeud_courant
                    pile.append((voisin, iter(voisins_accessibles(graphe, voisin))))
            except StopIteration:
                etats[noeud_courant] = TERMINE
                pile.pop()
                
    return None


def composantes_connexes(graphe: Graphe) -> List[List[str]]:
    """Retourne les composantes connexes d'un graphe non orienté."""
    sommets_visites = set()
    composantes = []
    
    for sommet in graphe.noeuds():
        if sommet not in sommets_visites:
            composante = parcours_profondeur(graphe, sommet)
            sommets_visites |= composante
            composantes.append(sorted(list(composante)))
            
    return composantes


def composantes_fortement_connexes(graphe: Graphe) -> List[List[str]]:
    """Retourne les composantes fortement connexes d'un graphe orienté (Kosaraju)."""
    sommets_visites = set()
    ordre_fin = []
    
    # Étape 1 : Obtenir l'ordre de fin de visite
    for sommet in graphe.noeuds():
        if sommet in sommets_visites:
            continue
            
        sommets_visites.add(sommet)
        pile = [(sommet, iter(voisins_accessibles(graphe, sommet)))]
        
        while pile:
            noeud, iterateur = pile[-1]
            try:
                voisin = next(iterateur)
                if voisin not in sommets_visites:
                    sommets_visites.add(voisin)
                    pile.append((voisin, iter(voisins_accessibles(graphe, voisin))))
            except StopIteration:
                ordre_fin.append(noeud)
                pile.pop()
                
    # Étape 2 : Créer le graphe transposé
    graphe_transpose = {noeud: [] for noeud in graphe.noeuds()}
    for u in graphe.noeuds():
        for v in voisins_accessibles(graphe, u):
            graphe_transpose[v].append(u)
            
    # Étape 3 : Parcours DFS sur le transposé en suivant l'ordre inverse
    sommets_visites.clear()
    composantes = []
    
    for sommet in reversed(ordre_fin):
        if sommet in sommets_visites:
            continue
            
        composante_courante = []
        pile = [sommet]
        sommets_visites.add(sommet)
        
        while pile:
            noeud = pile.pop()
            composante_courante.append(noeud)
            for voisin in graphe_transpose[noeud]:
                if voisin not in sommets_visites:
                    sommets_visites.add(voisin)
                    pile.append(voisin)
                    
        composantes.append(sorted(composante_courante))
        
    return composantes


def sites_inaccessibles(graphe: Graphe, sources: List[str]) -> List[str]:
    """Retourne la liste triée des sites non atteignables depuis les sources données."""
    sites_accessibles = parcours_profondeur(graphe, sources)
    return sorted(list(set(graphe.noeuds()) - sites_accessibles))


def sites_isoles(graphe: Graphe) -> List[str]:
    """Retourne les sites ne possédant aucun arc utilisable (ni entrant, ni sortant)."""
    noeuds_entrants = set()
    for u in graphe.noeuds():
        for v in voisins_accessibles(graphe, u):
            noeuds_entrants.add(v)
            
    return sorted([
        u for u in graphe.noeuds() 
        if not voisins_accessibles(graphe, u) and u not in noeuds_entrants
    ])
