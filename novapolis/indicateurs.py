"""Module 5 : indicateurs de résilience et comparaison de scénarios."""
from statistics import mean

from novapolis.graphes import chemins as ch
from novapolis.graphes import parcours as tr
from novapolis.graphes.arbre import kruskal, simuler_panne_et_reparer
from novapolis.graphes.scenarios import appliquer_scenario

TYPES_SECOURS = {"incendie": ["caserne"], "medical": ["hopital"]}
TYPES_SENSIBLES = {"hopital", "caserne", "ecole", "telecom"}
INF = float("inf")

# (clé, libellé) : ordre d'affichage du tableau comparatif
LIBELLES_RESUME = [
    ("demandes_inaccessibles", "Demandes inaccessibles"),
    ("devenues_inaccessibles", "  dont devenues inaccessibles"),
    ("retard_moyen", "Retard moyen"),
    ("retard_max", "Retard maximal"),
    ("sites_sensibles_pct", "Sites sensibles accessibles"),
    ("composantes_fibre", "Composantes de fibre"),
    ("cout_arbre", "Coût de l'arbre de fibre"),
    ("cout_reparation", "Coût de réparation"),
    ("surcout_arbre", "Surcoût de l'arbre"),
    ("pannes_irreparables", "Pannes sans raccordement"),
]


def formater_valeur(cle, valeur):
    if valeur is None:
        return "-"
    if cle in ("retard_moyen", "retard_max"):
        return f"{valeur:.1f} min"
    if cle == "sites_sensibles_pct":
        return f"{valeur:.0f} %"
    if cle in ("cout_arbre", "cout_reparation", "surcout_arbre"):
        return f"{valeur:+.1f}" if cle == "surcout_arbre" else f"{valeur:.1f}"
    return str(valeur)


def sites_de_type(sites, types):
    return [s for s, r in sites.items() if r["type"] in types]


# ---------- Trajets ----------

def calculer_trajets(routes, sites, demandes):
    """Pour chaque demande : {'temps','source','chemin'} depuis le site de secours le plus
    rapide, ou None si inaccessible. Un Dijkstra par site de secours (mis en cache)."""
    cache, trajets = {}, {}
    for d in demandes:
        types = TYPES_SECOURS.get(d["type"], ["caserne", "hopital"])
        meilleur = None
        for source in sites_de_type(sites, types):
            if source not in cache:
                cache[source] = ch.dijkstra(routes, source)
            distances, preds = cache[source]
            temps = distances.get(d["origine"], INF)
            if temps < INF and (meilleur is None or temps < meilleur["temps"]):
                meilleur = {"temps": temps, "source": source,
                            "chemin": ch.reconstruire_chemin(preds, source, d["origine"])}
        trajets[d["id"]] = meilleur
    return trajets


def comparer_trajets(demandes, avant, apres):
    """Une ligne par demande : temps avant/après, retard absolu et relatif, statut."""
    lignes = []
    for d in demandes:
        a, p = avant[d["id"]], apres[d["id"]]
        ligne = {"id": d["id"], "type": d["type"], "priorite": d["priorite"],
                 "origine": d["origine"],
                 "avant": a["temps"] if a else None, "apres": p["temps"] if p else None,
                 "chemin_avant": a["chemin"] if a else None,
                 "chemin_apres": p["chemin"] if p else None,
                 "retard": None, "retard_pct": None}
        if a and p:
            ligne["statut"] = "accessible"
            ligne["retard"] = p["temps"] - a["temps"]
            if a["temps"] > 0:
                ligne["retard_pct"] = 100 * ligne["retard"] / a["temps"]
        elif a:
            ligne["statut"] = "devenue inaccessible"
        elif p:
            ligne["statut"] = "redevenue accessible"
        else:
            ligne["statut"] = "inaccessible"
        lignes.append(ligne)
    return lignes


# ---------- Indicateurs ----------

def proportion_sites_sensibles(sites, routes):
    """Part (0 à 1) des sites sensibles atteignables depuis une caserne ou un hôpital."""
    sensibles = sites_de_type(sites, TYPES_SENSIBLES)
    atteints = set()
    for source in sites_de_type(sites, {"caserne", "hopital"}):
        distances, _ = ch.dijkstra(routes, source)
        atteints |= {s for s, d in distances.items() if d < INF}
    return sum(1 for s in sensibles if s in atteints) / len(sensibles) if sensibles else 1.0


def indicateurs_routiers(sites, routes_sc, lignes):
    retards = [l["retard"] for l in lignes if l["retard"] is not None]
    return {
        "demandes_inaccessibles": sum(1 for l in lignes if l["apres"] is None),
        "devenues_inaccessibles": sum(1 for l in lignes if l["statut"] == "devenue inaccessible"),
        "retard_moyen": mean(retards) if retards else 0.0,
        "retard_max": max(retards) if retards else 0.0,
        "sites_sensibles_pct": 100 * proportion_sites_sensibles(sites, routes_sc),
    }


def indicateurs_fibre(fibre_base, fibre_sc, actions):
    arbre_base, cout_base, _ = kruskal(fibre_base)
    _, cout_sc, _ = kruskal(fibre_sc)
    comps_base = len(tr.composantes_connexes(fibre_base))
    comps_sc = len(tr.composantes_connexes(fibre_sc))

    cout_reparation, irreparables = 0.0, 0
    for a in actions:
        if a["type_element"] != "fibre" or a["action"] not in ("supprimer", "interdire"):
            continue
        u, v = a["u"], a["v"]
        if not any({x, y} == {u, v} for x, y, _ in arbre_base):
            continue                       # tronçon hors de l'arbre : rien à réparer
        nouvelle, cout = simuler_panne_et_reparer(fibre_base, arbre_base, (u, v))
        if nouvelle is None:
            irreparables += 1
        else:
            cout_reparation += cout

    return {
        "composantes_fibre": comps_sc,
        "cout_arbre": cout_sc,
        # si le réseau est fragmenté, le coût de l'arbre n'est plus comparable
        "surcout_arbre": cout_sc - cout_base if comps_sc <= comps_base else None,
        "cout_reparation": cout_reparation,
        "pannes_irreparables": irreparables,
    }


# ---------- Scénarios ----------

def evaluer_scenario(sites, routes, fibre, demandes, actions, trajets_avant=None):
    """Applique le scénario sur des copies et calcule tous les indicateurs."""
    routes_sc, fibre_sc = appliquer_scenario(routes, fibre, actions)
    if trajets_avant is None:
        trajets_avant = calculer_trajets(routes, sites, demandes)
    trajets_apres = calculer_trajets(routes_sc, sites, demandes)
    lignes = comparer_trajets(demandes, trajets_avant, trajets_apres)
    resume = indicateurs_routiers(sites, routes_sc, lignes)
    resume.update(indicateurs_fibre(fibre, fibre_sc, actions))
    return {"resume": resume, "detail": lignes}


def comparer_scenarios(sites, routes, fibre, demandes, scenarios):
    """{nom: {'resume', 'detail'}} : 'normal' (référence) puis chaque scénario du CSV."""
    avant = calculer_trajets(routes, sites, demandes)
    resultats = {"normal": evaluer_scenario(sites, routes, fibre, demandes, [], avant)}
    for nom, actions in scenarios.items():
        if nom != "normal":
            resultats[nom] = evaluer_scenario(sites, routes, fibre, demandes, actions, avant)
    return resultats