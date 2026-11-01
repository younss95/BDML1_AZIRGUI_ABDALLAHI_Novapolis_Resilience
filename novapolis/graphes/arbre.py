"""
Implémentation des algorithmes d'arbres couvrants minimaux.
Contient la structure Union-Find ainsi que les algorithmes de Kruskal et Prim.
Gère les forêts pour les graphes non connexes et la simulation de pannes.
"""

from typing import List, Tuple, Set, Optional
import heapq
from .graphe import Graphe, Arete

STATUTS_BLOQUES = {"interdit", "travaux", "ferme"}


class UnionFind:
    """Structure de données pour gérer des ensembles disjoints avec compression de chemin."""

    def __init__(self, elements: List[str]):
        """Initialise la structure avec chaque élément dans son propre ensemble."""
        self.parent = {x: x for x in elements}
        self.rang = {x: 0 for x in elements}

    def trouver(self, x: str) -> str:
        """Trouve le représentant de l'ensemble contenant x avec compression de chemin."""
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def unir(self, a: str, b: str) -> bool:
        """Unit les ensembles contenant a et b. Retourne Vrai si l'union a été effectuée."""
        racine_a = self.trouver(a)
        racine_b = self.trouver(b)

        if racine_a == racine_b:
            return False

        if self.rang[racine_a] < self.rang[racine_b]:
            racine_a, racine_b = racine_b, racine_a

        self.parent[racine_b] = racine_a
        if self.rang[racine_a] == self.rang[racine_b]:
            self.rang[racine_a] += 1
        return True


def kruskal(graphe: Graphe) -> Tuple[List[Tuple[str, str, float]], float, int]:
    """
    Algorithme de Kruskal. Construit un arbre (ou une forêt) couvrant de poids minimum.
    Retourne la liste des arêtes, le coût total, et le nombre de composantes connexes (forêt).
    """
    aretes_valides = [
        arete for arete in graphe.aretes()
        if arete[3] not in STATUTS_BLOQUES
    ]
    aretes_triees = sorted(aretes_valides, key=lambda x: x[2])
    ensembles = UnionFind(graphe.noeuds())
    
    arbre_couvrant = []
    cout_total = 0.0
    composantes = len(graphe.noeuds())

    for origine, destination, poids, statut in aretes_triees:
        if ensembles.unir(origine, destination):
            arbre_couvrant.append((origine, destination, poids))
            cout_total += poids
            composantes -= 1

    return arbre_couvrant, cout_total, composantes


def prim(graphe: Graphe) -> Tuple[List[Tuple[str, str, float]], float, int]:
    """
    Algorithme de Prim. Construit un arbre (ou une forêt) couvrant de poids minimum.
    Retourne la liste des arêtes, le coût total, et le nombre de composantes connexes.
    """
    noeuds_restants = set(graphe.noeuds())
    arbre_couvrant = []
    cout_total = 0.0
    composantes = 0

    while noeuds_restants:
        sommet_depart = noeuds_restants.pop()
        noeuds_restants.add(sommet_depart)
        
        visites: Set[str] = {sommet_depart}
        noeuds_restants.remove(sommet_depart)
        
        aretes: List[Tuple[float, str, str]] = []
        for voisin, arete in graphe.adjacences[sommet_depart].items():
            if arete.statut not in STATUTS_BLOQUES:
                heapq.heappush(aretes, (arete.poids, sommet_depart, voisin))

        composantes += 1

        while aretes:
            poids, u, v = heapq.heappop(aretes)

            if v not in visites:
                visites.add(v)
                noeuds_restants.discard(v)
                arbre_couvrant.append((u, v, poids))
                cout_total += poids

                for voisin, arete in graphe.adjacences[v].items():
                    if voisin not in visites and arete.statut not in STATUTS_BLOQUES:
                        heapq.heappush(aretes, (arete.poids, v, voisin))

    return arbre_couvrant, cout_total, composantes


def simuler_panne_et_reparer(graphe: Graphe, arbre_actuel: List[Tuple[str, str, float]], arete_en_panne: Tuple[str, str]) -> Tuple[Optional[Tuple[str, str, float]], float]:
    """
    Simule la panne d'un tronçon de l'arbre et cherche le tronçon de remplacement le moins coûteux.
    Retourne la nouvelle arête de raccordement et son coût (ou None si irréparable).
    """
    u_panne, v_panne = arete_en_panne[0], arete_en_panne[1]
    
    arbre_restant = [
        (u, v, p) for (u, v, p) in arbre_actuel 
        if not ((u == u_panne and v == v_panne) or (u == v_panne and v == u_panne))
    ]
    
    ensembles = UnionFind(graphe.noeuds())
    for u, v, p in arbre_restant:
        ensembles.unir(u, v)
        
    aretes_valides = [
        (u, v, p, s) for (u, v, p, s) in graphe.aretes()
        if s not in STATUTS_BLOQUES and not ((u == u_panne and v == v_panne) or (u == v_panne and v == u_panne))
    ]
    aretes_triees = sorted(aretes_valides, key=lambda x: x[2])
    
    for u, v, poids, statut in aretes_triees:
        if ensembles.trouver(u) != ensembles.trouver(v):
            return (u, v, poids), poids
            
    return None, 0.0
