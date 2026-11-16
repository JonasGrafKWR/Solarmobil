"""Elektrisches Modell des Solargenerators (Naeherungsmodell!).

WICHTIG -- Datenlage:
  Fuer die Starterkit-Solarzellen ("vier Solarzellen, jeweils 2 V und 0,6 A",
  Quelle: solarmobil-augsburg.de) liegt KEIN Datenblatt vor.  Unbekannt sind
  Hersteller, Kennlinie, Abmessungen und Masse.  Deshalb:

  * "2 V" wird als NENNspannung eines Moduls aus 4 Silizium-Zellen in Reihe
    interpretiert (4 x ca. 0,5 V).  Begruendung: eine einzelne Si-Zelle hat
    physikalisch nur ca. 0,55-0,62 V Leerlaufspannung; 2 V Leerlaufspannung
    waeren mit ganzen Zellen nicht darstellbar.  Vergleichsmodul mit
    Datenblatt: TRU Components POLY-PVZ-8080-2V -> Nennwerte 2 V / 0,4 A,
    Leerlauf 2,4 V, Kurzschluss 0,42 A, 33 g, 80x80x3,1 mm (Haendlerangabe).
  * "0,6 A" wird als Strom nahe Kurzschluss bei voller Sonne (1000 W/m^2)
    interpretiert.
  -> Standardannahme je Modul:  U_oc = 2,40 V, I_sc = 0,60 A bei 1000 W/m^2,
     25 degC, Fuellfaktor ca. 0,70  (=> P_mpp ca. 1,0 W).
  Diese Werte MUESSEN nach tests/testplan (Test 1) gemessen und in
  params.py / kalibrierung.json ersetzt werden.

Modell: Eindiodenmodell je Zelle, Serien- und Parallelwiderstand in einer
effektiven Idealitaet n zusammengefasst (Fuellfaktor-Anpassung):

    I = I_ph - I_0 * (exp(U_z / (n*U_T)) - 1)
    I_ph = I_sc * (G/1000) * (1 + alpha*(T-25))
    U_oc(T) = U_oc25 + beta*(T-25)

Sperrbereich (Zelle staerker bestromt als ihr Fotostrom, z.B. abgeschattetes
Modul in einer Reihenschaltung): ohmscher Leckpfad R_rev je Zelle.  Module
dieser Groesse haben i.d.R. KEINE Bypassdioden -> das schwaechste Modul
begrenzt den Strangstrom.

Anordnung auf dem Fahrzeug: 2 x 2 Module.  "Paar V" = die beiden Module in
Fahrtrichtung vorn, "Paar H" = die beiden hinteren.  Beim Tunnel wird immer
ein ganzes Paar gleichzeitig abgeschattet.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math

import numpy as np

K_B = 1.380649e-23
Q_E = 1.602176634e-19


@dataclass(frozen=True)
class SolarModule:
    """Ein Starterkit-'Solarzelle' = Modul aus n_cells Si-Zellen in Reihe."""
    u_oc: float = 2.40        # V   bei 1000 W/m^2, 25 degC   (ANNAHME)
    i_sc: float = 0.60        # A   bei 1000 W/m^2, 25 degC   (ANNAHME aus Kit-Angabe)
    n_cells: int = 4          # (ANNAHME aus 2 V Nennspannung)
    n_ideal: float = 2.0      # effektive Idealitaet -> Fuellfaktor ca. 0,70 (ANNAHME)
    alpha_isc: float = 5e-4   # 1/K  (typisch kristallines Si, Literaturwert)
    beta_uoc_cell: float = -2.2e-3  # V/K je Zelle (Literaturwert)
    r_rev_cell: float = 20.0  # Ohm Leckwiderstand je Zelle im Sperrbereich (ANNAHME)
    mass: float = 0.036       # kg  (ANNAHME, skaliert vom TRU-Vergleichsmodul)
    length: float = 0.120     # m   (ANNAHME)
    width: float = 0.060      # m   (ANNAHME)
    thickness: float = 0.0031  # m  (ANNAHME)

    # --- Hilfsgroessen ------------------------------------------------------
    def _vt(self, t_cell):
        return self.n_ideal * K_B * (t_cell + 273.15) / Q_E

    def _iph(self, g, t_cell):
        return self.i_sc * np.asarray(g, float) / 1000.0 * (1.0 + self.alpha_isc * (t_cell - 25.0))

    def _i0(self, t_cell):
        uoc_cell = self.u_oc / self.n_cells + self.beta_uoc_cell * (t_cell - 25.0)
        iph_ref = self.i_sc * (1.0 + self.alpha_isc * (t_cell - 25.0))
        return iph_ref / math.expm1(uoc_cell / self._vt(t_cell))

    # --- Strang aus n_series gleich beleuchteten Modulen ---------------------
    def string_current(self, u, g, t_cell=25.0, n_series=1):
        """I(U) eines Strangs; u und g duerfen Arrays sein."""
        u = np.asarray(u, float)
        nz = self.n_cells * n_series
        iph = self._iph(g, t_cell)
        i_fwd = iph - self._i0(t_cell) * np.expm1(np.clip(u, 0, None) / (nz * self._vt(t_cell)))
        i_rev = iph - u / (self.r_rev_cell * nz)
        return np.where(u >= 0, i_fwd, i_rev)

    def string_voltage(self, i, g, t_cell=25.0, n_series=1):
        """U(I) eines Strangs (Umkehrfunktion, explizit)."""
        i = np.asarray(i, float)
        nz = self.n_cells * n_series
        iph = self._iph(g, t_cell) + 0.0 * i
        i0 = self._i0(t_cell)
        arg = (iph - i) / i0 + 1.0
        u_fwd = nz * self._vt(t_cell) * np.log(np.clip(arg, 1e-300, None))
        u_rev = -(i - iph) * self.r_rev_cell * nz
        return np.where(i <= iph, u_fwd, u_rev)


# Verschaltungen der vier Module.  Jede Verschaltung wird durch die Art der
# Loesung ("series": Strom ist die Unbekannte, "parallel": Spannung ist die
# Unbekannte) und die Strangstruktur beschrieben.
CONFIGS = {
    # Name    : (Typ,        Module in Reihe je Paar-Strang, parallele Straenge je Paar, Modulanzahl)
    "4s":       ("series",   2, 1, 4),   # alle 4 in Reihe: Paar V (2s) + Paar H (2s)
    "2s2p":     ("parallel", 2, 1, 4),   # Paar V in Reihe || Paar H in Reihe
    "4p":       ("parallel", 1, 2, 4),   # alle 4 parallel
    "2s":       ("series",   1, 1, 2),   # nur 2 Module (je 1 vorn/hinten) in Reihe
    "2p":       ("parallel", 1, 1, 2),   # nur 2 Module parallel
}


@dataclass(frozen=True)
class Generator:
    module: SolarModule = SolarModule()
    config: str = "4s"

    @property
    def n_modules(self) -> int:
        return CONFIGS[self.config][3]

    @property
    def mass(self) -> float:
        return self.n_modules * self.module.mass

    def current(self, u, g_v, g_h, t_cell=25.0):
        """Generatorstrom bei Klemmenspannung u (nur Parallel-Typen exakt)."""
        typ, ns, npar, _ = CONFIGS[self.config]
        m = self.module
        if typ == "parallel":
            return npar * (m.string_current(u, g_v, t_cell, ns) + m.string_current(u, g_h, t_cell, ns))
        # Reihentyp: numerische Umkehrung
        return _invert_decreasing(lambda i: self.voltage(i, g_v, g_h, t_cell), np.asarray(u, float),
                                  -2.0, 1.5 * m.i_sc * 1.5 + 0.5)

    def voltage(self, i, g_v, g_h, t_cell=25.0):
        """Klemmenspannung bei Generatorstrom i (nur Reihen-Typen exakt)."""
        typ, ns, npar, _ = CONFIGS[self.config]
        m = self.module
        if typ == "series":
            return m.string_voltage(i, g_v, t_cell, ns) + m.string_voltage(i, g_h, t_cell, ns)
        return _invert_decreasing(lambda u: self.current(u, g_v, g_h, t_cell), np.asarray(i, float),
                                  -60.0, 4 * m.u_oc + 2.0)

    # --- Kennwerte ----------------------------------------------------------
    def u_oc(self, g=1000.0, t_cell=25.0):
        return float(self.voltage(np.array(0.0), g, g, t_cell))

    def i_sc(self, g=1000.0, t_cell=25.0):
        return float(self.current(np.array(0.0), g, g, t_cell))

    def curve(self, g_v=1000.0, g_h=None, t_cell=25.0, n=400):
        g_h = g_v if g_h is None else g_h
        u = np.linspace(0.0, self.u_oc(max(g_v, g_h, 1.0), t_cell) * 1.02, n)
        i = self.current(u, g_v, g_h, t_cell)
        return u, i

    def mpp(self, g_v=1000.0, g_h=None, t_cell=25.0):
        u, i = self.curve(g_v, g_h, t_cell, 1200)
        p = u * i
        j = int(np.argmax(p))
        return {"U_mpp": float(u[j]), "I_mpp": float(i[j]), "P_mpp": float(p[j])}

    def fill_factor(self, g=1000.0, t_cell=25.0):
        return self.mpp(g, g, t_cell)["P_mpp"] / (self.u_oc(g, t_cell) * self.i_sc(g, t_cell))


def _invert_decreasing(func, target, lo, hi, iters=60):
    """Loest func(x) = target fuer monoton fallendes func (vektorisiert)."""
    target = np.asarray(target, float)
    a = np.full(target.shape, lo, float)
    b = np.full(target.shape, hi, float)
    for _ in range(iters):
        mid = 0.5 * (a + b)
        above = func(mid) > target
        a = np.where(above, mid, a)
        b = np.where(above, b, mid)
    return 0.5 * (a + b)


def solve_operating_point(gen: Generator, motor, omega, g_v, g_h, t_cell=25.0,
                          n_motors=1, r_wiring=0.2):
    """Gemeinsamer Arbeitspunkt Solargenerator <-> Motor(en) (quasistatisch).

    omega: Motorwinkelgeschwindigkeit [rad/s] (Array), g_v/g_h: Bestrahlung der
    beiden Modulpaare [W/m^2] (Arrays, broadcastbar).
    Motoren sind elektrisch parallel geschaltet.
    Rueckgabe: (I_gesamt, U_Generatorklemme, U_Motor)
    """
    omega, g_v, g_h = np.broadcast_arrays(np.asarray(omega, float), np.asarray(g_v, float), np.asarray(g_h, float))
    r_tot = motor.R / n_motors + r_wiring
    e = motor.k * omega
    typ = CONFIGS[gen.config][0]
    if typ == "series":
        # f(I) = U_gen(I) - e - I*r_tot, monoton fallend in I
        lo = np.minimum(-e / r_tot, 0.0) - 1e-3
        hi = np.full(e.shape, 2.0 * gen.module.i_sc * 1.6 + 0.5)
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            f = gen.voltage(mid, g_v, g_h, t_cell) - e - mid * r_tot
            pos = f > 0
            lo = np.where(pos, mid, lo)
            hi = np.where(pos, hi, mid)
        i = 0.5 * (lo + hi)
        u_gen = e + i * r_tot
    else:
        # g(U) = I_gen(U) - (U - e)/r_tot, monoton fallend in U
        lo = np.full(e.shape, -5.0)
        hi = np.maximum(e, 4 * gen.module.u_oc) + 5.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            g = gen.current(mid, g_v, g_h, t_cell) - (mid - e) / r_tot
            pos = g > 0
            lo = np.where(pos, mid, lo)
            hi = np.where(pos, hi, mid)
        u_gen = 0.5 * (lo + hi)
        i = (u_gen - e) / r_tot
    u_motor = e + i * motor.R / n_motors
    return i, u_gen, u_motor


# Beleuchtungsszenarien (alles ANNAHMEN -- vor Ort mit Kurzschlussstrom messen!)
@dataclass(frozen=True)
class LightScenario:
    name: str
    g: float                 # W/m^2 aequivalente Bestrahlung (auf Si-Spektrum bezogen)
    t_cell: float            # degC Zelltemperatur
    ripple: float = 0.0      # relative Amplitude der Ortsabhaengigkeit (Kunstlicht-Strahler)
    ripple_period: float = 1.25  # m
    tunnel_light: float = 0.02   # Restlichtanteil im Tunnel (0 = voellig dunkel)
    note: str = ""

    def g_at(self, x):
        """Bestrahlung an der Bahnposition x (ausserhalb des Tunnels)."""
        x = np.asarray(x, float)
        return self.g * (1.0 + self.ripple * np.cos(2 * np.pi * x / self.ripple_period))


SCENARIOS = {
    "sonne": LightScenario("sonne", 850.0, 50.0, note="klarer Sommertag, Modul waagerecht"),
    "bewoelkt": LightScenario("bewoelkt", 150.0, 25.0, note="geschlossene Wolkendecke (Bereich 80-300 W/m^2)"),
    "kunstlicht": LightScenario("kunstlicht", 200.0, 35.0, ripple=0.4, ripple_period=1.25,
                                note="500-W-Halogenstrahler in ca. 0,8 m Hoehe (DM-Reglement); Si-aequivalent geschaetzt"),
}


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

    rows = []
    for cfg in ("4s", "2s2p", "4p"):
        gen = Generator(config=cfg)
        for sc in SCENARIOS.values():
            mp = gen.mpp(sc.g, sc.g, sc.t_cell)
            half = gen.mpp(sc.g, sc.g * sc.tunnel_light, sc.t_cell)
            rows.append({
                "Verschaltung": cfg, "Szenario": sc.name, "G_W_m2": sc.g, "T_Zelle_C": sc.t_cell,
                "U_oc_V": round(gen.u_oc(sc.g, sc.t_cell), 2), "I_sc_A": round(gen.i_sc(sc.g, sc.t_cell), 3),
                "U_mpp_V": round(mp["U_mpp"], 2), "I_mpp_A": round(mp["I_mpp"], 3), "P_mpp_W": round(mp["P_mpp"], 3),
                "P_mpp_ein_Paar_im_Tunnel_W": round(half["P_mpp"], 3),
            })
    with open(out_c / "solargenerator_kennwerte.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter=";")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)
    print("Fuellfaktor STC:", round(Generator(config="4s").fill_factor(), 3))

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3))
    for ax, cfg in zip(axes, ("4s", "2s2p", "4p")):
        gen = Generator(config=cfg)
        for sc in SCENARIOS.values():
            u, i = gen.curve(sc.g, sc.g, sc.t_cell)
            ax.plot(u, i, label=f"{sc.name} ({sc.g:.0f} W/m², {sc.t_cell:.0f} °C)")
            mp = gen.mpp(sc.g, sc.g, sc.t_cell)
            ax.plot(mp["U_mpp"], mp["I_mpp"], "ko", ms=4)
        u, i = gen.curve(850, 850 * 0.02, 50)
        ax.plot(u, i, "k:", label="Sonne, ein Paar im Tunnel")
        ax.set_title(f"Verschaltung {cfg}")
        ax.set_xlabel("Spannung [V]")
        ax.set_ylabel("Strom [A]")
        ax.set_ylim(0, None)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
    fig.suptitle("Solargenerator-Kennlinien (NAEHERUNGSMODELL, Modulwerte angenommen) – Punkte = MPP")
    fig.tight_layout()
    fig.savefig(out_d / "solar_kennlinien.png", dpi=130)

    # Temperatur- und Teilabschattungseinfluss
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    gen = Generator(config="4s")
    for t in (10, 25, 50, 70):
        u, i = gen.curve(850, 850, t)
        axes[0].plot(u, u * i, label=f"{t} °C")
    axes[0].set_title("4s, 850 W/m²: Leistung über Spannung bei Zelltemperatur")
    axes[0].set_xlabel("Spannung [V]"); axes[0].set_ylabel("Leistung [W]"); axes[0].legend(); axes[0].grid(alpha=0.3)
    for cfg in ("4s", "2s2p", "4p"):
        gen = Generator(config=cfg)
        fr = np.linspace(0, 1, 30)
        p = [gen.mpp(850, 850 * f, 50)["P_mpp"] for f in fr]
        axes[1].plot(fr * 100, p, label=cfg)
    axes[1].set_title("Teilabschattung: ein Modulpaar erhält nur x % Licht")
    axes[1].set_xlabel("Licht auf abgeschattetem Paar [%]"); axes[1].set_ylabel("P_mpp gesamt [W]")
    axes[1].legend(); axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_d / "solar_temperatur_teilabschattung.png", dpi=130)
    print("Diagramme ->", out_d)
