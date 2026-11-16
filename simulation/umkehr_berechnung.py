"""Auslegungsrechnung des Umkehrmechanismus (Kraefte, Energien, Aufprall).

    python umkehr_berechnung.py   ->  results/calculations/umkehrmechanismus_auslegung.csv

Alle Ergebnisse sind BERECHNET aus Datenblattwerten [D], CAD-Massen [C] und
gekennzeichneten ANNAHMEN [A].  Sie sind nicht experimentell bestaetigt.
"""
from __future__ import annotations

import csv
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cad" / "source"))
import params_cad as C          # noqa: E402
from params import BASE_VEHICLE  # noqa: E402

M = BASE_VEHICLE.mass            # kg  [C]+[A]
MU = 0.25                        # [A] Reibwert PETG/PETG trocken (Literaturbereich 0,2-0,3)
F_LEVER = 0.78                   # N   [D] Omron D2F-L, Betaetigungskraft OF max. (80 gf)
F_MAG = 1.5                      # N   [A] Soll-Haltekraft Magnet/Stahlschraube (ueber Luftspalt einstellen, messen!)
MAG_RANGE = 0.0007               # m   [A] Weg, ueber den die Magnetkraft im Mittel wirkt
SPRING_F0, SPRING_C = 0.26, 30.0  # N, N/m [B] Rueckstellfeder: Vorspannung, Rate (d 0,25 / Dm 4,4 / 12 Wdg.)
M_ROD = 0.0022                   # kg  [C] Schaltstange + Federteller
M_SLIDER = 0.0022                # kg  [C]
PAD_AREA = C.PAD_W * C.PAD_H * 1e-6          # m^2
PAD_STROKE = C.PAD_COMPRESS * C.PAD_T * 1e-3  # m


def main():
    a = math.radians(C.RAMP_DEG)
    phi = math.atan(MU)
    wedge = math.tan(a + phi) + MU             # Axialkraft je Querkraft (Keil + Reibung an der Fuehrungswand)
    lat_total = 2 * C.SLIDE_H * 1e-3           # Schieberhub
    ax_total = lat_total / math.tan(a)
    rows = []

    def add(name, value, unit, origin, note=""):
        rows.append({"Groesse": name, "Wert": value, "Einheit": unit, "Herkunft": origin, "Bemerkung": note})

    f_break = F_MAG * wedge
    f_lever = F_LEVER * wedge
    e_mag = F_MAG * MAG_RANGE * wedge / math.tan(a) * math.tan(a)   # Querarbeit * Keilfaktor
    e_mag = F_MAG * MAG_RANGE * wedge
    lever_lat = 0.0017                         # m [A]/[D]: Hebelweg vom ersten Kontakt bis Endlage (FP - OP + Ueberweg)
    e_lever = F_LEVER * lever_lat * wedge
    travel = C.ROD_LEAD * 1e-3 + ax_total
    e_spring = (SPRING_F0 + 0.5 * SPRING_C * travel) * travel
    e_total = e_mag + e_lever + e_spring
    v_min = math.sqrt(2 * e_total / M)
    add("Keilfaktor F_axial/F_quer", round(wedge, 2), "-", "berechnet", f"tan({C.RAMP_DEG:.0f}°+arctan µ)+µ, µ={MU} [A]")
    add("Stangenweg bis Schieber umgelegt", round(travel * 1000, 2), "mm", "berechnet (CAD)", "Leerweg + Hub/tan(Rampe)")
    add("Losbrechkraft an der Stange (Magnet loesen)", round(f_break, 2), "N", "berechnet", f"Magnet-Haltekraft {F_MAG} N [A]")
    add("Stangenkraft beim Druecken des Schalthebels", round(f_lever, 2), "N", "berechnet", "OF max 0,78 N [D]")
    add("Arbeit Magnet loesen", round(e_mag * 1000, 2), "mJ", "berechnet", "")
    add("Arbeit Schalthebel", round(e_lever * 1000, 2), "mJ", "berechnet", "")
    add("Arbeit Rueckstellfeder bis Umschaltpunkt", round(e_spring * 1000, 2), "mJ", "berechnet", "")
    add("Schaltarbeit gesamt", round(e_total * 1000, 2), "mJ", "berechnet", "")
    add("Mindest-Aufprallgeschwindigkeit (E_kin = Schaltarbeit)", round(v_min, 2), "m/s", "berechnet",
        f"Fahrzeugmasse {M*1000:.0f} g; mit Sicherheitsfaktor 2 auf die Arbeit: {math.sqrt(2)*v_min:.2f} m/s")
    for sc, v in (("Sonne", 4.4), ("Kunstlicht", 2.0), ("bewoelkt", 1.85)):
        e = 0.5 * M * v * v
        add(f"Energiereserve {sc} (v_Aufprall {v} m/s, simuliert)", round(e / e_total), "x Schaltarbeit", "berechnet", f"E_kin = {e:.2f} J")
    # Traegheitskraefte waehrend des Aufpralls
    for v in (2.0, 3.0, 4.4):
        e = 0.5 * M * v * v
        f_avg = e / PAD_STROKE
        a_avg = f_avg / M
        p = f_avg / PAD_AREA
        add(f"Aufprall {v} m/s: Energie", round(e, 2), "J", "berechnet", "")
        add(f"Aufprall {v} m/s: mittlere Pufferkraft", round(f_avg), "N", "berechnet", f"Stauchweg {PAD_STROKE*1000:.0f} mm [A]")
        add(f"Aufprall {v} m/s: mittlere Verzoegerung", round(a_avg), "m/s^2", "berechnet", f"= {a_avg/9.81:.0f} g")
        add(f"Aufprall {v} m/s: noetige Schaum-Druckspannung", round(p / 1e6, 3), "MPa", "berechnet",
            "Schaumstoff so waehlen, dass sein Plateau etwa diesen Wert erreicht")
        add(f"Aufprall {v} m/s: Traegheitskraft auf die hintere Stange", round(M_ROD * a_avg, 2), "N", "berechnet",
            "wird von der Rastflaeche der gedrueckten vorderen Stange abgefangen (Formschluss)")
        add(f"Aufprall {v} m/s: Kraft je Modul auf Traegerplatte", round(C.MOD_MASS_G / 1000 * a_avg, 1), "N", "berechnet",
            "Modulmasse = Annahme")
    add("Querbeschleunigung, die den Schieber loesen wuerde", round((F_MAG - F_LEVER) / M_SLIDER), "m/s^2", "berechnet",
        "Aufprallkraefte wirken laengs, der Schieber bewegt sich quer -> unkritisch")
    add("Kippmoment-Hebelarm Puffer zu Schwerpunkt", 0.2, "mm", "berechnet (CAD)", "Puffermitte 47,5 mm, Schwerpunkt 47,7 mm")
    out = ROOT / "results" / "calculations" / "umkehrmechanismus_auslegung.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter=";")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['Groesse']:62s} {r['Wert']!s:>8} {r['Einheit']:16s} [{r['Herkunft']}] {r['Bemerkung']}")


if __name__ == "__main__":
    main()
