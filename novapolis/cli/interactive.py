"""
Interface en ligne de commande interactive pour analyser le réseau de Novapolis.
Utilise questionary pour les menus interactifs et rich pour le formatage.
"""

import os
import sys
from typing import Optional, Tuple, Dict, Any, List
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from novapolis.donnees.exceptions import ErreurValidation
from novapolis.donnees.csv_reader import charger_jeu
from novapolis.graphes import parcours as tr

console = Console()


def effacer_ecran() -> None:
    """Efface l'écran du terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def afficher_en_tete() -> None:
    """Affiche le bandeau de bienvenue."""
    titre = Text("Novapolis", style="bold cyan")
    titre.append(" - Outil d'Analyse du Réseau Urbain", style="white")
    console.print(Panel(titre, expand=False, border_style="cyan"))
    console.print("\n")


def selectionner_dossier_donnees(chemin_initial: str = ".") -> str:
    """Laisse l'utilisateur naviguer pour choisir un dossier contenant des CSV."""
    chemin_actuel = os.path.abspath(chemin_initial)
    
    while True:
        effacer_ecran()
        afficher_en_tete()
        console.print(f"Dossier actuel : [bold yellow]{chemin_actuel}[/bold yellow]\n")
        
        elements = [".. (Dossier parent)"]
        try:
            contenu = os.listdir(chemin_actuel)
            dossiers = [d for d in contenu if os.path.isdir(os.path.join(chemin_actuel, d)) and not d.startswith('.')]
            elements.extend(sorted(dossiers))
        except PermissionError:
            console.print("Err: Permission refusée pour ce dossier.", style="red")
            
        elements.append("✓ VALIDER CE DOSSIER")
        elements.append("✗ QUITTER")
        
        choix = questionary.select(
            "Naviguez et sélectionnez le dossier contenant vos données CSV :",
            choices=elements,
            use_indicator=True
        ).ask()
        
        if choix == "✗ QUITTER":
            sys.exit(0)
        elif choix == "✓ VALIDER CE DOSSIER":
            fichiers_requis = ["sites.csv", "routes.csv", "fibre.csv", "demandes.csv"]
            fichiers_presents = os.listdir(chemin_actuel)
            manquants = [f for f in fichiers_requis if f not in fichiers_presents]
            
            if manquants:
                console.print(f"\nErr: Fichiers manquants dans ce dossier : {', '.join(manquants)}", style="bold red")
                questionary.press_any_key_to_continue("Appuyez sur une touche pour réessayer...").ask()
            else:
                return chemin_actuel
        elif choix == ".. (Dossier parent)":
            chemin_actuel = os.path.dirname(chemin_actuel)
        else:
            chemin_actuel = os.path.join(chemin_actuel, choix)


def afficher_menu_principal() -> str:
    """Affiche le menu principal et retourne le choix de l'utilisateur."""
    effacer_ecran()
    afficher_en_tete()
    return questionary.select(
        "Que souhaitez-vous faire ?",
        choices=[
            questionary.Choice("Valider l'intégrité des données", "validate"),
            questionary.Choice("Diagnostic d'accessibilité des casernes", "accessibilite"),
            questionary.Choice("Quitter l'application", "quitter")
        ],
        style=questionary.Style([('selected', 'fg:cyan bold')])
    ).ask()


def executer_validation(sites: Dict, routes: Any, fibre: Any, demandes: List) -> None:
    """Affiche les statistiques globales du réseau."""
    table = Table(title="Résumé du Réseau", show_header=False, box=None)
    table.add_row("Sites recensés :", f"[cyan]{len(sites)}[/cyan]")
    table.add_row("Arcs routiers :", f"[cyan]{len(routes.aretes())}[/cyan]")
    table.add_row("Tronçons fibre :", f"[cyan]{len(fibre.aretes())}[/cyan]")
    table.add_row("Demandes en attente :", f"[cyan]{len(demandes)}[/cyan]")
    
    console.print(Panel(table, border_style="green"))


def executer_diagnostic(sites: Dict, routes: Any, fibre: Any, demandes: List) -> None:
    """Exécute l'analyse d'accessibilité orientée."""
    casernes = [s for s, r in sites.items() if r["type"] == "caserne"]
    console.print(f"Casernes identifiées : [bold cyan]{', '.join(casernes)}[/bold cyan]\n")

    distances, _ = tr.parcours_largeur(routes, casernes)
    sites_inaccessibles = tr.sites_inaccessibles(routes, casernes)
    
    # Accessibilité globale
    console.print("********** Accessibilité Routière **********", style="bold magenta")
    console.print(f"Sites couverts : [green]{len(distances)}/{len(sites)}[/green]")
    if sites_inaccessibles:
        console.print(f"Sites inaccessibles : [red]{', '.join(sites_inaccessibles)}[/red]")
    else:
        console.print("Sites inaccessibles : [green]Aucun[/green]")
        
    # Traitement des demandes
    console.print("\n********** Traitement des Demandes **********", style="bold magenta")
    table_demandes = Table(show_header=True, header_style="bold cyan")
    table_demandes.add_column("ID")
    table_demandes.add_column("Type")
    table_demandes.add_column("Priorité")
    table_demandes.add_column("Destination")
    table_demandes.add_column("Distance (arcs)")
    
    for d in demandes:
        dist_arcs = distances.get(d["origine"])
        texte_dist = f"{dist_arcs}" if dist_arcs is not None else "[red]INACCESSIBLE[/red]"
        table_demandes.add_row(d["id"], d["type"], d["priorite"], d["origine"], texte_dist)
    console.print(table_demandes)

    # Analyse structurelle
    console.print("\n********** Analyse Structurelle **********", style="bold magenta")
    cycle = tr.detecter_cycle_oriente(routes)
    if cycle:
        console.print(f"Cycle routier détecté : [yellow]{' -> '.join(cycle)}[/yellow]")
    else:
        console.print("Cycle routier détecté : [green]Aucun[/green]")

    scc = tr.composantes_fortement_connexes(routes)
    console.print(f"Composantes fortement connexes (routes) : [cyan]{len(scc)}[/cyan]")
    
    isoles = tr.sites_isoles(routes)
    if isoles:
        console.print(f"Sites isolés : [red]{', '.join(isoles)}[/red]")
    
    comps_fibre = tr.composantes_connexes(fibre)
    console.print(f"Composantes connexes (fibre) : [cyan]{len(comps_fibre)}[/cyan]")


def demarrer_cli() -> None:
    """Point d'entrée principal de l'application interactive."""
    try:
        effacer_ecran()
        afficher_en_tete()
        
        console.print("Bienvenue dans l'outil d'analyse de Novapolis.")
        questionary.press_any_key_to_continue("Appuyez sur une touche pour démarrer la sélection des données...").ask()
        
        dossier_donnees = selectionner_dossier_donnees()
        
        with console.status("[cyan]Chargement et validation des données en cours...[/cyan]"):
            try:
                sites, routes, reseau_fibre, demandes = charger_jeu(dossier_donnees)
            except ErreurValidation as erreur_validation:
                console.print(f"\nErr: Validation échouée.\n{erreur_validation}", style="bold red")
                sys.exit(1)
        
        console.print("\nDonnées chargées avec succès.", style="green")
        questionary.press_any_key_to_continue("Appuyez sur une touche pour accéder au menu...").ask()
        
        while True:
            choix = afficher_menu_principal()
            
            effacer_ecran()
            afficher_en_tete()
            
            if choix == "validate":
                executer_validation(sites, routes, reseau_fibre, demandes)
            elif choix == "accessibilite":
                executer_diagnostic(sites, routes, reseau_fibre, demandes)
            elif choix == "quitter":
                console.print("Fermeture de l'application. Au revoir.", style="cyan")
                sys.exit(0)
                
            console.print("\n")
            questionary.press_any_key_to_continue("Appuyez sur une touche pour retourner au menu...").ask()
            
    except KeyboardInterrupt:
        console.print("\n\nInterruption par l'utilisateur. Au revoir.", style="red")
        sys.exit(0)

if __name__ == "__main__":
    demarrer_cli()
