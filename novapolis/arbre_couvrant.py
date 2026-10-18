"""Arbres couvrants minimaux. Union-Find fourni ; Kruskal et Prim à écrire."""


class UnionFind:
    """Union-Find avec compression de chemin et union par rang."""

    def __init__(self, elements):
        self.parent = {x: x for x in elements}
        self.rang = {x: 0 for x in elements}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rang[ra] < self.rang[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rang[ra] == self.rang[rb]:
            self.rang[ra] += 1
        return True


# TODO Module 4 : kruskal(graph), prim(graph)
