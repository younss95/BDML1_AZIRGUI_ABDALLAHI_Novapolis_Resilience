"""Point d'entrée en ligne de commande."""
import argparse
import sys

from novapolis.lire_csv import charger_jeu, ValidationError
from novapolis import parcours as tr


def main():
    p = argparse.ArgumentParser(description="Novapolis Résilience : analyse du réseau urbain")
    p.add_argument("--data", required=True, help="dossier contenant les CSV (ex : data/petit)")
    p.add_argument("--scenario", default="normal", help="scénario à appliquer (défaut : normal)")
    p.add_argument("--op", required=True, choices=["validate", "accessibilite"])
    args = p.parse_args()

    try:
        sites, routes, fibre, demandes = charger_jeu(args.data)
    except ValidationError as e:
        print("Données invalides :\n" + str(e))
        sys.exit(1)

    if args.op == "validate":
        print(f"OK : {len(sites)} sites, {len(routes.edges())} arcs routiers, "
              f"{len(fibre.edges())} tronçons de fibre, {len(demandes)} demandes")

    if args.op == "accessibilite":
        diagnostic_accessibilite(sites, routes, fibre, demandes)


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