"""Point d'entrée en ligne de commande."""
import argparse
import sys

from novapolis.donnees.csv_reader import charger_jeu, charger_scenarios
from novapolis.donnees.exceptions import ErreurValidation
from novapolis.graphes import parcours as tr   
from novapolis.indicateurs import comparer_scenarios, formater_valeur, LIBELLES_RESUME


def main():
    p = argparse.ArgumentParser(description="Novapolis Résilience : analyse du réseau urbain")
    p.add_argument("--data", required=True, help="dossier contenant les CSV (ex : data/petit)")
    p.add_argument("--scenario", default="normal", help="scénario à appliquer (défaut : normal)")
    p.add_argument("--op", required=True, choices=["validate", "accessibilite", "resilience"])
    args = p.parse_args()

    try:
        sites, routes, fibre, demandes = charger_jeu(args.data)
        scenarios = charger_scenarios(args.data, sites)

    except ErreurValidation as e:
        print("Données invalides :\n" + str(e))
        sys.exit(1)

    if args.op == "validate":
        print(f"OK : {len(sites)} sites, {len(routes.aretes())} arcs routiers, "
              f"{len(fibre.aretes())} tronçons de fibre, {len(demandes)} demandes")

        if args.op == "resilience":
            afficher_resilience(sites, routes, fibre, demandes, scenarios, args.scenario)

    def afficher_resilience(sites, routes, fibre, demandes, scenarios, scenario):
        resultats = comparer_scenarios(sites, routes, fibre, demandes, scenarios)
        if scenario not in resultats:
            print(f"Scénario inconnu : '{scenario}'. Disponibles : {', '.join(resultats)}")
            sys.exit(1)

        noms = list(resultats)
        print(f"{'Indicateur':<32}" + "".join(f"{n:>22}" for n in noms))
        for cle, libelle in LIBELLES_RESUME:
            print(f"{libelle:<32}" + "".join(f"{formater_valeur(cle, resultats[n]['resume'][cle]):>22}" for n in noms))

        print(f"\nDétail des trajets : scénario '{scenario}'")
        print(f"{'Demande':<8}{'Site':<6}{'Avant':>8}{'Après':>8}{'Retard':>8}{'Retard %':>10}  Statut")
        for l in resultats[scenario]["detail"]:
            avant = f"{l['avant']:.1f}" if l["avant"] is not None else "-"
            apres = f"{l['apres']:.1f}" if l["apres"] is not None else "-"
            retard = f"{l['retard']:+.1f}" if l["retard"] is not None else "-"
            pct = f"{l['retard_pct']:+.1f} %" if l["retard_pct"] is not None else "-"
            print(f"{l['id']:<8}{l['origine']:<6}{avant:>8}{apres:>8}{retard:>8}{pct:>10}  {l['statut']}")


def diagnostic_accessibilite(sites, routes, fibre, demandes):
    casernes = [s for s, r in sites.items() if r["type"] == "caserne"]
    print(f"Casernes : {casernes}")

    dist, _ = tr.bfs(routes, casernes)
    print(f"\n[Accessibilité orientée depuis les casernes] {len(dist)}/{len(sites)} sites atteints")
    inacc = tr.sites_inaccessibles(routes, casernes)
    print(f"  Non atteignables : {inacc or 'aucun'}")

    print("\n[Demandes : nombre minimal d'arcs depuis la caserne la plus proche]")
    for d in demandes:
        d_arcs = dist.get(d["origine"])
        txt = f"{d_arcs} arc(s)" if d_arcs is not None else "INACCESSIBLE"
        print(f"  {d['id']} ({d['type']}, priorité {d['priorite']}) -> {d['origine']} : {txt}")

    cycle = tr.a_un_cycle_oriente(routes)
    print(f"\n[Cycle orienté dans les routes] {' -> '.join(cycle) if cycle else 'aucun'}")

    scc = tr.composantes_fortement_connexes(routes)
    print(f"[Connexité forte des routes] {len(scc)} composante(s) : {scc}")
    print(f"[Sites isolés (routes)] {tr.sites_isoles(routes) or 'aucun'}")

    comps = tr.composantes_connexes(fibre)
    print(f"\n[Fibre : composantes connexes] {len(comps)} : {comps}")


if __name__ == "__main__":
    main()