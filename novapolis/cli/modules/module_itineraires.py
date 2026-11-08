"""Module de gestion interactive des itinéraires de secours et simulation."""
import time
import questionary
from rich.table import Table
from typing import Dict, Any, List
from novapolis.cli.interface import console, afficher_section
from novapolis.graphes import chemins as ch
from novapolis.cli.config import CONFIGS_SECOURS

def executer_itineraires(sites: Dict, routes: Any, demandes: List) -> None:
    """Calcule et affiche les itinéraires de secours avec perturbations interactives."""
    afficher_section("Calcul des Itinéraires de Secours")
    
    perturbations = questionary.text(
        "Entrez les sites (ex: S1 S2) ou arcs (ex: S1-S2) à fermer (laissez vide pour aucune perturbation) :"
    ).ask().strip()
    
    routes_modifiees = routes.copier()
    if perturbations:
        for element in perturbations.split():
            if "-" in element:
                parties = element.split("-")
                if len(parties) == 2:
                    u, v = parties
                    if u in routes_modifiees.adjacences and v in routes_modifiees.adjacences[u]:
                        routes_modifiees.adjacences[u][v].statut = "ferme"
            else:
                s = element
                if s in routes_modifiees.adjacences:
                    for v in routes_modifiees.adjacences[s]:
                        routes_modifiees.adjacences[s][v].statut = "ferme"
                for u in routes_modifiees.adjacences:
                    if s in routes_modifiees.adjacences[u]:
                        routes_modifiees.adjacences[u][s].statut = "ferme"

    algo = questionary.select(
        "Choisissez l'algorithme :",
        choices=["Dijkstra", "Bellman-Ford", "Comparaison des deux"]
    ).ask()
    
    sites_secours_par_type = {}
    for config in CONFIGS_SECOURS:
        sites_secours = [s for s, r in sites.items() if r["type"] == config["type_site"]]
        if not sites_secours:
            console.print(f"Err: Aucun site de type '{config['type_site']}' disponible pour les urgences '{config['label']}'.", style="yellow")
        sites_secours_par_type[config["type_demande"]] = sites_secours
        
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Demande")
    table.add_column("Type de Secours")
    table.add_column("Origine")
    table.add_column("Dest.")
    
    if perturbations:
        table.add_column("Avant perturbation")
        table.add_column("Après perturbation")
    else:
        table.add_column("Temps (min)")
        
    if algo == "Comparaison des deux":
        table.add_column("Dijkstra (ms)")
        table.add_column("Bellman-Ford (ms)")
        table.add_column("Identique ?")
    else:
        if not perturbations:
            table.add_column("Chemin (Résumé)", overflow="fold")
            
    def calculer_trajet(graphe, sources, destination, nom_algo):
        meilleur_temps = float('inf')
        meilleure_source = None
        meilleur_chemin = None
        
        t_debut = time.perf_counter()
        for source in sources:
            if nom_algo.startswith("Dijkstra"):
                distances, predecesseurs = ch.dijkstra(graphe, source)
            else:
                distances, predecesseurs, _ = ch.bellman_ford(graphe, source)
                
            if distances[destination] < meilleur_temps:
                meilleur_temps = distances[destination]
                meilleure_source = source
                meilleur_chemin = ch.reconstruire_chemin(predecesseurs, source, destination)
        t_fin = time.perf_counter()
        return meilleur_temps, meilleure_source, meilleur_chemin, (t_fin - t_debut) * 1000

    def formater_resultat(temps, chemin):
        return f"{temps:.2f}" if chemin else "[red]INACCESSIBLE[/red]"

    with console.status("[cyan]Calcul des chemins en cours...[/cyan]"):
        for d in demandes:
            destination = d["origine"]
            type_d = d["type"]
            sources_secours = sites_secours_par_type.get(type_d)
            
            if not sources_secours:
                console.print(f"Demande {d['id']} ignorée (sources indisponibles ou type inconnu : {type_d}).", style="yellow")
                continue
                
            if algo == "Comparaison des deux":
                temps_av_dij, src_av_dij, chem_av_dij, exec_av_dij = calculer_trajet(routes, sources_secours, destination, "Dijkstra")
                temps_av_bel, src_av_bel, chem_av_bel, exec_av_bel = calculer_trajet(routes, sources_secours, destination, "Bellman-Ford")
                
                total_exec_dij = exec_av_dij
                total_exec_bel = exec_av_bel
                origine_str = str(src_av_dij) if src_av_dij else "-"
                
                if perturbations:
                    temps_ap_dij, src_ap_dij, chem_ap_dij, exec_ap_dij = calculer_trajet(routes_modifiees, sources_secours, destination, "Dijkstra")
                    temps_ap_bel, src_ap_bel, chem_ap_bel, exec_ap_bel = calculer_trajet(routes_modifiees, sources_secours, destination, "Bellman-Ford")
                    
                    total_exec_dij += exec_ap_dij
                    total_exec_bel += exec_ap_bel
                    
                    texte_avant = formater_resultat(temps_av_dij, chem_av_dij)
                    texte_apres = formater_resultat(temps_ap_dij, chem_ap_dij)
                    identique = "Oui" if (temps_av_dij == temps_av_bel and temps_ap_dij == temps_ap_bel) else "Non"
                    
                    table.add_row(d["id"], type_d, origine_str, destination, texte_avant, texte_apres, f"{total_exec_dij:.2f}", f"{total_exec_bel:.2f}", identique)
                else:
                    texte_avant = formater_resultat(temps_av_dij, chem_av_dij)
                    identique = "Oui" if temps_av_dij == temps_av_bel else "Non"
                    table.add_row(d["id"], type_d, origine_str, destination, texte_avant, f"{total_exec_dij:.2f}", f"{total_exec_bel:.2f}", identique)
            else:
                temps_av, src_av, chem_av, _ = calculer_trajet(routes, sources_secours, destination, algo)
                origine_str = str(src_av) if src_av else "-"
                
                if perturbations:
                    temps_ap, src_ap, chem_ap, _ = calculer_trajet(routes_modifiees, sources_secours, destination, algo)
                    texte_avant = formater_resultat(temps_av, chem_av)
                    texte_apres = formater_resultat(temps_ap, chem_ap)
                    table.add_row(d["id"], type_d, origine_str, destination, texte_avant, texte_apres)
                else:
                    texte_avant = formater_resultat(temps_av, chem_av)
                    texte_chemin = " -> ".join(chem_av) if chem_av else "-"
                    table.add_row(d["id"], type_d, origine_str, destination, texte_avant, texte_chemin)
                    
    console.print(table)
