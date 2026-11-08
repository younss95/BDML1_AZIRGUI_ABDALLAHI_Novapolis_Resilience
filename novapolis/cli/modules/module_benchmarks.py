"""Module pour l'exécution interactive des scénarios de benchmarks."""
import os
import questionary
from novapolis.cli.interface import console

def executer_lancement_benchmarks(chemin_actuel: str) -> None:
    """Lance et affiche la progression des benchmarks interactifs."""
    saisie_max_sommets = questionary.text("Jusqu'à combien de sommets faire les évaluations globales ?", default="1000").ask()
    saisie_max_fw = questionary.text("Maximum de sommets pour Floyd-Warshall ?", default="100").ask()

    try:
        max_sommets = int(saisie_max_sommets)
    except ValueError:
        max_sommets = 1000

    try:
        max_fw = int(saisie_max_fw)
    except ValueError:
        max_fw = 100

    from novapolis.benchmarks import executer_benchmarks
    dossier_sortie = os.path.join(chemin_actuel, "resultats")
    with console.status("[cyan]Exécution des benchmarks en cours...[/cyan]"):
        executer_benchmarks(dossier_sortie, max_sommets=max_sommets, max_fw=max_fw)
        
    console.print(f"Opération réussie. Benchmarks terminés. Graphiques sauvegardés dans [bold green]{dossier_sortie}[/bold green]")
    questionary.press_any_key_to_continue("Appuyez sur une touche pour continuer...").ask()
