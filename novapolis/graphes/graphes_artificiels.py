"""Graphes artificiels (avec des poids négatifs) pour tester la détection de circuits absorbants.
Un poids négatif n'est pas une durée réaliste : ces jeux ne servent qu'aux tests."""
from typing import Tuple
from .graphe import Graphe


def circuit_absorbant_accessible() -> Tuple[Graphe, str]:
    """Circuit B -> C -> D -> B de poids 1 - 3 + 1 = -1, accessible depuis A.
    E reste à distance finie (2) ; B, C, D et F valent -inf."""
    g = Graphe(oriente=True)
    for u, v, p in [("A", "B", 4), ("B", "C", 1), ("C", "D", -3), ("D", "B", 1),
                    ("A", "E", 2), ("D", "F", 5)]:
        g.ajouter_arete(u, v, p)
    return g, "A"


def circuit_absorbant_inaccessible() -> Tuple[Graphe, str]:
    """Circuit X -> Y -> Z -> X de poids 1 - 3 + 1 = -1, NON accessible depuis A.
    Depuis A : A = 0, B = 2, C = 5 (distances finies)."""
    g = Graphe(oriente=True)
    for u, v, p in [("A", "B", 2), ("B", "C", 3),
                    ("X", "Y", 1), ("Y", "Z", -3), ("Z", "X", 1)]:
        g.ajouter_arete(u, v, p)
    return g, "A"