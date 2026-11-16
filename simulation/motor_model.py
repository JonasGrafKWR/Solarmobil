"""Motormodell fuer RF-300- und FF-130-Gleichstrommotoren.

Quelle der Rohdaten (Herkunft "Datenblatt"):
  * quellen/RF300 Motoren Datenblatt.pdf          (Nostop, RF300-Serie)
  * quellen/Mabuchi_FF-130RH-SH_Datenblatt.pdf    (Mabuchi FF-130RH/SH)

Aus den Datenblattpunkten (Leerlauf, max. Wirkungsgrad, Blockieren) werden
per Ausgleichsrechnung drei physikalische Parameter bestimmt (Herkunft
"berechnet"):

    U = R*I + k*omega            (Ankerkreis, Induktivitaet vernachlaessigt)
    M = k*I - M_r                (Wellenmoment, M_r = konstantes Reibmoment)

Die Datenblattwerte gelten nur fuer die angegebene KONSTANTE Spannung.  Am
Solargenerator ist die Spannung lastabhaengig; deshalb wird der Arbeitspunkt
in vehicle_model.py gemeinsam mit der Solarkennlinie geloest.

Nicht im Datenblatt: Rotortraegheit.  Die hier eingetragenen Werte sind
ANNAHMEN (Groessenordnung typischer Kleinmotoren) und in der Fahrsimulation
nur von geringem Einfluss (siehe docs/berechnungen.md).
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy.optimize import least_squares

GCM = 9.80665e-5          # 1 g*cm in N*m
RPM = 2.0 * math.pi / 60  # 1 U/min in rad/s


@dataclass(frozen=True)
class MotorSpec:
    """Eine Zeile aus dem Datenblatt (alles bei U_nom = konstant)."""
    name: str
    series: str
    u_min: float
    u_max: float
    u_nom: float
    n0_rpm: float
    i0: float
    n_eta_rpm: float
    i_eta: float
    m_eta_gcm: float
    p_eta_w: float
    m_stall_gcm: float
    i_stall: float | None     # nur wenn im Datenblatt/Kennlinie angegeben
    mass_g: float
    j_rotor: float            # kg*m^2  -- ANNAHME
    source: str


_RF = "RF300 Motoren Datenblatt.pdf (Nostop)"
_FF = "Mabuchi FF-130RH/SH Datenblatt"
_J_RF300 = 4.0e-7   # ANNAHME: flacher Scheibenlaeufer, groesserer Durchmesser
_J_FF130 = 1.2e-7   # ANNAHME: 130er Dreinuter

MOTOR_SPECS: list[MotorSpec] = [
    MotorSpec("RF300CA-14270", "RF300", 0.5, 4.0, 1.9, 3450, 0.032, 2700, 0.120, 3.89, 0.110, 18.0, None, 22, _J_RF300, _RF),
    MotorSpec("RF300CA-11400@2V", "RF300", 0.7, 5.0, 2.0, 2400, 0.020, 1820, 0.062, 3.03, 0.057, 12.5, 0.195, 22, _J_RF300, _RF),
    MotorSpec("RF300CA-11400@3V", "RF300", 1.2, 6.0, 3.0, 3700, 0.018, 2970, 0.073, 3.80, 0.120, 20.0, None, 22, _J_RF300, _RF),
    MotorSpec("RF300CA-10460", "RF300", 0.8, 6.0, 3.2, 3350, 0.017, 2630, 0.062, 3.56, 0.096, 16.5, 0.225, 22, _J_RF300, _RF),
    MotorSpec("RF300CA-09550", "RF300", 1.0, 6.0, 3.0, 2700, 0.012, 2100, 0.042, 2.80, 0.060, 13.0, None, 22, _J_RF300, _RF),
    MotorSpec("RF300EA-1D390", "RF300", 2.8, 7.0, 3.9, 4400, 0.021, 3520, 0.084, 4.80, 0.170, 24.0, None, 22, _J_RF300, _RF),
    MotorSpec("RF300FA-11420", "RF300", 0.7, 5.0, 3.0, 2900, 0.017, 2320, 0.068, 4.30, 0.100, 22.0, None, 22, _J_RF300, _RF),
    MotorSpec("RF300FA-12350", "RF300", 1.5, 6.0, 3.0, 3500, 0.022, 2830, 0.093, 4.90, 0.140, 26.0, None, 22, _J_RF300, _RF),
    MotorSpec("RF300SA-12350", "RF300", 2.0, 6.0, 3.0, 3100, 0.027, 2450, 0.100, 6.10, 0.150, 29.0, None, 22, _J_RF300, _RF),
    MotorSpec("FF-130RH-15210", "FF130", 1.0, 4.0, 3.0, 5400, 0.045, 4280, 0.17, 5.8, 0.26, 28.0, 0.65, 24, _J_FF130, _FF),
    MotorSpec("FF-130SH-11340", "FF130", 3.0, 12.0, 7.5, 6100, 0.033, 4920, 0.14, 10.9, 0.55, 56.0, 0.57, 24, _J_FF130, _FF),
    MotorSpec("FF-130SH-14230", "FF130", 2.5, 10.0, 3.0, 3600, 0.037, 2850, 0.14, 7.5, 0.22, 36.0, 0.53, 24, _J_FF130, _FF),
]


@dataclass(frozen=True)
class Motor:
    """Identifiziertes Motormodell."""
    name: str
    series: str
    R: float        # Ohm
    k: float        # N*m/A  ==  V*s/rad
    m_fric: float   # N*m   konstantes Reibmoment
    u_min: float
    u_max: float
    mass: float     # kg
    j_rotor: float  # kg*m^2 (Annahme)
    fit_err: float  # groesster relativer Restfehler der Ausgleichsrechnung
    spec: MotorSpec

    # --- Kennlinien bei konstanter Klemmenspannung -------------------------
    def current(self, u, omega):
        return (np.asarray(u, float) - self.k * np.asarray(omega, float)) / self.R

    def torque(self, u, omega):
        """Wellenmoment bei Drehung in Antriebsrichtung (omega >= 0)."""
        return self.k * self.current(u, omega) - self.m_fric

    def omega_noload(self, u):
        return (u - self.m_fric / self.k * self.R) / self.k

    def stall_torque(self, u):
        return self.k * u / self.R - self.m_fric

    def stall_current(self, u):
        return u / self.R

    def p_mech(self, u, omega):
        return self.torque(u, omega) * np.asarray(omega, float)

    def efficiency(self, u, omega):
        i = self.current(u, omega)
        p_el = np.asarray(u, float) * i
        with np.errstate(divide="ignore", invalid="ignore"):
            eta = np.where(p_el > 0, self.p_mech(u, omega) / p_el, 0.0)
        return np.clip(eta, 0.0, 1.0)

    def p_mech_max(self, u):
        """Maximale mechanische Leistung bei konstanter Spannung u."""
        w0 = self.omega_noload(u)
        return 0.25 * self.stall_torque(u) * w0

    def start_current(self):
        """Mindeststrom, um das Reibmoment zu ueberwinden (Anlaufstrom)."""
        return self.m_fric / self.k


def identify(spec: MotorSpec) -> Motor:
    """Bestimmt R, k, M_r aus den Datenblattpunkten (kleinste Quadrate)."""
    u = spec.u_nom
    w0 = spec.n0_rpm * RPM
    w_eta = spec.n_eta_rpm * RPM
    m_eta = spec.m_eta_gcm * GCM
    m_st = spec.m_stall_gcm * GCM

    # Startwerte aus den einfachen Naeherungsformeln
    k0 = m_eta / max(spec.i_eta - spec.i0, 1e-6)
    i_st0 = spec.i_stall if spec.i_stall else spec.i0 + m_st / k0
    x0 = np.array([u / i_st0, k0, k0 * spec.i0])

    def resid(x):
        R, k, mf = x
        r = [
            ((u - (mf / k) * R) / k) / w0 - 1.0,            # Leerlaufdrehzahl
            (mf / k) / spec.i0 - 1.0,                       # Leerlaufstrom
            (k * u / R - mf) / m_st - 1.0,                  # Blockiermoment
            ((m_eta + mf) / k) / spec.i_eta - 1.0,          # Strom bei eta_max
            ((u - (m_eta + mf) / k * R) / k) / w_eta - 1.0  # Drehzahl bei eta_max
        ]
        if spec.i_stall:
            r.append((u / R) / spec.i_stall - 1.0)          # Blockierstrom
        return np.array(r)

    sol = least_squares(resid, x0, bounds=([0.1, 1e-4, 0.0], [200.0, 0.1, 1e-2]))
    R, k, mf = sol.x
    return Motor(spec.name, spec.series, float(R), float(k), float(mf),
                 spec.u_min, spec.u_max, spec.mass_g / 1000.0, spec.j_rotor,
                 float(np.max(np.abs(sol.fun))), spec)


def load_motors() -> dict[str, Motor]:
    return {s.name: identify(s) for s in MOTOR_SPECS}


def comparison_table(u_eval: float | None = None) -> list[dict]:
    """Vergleichstabelle; u_eval=None -> jeweils Nennspannung des Datenblatts."""
    rows = []
    for m in load_motors().values():
        u = m.spec.u_nom if u_eval is None else u_eval
        rows.append({
            "Motor": m.name,
            "U_Bereich_V": f"{m.u_min:g}-{m.u_max:g}",
            "U_V": u,
            "R_Ohm": round(m.R, 2),
            "k_mNm_A": round(m.k * 1e3, 2),
            "M_reib_mNm": round(m.m_fric * 1e3, 3),
            "I_anlauf_mA": round(m.start_current() * 1e3, 1),
            "n0_rpm": round(m.omega_noload(u) / RPM),
            "M_block_mNm": round(m.stall_torque(u) * 1e3, 2),
            "I_block_A": round(m.stall_current(u), 3),
            "P_mech_max_W": round(m.p_mech_max(u), 3),
            "eta_max_%": round(float(np.max(m.efficiency(u, np.linspace(0, m.omega_noload(u), 400)))) * 100, 1),
            "Masse_g": m.spec.mass_g,
            "Fit_Fehler_%": round(m.fit_err * 100, 1),
        })
    return rows


if __name__ == "__main__":
    import csv
    import pathlib
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    root = pathlib.Path(__file__).resolve().parents[1]
    out_c = root / "results" / "comparisons"
    out_d = root / "results" / "diagrams"
    out_c.mkdir(parents=True, exist_ok=True)
    out_d.mkdir(parents=True, exist_ok=True)

    for tag, u in (("nennspannung", None), ("bei_4V", 4.0)):
        rows = comparison_table(u)
        with open(out_c / f"motorvergleich_{tag}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter=";")
            w.writeheader()
            w.writerows(rows)
        print(f"\n== Motorvergleich ({tag}) ==")
        for r in rows:
            print("  ".join(f"{v!s:>9}" for v in r.values()))

    motors = load_motors()
    sel = ["RF300CA-11400@3V", "RF300CA-14270", "FF-130RH-15210", "FF-130SH-14230"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, name in zip(axes.ravel(), sel):
        m = motors[name]
        for u in (2.0, 4.0, 6.0, 8.0):
            if not (m.u_min <= u <= m.u_max):
                continue
            w = np.linspace(0, m.omega_noload(u), 200)
            ax.plot(m.torque(u, w) * 1e3, w / RPM, label=f"n bei {u:g} V")
        ax.set_title(f"{name}  (R={m.R:.1f} Ohm, k={m.k*1e3:.2f} mNm/A)")
        ax.set_xlabel("Drehmoment [mNm]")
        ax.set_ylabel("Drehzahl [1/min]")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle("Drehmoment-Drehzahl-Kennlinien bei KONSTANTER Spannung (berechnet aus Datenblatt)")
    fig.tight_layout()
    fig.savefig(out_d / "motor_drehmoment_drehzahl.png", dpi=130)

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, name in zip(axes.ravel(), sel):
        m = motors[name]
        u = min(max(4.0, m.u_min), m.u_max)
        w = np.linspace(0, m.omega_noload(u), 300)
        mm = m.torque(u, w) * 1e3
        ax.plot(mm, m.p_mech(u, w), label="P_mech [W]")
        ax.plot(mm, u * m.current(u, w), label="P_el [W]")
        ax2 = ax.twinx()
        ax2.plot(mm, m.efficiency(u, w) * 100, "g--", label="Wirkungsgrad [%]")
        ax2.set_ylim(0, 100)
        ax.set_title(f"{name} bei {u:g} V")
        ax.set_xlabel("Drehmoment [mNm]")
        ax.set_ylabel("Leistung [W]")
        ax2.set_ylabel("Wirkungsgrad [%]")
        ax.grid(alpha=0.3)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="upper center")
    fig.suptitle("Leistung und Wirkungsgrad bei konstanter Spannung (berechnet aus Datenblatt)")
    fig.tight_layout()
    fig.savefig(out_d / "motor_leistung_wirkungsgrad.png", dpi=130)
    print("\nDiagramme ->", out_d)
