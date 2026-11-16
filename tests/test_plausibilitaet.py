"""Plausibilitaetspruefungen fuer Simulation und Konstruktion.

    python -m pytest tests -q

Die Tests pruefen die innere Konsistenz der Modelle (Energieerhaltung,
Grenzfaelle, Datenblatt-Wiedergabe) und die Reglement-Huellmasse des CAD-
Modells.  Sie ersetzen KEINE Messung am realen Fahrzeug.
"""
from dataclasses import replace
import json
import pathlib
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulation"))

from motor_model import load_motors, MOTOR_SPECS, RPM, GCM        # noqa: E402
from solar_model import Generator, SolarModule, SCENARIOS, solve_operating_point  # noqa: E402
from vehicle_model import (Case, VehicleParams, TrackParams, ReversalParams, simulate_batch, drive_force,  # noqa: E402
                           resistance, effective_mass, steady_speed)
from params import BASE_VEHICLE, BASE_MODULE, BASE_TRACK, BASE_REV, DESIGN  # noqa: E402
import gear_geometry as gg                                        # noqa: E402

MOTORS = load_motors()
MOT = MOTORS[DESIGN["motor"]]


# ----------------------------------------------------------------- Motor
@pytest.mark.parametrize("spec", MOTOR_SPECS, ids=lambda s: s.name)
def test_motormodell_gibt_datenblatt_wieder(spec):
    m = MOTORS[spec.name]
    u = spec.u_nom
    assert m.omega_noload(u) / RPM == pytest.approx(spec.n0_rpm, rel=0.08)
    assert m.stall_torque(u) / GCM == pytest.approx(spec.m_stall_gcm, rel=0.08)
    assert m.start_current() == pytest.approx(spec.i0, rel=0.10)
    # Punkt maximalen Wirkungsgrads: Strom beim Datenblatt-Drehmoment
    i_eta = (spec.m_eta_gcm * GCM + m.m_fric) / m.k
    assert i_eta == pytest.approx(spec.i_eta, rel=0.10)


def test_motor_leistungsbilanz():
    w = np.linspace(0, MOT.omega_noload(6.0), 50)
    p_el = 6.0 * MOT.current(6.0, w)
    assert np.all(MOT.p_mech(6.0, w) <= p_el + 1e-9)
    assert MOT.p_mech_max(6.0) == pytest.approx(np.max(MOT.p_mech(6.0, np.linspace(0, MOT.omega_noload(6.0), 4001))), rel=1e-3)


# ----------------------------------------------------------------- Solargenerator
def test_solar_leerlauf_und_kurzschluss():
    g = Generator(BASE_MODULE, "4s")
    assert g.u_oc() == pytest.approx(4 * BASE_MODULE.u_oc, rel=1e-3)
    assert g.i_sc() == pytest.approx(BASE_MODULE.i_sc, rel=1e-3)
    p = Generator(BASE_MODULE, "4p")
    assert p.u_oc() == pytest.approx(BASE_MODULE.u_oc, rel=1e-3)
    assert p.i_sc() == pytest.approx(4 * BASE_MODULE.i_sc, rel=1e-3)


def test_solar_mpp_unabhaengig_von_verschaltung_bei_gleichmaessigem_licht():
    pm = [Generator(BASE_MODULE, c).mpp(800, 800, 40)["P_mpp"] for c in ("4s", "2s2p", "4p")]
    assert max(pm) == pytest.approx(min(pm), rel=0.01)
    assert 0.60 < Generator(BASE_MODULE, "4s").fill_factor() < 0.80


def test_solar_temperatur_und_bestrahlung():
    g = Generator(BASE_MODULE, "4s")
    assert g.u_oc(1000, 60) < g.u_oc(1000, 25)                 # Spannung sinkt mit der Temperatur
    assert g.mpp(1000, 1000, 60)["P_mpp"] < g.mpp(1000, 1000, 25)["P_mpp"]
    assert g.i_sc(500) == pytest.approx(0.5 * g.i_sc(1000), rel=0.01)   # I_sc proportional zu G


def test_teilabschattung_trifft_reihenschaltung_haerter():
    ser = Generator(BASE_MODULE, "4s").mpp(800, 16, 40)["P_mpp"]
    par = Generator(BASE_MODULE, "2s2p").mpp(800, 16, 40)["P_mpp"]
    full = Generator(BASE_MODULE, "4s").mpp(800, 800, 40)["P_mpp"]
    assert ser < 0.1 * full
    assert par > 0.4 * full


def test_arbeitspunkt_liegt_auf_beiden_kennlinien():
    for cfg in ("4s", "2s2p", "4p"):
        gen = Generator(BASE_MODULE, cfg)
        w = np.array([0.0, 200.0, 600.0])
        i, ug, um = solve_operating_point(gen, MOT, w, 700.0, 700.0, 40.0, 1, 0.2)
        assert np.allclose(gen.current(ug, 700.0, 700.0, 40.0), i, atol=2e-3)
        assert np.allclose((um - MOT.k * w) / MOT.R, i, atol=1e-6)
        assert np.all(i <= gen.i_sc(700.0, 40.0) * 1.001)
        assert np.all(ug * i <= gen.mpp(700, 700, 40)["P_mpp"] * 1.002)   # nie mehr als MPP-Leistung


# ----------------------------------------------------------------- Fahrzeug
def _case(sc="sonne", cfg="4s", **kw):
    return Case(replace(BASE_VEHICLE, **kw), MOT, Generator(BASE_MODULE, cfg), SCENARIOS[sc], BASE_TRACK, BASE_REV)


def test_im_dunkeln_keine_antriebskraft():
    c = _case()
    f = drive_force(c.veh, c.motor, c.gen, np.array([0.5, 2.0, 4.0]), 0.0, 0.0, 25.0)
    assert np.all(f <= 0.0)                                   # Motor bremst (Reibung, Generatorbetrieb)


def test_geschwindigkeit_unter_theoretischer_leerlaufgrenze():
    c = _case()
    r = simulate_batch([c], dt=0.002)
    v_theo = MOT.omega_noload(c.gen.u_oc(c.light.g, c.light.t_cell)) / c.veh.gear_ratio * c.veh.wheel_d / 2
    assert r["status"][0] == 0
    assert r["v_max"][0] < v_theo


def test_energiebilanz_erste_durchfahrt():
    c = _case()
    one = replace(c, track=replace(c.track, legs=1, tunnel_len=0.0))
    r = simulate_batch([one], dt=0.001)
    e_kin = 0.5 * effective_mass(c.veh, c.motor) * r["v_impact"][0, 0] ** 2
    e_sol = c.gen.mpp(c.light.g, c.light.g, c.light.t_cell)["P_mpp"] * r["t_leg"][0, 0]
    assert e_kin < e_sol                                      # kinetische Energie < eingestrahlte elektrische Energie


def test_mehr_licht_ist_schneller_und_schwerer_ist_langsamer():
    base = _case()
    dunkler = replace(base, light=replace(base.light, g=500.0))
    schwer = replace(base, veh=replace(base.veh, mass=base.veh.mass * 1.3))
    r = simulate_batch([base, dunkler, schwer], dt=0.003)
    assert r["t_total"][0] < r["t_total"][1]
    assert r["t_total"][0] < r["t_total"][2]


def test_zeitschritt_konvergenz():
    c = _case()
    a = simulate_batch([c], dt=0.004)["t_total"][0]
    b = simulate_batch([c], dt=0.001)["t_total"][0]
    assert a == pytest.approx(b, rel=0.01)


def test_schwachlicht_mit_empfohlener_verschaltung_kommt_an():
    r = simulate_batch([_case("kunstlicht", DESIGN["config_weak"]), _case("bewoelkt", DESIGN["config_weak"])], dt=0.003)
    assert np.all(r["status"] == 0)


def test_zu_langsamer_aufprall_wird_als_fehler_gemeldet():
    c = _case("bewoelkt", "2s2p")
    c = replace(c, rev=replace(c.rev, v_switch_min=10.0))
    assert simulate_batch([c], dt=0.004)["status"][0] == 3


# ----------------------------------------------------------------- Getriebe
@pytest.mark.parametrize("z", list(DESIGN["gear_pairs"].values()))
def test_zahnradpaare(z):
    g1, g2, a = gg.make_pair(DESIGN["gear_module"], *z)
    assert sum(z) == DESIGN["z_sum"]
    assert gg.contact_ratio(g1, g2, a) >= 1.15                # Ueberdeckung
    assert g1.x >= g1.x_min_undercut - 1e-9                   # kein Unterschnitt am Ritzel
    assert g1.sa >= 0.39 and g2.sa >= 0.39                    # druckbare Zahnkopfdicke
    assert min(gg.tip_root_clearance(g1, g2, a)) >= 0.15
    assert g2.da / 2 < BASE_VEHICLE.wheel_d * 1000 / 2 - 2.5  # Rad beruehrt die Fahrbahn nicht


# ----------------------------------------------------------------- CAD / Reglement
def test_cad_pruefbericht_und_reglement():
    p = ROOT / "cad" / "assemblies" / "pruefbericht.json"
    if not p.exists():
        pytest.skip("CAD noch nicht erzeugt (python cad/source/build_all.py)")
    rep = json.loads(p.read_text(encoding="utf-8"))
    assert rep["huelle"]["Laenge_mm"] <= 300.0
    assert rep["huelle"]["Breite_mm"] <= 140.0
    assert all(c["Ergebnis"] == "OK" for c in rep["checks"]), [c for c in rep["checks"] if c["Ergebnis"] != "OK"]
    # Simulation rechnet mit der CAD-Masse (Toleranz 5 %)
    assert rep["masse"]["Gesamtmasse_g"] == pytest.approx(BASE_VEHICLE.mass * 1000, rel=0.05)


def test_stl_dateien_validiert():
    p = ROOT / "exports" / "STL" / "_validierung.csv"
    if not p.exists():
        pytest.skip("STL-Validierung noch nicht gelaufen (python cad/source/validate_stl.py)")
    lines = p.read_text(encoding="utf-8").strip().splitlines()[1:]
    assert len(lines) >= 12
    assert all(line.endswith("OK") for line in lines)
