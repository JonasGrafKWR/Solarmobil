"""Validiert die exportierten STL-Dateien (Netzqualitaet, Volumen, Druckbarkeit).

    python validate_stl.py

Prueft je Datei: wasserdichtes Netz, konsistente Normalen, genau ein Koerper,
Volumenabgleich mit dem CAD-Volumen (bom/druckteile_massen.csv), Auflage auf
z = 0 und Anteil der Auflageflaeche.  Ergebnis: exports/STL/_validierung.csv
"""
from __future__ import annotations

import csv
import pathlib
import sys

import numpy as np
import trimesh

ROOT = pathlib.Path(__file__).resolve().parents[2]
STL = ROOT / "exports" / "STL"


def main() -> int:
    cad = {}
    with open(ROOT / "bom" / "druckteile_massen.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter=";"):
            cad[r["Teil"]] = float(r["Volumen_cm3"])
    rows, bad = [], 0
    for p in sorted(STL.glob("*.stl")):
        m = trimesh.load_mesh(p)
        bodies = m.split(only_watertight=False)
        v_cad = cad.get(p.stem)
        v = abs(m.volume) / 1000.0
        dv = (v / v_cad - 1.0) * 100 if v_cad else float("nan")
        down = m.face_normals[:, 2] < -0.99
        on_bed = down & (np.abs(m.triangles_center[:, 2]) < 0.02)
        contact = float(m.area_faces[on_bed].sum())
        # Ueberhaenge: nach unten geneigte Flaechen (> 50 Grad zur Senkrechten), die nicht auf dem Bett liegen
        over = (m.face_normals[:, 2] < -0.766) & ~on_bed
        over_area = float(m.area_faces[over].sum())
        ok = bool(m.is_watertight and m.is_winding_consistent and len(bodies) == 1 and abs(dv) < 1.0
                  and abs(m.bounds[0][2]) < 0.01 and contact > 1.0)
        bad += 0 if ok else 1
        rows.append({"Datei": p.name, "Dreiecke": len(m.faces), "wasserdicht": m.is_watertight,
                     "Normalen_konsistent": m.is_winding_consistent, "Koerper": len(bodies),
                     "Volumen_cm3": round(v, 3), "Abweichung_zu_CAD_%": round(dv, 2),
                     "x_mm": round(float(m.extents[0]), 1), "y_mm": round(float(m.extents[1]), 1),
                     "z_mm": round(float(m.extents[2]), 1), "Auflageflaeche_mm2": round(contact, 1),
                     "Ueberhangflaeche_mm2": round(over_area, 1), "Ergebnis": "OK" if ok else "PRUEFEN"})
        print(f"{'OK     ' if ok else 'PRUEFEN'} {p.name:45s} {len(m.faces):7d} Dreiecke  V={v:7.3f} cm³ ({dv:+.2f} %)  "
              f"Auflage {contact:7.1f} mm²  Überhang {over_area:6.1f} mm²")
    with open(STL / "_validierung.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter=";")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows) - bad} von {len(rows)} STL-Dateien OK")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
