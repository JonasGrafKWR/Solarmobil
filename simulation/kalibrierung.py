"""Kalibriert die Simulation mit realen Messwerten (Testplan docs/testplan.md).

Eingaben (CSV mit Semikolon, Vorlagen in tests/messprotokolle/):
  --solar  solar_kennlinie.csv     Spalten: R_Ohm;U_V   (EIN Modul, Lastwiderstaende; R=inf -> Leerlauf)
           --g-mess  Bestrahlung waehrend der Messung [W/m^2] (falls unbekannt: 1000 annehmen und
                     spaeter nur relative Vergleiche nutzen), --t-mess Zelltemperatur [degC]
  --ausroll ausrollversuch.csv     Spalten: v0_m_s;s_m  (Ausrollweg aus Anfangsgeschwindigkeit, Motor ABGEKLEMMT
                                   und Ritzel ausgerueckt -> reiner Roll-/Lagerwiderstand)
  --masse / --modulmasse           gewogene Werte [kg]
  --eta, --rueckprall, --t-schalt  direkt gemessene/abgeschaetzte Werte

Ausgabe: simulation/kalibrierung.json (wird von params.py automatisch geladen).
         `python kalibrierung.py --reset` loescht die Kalibrierung wieder.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib

import numpy as np
from scipy.optimize import least_squares

from solar_model import SolarModule

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "kalibrierung.json"


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader((ln for ln in f if not ln.startswith("#")), delimiter=";")]
    return {k: np.array([float(str(r[k]).replace(",", ".").replace("inf", "1e12")) for r in rows]) for k in rows[0]}


def fit_solar(path, g_mess, t_mess):
    d = read_csv(path)
    r, u = d["R_Ohm"], d["U_V"]
    i = u / r

    def resid(x):
        mod = SolarModule(u_oc=x[0], i_sc=x[1], n_ideal=x[2])
        # auf Messbedingungen umgerechnete Kennlinie
        return (mod.string_current(u, g_mess, t_mess) - i) / max(i.max(), 1e-3)

    sol = least_squares(resid, [max(u) * 1.02, max(i.max(), 0.05) * 1000 / g_mess, 2.0],
                        bounds=([0.5, 0.01, 1.0], [4.0, 5.0, 4.0]))
    rms = float(np.sqrt(np.mean(sol.fun ** 2)))
    return {"u_oc": round(float(sol.x[0]), 3), "i_sc": round(float(sol.x[1]), 3), "n_ideal": round(float(sol.x[2]), 2)}, rms


def fit_rollout(path):
    d = read_csv(path)
    crr = d["v0_m_s"] ** 2 / (2 * 9.80665 * d["s_m"])          # Luftwiderstand vernachlaessigt (v klein waehlen!)
    return float(np.median(crr)), float(np.std(crr))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solar"); ap.add_argument("--g-mess", type=float, default=1000.0); ap.add_argument("--t-mess", type=float, default=25.0)
    ap.add_argument("--ausroll")
    ap.add_argument("--masse", type=float); ap.add_argument("--modulmasse", type=float)
    ap.add_argument("--eta", type=float); ap.add_argument("--rueckprall", type=float); ap.add_argument("--t-schalt", type=float)
    ap.add_argument("--tunnelmitte", type=float); ap.add_argument("--bahnlaenge", type=float)
    ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()
    if a.reset:
        OUT.unlink(missing_ok=True)
        print("Kalibrierung geloescht - es gelten wieder die Annahmewerte aus params.py")
        return
    cal = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for k in ("module", "vehicle", "track", "reversal"):
        cal.setdefault(k, {})
    if a.solar:
        vals, rms = fit_solar(a.solar, a.g_mess, a.t_mess)
        cal["module"].update(vals)
        print(f"Solarmodul (auf 1000 W/m^2, 25 degC umgerechnet): {vals}, Restfehler {rms*100:.1f} % von I_max")
    if a.modulmasse:
        cal["module"]["mass"] = a.modulmasse
    if a.ausroll:
        crr, sd = fit_rollout(a.ausroll)
        cal["vehicle"]["crr"] = round(crr, 4)
        cal["vehicle"]["f_const"] = 0.0                      # im Ausrollversuch bereits enthalten
        print(f"Rollwiderstandsbeiwert c_rr = {crr:.4f} (Streuung {sd:.4f})")
    for key, grp, name in ((a.masse, "vehicle", "mass"), (a.eta, "vehicle", "eta_gear"), (a.rueckprall, "reversal", "restitution"),
                           (a.t_schalt, "reversal", "t_switch"), (a.tunnelmitte, "track", "tunnel_center"),
                           (a.bahnlaenge, "track", "length")):
        if key is not None:
            cal[grp][name] = key
    OUT.write_text(json.dumps(cal, indent=2), encoding="utf-8")
    print("geschrieben:", OUT, "\n", json.dumps(cal, indent=2))


if __name__ == "__main__":
    main()
