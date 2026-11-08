"""Module pour la détection interactive des circuits absorbants."""
import questionary
from rich.table import Table
from typing import Any
from novapolis.cli.interface import console, afficher_section
from novapolis.cli.formatter import formater_distance
from novapolis.graphes import chemins as ch
from novapolis.graphes import graphes_artificiels as artificiels

def executer_circuits_absorbants(routes: Any) -> None:
    """Détecte les circuits absorbants sur le réseau ou un réseau de test."""
    afficher_section("Détection de Circuits Absorbants")

    jeu = questionary.select(
        "Sur quel graphe travailler ?",
        choices=[
            "Réseau routier chargé (temps positifs)",
            "Test 1 : circuit absorbant ACCESSIBLE depuis A",
            "Test 2 : circuit absorbant NON accessible depuis A",
        ]
    ).ask()

    source_test = None
    if jeu.startswith("Test 1"):
        graphe, source_test = artificiels.circuit_absorbant_accessible()
    elif jeu.startswith("Test 2"):
        graphe, source_test = artificiels.circuit_absorbant_inaccessible()
    else:
        graphe = routes
        
    if source_test:
        console.print("Graphe artificiel à poids négatifs (jeu de test, pas une durée réaliste).", style="yellow")

    algo = questionary.select(
        "Choisissez l'algorithme d'analyse :",
        choices=["Bellman-Ford (Depuis une source spécifique)", "Floyd-Warshall (Analyse globale)"]
    ).ask()

    noeuds = graphe.noeuds()
    if not noeuds:
        console.print("Err: Aucun noeud n'est disponible dans le graphe.", style="red")
        return

    if algo.startswith("Bellman-Ford"):
        if source_test:
            source = source_test
        elif len(noeuds) < 10:
            source = questionary.select("Sélectionnez le noeud source pour l'analyse :", choices=noeuds).ask()
        else:
            source = questionary.autocomplete("Saisissez le noeud source pour l'analyse :", choices=noeuds).ask()

        if source not in noeuds:
            console.print(f"Err: Le noeud '{source}' n'existe pas dans le graphe.", style="red")
            return

        distances, _, cycle_present = ch.bellman_ford(graphe, source)
        if cycle_present:
            console.print(f"Circuit absorbant [red]DÉTECTÉ[/red], accessible depuis {source}.")
        else:
            console.print(f"Opération réussie. Aucun circuit absorbant accessible depuis {source}.", style="green")

        if len(noeuds) <= 15:
            table = Table(show_header=True, header_style="bold cyan", title=f"Distances depuis {source}")
            table.add_column("Site")
            table.add_column("Distance", justify="right")
            for n in noeuds:
                table.add_row(n, formater_distance(distances[n]))
            console.print(table)
        else:
            affectes = [n for n in noeuds if distances[n] == float("-inf")]
            console.print(f"{len(affectes)} site(s) sans distance finie (-∞).")
    else:
        distances, _, noeuds_cycles = ch.floyd_warshall(graphe)
        if noeuds_cycles:
            console.print(f"Circuits absorbants [red]DÉTECTÉS[/red] dans le graphe ({len(noeuds_cycles)} site(s) concerné(s)).")
            console.print(f"Sites sur un circuit : [yellow]{', '.join(noeuds_cycles[:10])}{'...' if len(noeuds_cycles) > 10 else ''}[/yellow]")
            if source_test:
                table = Table(show_header=True, header_style="bold cyan", title=f"Distances depuis {source_test}")
                table.add_column("Site")
                table.add_column("Distance", justify="right")
                for n in noeuds:
                    table.add_row(n, formater_distance(distances[source_test][n]))
                console.print(table)
                if all(distances[source_test][n] != float("-inf") for n in noeuds):
                    console.print(f"Le circuit existe mais n'est pas accessible depuis {source_test}.", style="yellow")
        else:
            console.print("Opération réussie. Aucun circuit absorbant n'existe dans le graphe.", style="green")
