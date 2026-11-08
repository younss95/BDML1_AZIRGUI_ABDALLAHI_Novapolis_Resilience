import pytest
from novapolis.graphes.arbre import kruskal, prim, simuler_panne_et_reparer
from novapolis.graphes.graphe import Graphe

@pytest.fixture
def fiber_graph():
    graph = Graphe(oriente=False)
    graph.ajouter_arete("A", "B", 4.0)
    graph.ajouter_arete("A", "C", 2.0)
    graph.ajouter_arete("B", "C", 1.0)
    graph.ajouter_arete("B", "D", 5.0)
    graph.ajouter_arete("C", "D", 8.0)
    graph.ajouter_arete("C", "E", 10.0)
    graph.ajouter_arete("D", "E", 2.0)
    graph.ajouter_arete("D", "F", 6.0)
    graph.ajouter_arete("E", "F", 3.0)
    return graph

def test_kruskal_algorithm_cost(fiber_graph):
    mst_edges, total_cost, components = kruskal(fiber_graph)
    assert total_cost == 13.0
    assert components == 1
    assert len(mst_edges) == 5

def test_prim_algorithm_cost(fiber_graph):
    mst_edges, total_cost, components = prim(fiber_graph)
    assert total_cost == 13.0
    assert components == 1
    assert len(mst_edges) == 5

def test_simuler_panne_et_reparer(fiber_graph):
    mst_edges, _, _ = kruskal(fiber_graph)
    
    new_edge, repair_cost = simuler_panne_et_reparer(fiber_graph, mst_edges, ("D", "E"))
    
    assert new_edge is not None
    assert repair_cost == 6.0
    assert (new_edge[0] == "D" and new_edge[1] == "F") or (new_edge[0] == "F" and new_edge[1] == "D")
