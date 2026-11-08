"""Point d'entrée en ligne de commande."""
import argparse
import sys
import os

from novapolis.donnees.csv_loader import charger_jeu, charger_scenarios
from novapolis.donnees.exceptions import ErreurValidation
from novapolis.cli.commandes_base import diagnostic_accessibilite, afficher_resilience

EXEMPLES = """opérations (--op) :
  validate       vérifie les CSV
  accessibilite  Module 1 : diagnostic d'accessibilité
  resilience     Module 5 : comparaison des scénarios
  generate       Génère un dataset synthétique (Module 5 Expériences)
  benchmark      Exécute les benchmarks des performances (Module 5)
  (menus)        modules 2, 3 et 4 : python3 -m novapolis.cli.interactive

exemples :
  python3 main.py --data data/petit --op accessibilite
  python3 main.py --data data/nouveau --op generate --sites 2000 --dossier grand
  python3 main.py --data . --op benchmark --max-sommets 5000
  python3 main.py --data data/petit --op resilience --scenario fermeture_axe"""


def main():
    p = argparse.ArgumentParser(
        usage="python3 main.py --data DOSSIER --op OPERATION [--scenario NOM]",
        description="Novapolis Résilience : analyse d'un réseau urbain.",
        epilog=EXEMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--data", required=True, metavar="DOSSIER",
                   help="dossier des CSV (ex : data/petit)")
    p.add_argument("--scenario", default="normal", metavar="NOM",
                   help="scénario affiché en détail pour --op resilience (défaut : normal)")
    p.add_argument("--op", required=True, metavar="OPERATION",
                           choices=["validate", "accessibilite", "resilience", "generate", "benchmark"],
                           help="opération à lancer (liste ci-dessous)")
    p.add_argument("--sites", type=int, default=1000,
                           help="Nombre de sommets à générer (pour --op generate)")
    p.add_argument("--dossier", type=str, default="grand",
                           help="Nom du dossier de génération dans data/ (pour --op generate)")
    p.add_argument("--max-sommets", type=int, default=1000,
                           help="Maximum de sommets pour benchmarks (pour --op benchmark)")
    p.add_argument("--max-fw", type=int, default=100,
                           help="Maximum de sommets pour Floyd-Warshall (pour --op benchmark)")
    args = p.parse_args()

    if args.op == "generate":
        chemin_sauvegarde = os.path.join("data", args.dossier)
        nb_demandes = max(10, args.sites // 20)
        from novapolis.generateur import generer_jeu_de_donnees
        generer_jeu_de_donnees(chemin_sauvegarde, nb_sites=args.sites, nb_demandes=nb_demandes, degre_moyen=5)
        print(f"Opération réussie. Données générées avec succès dans {chemin_sauvegarde}")
        sys.exit(0)
        
    elif args.op == "benchmark":
        from novapolis.benchmarks import executer_benchmarks
        executer_benchmarks(args.data, max_sommets=args.max_sommets, max_fw=args.max_fw)
        print(f"Opération réussie. Graphiques sauvegardés dans {args.data}")
        sys.exit(0)

    try:
        sites, routes, fibre, demandes = charger_jeu(args.data)
        scenarios = charger_scenarios(args.data, sites)
    except ErreurValidation as e:
        print(f"Err: Données invalides :\n{e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Err: Fichier ou dossier introuvable : {e.filename}")
        sys.exit(1)

    if args.op == "validate":
        print(f"Opération réussie. OK : {len(sites)} sites, {len(routes.aretes())} arcs routiers, "
              f"{len(fibre.aretes())} tronçons de fibre, {len(demandes)} demandes")
    elif args.op == "accessibilite":
        diagnostic_accessibilite(sites, routes, fibre, demandes)
    elif args.op == "resilience":
        afficher_resilience(sites, routes, fibre, demandes, scenarios, args.scenario)


if __name__ == "__main__":
    main()