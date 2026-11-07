"""Application d'un scénario de perturbation sur des COPIES des graphes de base."""
from novapolis.donnees.exceptions import ErreurValidation
from .graphe import Graphe


def _changer_statut(graphe: Graphe, u: str, v: str, statut: str) -> None:
    graphe.adjacences[u][v].statut = statut
    if not graphe.oriente:                      # fibre : les deux sens sont stockés
        graphe.adjacences[v][u].statut = statut


def appliquer_scenario(routes: Graphe, fibre: Graphe, actions: list):
    """Retourne (routes_modifiees, fibre_modifiee). Les graphes d'origine ne sont jamais modifiés."""
    routes_sc, fibre_sc = routes.copier(), fibre.copier()
    for a in actions:
        graphe = routes_sc if a["type_element"] == "route" else fibre_sc
        u, v = a["u"], a["v"]
        if v not in graphe.adjacences.get(u, {}):
            raise ErreurValidation(
                f"scénario '{a['scenario']}' : {a['type_element']} {u} -> {v} inexistante")
        if a["action"] == "fermer":
            _changer_statut(graphe, u, v, "ferme")
        elif a["action"] == "ouvrir":
            _changer_statut(graphe, u, v, "ouvert")
        elif a["action"] == "interdire":
            _changer_statut(graphe, u, v, "interdit")
        elif a["action"] == "supprimer":
            graphe.supprimer_arete(u, v)
    return routes_sc, fibre_sc