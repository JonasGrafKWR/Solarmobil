"""Simulation des vollstaendigen Rennablaufs (4 Durchfahrten, 3 Richtungswechsel, Tunnel).

Beispiele:
    python race_simulation.py                                  alle Szenarien mit der Auslegung aus params.py
    python race_simulation.py --szenario sonne --i 5.0 --verschaltung 4s
    python race_simulation.py --motor "RF300CA-11400@3V" --masse 0.20 --rad 0.044 --mc 500
    python race_simulation.py --licht 600 --tunnellicht 0.05 --eta 0.85 --crr 0.03 --t-schalt 0.05

Alle Ergebnisse sind SIMULATIONSWERTE auf Basis von Datenblatt- und
Annahmewerten -- keine Messung.  Diagramme: results/diagrams/, Tabellen:
results/calculations/.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
import pathlib

import numpy as np

from motor_model import load_motors, RPM
from solar_model import Generator, SCENARIOS, solve_operating_point
from vehicle_model import (Case, simulate_batch, drive_force, resistance, effective_mass, steady_speed,
                           start_margin, STATUS_TEXT, G0)
from gear_optimizer import sample_cases, write_csv
from params import BASE_VEHICLE, BASE_MODULE, BASE_TRACK, BASE_REV, DESIGN, CALIBRATED

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_D = ROOT / "results" / "diagrams"
OUT_C = ROOT / "results" / "calculations"


def build_case(args, scenario: str, config: str | None = None, ratio: float | None = None) -> Case:
    motors = load_motors()
    sc = SCENARIOS[scenario]
    if args.licht is not None:
        sc = replace(sc, g=args.licht)
    if args.tunnellicht is not None:
        sc = replace(sc, tunnel_light=args.tunnellicht)
    cfg = config or args.verschaltung or (DESIGN["config_sun"] if scenario == "sonne" else DESIGN["config_weak"])
    veh = replace(BASE_VEHICLE,
                  gear_ratio=ratio if ratio is not None else (args.i if args.i is not None else BASE_VEHICLE.gear_ratio),
                  mass=args.masse if args.masse is not None else BASE_VEHICLE.mass,
                  wheel_d=args.rad if args.rad is not None else BASE_VEHICLE.wheel_d,
                  eta_gear=args.eta if args.eta is not None else BASE_VEHICLE.eta_gear,
                  crr=args.crr if args.crr is not None else BASE_VEHICLE.crr,
                  mu_traction=args.mu if args.mu is not None else BASE_VEHICLE.mu_traction)
    rev = replace(BASE_REV, t_switch=args.t_schalt if args.t_schalt is not None else BASE_REV.t_switch,
                  restitution=args.rueckprall if args.rueckprall is not None else BASE_REV.restitution)
    track = replace(BASE_TRACK, tunnel_len=args.tunnel if args.tunnel is not None else BASE_TRACK.tunnel_len)
    return Case(veh, motors[args.motor or DESIGN["motor"]], Generator(BASE_MODULE, cfg), sc, track, rev)


def summarize(name: str, case: Case, res: dict, j: int = 0) -> dict:
    mot, veh = case.motor, case.veh
    f0 = float(drive_force(veh, mot, case.gen, 0.0, case.light.g, case.light.g, case.light.t_cell))
    a0 = (f0 - float(resistance(veh, 0.0))) / effective_mass(veh, mot)
    vss = steady_speed(veh, mot, case.gen, case.light)
    ok = res["status"][j] == 0
    tl = res["t_leg"][j]
    return {
        "Szenario": name, "Motor": mot.name, "Verschaltung": case.gen.config, "G_W_m2": case.light.g,
        "i": veh.gear_ratio, "Rad_d_mm": round(veh.wheel_d * 1000, 1), "Masse_g": round(veh.mass * 1000),
        "Anfahrkraft_N": round(f0, 3), "Anfahrreserve": round(start_margin(veh, mot, case.gen, case.light), 2),
        "a_Start_m_s2": round(a0, 2), "v_Beharrung_m_s": round(vss, 2), "v_max_Rennen_m_s": round(float(res["v_max"][j]), 2),
        "t_Durchfahrt_1_s": round(float(tl[0]), 2) if np.isfinite(tl[0]) else "",
        "t_Durchfahrt_2_s": round(float(tl[1]), 2) if np.isfinite(tl[1]) else "",
        "t_Durchfahrt_3_s": round(float(tl[2]), 2) if np.isfinite(tl[2]) else "",
        "t_Durchfahrt_4_s": round(float(tl[3]), 2) if np.isfinite(tl[3]) else "",
        "t_gesamt_s": round(float(res["t_total"][j]), 2) if ok else "",
        "v_Aufprall_max_m_s": round(float(np.nanmax(res["v_impact"][j])), 2) if np.any(np.isfinite(res["v_impact"][j])) else "",
        "v_Tunnel_min_m_s": round(float(res["v_tunnel_min"][j]), 2) if np.isfinite(res["v_tunnel_min"][j]) else "",
        "Status": STATUS_TEXT[int(res["status"][j])],
        "Herkunft": "simuliert" + (" (kalibriert)" if CALIBRATED else " (Annahmewerte, unkalibriert)"),
    }


def reversal_loss(case: Case, dt=0.002) -> float:
    """Zeitverlust durch Richtungswechsel = t(4 Durchfahrten) - 4 * t(fliegende Durchfahrt)."""
    one = replace(case, track=replace(case.track, legs=1))
    r4 = simulate_batch([case], dt=dt)
    # "fliegend": Einfahrt mit der Beharrungs-Endgeschwindigkeit der Vorrunde ist nicht definierbar;
    # Vergleichsgroesse ist daher die Zeit ohne Rueckprall-Verlust und ohne Totzeit
    ideal = replace(case, rev=replace(case.rev, restitution=1.0, t_switch=0.0))
    ri = simulate_batch([ideal], dt=dt)
    return float(r4["t_total"][0] - ri["t_total"][0])


def plots(case: Case, tag: str, plt):
    res = simulate_batch([case], dt=0.001, record=True)
    h = res["hist"]
    t, v, x, f, leg = h["t"][:, 0], h["v"][:, 0], h["x"][:, 0], h["f"][:, 0], h["leg"][:, 0]
    n = int(np.searchsorted(t, res["t_total"][0])) if res["status"][0] == 0 else len(t)
    t, v, x, f, leg = t[:n], v[:n], x[:n], f[:n], leg[:n]
    tr = case.track
    t0, t1 = tr.tunnel_center - tr.tunnel_len / 2, tr.tunnel_center + tr.tunnel_len / 2
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    ax = axes[0, 0]
    ax.plot(t, v)
    ax.set_xlabel("Zeit [s]"); ax.set_ylabel("Geschwindigkeit [m/s] (Vorzeichen = Fahrtrichtung)")
    ax.set_title("Geschwindigkeit über der Zeit"); ax.grid(alpha=0.3)
    ax = axes[0, 1]
    for k in range(tr.legs):
        m = leg == k
        ax.plot(x[m], np.abs(v[m]), label=f"Durchfahrt {k+1}")
    ax.axvspan(t0, t1, color="k", alpha=0.12, label="Tunnel (Annahme: Bahnmitte)")
    ax.set_xlabel("Bahnposition Fahrzeugmitte [m]"); ax.set_ylabel("|v| [m/s]")
    ax.set_title("Geschwindigkeit über der Strecke"); ax.grid(alpha=0.3); ax.legend(fontsize=8)
    ax = axes[1, 0]
    a = np.gradient(v, t)
    ax.plot(t, np.clip(a, -15, 15), lw=0.8)
    ax.set_xlabel("Zeit [s]"); ax.set_ylabel("Beschleunigung [m/s²] (begrenzt auf ±15)")
    ax.set_title("Beschleunigung (Spitzen = Aufprall/Rückprall)"); ax.grid(alpha=0.3)
    ax = axes[1, 1]
    p_drive = f * np.abs(v)
    mp = case.gen.mpp(case.light.g, case.light.g, case.light.t_cell)["P_mpp"]
    ax.plot(t, p_drive, label="Fahrleistung F·v am Rad")
    ax.axhline(mp, color="orange", ls="--", label=f"Solar-MPP {mp:.2f} W (Modell)")
    ax.set_xlabel("Zeit [s]"); ax.set_ylabel("Leistung [W]")
    ax.set_title("Solarleistung und Fahrleistung"); ax.grid(alpha=0.3); ax.legend(fontsize=8)
    fig.suptitle(f"Rennsimulation {tag}: {case.motor.name}, {case.gen.config}, i = {case.veh.gear_ratio:g}, "
                 f"{case.light.g:.0f} W/m² – Gesamtzeit {res['t_total'][0]:.2f} s (SIMULATION)")
    fig.tight_layout()
    fig.savefig(OUT_D / f"rennen_{tag}.png", dpi=125)
    plt.close(fig)
    return res


def operating_point_plot(case_sun: Case, case_weak: Case, plt):
    """Arbeitspunkt Solargenerator <-> Motor ueber der Fahrgeschwindigkeit."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    for case, ls in ((case_sun, "-"), (case_weak, "--")):
        veh, mot = case.veh, case.motor
        v = np.linspace(0, steady_speed(veh, mot, case.gen, case.light) * 1.05 + 0.2, 300)
        f, i, ug, um, om, ms = drive_force(veh, mot, case.gen, v, case.light.g, case.light.g, case.light.t_cell, True)
        lab = f"{case.light.name}, {case.gen.config}"
        axes[0].plot(v, um, ls, label=f"U_Motor ({lab})")
        axes[0].plot(v, i * 10, ls, alpha=0.6, label=f"10 × I ({lab})")
        axes[1].plot(v, f, ls, label=f"Zugkraft ({lab})")
        axes[1].plot(v, resistance(veh, v), ":", color="gray")
        p_el = ug * i
        with np.errstate(divide="ignore", invalid="ignore"):
            eta = np.where(p_el > 1e-6, f * v / p_el, 0)
        axes[2].plot(v, np.clip(eta, 0, 1) * 100, ls, label=f"Gesamtwirkungsgrad Rad/Generator ({lab})")
        axes[2].plot(v, np.clip(np.where(um * i > 1e-6, ms * om / (um * i), 0), 0, 1) * 100, ls, alpha=0.5,
                     label=f"Motorwirkungsgrad ({lab})")
    axes[0].axhline(case_sun.motor.u_max, color="r", lw=0.8); axes[0].text(0.05, case_sun.motor.u_max + 0.1, "U_max Motor", color="r", fontsize=8)
    axes[0].set_xlabel("v [m/s]"); axes[0].set_ylabel("Spannung [V] bzw. 10·Strom [A]"); axes[0].set_title("Elektrischer Arbeitspunkt")
    axes[1].set_xlabel("v [m/s]"); axes[1].set_ylabel("Kraft [N]"); axes[1].set_title("Zugkraft und Fahrwiderstand (grau)")
    axes[2].set_xlabel("v [m/s]"); axes[2].set_ylabel("[%]"); axes[2].set_title("Wirkungsgrade")
    for ax in axes:
        ax.grid(alpha=0.3); ax.legend(fontsize=7)
    fig.suptitle("Gemeinsamer Arbeitspunkt Solargenerator – Motor (berechnet; Solarmodulwerte = Annahme)")
    fig.tight_layout()
    fig.savefig(OUT_D / "arbeitspunkt_solar_motor.png", dpi=125)
    plt.close(fig)


def mass_plot(args, plt):
    masses = np.linspace(0.10, 0.32, 12)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    rows = []
    for sc in ("sonne", "kunstlicht"):
        base = build_case(args, sc)
        ts, a0s = [], []
        for m in masses:
            best_t, best_a = np.nan, np.nan
            cases = [replace(base, veh=replace(base.veh, mass=float(m), gear_ratio=float(i))) for i in np.arange(2.5, 8.01, 0.5)]
            r = simulate_batch(cases, dt=0.004)
            if np.any(np.isfinite(r["t_total"])):
                j = int(np.nanargmin(r["t_total"]))
                c = cases[j]
                f0 = float(drive_force(c.veh, c.motor, c.gen, 0.0, c.light.g, c.light.g, c.light.t_cell))
                best_t, best_a = float(r["t_total"][j]), (f0 - float(resistance(c.veh, 0.0))) / effective_mass(c.veh, c.motor)
                rows.append({"Szenario": sc, "Masse_g": round(m * 1000), "i_opt": c.veh.gear_ratio, "t_gesamt_s": round(best_t, 2),
                             "a_Start_m_s2": round(best_a, 2)})
            ts.append(best_t); a0s.append(best_a)
        axes[0].plot(masses * 1000, ts, marker="o", label=sc)
        axes[1].plot(masses * 1000, a0s, marker="o", label=sc)
    for ax, yl, tt in ((axes[0], "Gesamtzeit [s] (i jeweils optimiert)", "Gesamtmasse und Rennzeit"),
                       (axes[1], "Anfahrbeschleunigung [m/s²]", "Gesamtmasse und Beschleunigung")):
        ax.axvline(BASE_VEHICLE.mass * 1000, color="gray", ls=":")
        ax.set_xlabel("Fahrzeugmasse [g]"); ax.set_ylabel(yl); ax.set_title(tt); ax.grid(alpha=0.3); ax.legend()
    fig.suptitle("Einfluss der Fahrzeugmasse (Simulation; gepunktet = Konstruktionsstand)")
    fig.tight_layout()
    fig.savefig(OUT_D / "masse_beschleunigung_rennzeit.png", dpi=125)
    plt.close(fig)
    write_csv(OUT_C / "masseneinfluss.csv", rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--szenario", choices=list(SCENARIOS), help="nur dieses Szenario")
    ap.add_argument("--verschaltung", choices=["4s", "2s2p", "4p", "2s", "2p"])
    ap.add_argument("--motor", help="Motorname aus motor_model.MOTOR_SPECS")
    ap.add_argument("--i", type=float, help="Getriebeuebersetzung")
    ap.add_argument("--rad", type=float, help="Raddurchmesser [m]")
    ap.add_argument("--masse", type=float, help="Fahrzeugmasse [kg]")
    ap.add_argument("--licht", type=float, help="Bestrahlungsstaerke [W/m^2]")
    ap.add_argument("--tunnellicht", type=float, help="Restlichtanteil im Tunnel (0..1)")
    ap.add_argument("--tunnel", type=float, help="Tunnellaenge [m]")
    ap.add_argument("--eta", type=float, help="Getriebewirkungsgrad")
    ap.add_argument("--crr", type=float, help="Rollwiderstandsbeiwert")
    ap.add_argument("--mu", type=float, help="Haftreibungszahl Antriebsraeder")
    ap.add_argument("--t-schalt", dest="t_schalt", type=float, help="Umschalt-Totzeit [s]")
    ap.add_argument("--rueckprall", type=float, help="Rueckprallzahl 0..1")
    ap.add_argument("--mc", type=int, default=400, help="Monte-Carlo-Stichprobe je Szenario (0 = aus)")
    ap.add_argument("--keine-diagramme", action="store_true")
    args = ap.parse_args()

    OUT_D.mkdir(parents=True, exist_ok=True)
    OUT_C.mkdir(parents=True, exist_ok=True)
    scen = [args.szenario] if args.szenario else list(SCENARIOS)
    # Abweichungen von der Auslegung werden unter eigenem Namen gespeichert (ueberschreiben die Auslegungstabellen nicht)
    custom = any(v is not None for v in (args.szenario, args.verschaltung, args.motor, args.i, args.rad, args.masse, args.licht,
                                         args.tunnellicht, args.tunnel, args.eta, args.crr, args.mu, args.t_schalt, args.rueckprall))
    sfx = "_variante" if custom else ""
    rows, mc_rows, var_rows = [], [], []
    plt = None
    if not args.keine_diagramme:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

    for sc in scen:
        case = build_case(args, sc)
        res = plots(case, sc + sfx, plt) if plt else simulate_batch([case], dt=0.001)
        row = summarize(sc, case, res)
        row["Zeitverlust_Richtungswechsel_s"] = round(reversal_loss(case), 2) if res["status"][0] == 0 else ""
        rows.append(row)
        print(f"\n== {sc}: {row['Motor']}, {row['Verschaltung']}, i = {row['i']:g} ==")
        for k, v in row.items():
            print(f"   {k:32s} {v}")
        # alle drei Getriebevarianten
        for vname, (z1, z2) in DESIGN["gear_pairs"].items():
            c = build_case(args, sc, ratio=z2 / z1)
            r = simulate_batch([c], dt=0.002)
            s = summarize(sc, c, r)
            s = {"Variante": f"V{vname} {z1}:{z2}", **s}
            var_rows.append(s)
        if args.mc:
            rng = np.random.default_rng(7)
            cases = sample_cases(case, args.mc, rng)
            r = simulate_batch(cases, dt=0.004)
            ok = r["status"] == 0
            tt = r["t_total"][ok]
            vi = np.nanmax(np.where(np.isfinite(r["v_impact"]), r["v_impact"], -1), axis=1)
            mc_rows.append({
                "Szenario": sc, "Verschaltung": case.gen.config, "i": case.veh.gear_ratio, "n": args.mc,
                "Zieleinlauf_%": round(100 * ok.mean(), 1),
                "t_P10_s": round(float(np.percentile(tt, 10)), 2) if ok.any() else "",
                "t_Median_s": round(float(np.median(tt)), 2) if ok.any() else "",
                "t_P90_s": round(float(np.percentile(tt, 90)), 2) if ok.any() else "",
                "v_Aufprall_P90_m_s": round(float(np.percentile(vi[ok], 90)), 2) if ok.any() else "",
                "kein_Anlauf_%": round(100 * float(np.mean(r["status"] == 1)), 1),
                "Stillstand_Strecke/Tunnel_%": round(100 * float(np.mean(r["status"] == 2)), 1),
                "kein_Umschalten_%": round(100 * float(np.mean(r["status"] == 3)), 1),
            })
            print("   Monte-Carlo:", mc_rows[-1])

    write_csv(OUT_C / f"rennsimulation_auslegung{sfx}.csv", rows)
    write_csv(OUT_C / f"rennsimulation_getriebevarianten{sfx}.csv", var_rows)
    if mc_rows:
        write_csv(OUT_C / f"rennsimulation_unsicherheit{sfx}.csv", mc_rows)
    print("\n== Getriebevarianten ==")
    for s in var_rows:
        print(f"   {s['Variante']:10s} {s['Szenario']:10s} {s['Verschaltung']:5s} F0={s['Anfahrkraft_N']} N  a0={s['a_Start_m_s2']}  "
              f"v_Beh={s['v_Beharrung_m_s']}  v_max={s['v_max_Rennen_m_s']}  t1={s['t_Durchfahrt_1_s']}  t={s['t_gesamt_s']}  "
              f"v_Aufprall={s['v_Aufprall_max_m_s']}  {s['Status']}")
    if plt and not custom:
        operating_point_plot(build_case(args, "sonne"), build_case(args, "kunstlicht"), plt)
        mass_plot(args, plt)
    print("\nTabellen ->", OUT_C, "\nDiagramme ->", OUT_D)


if __name__ == "__main__":
    main()
