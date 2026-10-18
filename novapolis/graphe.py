"""Structure de graphe : listes d'adjacence, orienté ou non."""
from dataclasses import dataclass
import copy as _copy


@dataclass
class Edge:
    poids: float
    statut: str = "ouvert"


class Graph:
    def __init__(self, oriente=True):
        self.oriente = oriente
        self.adj = {}  # adj[u][v] = Edge

    def add_node(self, u):
        self.adj.setdefault(u, {})

    def add_edge(self, u, v, poids, statut="ouvert"):
        self.add_node(u)
        self.add_node(v)
        self.adj[u][v] = Edge(poids, statut)
        if not self.oriente:
            self.adj[v][u] = Edge(poids, statut)

    def remove_edge(self, u, v):
        self.adj.get(u, {}).pop(v, None)
        if not self.oriente:
            self.adj.get(v, {}).pop(u, None)

    def nodes(self):
        return list(self.adj)

    def edges(self):
        """Liste d'arcs (u, v, poids, statut). Non orienté : chaque arête une seule fois."""
        out = []
        for u, voisins in self.adj.items():
            for v, e in voisins.items():
                if self.oriente or str(u) <= str(v):
                    out.append((u, v, e.poids, e.statut))
        return out

    def copy(self):
        """Copie indépendante : les scénarios s'appliquent dessus, jamais sur la base."""
        return _copy.deepcopy(self)
