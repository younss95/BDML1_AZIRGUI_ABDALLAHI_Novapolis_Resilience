"""
Implémentation des algorithmes d'arbres couvrants minimaux.
Contient la structure Union-Find ainsi que les algorithmes de Kruskal et Prim.
"""

from typing import List


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

# TODO Module 4 : kruskal(graph), prim(graph)