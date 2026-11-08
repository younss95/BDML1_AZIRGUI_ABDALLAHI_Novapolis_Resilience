"""
Interface en ligne de commande interactive pour analyser le réseau de Novapolis.
Utilise questionary pour les menus interactifs et rich pour le formatage.
"""

import os
import subprocess
import sys
import time
from typing import Optional, Tuple, Dict, Any, List
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from novapolis.donnees.exceptions import ErreurValidation
from novapolis.donnees.csv_reader import charger_jeu, charger_scenarios
from novapolis.graphes import parcours as tr
from novapolis.graphes import chemins as ch
from novapolis.graphes import graphes_artificiels as artificiels
from novapolis.graphes.arbre import kruskal, prim, simuler_panne_et_reparer
from novapolis.graphes.graphe import Graphe
from novapolis.indicateurs import comparer_scenarios, formater_valeur, LIBELLES_RESUME


console = Console()

CONFIGS_SECOURS = [
    {"type_demande": "incendie", "type_site": "caserne", "label": "Incendie"},
    {"type_demande": "medical", "type_site": "hopital", "label": "Médical"}
]


def effacer_ecran() -> None:
    """Efface l'écran du terminal."""
    subprocess.run("cls" if os.name == "nt" else "clear", shell=True)


def afficher_en_tete() -> None:
    """Affiche le bandeau de bienvenue."""
    titre = Text("Novapolis", style="bold cyan")
    titre.append(" - Outil d'Analyse du Réseau Urbain", style="white")
    console.print(Panel(titre, expand=False, border_style="cyan"))
    console.print("\n")
    
def afficher_section(titre: str) -> None:
    """Affiche un titre de section."""
    console.print(Panel(titre, style="bold magenta italic", expand=False))


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
            saisie_sites = questionary.text("Combien de sommets souhaitez-vous créer ?", default="1000").ask()
            saisie_dossier = questionary.text("Nom du dossier (sera placé dans 'data/') :", default="grand").ask()
            ask_negative_costs = questionary.confirm("Voulez-vous des coûts négatifs ?").ask()
            ask_absorbing_circuit = questionary.confirm("Voulez-vous un circuit absorbant (pour essayer Bellman-Ford) ?").ask()

            try:
                nb_sites = int(saisie_sites)
            except ValueError:
                nb_sites = 1000
                console.print("Valeur invalide, utilisation de 1000 par défaut.", style="yellow")

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
                
            console.print(f"Jeu de données généré avec succès dans : [bold green]{chemin_sauvegarde}[/bold green]")
            if circuit_genere:
                console.print(f"\nCircuit absorbant généré : [bold red]{' -> '.join(circuit_genere)}[/bold red]")
                
            questionary.press_any_key_to_continue("Appuyez sur une touche pour recharger...").ask()

        elif choix == "📈 LANCER LES BENCHMARKS":
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
                
            console.print(f"Benchmarks terminés. Graphiques sauvegardés dans [bold green]{dossier_sortie}[/bold green]")
            questionary.press_any_key_to_continue("Appuyez sur une touche pour continuer...").ask()
            
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
            origine = chemin[0] if chemin else "N/A"
            texte_chemin = " -> ".join(chemin)
        else:
            texte_dist = "[red]INACCESSIBLE[/red]"
            origine = "N/A"
            texte_chemin = "-"
            
        table_demandes.add_row(d["id"], type_d, str(d["priorite"]), origine, destination, texte_dist, texte_chemin)
        
    console.print(table_demandes)

    # Analyse structurelle
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


def executer_itineraires(sites: Dict, routes: Any, demandes: List) -> None:
    """Calcule et affiche les itinéraires de secours pour chaque demande avec simulations dynamiques."""
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

    def formater_resultat(temps, source, chemin):
        if chemin:
            return f"{temps:.2f}"
        return "[red]INACCESSIBLE[/red]"

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
                    
                    texte_avant = formater_resultat(temps_av_dij, src_av_dij, chem_av_dij)
                    texte_apres = formater_resultat(temps_ap_dij, src_ap_dij, chem_ap_dij)
                    identique = "Oui" if (temps_av_dij == temps_av_bel and temps_ap_dij == temps_ap_bel) else "Non"
                    
                    table.add_row(d["id"], origine_str, destination, texte_avant, texte_apres, f"{total_exec_dij:.2f}", f"{total_exec_bel:.2f}", identique)
                else:
                    texte_avant = formater_resultat(temps_av_dij, src_av_dij, chem_av_dij)
                    identique = "Oui" if temps_av_dij == temps_av_bel else "Non"
                    
                    table.add_row(d["id"], origine_str, destination, texte_avant, f"{total_exec_dij:.2f}", f"{total_exec_bel:.2f}", identique)
            else:
                temps_av, src_av, chem_av, _ = calculer_trajet(routes, sources_secours, destination, algo)
                origine_str = str(src_av) if src_av else "-"
                
                if perturbations:
                    temps_ap, src_ap, chem_ap, _ = calculer_trajet(routes_modifiees, sources_secours, destination, algo)
                    texte_avant = formater_resultat(temps_av, src_av, chem_av)
                    texte_apres = formater_resultat(temps_ap, src_ap, chem_ap)
                    table.add_row(d["id"], origine_str, destination, texte_avant, texte_apres)
                else:
                    texte_avant = formater_resultat(temps_av, src_av, chem_av)
                    texte_chemin = " -> ".join(chem_av) if chem_av else "-"
                    table.add_row(d["id"], type_d, origine_str, destination, texte_avant, texte_chemin)
                    
    console.print(table)


def formater_distance(d: float) -> str:
    """-inf et inf ne sont pas des durées : on les affiche comme des états."""
    if d == float("-inf"):
        return "[red]-∞ (non définie)[/red]"
    if d == float("inf"):
        return "inaccessible"
    return f"{d:g}"


def executer_circuits_absorbants(routes: Any) -> None:
    """Détecte les circuits absorbants, sur le réseau chargé ou sur un graphe de test artificiel."""
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
            console.print(f"Aucun circuit absorbant accessible depuis {source}.", style="green")

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
            console.print("Aucun circuit absorbant n'existe dans le graphe.", style="green")


def executer_arbres(fibre: Any) -> None:
    """Calcule l'arbre couvrant de la fibre et permet la simulation de pannes."""
    afficher_section("Architecture Réseau Fibre")
    
    algo = questionary.select(
        "Quel algorithme souhaitez-vous utiliser ?",
        choices=["Kruskal", "Prim", "Comparaison (Kruskal vs Prim)"]
    ).ask()
    
    arbre = []
    cout = 0.0
    composantes = 0
    
    with console.status("[cyan]Calcul en cours...[/cyan]"):
        if algo == "Comparaison (Kruskal vs Prim)":
            t_debut_k = time.perf_counter()
            arbre_k, cout_k, composantes_k = kruskal(fibre)
            t_fin_k = time.perf_counter()
            
            t_debut_p = time.perf_counter()
            arbre_p, cout_p, composantes_p = prim(fibre)
            t_fin_p = time.perf_counter()
            
            console.print(f"Kruskal : Coût {cout_k:.2f} (en {(t_fin_k - t_debut_k)*1000:.2f} ms)")
            console.print(f"Prim    : Coût {cout_p:.2f} (en {(t_fin_p - t_debut_p)*1000:.2f} ms)")
            
            arbre = arbre_k
            cout = cout_k
            composantes = composantes_k
            console.print("\n[bold green]Résultats basés sur Kruskal conservés pour la suite.[/bold green]")
        elif algo == "Kruskal":
            arbre, cout, composantes = kruskal(fibre)
            console.print(f"\nAlgorithme utilisé : [bold green]{algo}[/bold green]")
        else:
            arbre, cout, composantes = prim(fibre)
            console.print(f"\nAlgorithme utilisé : [bold green]{algo}[/bold green]")
            
    if algo != "Comparaison (Kruskal vs Prim)":
        console.print(f"Coût total de l'infrastructure : [bold yellow]{cout:.2f}[/bold yellow]")
        console.print(f"Nombre de liaisons établies : [bold cyan]{len(arbre)}[/bold cyan]")
    
    if composantes > 1:
        console.print(f"Attention : Le réseau est divisé en [red]{composantes}[/red] zones distinctes (Forêt couvrante).")
        graphe_foret = Graphe(oriente=False)
        for n in fibre.noeuds():
            graphe_foret.ajouter_noeud(n)
        for u, v, poids in arbre:
            graphe_foret.ajouter_arete(u, v, poids)
            
        composantes_foret = tr.composantes_connexes(graphe_foret)
        for idx, comp in enumerate(composantes_foret, 1):
            console.print(f"  Arbre {idx} : [yellow]{', '.join(comp)}[/yellow]")
    else:
        console.print("Réseau entièrement connexe.", style="green")

    if not arbre:
        return

    table_aretes = Table(title="Liste des tronçons gardés", show_header=True)
    table_aretes.add_column("Origine")
    table_aretes.add_column("Destination")
    table_aretes.add_column("Coût")
    for u, v, poids in arbre:
        table_aretes.add_row(u, v, f"{poids:.2f}")
    console.print(table_aretes)

    simuler = questionary.confirm("Voulez-vous simuler la panne d'un tronçon majeur et évaluer la résilience ?").ask()
    if simuler:
        troncon_majeur = max(arbre, key=lambda x: x[2])
        texte_troncon_defaut = f"{troncon_majeur[0]}-{troncon_majeur[1]}"
        
        saisie_troncon = questionary.text(
            f"Quel tronçon fermer ? (par défaut {texte_troncon_defaut} qui est le plus coûteux) :",
            default=texte_troncon_defaut
        ).ask().strip()
        
        u_panne, v_panne = None, None
        if "-" in saisie_troncon:
            parties = saisie_troncon.split("-")
            if len(parties) == 2:
                u_panne, v_panne = parties
                
        troncon_a_casser = None
        for u, v, poids in arbre:
            if (u == u_panne and v == v_panne) or (u == v_panne and v == u_panne):
                troncon_a_casser = (u, v, poids)
                break
                
        if not troncon_a_casser:
            console.print(f"Err: Le tronçon {saisie_troncon} n'existe pas dans l'arbre. Annulation.", style="bold red")
            return
            
        console.print(f"\nSimulation de panne sur la liaison : [bold red]{troncon_a_casser[0]} <-> {troncon_a_casser[1]}[/bold red] (Coût: {troncon_a_casser[2]:.2f})")
        
        nouvelle_arete, cout_reparation = simuler_panne_et_reparer(fibre, arbre, (troncon_a_casser[0], troncon_a_casser[1]))
        
        if nouvelle_arete:
            console.print("Opération réussie. Route de secours identifiée.", style="green")
            console.print(f"Nouveau raccordement : [cyan]{nouvelle_arete[0]} <-> {nouvelle_arete[1]}[/cyan] (Coût: {cout_reparation:.2f})")
            surcout = cout_reparation - troncon_a_casser[2]
            console.print(f"Impact financier de l'incident : [yellow]+{surcout:.2f}[/yellow]")
        else:
            console.print("Err: Aucun raccordement alternatif disponible. Rupture de connectivité réseau.", style="bold red")


def executer_resilience(sites: Dict, routes: Any, fibre: Any, demandes: List, scenarios: Dict) -> None:
    """Compare la situation normale et les scénarios du fichier scenarios.csv."""
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
                scenarios = charger_scenarios(dossier_donnees, sites)

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
            elif choix == "itineraires":
                executer_itineraires(sites, routes, demandes)
            elif choix == "absorbants":
                executer_circuits_absorbants(routes)
            elif choix == "arbres":
                executer_arbres(reseau_fibre)
            elif choix == "resilience":
                executer_resilience(sites, routes, reseau_fibre, demandes, scenarios)
            elif choix == "benchmark":
                from novapolis.benchmarks import executer_benchmarks
                
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
                
                dossier_sortie = questionary.text("Dossier des résultats (graphiques) :", default="resultats").ask()
                with console.status("[cyan]Exécution des benchmarks en cours...[/cyan]"):
                    executer_benchmarks(dossier_sortie, max_sommets=max_sommets, max_fw=max_fw)
                console.print(f"Benchmarks terminés. Graphiques sauvegardés dans [bold green]{dossier_sortie}[/bold green]")
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
