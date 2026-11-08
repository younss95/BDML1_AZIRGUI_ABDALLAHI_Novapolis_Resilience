"""Module pour l'exécution du diagnostic d'accessibilité interactif."""
from typing import Dict, Any, List
from rich.table import Table
from novapolis.cli.interface import console, afficher_section
from novapolis.graphes import parcours as tr
from novapolis.cli.config import CONFIGS_SECOURS

def executer_diagnostic(sites: Dict, routes: Any, fibre: Any, demandes: List) -> None:
    """Exécute l'analyse d'accessibilité orientée."""
    afficher_section("Accessibilité Routière")
    
    distances_par_type = {}
    predecesseurs_par_type = {}
    
    for config in CONFIGS_SECOURS:
        sites_secours = [s for s, r in sites.items() if r["type"] == config["type_site"]]
        console.print(f"Sites {config['label']} identifiés : [bold cyan]{', '.join(sites_secours) if sites_secours else 'Aucun'}[/bold cyan]")
        
        if sites_secours:
            distances, predecesseurs = tr.parcours_largeur(routes, sites_secours)
            inaccessibles = tr.sites_inaccessibles(routes, sites_secours)
            distances_par_type[config["type_demande"]] = distances
            predecesseurs_par_type[config["type_demande"]] = predecesseurs
            
            console.print(f"Sites couverts ({config['label']}) : [green]{len(distances)}/{len(sites)}[/green]")
            if inaccessibles:
                console.print(f"Sites inaccessibles ({config['label']}) : [red]{', '.join(inaccessibles)}[/red]\n")
            else:
                console.print(f"Sites inaccessibles ({config['label']}) : [green]Aucun[/green]\n")
        else:
            distances_par_type[config["type_demande"]] = {}
            predecesseurs_par_type[config["type_demande"]] = {}
            console.print(f"Sites couverts ({config['label']}) : [red]0/{len(sites)}[/red]")
            console.print(f"Sites inaccessibles ({config['label']}) : [red]Tous[/red]\n")
        
    afficher_section("Traitement des Demandes")
    table_demandes = Table(show_header=True, header_style="bold cyan")
    table_demandes.add_column("ID")
    table_demandes.add_column("Type")
    table_demandes.add_column("Priorité")
    table_demandes.add_column("Origine")
    table_demandes.add_column("Destination")
    table_demandes.add_column("Distance (arcs)")
    table_demandes.add_column("Chemin (Résumé)", overflow="fold")
    
    for d in demandes:
        type_d = d["type"]
        distances = distances_par_type.get(type_d, {})
        predecesseurs = predecesseurs_par_type.get(type_d, {})
        
        destination = d["origine"]
        dist_arcs = distances.get(destination)
        
        if dist_arcs is not None:
            texte_dist = f"{dist_arcs}"
            chemin = []
            courant = destination
            while courant is not None:
                chemin.append(courant)
                courant = predecesseurs.get(courant)
            chemin = chemin[::-1]
            texte_chemin = " -> ".join(chemin)
        else:
            texte_dist = "[red]INACCESSIBLE[/red]"
            texte_chemin = "-"
            
        table_demandes.add_row(d["id"], type_d, str(d["priorite"]), chemin[0] if chemin else "N/A", destination, texte_dist, texte_chemin)
        
    console.print(table_demandes)

    afficher_section("Analyse Structurelle")
    cycle = tr.detecter_cycle_oriente(routes)
    if cycle:
        console.print(f"Cycle routier détecté : [yellow]{' -> '.join(cycle)}[/yellow]")
    else:
        console.print("Cycle routier détecté : [green]Aucun[/green]")

    composantes_fortes = tr.composantes_fortement_connexes(routes)
    console.print(f"Composantes fortement connexes (routes) : [cyan]{len(composantes_fortes)}[/cyan]")

    isoles = tr.sites_isoles(routes)
    if isoles:
        console.print(f"Sites isolés : [red]{', '.join(isoles)}[/red]")

    composantes_fibre = tr.composantes_connexes(fibre)
    console.print(f"Composantes connexes (fibre) : [cyan]{len(composantes_fibre)}[/cyan]")
    for idx, component in enumerate(composantes_fibre, 1):
        console.print(f"  Composante {idx} : [yellow]{', '.join(component)}[/yellow]")
