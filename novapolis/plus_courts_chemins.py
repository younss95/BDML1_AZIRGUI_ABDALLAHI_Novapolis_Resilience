"""Module 2 : plus courts chemins (durées en minutes)."""
import heapq

from .parcours import STATUTS_BLOQUES


def arcs_utilisables(g, u):
    """Arcs (voisin, poids) partant de u, en ignorant les routes fermées."""
    return [(v, e.poids) for v, e in g.adj[u].items()
            if e.statut not in STATUTS_BLOQUES]


def reconstruire_chemin(pred, cible):
    """Remonte pred depuis la cible. None si la cible n'a pas été atteinte."""
    if cible not in pred:
        return None
    chemin, u = [], cible
    while u is not None:
        chemin.append(u)
        u = pred[u]
    return chemin[::-1]


def dijkstra(g, source):
    """Dijkstra avec tas binaire (poids >= 0). Retourne (dist, pred)."""
    dist = {source: 0}
    pred = {source: None}
    tas = [(0, source)]
    while tas:
        d, u = heapq.heappop(tas)
        if d > dist[u]:          # entrée périmée : un meilleur chemin existe déjà
            continue
        for v, poids in arcs_utilisables(g, u):
            nd = d + poids
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                pred[v] = u
                heapq.heappush(tas, (nd, v))
    return dist, pred