"""
Structure de données pour représenter un graphe.
Gère les listes d'adjacence pour des graphes orientés ou non orientés.
"""

from dataclasses import dataclass
import copy as copie_module
from typing import Dict, List, Tuple


@dataclass
class Arete:
    """Représente un arc ou une arête avec son poids et son statut."""
    poids: float
    statut: str = "ouvert"


class Graphe:
    """Graphe basé sur un dictionnaire d'adjacences."""

    def __init__(self, oriente: bool = True):
        """Initialise un graphe orienté (par défaut) ou non orienté."""
        self.oriente = oriente
        self.adjacences: Dict[str, Dict[str, Arete]] = {}

    def ajouter_noeud(self, u: str) -> None:
        """Ajoute un sommet au graphe s'il n'existe pas déjà."""
        self.adjacences.setdefault(u, {})

    def ajouter_arete(self, u: str, v: str, poids: float, statut: str = "ouvert") -> None:
        """Ajoute une arête entre les sommets u et v avec un poids et un statut."""
        self.ajouter_noeud(u)
        self.ajouter_noeud(v)
        self.adjacences[u][v] = Arete(poids, statut)
        
        if not self.oriente:
            self.adjacences[v][u] = Arete(poids, statut)

    def supprimer_arete(self, u: str, v: str) -> None:
        """Supprime l'arête entre u et v, si elle existe."""
        self.adjacences.get(u, {}).pop(v, None)
        
        if not self.oriente:
            self.adjacences.get(v, {}).pop(u, None)

    def noeuds(self) -> List[str]:
        """Retourne la liste de tous les sommets du graphe."""
        return list(self.adjacences.keys())

    def aretes(self) -> List[Tuple[str, str, float, str]]:
        """
        Retourne une liste d'arcs sous la forme (origine, destination, poids, statut).
        Pour un graphe non orienté, chaque arête n'apparaît qu'une seule fois pour éviter les doublons.
        """
        resultat = []
        for u, voisins in self.adjacences.items():
            for v, arete in voisins.items():
                if self.oriente or str(u) <= str(v):
                    resultat.append((u, v, arete.poids, arete.statut))
        return resultat

    def copier(self) -> 'Graphe':
        """
        Retourne une copie indépendante du graphe en profondeur.
        Utile pour appliquer des scénarios de simulation sans altérer le réseau de base.
        """
        return copie_module.deepcopy(self)
