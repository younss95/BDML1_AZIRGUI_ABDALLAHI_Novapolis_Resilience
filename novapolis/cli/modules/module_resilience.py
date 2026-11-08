"""Module d'évaluation interactive de la résilience aux pannes réseau."""
import questionary
from rich.table import Table
from typing import Dict, Any, List
from novapolis.cli.interface import console, afficher_section
from novapolis.indicateurs import comparer_scenarios
from novapolis.cli.formatter import LIBELLES_RESUME, formater_valeur

def executer_resilience(sites: Dict, routes: Any, fibre: Any, demandes: List, scenarios: Dict) -> None:
    """Compare la situation normale et les scénarios du fichier scenarios.csv de manière interactive."""
    afficher_section("Résilience : comparaison des scénarios")
    if not scenarios:
        console.print("Aucun scenarios.csv dans ce dossier : seule la situation normale est évaluée.", style="yellow")
    with console.status("[cyan]Calcul...[/cyan]"):
        resultats = comparer_scenarios(sites, routes, fibre, demandes, scenarios)

    table = Table(show_header=True, header_style="bold cyan", title="Indicateurs par scénario")
    table.add_column("Indicateur")
    for nom in resultats:
        table.add_column(nom, justify="right")
    for cle, libelle in LIBELLES_RESUME:
        table.add_row(libelle, *[formater_valeur(cle, r["resume"][cle]) for r in resultats.values()])
    console.print(table)

    choix = questionary.select("Voir le détail des trajets pour quel scénario ?",
                               choices=list(resultats),
                               instruction="(flèches ↑↓ puis Entrée)").ask()
    detail = Table(show_header=True, header_style="bold cyan", title=f"Trajets : {choix}")
    for col in ("Demande", "Site", "Avant (min)", "Après (min)", "Retard", "Retard %", "Statut"):
        detail.add_column(col)
    for l in resultats[choix]["detail"]:
        detail.add_row(
            l["id"], l["origine"],
            f"{l['avant']:.1f}" if l["avant"] is not None else "-",
            f"{l['apres']:.1f}" if l["apres"] is not None else "-",
            f"{l['retard']:+.1f}" if l["retard"] is not None else "-",
            f"{l['retard_pct']:+.1f} %" if l["retard_pct"] is not None else "-",
            l["statut"] if l["statut"] == "accessible" else f"[red]{l['statut']}[/red]")
    console.print(detail)
