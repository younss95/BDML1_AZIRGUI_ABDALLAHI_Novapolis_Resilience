"""Module interactif de génération de jeux de données synthétiques."""
import os
import questionary
from novapolis.cli.interface import console

def executer_generation(chemin_actuel: str) -> None:
    """Lance les requêtes utilisateur pour générer un dataset dans le dossier cible."""
    saisie_sites = questionary.text("Combien de sommets souhaitez-vous créer ?", default="1000").ask()
    saisie_dossier = questionary.text("Nom du dossier (sera placé dans 'data/') :", default="grand").ask()
    ask_negative_costs = questionary.confirm("Voulez-vous des coûts négatifs ?").ask()
    ask_absorbing_circuit = questionary.confirm("Voulez-vous un circuit absorbant (pour essayer Bellman-Ford) ?").ask()

    try:
        nb_sites = int(saisie_sites)
    except ValueError:
        nb_sites = 1000
        console.print("Err: Valeur invalide, utilisation de 1000 par défaut.", style="yellow")

    nom_dossier = saisie_dossier.strip() or "grand"
    chemin_sauvegarde = os.path.join("data", nom_dossier)

    from novapolis.generateur import generer_jeu_de_donnees
    with console.status("[cyan]Génération en cours...[/cyan]"):
        nb_demandes = max(10, nb_sites // 20)
        circuit_genere = generer_jeu_de_donnees(
            chemin_sauvegarde, 
            nb_sites=nb_sites, 
            nb_demandes=nb_demandes, 
            degre_moyen=5,
            poids_negatifs=ask_negative_costs,
            circuit_absorbant=ask_absorbing_circuit
        )
        
    console.print(f"Opération réussie. Jeu de données généré avec succès dans : [bold green]{chemin_sauvegarde}[/bold green]")
    if circuit_genere:
        console.print(f"\nCircuit absorbant généré : [bold red]{' -> '.join(circuit_genere)}[/bold red]")
        
    questionary.press_any_key_to_continue("Appuyez sur une touche pour recharger...").ask()
