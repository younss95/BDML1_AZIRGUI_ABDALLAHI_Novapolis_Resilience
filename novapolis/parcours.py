from collections import deque

STATUTS_BLOQUES = {"ferme", "interdit"}


def voisins(g, u):
    """Voisins atteignables depuis u en ignorant les arcs bloqués."""
    return [v for v, e in g.adj[u].items() if e.statut not in STATUTS_BLOQUES]


def bfs(g, sources):
    """BFS multi-sources. Retourne (dist, pred) : dist = nb minimal d'arcs."""
    if isinstance(sources, str):
        sources = [sources]
    dist, pred = {}, {}
    file = deque()
    for s in sources:
        dist[s], pred[s] = 0, None
        file.append(s)
    while file:
        u = file.popleft()
        for v in voisins(g, u):
            if v not in dist:
                dist[v] = dist[u] + 1
                pred[v] = u
                file.append(v)
    return dist, pred


def dfs(g, sources):
    """DFS itératif (pas de récursion). Retourne l'ensemble des sommets atteints."""
    if isinstance(sources, str):
        sources = [sources]
    vus = set()
    pile = list(sources)
    while pile:
        u = pile.pop()
        if u in vus:
            continue
        vus.add(u)
        for v in voisins(g, u):
            if v not in vus:
                pile.append(v)
    return vus


def chemin_min_arcs(g, source, cible):
    """Itinéraire minimisant le nombre d'arcs (BFS). None si inaccessible."""
    dist, pred = bfs(g, source)
    if cible not in dist:
        return None
    chemin, u = [], cible
    while u is not None:
        chemin.append(u)
        u = pred[u]
    return chemin[::-1]


def a_un_cycle_oriente(g):
    """Détection de cycle orienté par DFS blanc/gris/noir.
    Retourne un cycle (liste de sommets) ou None."""
    BLANC, GRIS, NOIR = 0, 1, 2
    couleur = {u: BLANC for u in g.nodes()}
    parent = {}
    for s in g.nodes():
        if couleur[s] != BLANC:
            continue
        couleur[s] = GRIS
        parent[s] = None
        pile = [(s, iter(voisins(g, s)))]
        while pile:
            u, it = pile[-1]
            for v in it:
                if couleur[v] == GRIS:          # arc retour -> cycle
                    cycle, x = [v], u
                    while x != v:
                        cycle.append(x)
                        x = parent[x]
                    cycle.append(v)
                    return cycle[::-1]
                if couleur[v] == BLANC:
                    couleur[v] = GRIS
                    parent[v] = u
                    pile.append((v, iter(voisins(g, v))))
                    break
            else:
                couleur[u] = NOIR
                pile.pop()
    return None

def composantes_connexes(g):
    """Composantes connexes d'un graphe NON orienté (fibre). Liste de listes."""
    vus, comps = set(), []
    for s in g.nodes():
        if s not in vus:
            comp = dfs(g, s)
            vus |= comp
            comps.append(sorted(comp))
    return comps


def composantes_fortement_connexes(g):
    """Composantes fortement connexes (Kosaraju, itératif) d'un graphe orienté."""
    # 1) ordre de fin de visite
    vus, ordre = set(), []
    for s in g.nodes():
        if s in vus:
            continue
        vus.add(s)
        pile = [(s, iter(voisins(g, s)))]
        while pile:
            u, it = pile[-1]
            for v in it:
                if v not in vus:
                    vus.add(v)
                    pile.append((v, iter(voisins(g, v))))
                    break
            else:
                ordre.append(u)
                pile.pop()
    # 2) graphe transposé
    inverse = {u: [] for u in g.nodes()}
    for u in g.nodes():
        for v in voisins(g, u):
            inverse[v].append(u)
    # 3) parcours dans l'ordre inverse sur le transposé
    vus, comps = set(), []
    for s in reversed(ordre):
        if s in vus:
            continue
        comp, pile = [], [s]
        vus.add(s)
        while pile:
            u = pile.pop()
            comp.append(u)
            for v in inverse[u]:
                if v not in vus:
                    vus.add(v)
                    pile.append(v)
        comps.append(sorted(comp))
    return comps


def sites_inaccessibles(g, sources):
    """Sites non atteignables depuis les sources (accessibilité ORIENTÉE)."""
    return sorted(set(g.nodes()) - dfs(g, sources))


def sites_isoles(g):
    """Sites sans aucun arc utilisable, entrant ou sortant."""
    entrants = set()
    for u in g.nodes():
        for v in voisins(g, u):
            entrants.add(v)
    return sorted(u for u in g.nodes() if not voisins(g, u) and u not in entrants)