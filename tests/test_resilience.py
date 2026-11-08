import pytest

from novapolis.donnees.csv_loader import charger_jeu, charger_scenarios
from novapolis.donnees.exceptions import ErreurValidation
from novapolis.graphes.scenarios import appliquer_scenario
from novapolis.indicateurs import evaluer_scenario, comparer_scenarios

DOSSIER = "data/petit"


@pytest.fixture
def jeu():
    return charger_jeu(DOSSIER)


def action(type_element, u, v, act, nom="test"):
    return {"scenario": nom, "type_element": type_element, "u": u, "v": v, "action": act}


def test_scenario_ne_modifie_pas_les_originaux(jeu):
    sites, routes, fibre, demandes = jeu
    routes_avant, fibre_avant = routes.aretes(), fibre.aretes()
    appliquer_scenario(routes, fibre, [action("route", "S2", "S5", "fermer"),
                                       action("fibre", "S2", "S5", "supprimer")])
    assert routes.aretes() == routes_avant
    assert fibre.aretes() == fibre_avant


def test_situation_normale_aucun_retard(jeu):
    sites, routes, fibre, demandes = jeu
    r = evaluer_scenario(sites, routes, fibre, demandes, [])["resume"]
    assert r["retard_moyen"] == 0 and r["retard_max"] == 0
    assert r["demandes_inaccessibles"] == 1          # D4 vise S7, sans aucune route
    assert r["composantes_fibre"] == 2 and r["cout_arbre"] == 59


def test_fermeture_axe_retard(jeu):
    sites, routes, fibre, demandes = jeu
    res = evaluer_scenario(sites, routes, fibre, demandes, [action("route", "S2", "S5", "fermer")])
    d1 = next(l for l in res["detail"] if l["id"] == "D1")
    assert (d1["avant"], d1["apres"], d1["retard"]) == (13, 14, 1)
    assert d1["retard_pct"] == pytest.approx(100 / 13)
    assert res["resume"]["retard_max"] == 1


def test_fermeture_sans_effet(jeu):
    sites, routes, fibre, demandes = jeu
    acts = [action("route", "S2", "S3", "fermer"), action("route", "S3", "S2", "fermer")]
    assert evaluer_scenario(sites, routes, fibre, demandes, acts)["resume"]["retard_max"] == 0


def test_panne_fibre_raccordement(jeu):
    sites, routes, fibre, demandes = jeu
    r = evaluer_scenario(sites, routes, fibre, demandes,
                         [action("fibre", "S2", "S5", "supprimer")])["resume"]
    assert r["cout_reparation"] == 12 and r["surcout_arbre"] == 4
    assert r["composantes_fibre"] == 2 and r["pannes_irreparables"] == 0


def test_panne_fibre_sans_raccordement_possible(jeu):
    sites, routes, fibre, demandes = jeu
    r = evaluer_scenario(sites, routes, fibre, demandes,
                         [action("fibre", "S3", "S6", "supprimer")])["resume"]
    assert r["composantes_fibre"] == 3 and r["pannes_irreparables"] == 1
    assert r["surcout_arbre"] is None                # réseau fragmenté : non comparable


def test_demande_devenue_inaccessible(jeu):
    sites, routes, fibre, demandes = jeu
    acts = [action("route", "S2", "S3", "fermer"), action("route", "S5", "S3", "fermer")]
    r = evaluer_scenario(sites, routes, fibre, demandes, acts)["resume"]
    assert r["devenues_inaccessibles"] == 2          # D1 (S3) et D3 (S6)


def test_comparer_scenarios_inclut_normal_en_premier(jeu):
    sites, routes, fibre, demandes = jeu
    scen = charger_scenarios(DOSSIER, sites)
    assert list(comparer_scenarios(sites, routes, fibre, demandes, scen))[0] == "normal"


def test_scenario_arc_inexistant(jeu):
    sites, routes, fibre, demandes = jeu
    with pytest.raises(ErreurValidation):
        appliquer_scenario(routes, fibre, [action("route", "S1", "S3", "fermer")])


def test_scenarios_csv_invalide(tmp_path, jeu):
    sites = jeu[0]
    (tmp_path / "scenarios.csv").write_text(
        "scenario,type_element,u,v,action\nx,route,S1,S99,fermer\ny,route,S1,S2,supprimer\n")
    with pytest.raises(ErreurValidation) as e:
        charger_scenarios(str(tmp_path), sites)
    assert "S99" in str(e.value) and "invalide" in str(e.value)