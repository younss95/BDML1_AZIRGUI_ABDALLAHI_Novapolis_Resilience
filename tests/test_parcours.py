import pytest
from novapolis.graphes.parcours import (
    parcours_largeur, 
    detecter_cycle_oriente, 
    composantes_fortement_connexes, 
    composantes_connexes
)
from novapolis.graphes.graphe import Graphe

def test_bfs_distances_computation():
    directed_graph = Graphe(oriente=True)
    directed_graph.ajouter_arete("A", "B", 1.0)
    directed_graph.ajouter_arete("B", "C", 1.0)
    directed_graph.ajouter_arete("A", "D", 1.0)
    
    distances_map, predecessors_map = parcours_largeur(directed_graph, ["A"])
    
    assert distances_map["C"] == 2
    assert distances_map["D"] == 1
    assert distances_map["A"] == 0
    assert "X" not in distances_map

def test_directed_cycle_detection():
    directed_graph = Graphe(oriente=True)
    directed_graph.ajouter_arete("A", "B", 1.0)
    directed_graph.ajouter_arete("B", "C", 1.0)
    directed_graph.ajouter_arete("C", "A", 1.0)
    
    cycle_nodes = detecter_cycle_oriente(directed_graph)
    
    assert cycle_nodes is not None
    assert len(cycle_nodes) == 4
    assert cycle_nodes[0] == cycle_nodes[-1]

def test_strongly_connected_components():
    directed_graph = Graphe(oriente=True)
    directed_graph.ajouter_arete("A", "B", 1.0)
    directed_graph.ajouter_arete("B", "C", 1.0)
    directed_graph.ajouter_arete("C", "A", 1.0)
    directed_graph.ajouter_arete("C", "D", 1.0)
    
    scc_list = composantes_fortement_connexes(directed_graph)
    
    assert len(scc_list) == 2

def test_connected_components():
    undirected_graph = Graphe(oriente=False)
    undirected_graph.ajouter_arete("A", "B", 1.0)
    undirected_graph.ajouter_arete("C", "D", 1.0)
    
    cc_list = composantes_connexes(undirected_graph)
    
    assert len(cc_list) == 2
