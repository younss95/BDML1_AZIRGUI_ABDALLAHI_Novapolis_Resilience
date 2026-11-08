"""Module pour la validation interactive des données."""
from rich.panel import Panel
from rich.table import Table
from typing import Dict, Any, List
from novapolis.cli.interface import console

def executer_validation(sites: Dict, routes: Any, fibre: Any, demandes: List) -> None:
    """Affiche les statistiques globales du réseau."""
    table = Table(title="Résumé du Réseau", show_header=False, box=None)
    table.add_row("Sites recensés :", f"[cyan]{len(sites)}[/cyan]")
    table.add_row("Arcs routiers :", f"[cyan]{len(routes.aretes())}[/cyan]")
    table.add_row("Tronçons fibre :", f"[cyan]{len(fibre.aretes())}[/cyan]")
    table.add_row("Demandes en attente :", f"[cyan]{len(demandes)}[/cyan]")
    
    console.print(Panel(table, border_style="green"))
