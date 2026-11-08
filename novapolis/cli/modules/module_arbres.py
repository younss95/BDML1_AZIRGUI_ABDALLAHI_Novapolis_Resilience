"""Module pour l'analyse interactive de la connectivité fibre (arbres couvrants)."""
import time
import questionary
from rich.table import Table
from typing import Any
from novapolis.cli.interface import console, afficher_section
from novapolis.graphes import parcours as tr
from novapolis.graphes.arbre import kruskal, prim, simuler_panne_et_reparer
from novapolis.graphes.graphe import Graphe

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
        console.print("Opération réussie. Réseau entièrement connexe.", style="green")

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
