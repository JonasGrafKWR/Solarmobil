"""Fahrzeug-Laengsdynamik und Rennablauf (zeitabhaengige Simulation).

Gleichungen
-----------
  v      = pi * d * n_Rad / 60            n_Rad = n_Motor / i
  F_an   = eta * i * M_Motor / r          (Antrieb;  beim Schleppen: i*M/(eta*r))
  M_Motor= k * I - M_r                    I aus gemeinsamem Arbeitspunkt
                                          Solargenerator <-> Motor (solar_model)
  F_w    = c_rr*m*g + F_konst + 0.5*rho*cW*A*v^2 + m*g*Steigung
  m_eff  = m + (J_Raeder + J_Achse)/r^2 + (J_Rotor + J_Ritzel)*i^2/r^2
  dv/dt  = (min(F_an, mu*N_Antrieb) - F_w) / m_eff

Der elektrische Teil wird quasistatisch behandelt (elektrische Zeitkonstante
L/R << mechanische Zeitkonstante).  Fuer jede Parameterkombination wird die
Zugkraft F_an(v, G) einmal als Tabelle berechnet; die Zeitintegration laeuft
vektorisiert ueber beliebig viele Parametersaetze gleichzeitig (Monte-Carlo).

Rennablauf (Ultraleicht-Expert): `legs` Durchfahrten zwischen zwei
Anschlagbrettern, dazwischen automatische Richtungswechsel.  Modell des
Richtungswechsels: Aufprall mit v_auf -> Schaltstange polt um (nur wenn
v_auf >= v_schalt_min), Rueckprall mit e*v_auf, Totzeit t_schalt ohne Antrieb.

Alle Zahlenwerte in den Dataclasses sind Standardannahmen; Herkunft siehe
Kommentar.  Kalibrierung: simulation/kalibrierung.py.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math

import numpy as np

from solar_model import Generator, LightScenario, solve_operating_point

G0 = 9.80665


@dataclass(frozen=True)
class VehicleParams:
    mass: float = 0.260             # kg   Gesamtmasse (CAD + Annahme Modulmasse, siehe bom/)
    wheel_d: float = 0.050          # m    Raddurchmesser (Konstruktion)
    gear_ratio: float = 5.0         # -    i = n_Motor / n_Rad
    eta_gear: float = 0.88          # -    eine gedruckte Stirnradstufe (ANNAHME, Test 4)
    crr: float = 0.020              # -    Rollwiderstand inkl. Lager (ANNAHME, Test 6)
    f_const: float = 0.010          # N    Fuehrungsrolle / Schleifkontakte (ANNAHME)
    cda: float = 0.0050             # m^2  cW*A (ANNAHME: Stirnflaeche ca. 0,005 m^2, cW ca. 1)
    rho_air: float = 1.20           # kg/m^3
    j_wheels: float = 4.4e-6        # kg*m^2 alle vier Raeder (CAD)
    j_axle_gear: float = 8.0e-7     # kg*m^2 Abtriebsrad (CAD)
    j_pinion: float = 3.8e-9        # kg*m^2 Ritzel (CAD)
    mu_traction: float = 0.60       # -    Haftreibung O-Ring auf Bahn (ANNAHME)
    driven_load_frac: float = 0.55  # -    Achslastanteil der Antriebsachse (CAD-Schwerpunkt)
    length: float = 0.296           # m    Laenge ueber alles (CAD)
    pair_offset: float = 0.060      # m    Abstand Modulpaar-Mitte von Fahrzeugmitte
    pair_len: float = 0.120         # m    Laenge eines Modulpaars in Fahrtrichtung
    grade: float = 0.0              # -    Steigung (Bahn laut Reglement eben)
    breakaway: float = 1.5          # -    Losbrechfaktor auf Roll-/Lagerreibung im Stand (ANNAHME)
    n_motors: int = 1
    r_wiring: float = 0.20          # Ohm  Leitungen + Schaltkontakte (ANNAHME, Datenblatt D2F: <= 30 mOhm/Kontakt)


@dataclass(frozen=True)
class TrackParams:
    length: float = 10.0            # m    "ca. 10 m" (Reglement)
    tunnel_len: float = 1.6         # m    (Reglement)
    tunnel_center: float = 5.0      # m    ANNAHME: Tunnel in Bahnmitte (im Reglement nicht angegeben)
    legs: int = 4                   # Durchfahrten (Reglement)


@dataclass(frozen=True)
class ReversalParams:
    restitution: float = 0.30       # -    Rueckprallzahl mit Schaumstoff-Puffer (ANNAHME, Test 8)
    t_switch: float = 0.030         # s    Totzeit Schalter + Prellen (ANNAHME)
    v_switch_min: float = 0.25      # m/s  Mindestgeschwindigkeit zum Umschalten (berechnet, docs/umkehrmechanismus.md)
    v_impact_design: float = 4.0    # m/s  Auslegungsgrenze Aufprall (ANNAHME, Crashtest noetig)


# ----------------------------------------------------------------------------
# Zugkrafttabellen
# ----------------------------------------------------------------------------
V_GRID = np.concatenate([np.linspace(0.0, 0.5, 26)[:-1], np.linspace(0.5, 14.0, 136)])
G_REL = np.concatenate([[0.0, 0.005, 0.01, 0.02, 0.04, 0.07], np.linspace(0.1, 1.6, 16)])  # x 1000 W/m^2


def effective_mass(veh: VehicleParams, motor) -> float:
    r = veh.wheel_d / 2
    return (veh.mass + (veh.j_wheels + veh.j_axle_gear) / r**2
            + veh.n_motors * (motor.j_rotor + veh.j_pinion) * veh.gear_ratio**2 / r**2)


def resistance(veh: VehicleParams, v):
    """Fahrwiderstand [N] bei v > 0."""
    v = np.asarray(v, float)
    return (veh.crr * veh.mass * G0 + veh.f_const + 0.5 * veh.rho_air * veh.cda * v**2
            + veh.mass * G0 * veh.grade)


def drive_force(veh: VehicleParams, motor, gen: Generator, v, g_v, g_h, t_cell=25.0,
                with_details=False):
    """Zugkraft am Radumfang [N] (ohne Fahrwiderstand, mit Traktionsgrenze)."""
    r = veh.wheel_d / 2
    omega = np.asarray(v, float) * veh.gear_ratio / r
    i_tot, u_gen, u_mot = solve_operating_point(gen, motor, omega, g_v, g_h, t_cell,
                                                veh.n_motors, veh.r_wiring)
    m_shaft = motor.k * i_tot - veh.n_motors * motor.m_fric
    f = np.where(m_shaft >= 0,
                 veh.eta_gear * veh.gear_ratio * m_shaft / r,
                 veh.gear_ratio * m_shaft / (veh.eta_gear * r))
    f_trac = veh.mu_traction * veh.mass * G0 * veh.driven_load_frac
    f = np.clip(f, -f_trac, f_trac)
    if with_details:
        return f, i_tot, u_gen, u_mot, omega, m_shaft
    return f


def thrust_tables(veh: VehicleParams, motor, gen: Generator, sc: LightScenario):
    """Tabellen F(G_rel, v): beide Paare beleuchtet / ein Paar im Tunnel."""
    vv, gg = np.meshgrid(V_GRID, G_REL * 1000.0)
    full = drive_force(veh, motor, gen, vv, gg, gg, sc.t_cell)
    half = drive_force(veh, motor, gen, vv, gg, gg * sc.tunnel_light, sc.t_cell)
    return full, half


def _interp2(tab, gi, vi):
    """Bilineare Interpolation; tab[N, NG, NV], gi/vi = gebrochene Indizes je Kandidat."""
    n = np.arange(tab.shape[0])
    g0 = np.clip(np.floor(gi).astype(int), 0, tab.shape[1] - 2)
    v0 = np.clip(np.floor(vi).astype(int), 0, tab.shape[2] - 2)
    fg = np.clip(gi - g0, 0.0, 1.0)
    fv = np.clip(vi - v0, 0.0, 1.0)
    return ((1 - fg) * (1 - fv) * tab[n, g0, v0] + (1 - fg) * fv * tab[n, g0, v0 + 1]
            + fg * (1 - fv) * tab[n, g0 + 1, v0] + fg * fv * tab[n, g0 + 1, v0 + 1])


def _frac_index(grid, x):
    j = np.clip(np.searchsorted(grid, x, side="right") - 1, 0, len(grid) - 2)
    return j + (x - grid[j]) / (grid[j + 1] - grid[j])


# ----------------------------------------------------------------------------
# Rennsimulation (vektorisiert ueber N Parametersaetze)
# ----------------------------------------------------------------------------
@dataclass
class Case:
    """Ein vollstaendiger Parametersatz fuer einen Rennlauf."""
    veh: VehicleParams
    motor: object
    gen: Generator
    light: LightScenario
    track: TrackParams = TrackParams()
    rev: ReversalParams = ReversalParams()


def simulate_batch(cases: list[Case], dt: float = 0.002, t_max: float = 120.0,
                   record: bool = False) -> dict:
    """Simuliert alle Faelle gleichzeitig.  Rueckgabe: dict mit Arrays je Fall.

    status: 0 = Ziel erreicht, 1 = kein Anlauf am Start, 2 = Stillstand auf der
            Strecke (z.B. im Tunnel), 3 = Aufprall zu langsam zum Umschalten,
            4 = Zeitlimit.
    """
    n = len(cases)
    full = np.empty((n, len(G_REL), len(V_GRID)))
    half = np.empty_like(full)
    for j, c in enumerate(cases):
        full[j], half[j] = thrust_tables(c.veh, c.motor, c.gen, c.light)

    def arr(fn):
        return np.array([fn(c) for c in cases], float)

    m_eff = arr(lambda c: effective_mass(c.veh, c.motor))
    f_roll = arr(lambda c: c.veh.crr * c.veh.mass * G0 + c.veh.f_const + c.veh.mass * G0 * c.veh.grade)
    k_air = arr(lambda c: 0.5 * c.veh.rho_air * c.veh.cda)
    brk = arr(lambda c: c.veh.breakaway)
    l_leg = arr(lambda c: c.track.length - c.veh.length)
    half_len = arr(lambda c: c.veh.length / 2)
    d_pair = arr(lambda c: c.veh.pair_offset)
    h_pair = arr(lambda c: c.veh.pair_len / 2)
    trk_len = arr(lambda c: c.track.length)
    tun0 = arr(lambda c: c.track.tunnel_center - c.track.tunnel_len / 2)
    tun1 = arr(lambda c: c.track.tunnel_center + c.track.tunnel_len / 2)
    legs = arr(lambda c: c.track.legs).astype(int)
    g_mean = arr(lambda c: c.light.g)
    rip = arr(lambda c: c.light.ripple)
    rip_p = arr(lambda c: c.light.ripple_period)
    tl = arr(lambda c: c.light.tunnel_light)
    is_series = np.array([c.gen.config in ("4s", "2s") for c in cases])
    e_rest = arr(lambda c: c.rev.restitution)
    t_sw = arr(lambda c: c.rev.t_switch)
    v_sw = arr(lambda c: c.rev.v_switch_min)

    s = np.zeros(n)            # Weg der Fahrzeugmitte seit dem letzten Anschlag
    v = np.zeros(n)
    leg = np.zeros(n, int)
    dead = np.zeros(n)
    t = np.zeros(n)
    status = np.full(n, -1)
    still = np.zeros(n)        # Zeit im Stillstand
    v_max = np.zeros(n)
    v_tun_min = np.full(n, np.inf)
    max_legs = int(legs.max())
    v_imp = np.full((n, max_legs), np.nan)
    t_leg = np.full((n, max_legs), np.nan)
    t_leg_start = np.zeros(n)
    u_mot_max = np.zeros(n)

    hist = {"t": [], "s": [], "x": [], "v": [], "f": [], "leg": [], "mode": []} if record else None

    steps = int(t_max / dt)
    for _ in range(steps):
        act = status < 0
        if not act.any():
            break
        # Bahnposition (Richtung wechselt je Durchfahrt)
        c_leg = half_len + s
        fwd = (leg % 2) == 0
        x_c = np.where(fwd, c_leg, trk_len - c_leg)
        sign = np.where(fwd, 1.0, -1.0)
        x_lead = x_c + sign * d_pair
        x_trail = x_c - sign * d_pair
        in_lead = (x_lead + h_pair > tun0) & (x_lead - h_pair < tun1)
        in_trail = (x_trail + h_pair > tun0) & (x_trail - h_pair < tun1)
        g_lead = g_mean * (1 + rip * np.cos(2 * np.pi * x_lead / rip_p))
        g_trail = g_mean * (1 + rip * np.cos(2 * np.pi * x_trail / rip_p))
        both_lit = ~in_lead & ~in_trail
        both_dark = in_lead & in_trail
        g_comb = np.where(is_series, np.minimum(g_lead, g_trail), 0.5 * (g_lead + g_trail))
        g_eff = np.where(both_lit, g_comb,
                         np.where(both_dark, g_comb * tl, np.where(in_lead, g_trail, g_lead)))
        gi = _frac_index(G_REL, np.clip(g_eff / 1000.0, 0, G_REL[-1]))
        vi = _frac_index(V_GRID, np.clip(v, 0, V_GRID[-1]))
        f_drive = np.where(both_lit | both_dark, _interp2(full, gi, vi), _interp2(half, gi, vi))
        f_drive = np.where(dead > 0, np.minimum(f_drive, 0.0), f_drive)

        f_res = f_roll + k_air * v**2
        moving = v > 1e-4
        a = (f_drive - f_res) / m_eff
        # Stillstand: nur anfahren, wenn Antrieb die Losbrechreibung uebersteigt
        can_start = f_drive > brk * f_roll
        a = np.where(moving, a, np.where(can_start, (f_drive - f_roll) / m_eff, 0.0))
        v_new = np.maximum(v + a * dt, 0.0)
        s_new = s + 0.5 * (v + v_new) * dt

        v = np.where(act, v_new, v)
        s = np.where(act, s_new, s)
        t = np.where(act, t + dt, t)
        dead = np.maximum(dead - dt, 0.0)
        v_max = np.maximum(v_max, v)
        in_tun = (in_lead | in_trail) & act
        v_tun_min = np.where(in_tun, np.minimum(v_tun_min, v), v_tun_min)

        if record:
            hist["t"].append(t.copy()); hist["s"].append(s.copy()); hist["x"].append(x_c.copy())
            hist["v"].append(v.copy() * sign); hist["f"].append(f_drive.copy()); hist["leg"].append(leg.copy())
            hist["mode"].append(np.where(both_lit, 0, np.where(both_dark, 2, 1)))

        # Stillstandserkennung
        still = np.where(act & (v < 1e-4), still + dt, 0.0)
        stuck = act & (still > 1.0)
        status = np.where(stuck & (t < 1.5) & (leg == 0), 1, status)
        status = np.where(stuck & (status < 0), 2, status)

        # Anschlag erreicht
        hit = act & (s >= l_leg) & (status < 0)
        if hit.any():
            idx = np.nonzero(hit)[0]
            for j in idx:
                v_imp[j, leg[j]] = v[j]
                t_leg[j, leg[j]] = t[j] - t_leg_start[j]
                t_leg_start[j] = t[j]
                if leg[j] + 1 >= legs[j]:
                    status[j] = 0                       # Ziel
                elif v[j] < v_sw[j]:
                    status[j] = 3                       # schaltet nicht um
                else:
                    leg[j] += 1
                    s[j] = 0.0
                    v[j] = e_rest[j] * v[j]
                    dead[j] = t_sw[j]
    status = np.where(status < 0, 4, status)

    out = {
        "status": status, "t_total": np.where(status == 0, t, np.nan), "v_max": v_max,
        "v_impact": v_imp, "t_leg": t_leg, "v_tunnel_min": v_tun_min, "m_eff": m_eff,
    }
    if record:
        out["hist"] = {k: np.array(val) for k, val in hist.items()}
    return out


STATUS_TEXT = {0: "Ziel erreicht", 1: "kein Anlauf am Start", 2: "Stillstand auf der Strecke/Tunnel",
               3: "Aufprall zu langsam - kein Umschalten", 4: "Zeitlimit"}


def steady_speed(veh: VehicleParams, motor, gen: Generator, sc: LightScenario) -> float:
    """Beharrungsgeschwindigkeit (Zugkraft = Fahrwiderstand) bei voller Beleuchtung."""
    v = np.linspace(0.01, 14.0, 1400)
    f = drive_force(veh, motor, gen, v, sc.g, sc.g, sc.t_cell) - resistance(veh, v)
    idx = np.nonzero(f < 0)[0]
    if len(idx) == 0:
        return float(v[-1])
    if idx[0] == 0:
        return 0.0
    return float(v[idx[0]])


def start_margin(veh: VehicleParams, motor, gen: Generator, sc: LightScenario) -> float:
    """Anfahrkraft im Stand / Losbrechwiderstand (>1 = faehrt selbststaendig an)."""
    f0 = float(drive_force(veh, motor, gen, 0.0, sc.g, sc.g, sc.t_cell))
    need = veh.breakaway * (veh.crr * veh.mass * G0 + veh.f_const + veh.mass * G0 * veh.grade)
    return f0 / need
