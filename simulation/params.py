"""Zentrale Auslegungsparameter (eine Stelle fuer Simulation und Dokumentation).

Herkunft der Werte:
  [R]  Reglement / offizielle Quelle        [D]  Datenblatt
  [C]  aus CAD berechnet (cad/source)       [B]  berechnet
  [A]  ANNAHME - muss gemessen werden (Testplan)

Kalibrierung: Wenn neben dieser Datei eine `kalibrierung.json` liegt
(erzeugt von kalibrierung.py aus Messprotokollen), ueberschreiben deren Werte
die Standardwerte unten.
"""
from __future__ import annotations

from dataclasses import replace, fields
import json
import pathlib

from solar_model import SolarModule
from vehicle_model import VehicleParams, TrackParams, ReversalParams

# --- Solarmodul des Starterkits -------------------------------------------------
BASE_MODULE = SolarModule(
    u_oc=2.40,        # [A] V   (4 Si-Zellen in Reihe, Vergleichsmodul TRU POLY-PVZ-8080-2V: 2,4 V)
    i_sc=0.60,        # [A] A   (Kit-Angabe "0,6 A" als Kurzschlussstrom bei 1000 W/m^2 gedeutet)
    n_cells=4,        # [A]
    n_ideal=2.0,      # [A] -> Fuellfaktor ca. 0,72
    mass=0.036,       # [A] kg  (Flaechengewicht des TRU-Vergleichsmoduls 5,2 kg/m^2 x 120x60 mm)
    length=0.120,     # [A] m
    width=0.060,      # [A] m
    thickness=0.0031,  # [A] m
)

# --- Fahrzeug ---------------------------------------------------------------------
BASE_VEHICLE = VehicleParams(
    mass=0.260,            # [C]+[A] kg  cad/assemblies/pruefbericht.md (davon 144 g Module = Annahme)
    wheel_d=0.050,         # [C] m
    gear_ratio=5.0,        # [B] Variante 2 "Ausgewogen" (60:12)
    eta_gear=0.88,         # [A]
    crr=0.020,             # [A]
    f_const=0.010,         # [A] N
    cda=0.0050,            # [A] m^2
    j_wheels=4.4e-6,       # [C] kg*m^2
    j_axle_gear=8.0e-7,    # [C] kg*m^2
    j_pinion=3.8e-9,       # [C] kg*m^2
    mu_traction=0.60,      # [A]
    driven_load_frac=0.55,  # [C]
    length=0.296,          # [C] m  Laenge ueber alles
    pair_offset=0.060,     # [C] m
    pair_len=0.120,        # [A] m
    r_wiring=0.20,         # [A] Ohm
)

BASE_TRACK = TrackParams(
    length=10.0,           # [R] "ca. 10 m"
    tunnel_len=1.6,        # [R]
    tunnel_center=5.0,     # [A] Lage des Tunnels nicht dokumentiert
    legs=4,                # [R]
)

BASE_REV = ReversalParams(
    restitution=0.30,      # [A]
    t_switch=0.030,        # [A] s
    v_switch_min=0.25,     # [B] m/s (docs/umkehrmechanismus.md)
    v_impact_design=4.0,   # [A] m/s
)

# --- Konstruktive Festlegungen ------------------------------------------------------
DESIGN = {
    "motor": "FF-130SH-14230",          # [B] Ergebnis der Motorstudie
    "motor_fallback": "RF300CA-11400@3V",  # Starterkit-Motor
    "config_sun": "4s",
    "config_weak": "2s2p",
    "gear_module": 0.7,                 # mm
    "z_sum": 72,                        # z1 + z2 -> Achsabstand 25,2 mm (+0,1 Spiel)
    "gear_targets": {"1 Schnell (gutes Licht)": 4.1, "2 Ausgewogen": 5.0, "3 Anfahrstark (schwaches Licht)": 6.2},
    "gear_pairs": {"1": (14, 58), "2": (12, 60), "3": (10, 62)},
}


def _apply(obj, data: dict):
    names = {f.name for f in fields(obj)}
    return replace(obj, **{k: v for k, v in data.items() if k in names})


_cal = pathlib.Path(__file__).with_name("kalibrierung.json")
if _cal.exists():
    _d = json.loads(_cal.read_text(encoding="utf-8"))
    BASE_MODULE = _apply(BASE_MODULE, _d.get("module", {}))
    BASE_VEHICLE = _apply(BASE_VEHICLE, _d.get("vehicle", {}))
    BASE_TRACK = _apply(BASE_TRACK, _d.get("track", {}))
    BASE_REV = _apply(BASE_REV, _d.get("reversal", {}))
    CALIBRATED = True
else:
    CALIBRATED = False
