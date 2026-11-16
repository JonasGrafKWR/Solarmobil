"""Numerische Optimierung von Motor, Verschaltung und Getriebeuebersetzung.

Aufruf:   python gear_optimizer.py            (alle Studien, ca. 1-2 min)
          python gear_optimizer.py --quick    (grobes Raster)

Ergebnisse:  results/comparisons/*.csv,  results/diagrams/*.png

Alle Zeiten sind SIMULIERT (kein Messergebnis).  Zielgroesse ist die
Gesamtzeit fuer vier Durchfahrten inklusive dreier Richtungswechsel.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import replace
import pathlib

import numpy as np

from motor_model import load_motors, RPM
from solar_model import Generator, SolarModule, SCENARIOS, solve_operating_point
from vehicle_model import (Case, VehicleParams, TrackParams, ReversalParams, simulate_batch,
                           steady_speed, start_margin, drive_force, resistance, effective_mass,
                           STATUS_TEXT, G0)
import gear_geometry as gg

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_C = ROOT / "results" / "comparisons"
OUT_D = ROOT / "results" / "diagrams"

# Auslegungs-Basis (wird durch params.BASE ueberschrieben, wenn vorhanden)
try:
    from params import BASE_VEHICLE, BASE_MODULE, BASE_TRACK, BASE_REV, DESIGN
except Exception:                                    # pragma: no cover
    BASE_VEHICLE, BASE_MODULE, BASE_TRACK, BASE_REV = VehicleParams(), SolarModule(), TrackParams(), ReversalParams()
    DESIGN = {"motor": "FF-130SH-14230"}


def write_csv(path: pathlib.Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(rows)


def make_case(motor, cfg, sc, ratio, veh=None, module=None, track=None, rev=None, **veh_kw):
    veh = replace(veh or BASE_VEHICLE, gear_ratio=float(ratio), **veh_kw)
    return Case(veh, motor, Generator(module or BASE_MODULE, cfg), SCENARIOS[sc] if isinstance(sc, str) else sc,
                track or BASE_TRACK, rev or BASE_REV)


def u_motor_at(case: Case, v: float) -> float:
    """Motorspannung bei Geschwindigkeit v und voller Beleuchtung."""
    r = case.veh.wheel_d / 2
    _, _, um = solve_operating_point(case.gen, case.motor, np.array(v * case.veh.gear_ratio / r),
                                     case.light.g, case.light.g, case.light.t_cell,
                                     case.veh.n_motors, case.veh.r_wiring)
    return float(um)


# ----------------------------------------------------------------------------
# Studie 1: Motor x Verschaltung x Licht, Uebersetzung jeweils optimiert
# ----------------------------------------------------------------------------
def study_motor_matrix(ratios, dt):
    motors = load_motors()
    rows, cases, keys = [], [], []
    for mname, mot in motors.items():
        if mname.endswith("@2V"):
            continue                       # gleiche Wicklung wie @3V
        for cfg in ("4s", "2s2p", "4p"):
            for sc in SCENARIOS:
                for i in ratios:
                    cases.append(make_case(mot, cfg, sc, i))
                    keys.append((mname, cfg, sc, i))
    res = simulate_batch(cases, dt=dt)
    t = res["t_total"]
    best = {}
    for j, (mname, cfg, sc, i) in enumerate(keys):
        key = (mname, cfg, sc)
        if np.isfinite(t[j]) and (key not in best or t[j] < t[best[key]]):
            best[key] = j
    for mname, mot in motors.items():
        if mname.endswith("@2V"):
            continue
        for cfg in ("4s", "2s2p", "4p"):
            for sc in SCENARIOS:
                key = (mname, cfg, sc)
                if key not in best:
                    rows.append({"Motor": mname, "Verschaltung": cfg, "Szenario": sc, "i_opt": "", "t_gesamt_s": "",
                                 "v_max_m_s": "", "v_Aufprall_max_m_s": "", "U_Motor_max_V": "",
                                 "U_im_Bereich": "", "Status": "kein Zieleinlauf im Raster"})
                    continue
                j = best[key]
                um = u_motor_at(cases[j], res["v_max"][j])
                rows.append({
                    "Motor": mname, "Verschaltung": cfg, "Szenario": sc, "i_opt": keys[j][3],
                    "t_gesamt_s": round(float(t[j]), 2), "v_max_m_s": round(float(res["v_max"][j]), 2),
                    "v_Aufprall_max_m_s": round(float(np.nanmax(res["v_impact"][j])), 2),
                    "U_Motor_max_V": round(um, 2),
                    "U_im_Bereich": "ja" if um <= mot.u_max * 1.02 else f"NEIN (>{mot.u_max:g} V)",
                    "Status": STATUS_TEXT[0],
                })
    write_csv(OUT_C / "motor_verschaltung_matrix.csv", rows)
    return rows


# ----------------------------------------------------------------------------
# Studie 2: Uebersetzungs-Sweep fuer die Auslegung (inkl. Kennwerten)
# ----------------------------------------------------------------------------
def study_ratio_sweep(motor, combos, ratios, dt):
    rows = []
    curves = {}
    for cfg, sc in combos:
        cases = [make_case(motor, cfg, sc, i) for i in ratios]
        res = simulate_batch(cases, dt=dt)
        curves[(cfg, sc)] = res["t_total"].copy()
        for j, i in enumerate(ratios):
            c = cases[j]
            r = c.veh.wheel_d / 2
            f0 = float(drive_force(c.veh, motor, c.gen, 0.0, c.light.g, c.light.g, c.light.t_cell))
            vss = steady_speed(c.veh, motor, c.gen, c.light)
            v_theo = motor.omega_noload(c.gen.u_oc(c.light.g, c.light.t_cell)) / i * r
            a0 = (f0 - float(resistance(c.veh, 0.0))) / effective_mass(c.veh, motor)
            rows.append({
                "Verschaltung": cfg, "Szenario": sc, "i": round(float(i), 2),
                "Anfahrkraft_N": round(f0, 3), "Anfahrreserve": round(start_margin(c.veh, motor, c.gen, c.light), 2),
                "a_Start_m_s2": round(a0, 2),
                "v_theor_Leerlauf_m_s": round(v_theo, 2), "v_Beharrung_m_s": round(vss, 2),
                "v_max_im_Rennen_m_s": round(float(res["v_max"][j]), 2),
                "t_Durchfahrt_1_s": round(float(res["t_leg"][j, 0]), 2) if np.isfinite(res["t_leg"][j, 0]) else "",
                "t_gesamt_s": round(float(res["t_total"][j]), 2) if res["status"][j] == 0 else "",
                "v_Aufprall_max_m_s": round(float(np.nanmax(res["v_impact"][j])), 2) if res["status"][j] == 0 else "",
                "v_Tunnel_min_m_s": round(float(res["v_tunnel_min"][j]), 2) if np.isfinite(res["v_tunnel_min"][j]) else "",
                "Status": STATUS_TEXT[int(res["status"][j])],
            })
    write_csv(OUT_C / "uebersetzung_sweep.csv", rows)
    return rows, curves


# ----------------------------------------------------------------------------
# Studie 3: Raddurchmesser x Uebersetzung
# ----------------------------------------------------------------------------
def study_wheel_ratio(motor, cfg, sc, diameters, ratios, dt):
    cases, keys = [], []
    for d in diameters:
        # Radtraegheit ~ d^2 * Masse(d) ~ d^3 (Felge + O-Ring skaliert)
        jw = BASE_VEHICLE.j_wheels * (d / BASE_VEHICLE.wheel_d) ** 3
        for i in ratios:
            cases.append(make_case(motor, cfg, sc, i, wheel_d=d, j_wheels=jw))
            keys.append((d, i))
    res = simulate_batch(cases, dt=dt)
    T = res["t_total"].reshape(len(diameters), len(ratios))
    rows = []
    for a, d in enumerate(diameters):
        if np.all(np.isnan(T[a])):
            continue
        b = int(np.nanargmin(T[a]))
        rows.append({"Verschaltung": cfg, "Szenario": sc, "Rad_d_mm": round(d * 1000), "i_opt": round(float(ratios[b]), 2),
                     "i_opt/r_1_mm": round(float(ratios[b]) / (d * 500), 3), "t_gesamt_s": round(float(T[a, b]), 2),
                     "Achse_ueber_Schiene": "ja" if d * 500 - 1.5 >= 15 + 3 else "NEIN (Portal-/Stummelachse noetig)"})
    return T, rows


# ----------------------------------------------------------------------------
# Studie 4: Unsicherheiten (Monte-Carlo)
# ----------------------------------------------------------------------------
def sample_cases(base: Case, n: int, rng: np.random.Generator) -> list[Case]:
    """Zieht n Parametersaetze innerhalb der angenommenen Unsicherheitsbereiche."""
    out = []
    for _ in range(n):
        f_light = rng.triangular(0.75, 1.0, 1.20)            # Bestrahlung / Modulstrom
        mod = replace(base.gen.module, i_sc=base.gen.module.i_sc * rng.uniform(0.85, 1.10),
                      n_ideal=rng.uniform(1.7, 2.4))          # Fuellfaktor ca. 0,66-0,76
        light = replace(base.light, g=base.light.g * f_light, tunnel_light=rng.uniform(0.0, 0.10),
                        ripple=base.light.ripple * rng.uniform(0.5, 1.5))
        veh = replace(base.veh, mass=base.veh.mass * rng.uniform(0.90, 1.12), crr=rng.uniform(0.010, 0.035),
                      eta_gear=rng.uniform(0.78, 0.94), f_const=rng.uniform(0.0, 0.03),
                      cda=base.veh.cda * rng.uniform(0.7, 1.4), mu_traction=rng.uniform(0.4, 0.8),
                      r_wiring=rng.uniform(0.1, 0.5))
        # Motorstreuung: k und R jeweils +-7 %
        mot = replace(base.motor, R=base.motor.R * rng.uniform(0.93, 1.07), k=base.motor.k * rng.uniform(0.93, 1.07),
                      m_fric=base.motor.m_fric * rng.uniform(0.8, 1.4))
        rev = replace(base.rev, restitution=rng.uniform(0.10, 0.50), t_switch=rng.uniform(0.01, 0.08))
        track = replace(base.track, tunnel_center=rng.uniform(4.0, 6.0))
        out.append(Case(veh, mot, replace(base.gen, module=mod), light, track, rev))
    return out


def study_uncertainty(motor, combos, ratios, n, dt, seed=1):
    rows = []
    for cfg, sc in combos:
        for i in ratios:
            rng = np.random.default_rng(seed)        # gleiche Stichprobe fuer jede Uebersetzung
            cases = sample_cases(make_case(motor, cfg, sc, i), n, rng)
            res = simulate_batch(cases, dt=dt)
            ok = res["status"] == 0
            t = res["t_total"][ok]
            vi = np.nanmax(res["v_impact"], axis=1)
            rows.append({
                "Verschaltung": cfg, "Szenario": sc, "i": round(float(i), 2), "n": n,
                "Ausfallquote_%": round(100 * (1 - ok.mean()), 1),
                "t_median_s": round(float(np.median(t)), 2) if ok.any() else "",
                "t_P10_s": round(float(np.percentile(t, 10)), 2) if ok.any() else "",
                "t_P90_s": round(float(np.percentile(t, 90)), 2) if ok.any() else "",
                "v_Aufprall_P90_m_s": round(float(np.nanpercentile(vi, 90)), 2) if ok.any() else "",
                "Anteil_kein_Anlauf_%": round(100 * float(np.mean(res["status"] == 1)), 1),
                "Anteil_Tunnel/Strecke_%": round(100 * float(np.mean(res["status"] == 2)), 1),
                "Anteil_kein_Umschalten_%": round(100 * float(np.mean(res["status"] == 3)), 1),
            })
    write_csv(OUT_C / "uebersetzung_unsicherheit.csv", rows)
    return rows


# ----------------------------------------------------------------------------
# Studie 5: Konzeptvergleich
# ----------------------------------------------------------------------------
def study_concepts(ratios, dt):
    motors = load_motors()
    mot = motors[DESIGN["motor"]]
    kit = motors["RF300CA-11400@3V"]
    light_mod = replace(BASE_MODULE, mass=0.008)     # ANNAHME: laminierte Einzelzellen, 8 g je "Modul"
    base_m = BASE_VEHICLE.mass
    d_light = 4 * (BASE_MODULE.mass - light_mod.mass)
    concepts = {
        "A  1 Motor FF-130SH-14230, Heckantrieb, Stirnrad (Basis)": dict(motor=mot),
        "A' wie A, aber Starterkit-Motor RF300CA-11400": dict(motor=kit, mass=base_m - 0.002),
        "B  1 Motor, Leichtbau-Chassis (-15 g), Riemen eta 0,92": dict(motor=mot, mass=base_m - 0.015, eta_gear=0.92),
        "C  2 Motoren FF-130SH-14230 (Allrad, +30 g)": dict(motor=mot, mass=base_m + 0.030, n_motors=2,
                                                            driven_load_frac=1.0, f_const=0.015),
        "D  wie A, nur 2 Module in Reihe (-72 g)": dict(motor=mot, mass=base_m - 2 * BASE_MODULE.mass, cfgs=("2s", "2p")),
        "E  wie A, Leichtbau-Zellen statt Kit-Module": dict(motor=mot, mass=base_m - d_light, module=light_mod),
    }
    rows = []
    for cname, kw in concepts.items():
        kw = dict(kw)
        motor = kw.pop("motor")
        cfgs = kw.pop("cfgs", ("4s", "2s2p"))
        module = kw.pop("module", None)
        for sc in SCENARIOS:
            best = None
            for cfg in cfgs:
                cases = [make_case(motor, cfg, sc, i, module=module, **kw) for i in ratios]
                res = simulate_batch(cases, dt=dt)
                if np.all(np.isnan(res["t_total"])):
                    continue
                j = int(np.nanargmin(res["t_total"]))
                if best is None or res["t_total"][j] < best[0]:
                    c = cases[j]
                    f0 = float(drive_force(c.veh, motor, c.gen, 0.0, c.light.g, c.light.g, c.light.t_cell))
                    best = (float(res["t_total"][j]), cfg, float(ratios[j]), float(res["v_max"][j]),
                            float(np.nanmax(res["v_impact"][j])), c.veh.mass, f0,
                            (f0 - float(resistance(c.veh, 0.0))) / effective_mass(c.veh, motor),
                            start_margin(c.veh, motor, c.gen, c.light))
            if best is None:
                rows.append({"Konzept": cname, "Szenario": sc, "Masse_g": round(kw.get("mass", base_m) * 1000),
                             "beste_Verschaltung": "-", "i_opt": "", "t_gesamt_s": "", "v_max_m_s": "",
                             "v_Aufprall_m_s": "", "Anfahrkraft_N": "", "a_Start_m_s2": "", "Anfahrreserve": ""})
            else:
                rows.append({"Konzept": cname, "Szenario": sc, "Masse_g": round(best[5] * 1000),
                             "beste_Verschaltung": best[1], "i_opt": round(best[2], 2), "t_gesamt_s": round(best[0], 2),
                             "v_max_m_s": round(best[3], 2), "v_Aufprall_m_s": round(best[4], 2),
                             "Anfahrkraft_N": round(best[6], 3), "a_Start_m_s2": round(best[7], 2),
                             "Anfahrreserve": round(best[8], 2)})
    write_csv(OUT_C / "konzeptvergleich_simulation.csv", rows)
    return rows


# ----------------------------------------------------------------------------
# Konkrete Zahnradpaare
# ----------------------------------------------------------------------------
def gear_variants(module_mm: float, z_sum: int, targets: dict[str, float], wheel_d_mm: float,
                  ground_clear_mm: float = 3.0, z1_min: int = 10):
    rows = []
    for name, i_t in targets.items():
        best = None
        for z1 in range(z1_min, 30):
            z2 = z_sum - z1
            if z2 <= z1:
                break
            if best is None or abs(z2 / z1 - i_t) < abs(best[1] / best[0] - i_t):
                best = (z1, z2)
        rep = gg.pair_report(module_mm, *best)
        rep = {"Variante": name, "i_Ziel": round(i_t, 2), **rep}
        rep["Bodenfreiheit_Rad2_mm"] = round(wheel_d_mm / 2 - rep["da2_mm"] / 2, 2)
        rep["passt_unter_Achse"] = "ja" if rep["Bodenfreiheit_Rad2_mm"] >= ground_clear_mm else "NEIN"
        rows.append(rep)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--n-mc", type=int, default=300)
    args = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    OUT_C.mkdir(parents=True, exist_ok=True)
    OUT_D.mkdir(parents=True, exist_ok=True)
    dt = 0.005 if args.quick else 0.003
    ratios = np.round(np.arange(2.0, 10.01, 1.0 if args.quick else 0.5), 2)
    motors = load_motors()
    mot = motors[DESIGN["motor"]]

    print("== Studie 1: Motor x Verschaltung x Licht ==")
    rows = study_motor_matrix(ratios, dt)
    for sc in SCENARIOS:
        top = sorted([r for r in rows if r["Szenario"] == sc and r["t_gesamt_s"] != ""], key=lambda r: r["t_gesamt_s"])[:6]
        print(f"-- {sc}: beste Kombinationen")
        for r in top:
            print(f"   {r['Motor']:18s} {r['Verschaltung']:5s} i={r['i_opt']:<4} t={r['t_gesamt_s']:6.2f} s  "
                  f"v_max={r['v_max_m_s']} m/s  U_mot={r['U_Motor_max_V']} V  im Bereich: {r['U_im_Bereich']}")

    print("\n== Studie 2: Uebersetzungs-Sweep", mot.name, "==")
    combos = [("4s", "sonne"), ("2s2p", "sonne"), ("2s2p", "bewoelkt"), ("2s2p", "kunstlicht"), ("4s", "kunstlicht")]
    fine = np.round(np.arange(2.0, 10.01, 0.5 if args.quick else 0.25), 2)
    _, curves = study_ratio_sweep(mot, combos, fine, dt)
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for (cfg, sc), t in curves.items():
        ax.plot(fine, t, marker=".", label=f"{sc}, {cfg}")
        if np.any(np.isfinite(t)):
            j = int(np.nanargmin(t))
            ax.plot(fine[j], t[j], "k*", ms=11)
            print(f"   {sc:10s} {cfg:5s}: i_opt = {fine[j]:.2f}, t = {t[j]:.2f} s")
    ax.set_xlabel("Übersetzung i = n_Motor / n_Rad  (Rad Ø %.0f mm)" % (BASE_VEHICLE.wheel_d * 1000))
    ax.set_ylabel("simulierte Gesamtzeit 4 Durchfahrten [s]")
    ax.set_title(f"Streckenzeit über der Übersetzung – {mot.name} (Simulation, Stern = Optimum)")
    ax.set_ylim(8, 60)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_D / "streckenzeit_ueber_uebersetzung.png", dpi=130)

    print("\n== Studie 3: Raddurchmesser ==")
    dias = np.array([0.020, 0.030, 0.040, 0.044, 0.050, 0.060])
    r3 = np.round(np.arange(1.0, 12.01, 0.5), 2)
    wr_rows = []
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, (cfg, sc) in zip(axes, (("4s", "sonne"), ("2s2p", "kunstlicht"))):
        T, rr = study_wheel_ratio(mot, cfg, sc, dias, r3, dt)
        wr_rows += rr
        for a, d in enumerate(dias):
            ax.plot(r3, T[a], label=f"Rad Ø {d*1000:.0f} mm")
        ax.set_title(f"{sc}, {cfg}")
        ax.set_xlabel("Übersetzung i")
        ax.set_ylabel("Gesamtzeit [s]")
        ax.set_ylim(8, 60)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle("Raddurchmesser und Übersetzung (Simulation): entscheidend ist das Verhältnis i / r")
    fig.tight_layout()
    fig.savefig(OUT_D / "raddurchmesser_uebersetzung.png", dpi=130)
    write_csv(OUT_C / "raddurchmesser_optimum.csv", wr_rows)
    for r in wr_rows:
        print("  ", r)

    print("\n== Studie 4: Unsicherheiten (Monte-Carlo, n = %d) ==" % args.n_mc)
    mc_r = np.array([3.0, 4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0])
    mc_rows = study_uncertainty(mot, [("4s", "sonne"), ("2s2p", "bewoelkt"), ("2s2p", "kunstlicht"), ("4s", "kunstlicht")],
                                mc_r, 80 if args.quick else args.n_mc, 0.005)
    for r in mc_rows:
        print(f"   {r['Szenario']:10s} {r['Verschaltung']:5s} i={r['i']:<4}: Ausfall {r['Ausfallquote_%']:5.1f} %  "
              f"t50={r['t_median_s']}  t90={r['t_P90_s']}  v_Aufprall90={r['v_Aufprall_P90_m_s']}")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    for key in sorted({(r["Verschaltung"], r["Szenario"]) for r in mc_rows}):
        sel = [r for r in mc_rows if (r["Verschaltung"], r["Szenario"]) == key and r["t_median_s"] != ""]
        if not sel:
            continue
        x = [r["i"] for r in sel]
        axes[0].fill_between(x, [r["t_P10_s"] for r in sel], [r["t_P90_s"] for r in sel], alpha=0.2)
        axes[0].plot(x, [r["t_median_s"] for r in sel], marker="o", label=f"{key[1]}, {key[0]}")
        selall = [r for r in mc_rows if (r["Verschaltung"], r["Szenario"]) == key]
        axes[1].plot([r["i"] for r in selall], [r["Ausfallquote_%"] for r in selall], marker="o", label=f"{key[1]}, {key[0]}")
    axes[0].set_xlabel("Übersetzung i"); axes[0].set_ylabel("Gesamtzeit [s] (Median, Band P10–P90)")
    axes[0].set_ylim(8, 60); axes[0].grid(alpha=0.3); axes[0].legend(fontsize=8)
    axes[1].set_xlabel("Übersetzung i"); axes[1].set_ylabel("Ausfallquote [%]"); axes[1].grid(alpha=0.3); axes[1].legend(fontsize=8)
    fig.suptitle("Einfluss der Unsicherheiten (Monte-Carlo-Simulation, Annahmen siehe sample_cases)")
    fig.tight_layout()
    fig.savefig(OUT_D / "unsicherheit_uebersetzung.png", dpi=130)

    print("\n== Studie 5: Konzeptvergleich ==")
    for r in study_concepts(ratios, dt):
        print(f"   {r['Konzept'][:52]:52s} {r['Szenario']:10s} m={r['Masse_g']} g  {r['beste_Verschaltung']:5s} "
              f"i={r['i_opt']}  t={r['t_gesamt_s']} s  a0={r['a_Start_m_s2']}  v_Aufprall={r['v_Aufprall_m_s']}")

    print("\n== Zahnradvarianten ==")
    gv = gear_variants(DESIGN.get("gear_module", 0.7), DESIGN.get("z_sum", 72),
                       DESIGN.get("gear_targets", {"1 Schnell": 4.0, "2 Ausgewogen": 5.0, "3 Anfahrstark": 6.2}),
                       BASE_VEHICLE.wheel_d * 1000)
    write_csv(OUT_C / "zahnradvarianten.csv", gv)
    for r in gv:
        print("  ", r)


if __name__ == "__main__":
    main()
