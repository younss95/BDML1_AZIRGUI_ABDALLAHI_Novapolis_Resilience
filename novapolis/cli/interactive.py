"""Interface en ligne de commande interactive pour analyser le réseau de Novapolis.
Orchestre l'ensemble des modules interactifs."""
import os
import sys
import questionary

from novapolis.donnees.exceptions import ErreurValidation
from novapolis.donnees.csv_loader import charger_jeu, charger_scenarios
from novapolis.cli.interface import effacer_ecran, afficher_en_tete, console
from novapolis.cli.modules.module_validation import executer_validation
from novapolis.cli.modules.module_accessibilite import executer_diagnostic
from novapolis.cli.modules.module_itineraires import executer_itineraires
from novapolis.cli.modules.module_absorbants import executer_circuits_absorbants
from novapolis.cli.modules.module_arbres import executer_arbres
from novapolis.cli.modules.module_resilience import executer_resilience
from novapolis.cli.modules.module_generation import executer_generation
from novapolis.cli.modules.module_benchmarks import executer_lancement_benchmarks

def selectionner_dossier_donnees(chemin_initial: str = ".") -> str:
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
        elements.append("⚙ GÉNÉRER UN DATASET")
        elements.append("📈 LANCER LES BENCHMARKS")
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
        elif choix == "⚙ GÉNÉRER UN DATASET":
            executer_generation(chemin_actuel)
        elif choix == "📈 LANCER LES BENCHMARKS":
            executer_lancement_benchmarks(chemin_actuel)
        elif choix == ".. (Dossier parent)":
            chemin_actuel = os.path.dirname(chemin_actuel)
        else:
            chemin_actuel = os.path.join(chemin_actuel, choix)

def afficher_menu_principal() -> str:
    effacer_ecran()
    afficher_en_tete()
    return questionary.select(
        "Que souhaitez-vous faire ?",
        choices=[
            questionary.Choice("Valider l'intégrité des données", "validate"),
            questionary.Choice("Module 1 : Diagnostic d'accessibilité", "accessibilite"),
            questionary.Choice("Module 2 : Itinéraires des secours", "itineraires"),
            questionary.Choice("Module 3 : Détection de circuits absorbants", "absorbants"),
            questionary.Choice("Module 4 : Conception du réseau fibre", "arbres"),
            questionary.Choice("Module 5 : Résilience et scénarios", "resilience"),
            questionary.Choice("Exécuter les benchmarks (Module 5 Expériences)", "benchmark"),
            questionary.Choice("Quitter l'application", "quitter")
        ],
        style=questionary.Style([('selected', 'fg:cyan bold')])
    ).ask()

def demarrer_cli() -> None:
    try:
        effacer_ecran()
        afficher_en_tete()
        
        console.print("Bienvenue dans l'outil d'analyse de Novapolis.")
        questionary.press_any_key_to_continue("Appuyez sur une touche pour démarrer la sélection des données...").ask()
        
        dossier_donnees = selectionner_dossier_donnees()
        
        with console.status("[cyan]Chargement et validation des données en cours...[/cyan]"):
            try:
                sites, routes, reseau_fibre, demandes = charger_jeu(dossier_donnees)
                scenarios = charger_scenarios(dossier_donnees, sites)

            except ErreurValidation as erreur_validation:
                console.print(f"\nErr: Validation échouée.\n{erreur_validation}", style="bold red")
                sys.exit(1)
        
        console.print("\nOpération réussie. Données chargées avec succès.", style="green")
        questionary.press_any_key_to_continue("Appuyez sur une touche pour accéder au menu...").ask()
        
        while True:
            choix = afficher_menu_principal()
            
            effacer_ecran()
            afficher_en_tete()
            
            if choix == "validate":
                executer_validation(sites, routes, reseau_fibre, demandes)
            elif choix == "accessibilite":
                executer_diagnostic(sites, routes, reseau_fibre, demandes)
            elif choix == "itineraires":
                executer_itineraires(sites, routes, demandes)
            elif choix == "absorbants":
                executer_circuits_absorbants(routes)
            elif choix == "arbres":
                executer_arbres(reseau_fibre)
            elif choix == "resilience":
                executer_resilience(sites, routes, reseau_fibre, demandes, scenarios)
            elif choix == "benchmark":
                executer_lancement_benchmarks(dossier_donnees)
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
