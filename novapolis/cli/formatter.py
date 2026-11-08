"""Module de formatage des données pour l'affichage CLI."""

LIBELLES_RESUME = [
    ("demandes_inaccessibles", "Demandes inaccessibles"),
    ("devenues_inaccessibles", "  dont devenues inaccessibles"),
    ("retard_moyen", "Retard moyen"),
    ("retard_max", "Retard maximal"),
    ("sites_sensibles_pct", "Sites sensibles accessibles"),
    ("composantes_fibre", "Composantes de fibre"),
    ("cout_arbre", "Coût de l'arbre de fibre"),
    ("cout_reparation", "Coût de réparation"),
    ("surcout_arbre", "Surcoût de l'arbre"),
    ("pannes_irreparables", "Pannes sans raccordement"),
]

def formater_valeur(cle, valeur):
    """Applique un formatage spécifique en fonction de la métrique ciblée."""
    if valeur is None:
        return "-"
    if cle in ("retard_moyen", "retard_max"):
        return f"{valeur:.1f} min"
    if cle == "sites_sensibles_pct":
        return f"{valeur:.0f} %"
    if cle in ("cout_arbre", "cout_reparation", "surcout_arbre"):
        return f"{valeur:+.1f}" if cle == "surcout_arbre" else f"{valeur:.1f}"
    return str(valeur)

def formater_distance(d: float) -> str:
    """Affiche une distance mathématique au format lisible."""
    if d == float("-inf"):
        return "[red]-∞ (non définie)[/red]"
    if d == float("inf"):
        return "inaccessible"
    return f"{d:g}"
