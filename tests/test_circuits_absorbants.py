import pytest

from novapolis.donnees.csv_loader import charger_jeu
from novapolis.graphes import chemins as ch
from novapolis.graphes.graphe import Graphe
from novapolis.graphes.graphes_artificiels import circuit_absorbant_accessible, circuit_absorbant_inaccessible

INF = float("inf")


def test_bellman_ford_circuit_accessible():
    g, source = circuit_absorbant_accessible()
    dist, _, cycle = ch.bellman_ford(g, source)
    assert cycle is True
    assert dist["A"] == 0 and dist["E"] == 2                 # hors de portée du circuit
    assert all(dist[n] == -INF for n in "BCDF")              # jamais une valeur finie


def test_bellman_ford_circuit_inaccessible():
    g, source = circuit_absorbant_inaccessible()
    dist, _, cycle = ch.bellman_ford(g, source)
    assert cycle is False
    assert (dist["A"], dist["B"], dist["C"]) == (0, 2, 5)
    assert dist["X"] == INF                                   # non atteint, pas -inf


def test_floyd_warshall_circuit_accessible():
    g, _ = circuit_absorbant_accessible()
    dist, _, noeuds = ch.floyd_warshall(g)
    assert sorted(noeuds) == ["B", "C", "D"]
    assert dist["A"]["B"] == -INF and dist["A"]["F"] == -INF
    assert dist["A"]["E"] == 2


def test_floyd_warshall_circuit_inaccessible_depuis_a():
    g, _ = circuit_absorbant_inaccessible()
    dist, _, noeuds = ch.floyd_warshall(g)
    assert sorted(noeuds) == ["X", "Y", "Z"]                  # le circuit existe bien
    assert dist["A"]["C"] == 5 and dist["A"]["X"] == INF      # mais n'affecte pas A
    assert dist["X"]["Y"] == -INF


def test_reconstruire_chemin_ne_boucle_pas():
    g, source = circuit_absorbant_accessible()
    _, pred, _ = ch.bellman_ford(g, source)
    assert ch.reconstruire_chemin(pred, source, "C") is None   # et surtout : il se termine
    assert ch.reconstruire_chemin(pred, source, "E") == ["A", "E"]


def test_poids_negatif_sans_circuit():
    g = Graphe()
    g.ajouter_arete("A", "B", 4)
    g.ajouter_arete("A", "C", 2)
    g.ajouter_arete("C", "B", -3)
    dist, pred, cycle = ch.bellman_ford(g, "A")
    assert cycle is False and dist["B"] == -1
    assert ch.reconstruire_chemin(pred, "A", "B") == ["A", "C", "B"]


def test_dijkstra_bellman_floyd_identiques_sur_le_petit_jeu():
    _, routes, _, _ = charger_jeu("data/petit")
    d_dij, _ = ch.dijkstra(routes, "S1")
    d_bf, _, cycle = ch.bellman_ford(routes, "S1")
    d_fw, _, noeuds = ch.floyd_warshall(routes)
    assert cycle is False and noeuds == []
    for n in routes.noeuds():
        assert d_dij[n] == d_bf[n] == d_fw["S1"][n]