"""Erzeugt alle CAD-Daten des SolarMobils und prueft die Konstruktion.

    python build_all.py            alles (STL, STEP, Zeichnungen, Pruefbericht)
    python build_all.py --fast     ohne Zeichnungen

Ausgaben:
    exports/STL/*.stl          Druckteile in Drucklage (z = Bauplattform-Normale)
    exports/STEP/*.step        Druckteile + Gesamtzusammenbau (in FreeCAD oeffenbar)
    cad/drawings/*.svg         Massblaetter (Dreiseitenansicht + Hauptmasse)
    cad/assemblies/*.svg       Zusammenbau- und Explosionsdarstellung
    cad/assemblies/pruefbericht.md / .json   Kollisions-, Verzahnungs-, Reglementpruefung
    bom/druckteile_massen.csv  Volumen und Masse der Druckteile (aus CAD)

Geprueft wird nur die GEOMETRIE.  Funktion und Festigkeit sind damit nicht
experimentell nachgewiesen (siehe docs/testplan.md).
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import pathlib
import sys

import cadquery as cq
from cadquery import exporters

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from parts import *          # noqa: E402,F401,F403
import parts as P            # noqa: E402
import gear_geometry as gg   # noqa: E402

STL, STEP = ROOT / "exports" / "STL", ROOT / "exports" / "STEP"
DRAW, ASM, BOM = ROOT / "cad" / "drawings", ROOT / "cad" / "assemblies", ROOT / "bom"
for d in (STL, STEP, DRAW, ASM, BOM):
    d.mkdir(parents=True, exist_ok=True)


def solid(wp):
    v = wp.vals()
    return v[0] if len(v) == 1 else cq.Compound.makeCompound(v)


def vol(wp):
    return sum(s.Volume() for s in wp.vals())


def bbox(wp):
    b = solid(wp).BoundingBox()
    return (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)


def inter_vol(a, b):
    ba, bb = bbox(a), bbox(b)
    if ba[1] < bb[0] or bb[1] < ba[0] or ba[3] < bb[2] or bb[3] < ba[2] or ba[5] < bb[4] or bb[5] < ba[4]:
        return 0.0
    try:
        return sum(s.Volume() for s in a.intersect(b).vals())
    except Exception:
        return 0.0


def to_print(wp, rx=0.0, ry=0.0):
    """Dreht in Drucklage und setzt das Teil auf z = 0, mittig auf x/y."""
    r = wp
    if rx:
        r = r.rotate((0, 0, 0), (1, 0, 0), rx)
    if ry:
        r = r.rotate((0, 0, 0), (0, 1, 0), ry)
    b = bbox(r)
    return r.translate((-(b[0] + b[1]) / 2, -(b[2] + b[3]) / 2, -b[4]))


# ------------------------------------------------------------------ Zeichnungen
def _svg_view(shape, kind, w, h):
    """Eine Ansicht als SVG-Fragment.  Orthogonale Ansichten werden so gedreht, dass die
    Blickrichtung +z ist (x nach rechts, y nach oben), formatfuellend skaliert und zentriert.
    Rueckgabe: (svg_text, massstab_px_je_mm, breite_mm, hoehe_mm)"""
    import re
    opts = {"width": w, "height": h, "marginLeft": 12, "marginTop": 12, "showAxes": False, "strokeWidth": 0.35,
            "strokeColor": (20, 20, 20), "hiddenColor": (165, 165, 165), "showHidden": True}
    if kind.startswith("iso"):
        opts["projectionDir"] = (1, -1, -0.8) if kind.endswith("unten") else (1, -1, 0.8)
        s = exporters.getSVG(shape, opts=opts)
        return s[s.find("<svg"):], None, None, None
    sh = shape
    if kind == "seite":            # Blick von -y: x nach rechts, z nach oben
        sh = sh.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -90)
    elif kind == "stirn":          # Blick von +x: y nach rechts, z nach oben
        sh = sh.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), -90).rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -90)
    elif kind == "unten":          # Blick von -z
        sh = sh.rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 180)
    bb = sh.BoundingBox()
    opts["projectionDir"] = (0, 0, 1)
    s = exporters.getSVG(sh, opts=opts)
    s = s[s.find("<svg"):]
    sc = min((w - 70) / max(bb.xlen, 1e-6), (h - 70) / max(bb.ylen, 1e-6))
    tx = w / (2 * sc) - (bb.xmin + bb.xmax) / 2
    ty = -h / (2 * sc) - (bb.ymin + bb.ymax) / 2
    s = re.sub(r'transform="scale\([^)]*\)\s*translate\([^)]*\)"', f'transform="scale({sc:.5f}, {-sc:.5f}) translate({tx:.4f},{ty:.4f})"', s, count=1)
    s = re.sub(r'stroke-width="[^"]*"', f'stroke-width="{0.9 / sc:.5f}"', s)
    return s, sc, bb.xlen, bb.ylen


def drawing(wp, name, title, notes, views=None):
    shape = solid(wp)
    b = shape.BoundingBox()
    views = views or [("Draufsicht (von oben)", "oben"), ("Seitenansicht (von links, Fahrtrichtung nach rechts)", "seite"),
                      ("Stirnansicht (von vorn)", "stirn"), ("Isometrie", "iso")]
    W, H, vw, vh = 1180, 830, 560, 330
    pos = [(15, 55), (15, 400), (600, 400), (600, 55)]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           f'<rect width="{W}" height="{H}" fill="white"/>',
           f'<rect x="5" y="5" width="{W-10}" height="{H-10}" fill="none" stroke="black" stroke-width="1"/>',
           f'<text x="18" y="30" font-family="Arial" font-size="19" font-weight="bold">{title}</text>',
           f'<text x="18" y="48" font-family="Arial" font-size="12">Hüllmaße (Einbaulage): L(x) = {b.xlen:.1f} mm · '
           f'B(y) = {b.ylen:.1f} mm · H(z) = {b.zlen:.1f} mm · Volumen = {vol(wp)/1000:.2f} cm³ · alle Maße in mm · '
           f'erzeugt aus cad/source (parametrisch)</text>']
    for (label, kind), (x, y) in zip(views, pos):
        inner, sc, xl, yl = _svg_view(shape, kind, vw, vh)
        body = inner[inner.find(">", inner.find("<svg")) + 1:inner.rfind("</svg>")]     # ohne verschachteltes <svg>:
        out.append(f'<g transform="translate({x},{y})">{body}</g>')                     # gleiche Darstellung in allen Viewern
        out.append(f'<text x="{x+6}" y="{y+12}" font-family="Arial" font-size="11" fill="#333">{label}'
                   + (f' – Maßstab {sc/3.7795:.2f} : 1 (bei 96 dpi)' if sc else '') + '</text>')
        if sc:      # Masslinien fuer die Huellmasse der Ansicht
            cx, cy = x + vw / 2, y + vh / 2
            l, r, t, bt = cx - sc * xl / 2, cx + sc * xl / 2, cy - sc * yl / 2, cy + sc * yl / 2
            yd, xd = bt + 16, l - 16
            st = 'stroke="#0a4a9a" stroke-width="0.8" fill="none"'
            out.append(f'<path d="M{l:.1f},{bt+3:.1f} V{yd+4:.1f} M{r:.1f},{bt+3:.1f} V{yd+4:.1f} M{l:.1f},{yd:.1f} H{r:.1f} '
                       f'M{l:.1f},{yd:.1f} l6,-3 M{l:.1f},{yd:.1f} l6,3 M{r:.1f},{yd:.1f} l-6,-3 M{r:.1f},{yd:.1f} l-6,3" {st}/>')
            out.append(f'<text x="{cx:.1f}" y="{yd-3:.1f}" font-family="Arial" font-size="11" fill="#0a4a9a" text-anchor="middle">{xl:.1f}</text>')
            out.append(f'<path d="M{l-3:.1f},{t:.1f} H{xd-4:.1f} M{l-3:.1f},{bt:.1f} H{xd-4:.1f} M{xd:.1f},{t:.1f} V{bt:.1f} '
                       f'M{xd:.1f},{t:.1f} l-3,6 M{xd:.1f},{t:.1f} l3,6 M{xd:.1f},{bt:.1f} l-3,-6 M{xd:.1f},{bt:.1f} l3,-6" {st}/>')
            out.append(f'<text x="{xd-4:.1f}" y="{cy:.1f}" font-family="Arial" font-size="11" fill="#0a4a9a" text-anchor="middle" '
                       f'transform="rotate(-90 {xd-4:.1f} {cy:.1f})">{yl:.1f}</text>')
    yy = 755
    out.append(f'<rect x="590" y="{yy-22}" width="578" height="{H-yy+12}" fill="#f6f6f6" stroke="black" stroke-width="0.6"/>')
    for i, n in enumerate(notes[:5]):
        out.append(f'<text x="598" y="{yy-6+i*15}" font-family="Arial" font-size="11">{n}</text>')
    out.append("</svg>")
    (DRAW if not name.startswith("zusammenbau") else ASM).joinpath(name + ".svg").write_text("\n".join(out), encoding="utf-8")


def render_png(parts: dict, colors: dict, path, elev, azim, title, tol=0.25):
    """Einfache schattierte Vorschau (matplotlib) aus den tessellierten CAD-Koerpern."""
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(11, 7.5))
    ax = fig.add_subplot(111, projection="3d")
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    light = np.array([0.3, -0.5, 0.8]); light = light / np.linalg.norm(light)
    polys, cols = [], []
    for n, v in parts.items():
        c = np.array(colors.get(n.split("_")[0], (0.7, 0.7, 0.7)))
        for sol in v.vals():
            vs, tris = sol.tessellate(tol)
            if not tris:
                continue
            V = np.array([(q.x, q.y, q.z) for q in vs])
            Pt = V[np.array(tris)]
            nrm = np.cross(Pt[:, 1] - Pt[:, 0], Pt[:, 2] - Pt[:, 0])
            ln = np.linalg.norm(nrm, axis=1); ln[ln == 0] = 1
            sh = 0.45 + 0.55 * np.abs((nrm / ln[:, None]) @ light)
            polys.append(Pt); cols.append(np.clip(c[None, :] * sh[:, None], 0, 1))
            lo, hi = np.minimum(lo, V.min(0)), np.maximum(hi, V.max(0))
    # EINE Sammlung -> Tiefensortierung je Dreieck (sonst verdecken sich ganze Bauteile falsch)
    ax.add_collection3d(Poly3DCollection(np.concatenate(polys), facecolors=np.concatenate(cols), edgecolors="none"))
    ctr, rng = (lo + hi) / 2, (hi - lo).max() / 2 * 0.62
    ax.set_xlim(ctr[0] - rng, ctr[0] + rng); ax.set_ylim(ctr[1] - rng, ctr[1] + rng); ax.set_zlim(ctr[2] - rng, ctr[2] + rng)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    ax.set_title(title, fontsize=12)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=0.95)
    fig.savefig(path, dpi=110)
    plt.close(fig)

# ------------------------------------------------------------------ Hauptprogramm
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="ohne Zeichnungen")
    args = ap.parse_args()
    report = {"checks": [], "warn": []}

    def check(name, ok, detail):
        report["checks"].append({"Pruefung": name, "Ergebnis": "OK" if ok else "FEHLER", "Detail": detail})
        print(("  [OK]     " if ok else "  [FEHLER] ") + name + " -- " + detail)

    print("== Bauteile erzeugen ==")
    deck = make_deck()
    wheel = make_wheel_local()
    bracket = make_bracket()
    rod = make_rod()
    collar = make_collar()
    base = make_base()
    slider = make_slider()
    clip = make_clip()
    spacer = make_spacer()
    gears = {}
    for name in GEAR_PAIRS:
        g1, g2, a = gear_pair(name)
        gears[name] = (g1, g2, a, make_pinion_local(g1), make_gear_local(g2))

    # ---- Druckteile: (Name, Koerper in Drucklage, Werkstoff, Stueck, Drucklage-Hinweis)
    printed = [
        ("01_deck_hauptrahmen", to_print(deck, rx=180), "ASA", 1, "Oberseite auf der Platte, Rippen/Lagerböcke nach oben"),
        ("02_rad", to_print(wheel, rx=180), "PLA Basic", 4, "Außenseite auf der Platte, Nabenbund nach oben; O-Ring 45x2 aufziehen"),
        ("03_stossfaengertraeger", to_print(bracket, ry=90), "PETG HF", 2, "Pufferfläche auf der Platte"),
        ("04_schaltstange", to_print(rod), "PETG HF", 2, "flach (Nockenkontur in der Druckebene)"),
        ("05_federteller", to_print(collar, ry=90), "PETG HF", 2, "Bohrung senkrecht"),
        ("06_schaltbasis", to_print(base), "PETG HF", 1, "Grundplatte unten"),
        ("07_schaltschieber", to_print(slider), "PETG HF", 1, "Platte unten, Stifte nach oben"),
        ("08_modulklammer", to_print(clip, rx=180), "PETG HF", 8, "Lippe auf der Platte"),
        ("09_distanzhuelse_fuehrung", to_print(spacer), "PETG HF", 2, "stehend"),
    ]
    for name, (g1, g2, a, pin, gear) in gears.items():
        printed.append((f"10_ritzel_z{g1.z}_{name}", to_print(pin), "PLA Basic", 1, "flach, 0,2-mm-Düse"))
        printed.append((f"11_abtriebsrad_z{g2.z}_{name}", to_print(gear), "PLA Basic", 1,
                        "Stegseite auf der Platte, Nabe oben, 0,2-mm-Düse"))

    print("== Export STL / STEP ==")
    rows = []
    for name, body, mat, qty, hint in printed:
        exporters.export(body, str(STL / f"{name}.stl"), tolerance=0.02, angularTolerance=0.15)
        exporters.export(body, str(STEP / f"{name}.step"))
        b = bbox(body)
        v = vol(body) / 1000.0
        rows.append({"Teil": name, "Werkstoff": mat, "Stueck": qty, "Volumen_cm3": round(v, 3),
                     "Masse_je_Stueck_g": round(v * DENSITY[mat], 2), "Masse_gesamt_g": round(v * DENSITY[mat] * qty, 2),
                     "Druckmass_x_mm": round(b[1] - b[0], 1), "Druckmass_y_mm": round(b[3] - b[2], 1),
                     "Druckhoehe_z_mm": round(b[5] - b[4], 1), "Drucklage": hint})
        print(f"   {name:42s} {v:7.2f} cm³  {v*DENSITY[mat]:6.2f} g  {b[1]-b[0]:6.1f} x {b[3]-b[2]:6.1f} x {b[5]-b[4]:5.1f} mm")
    with open(BOM / "druckteile_massen.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter=";")
        w.writeheader()
        w.writerows(rows)

    # ---- Zusammenbau (Einbaulage), Grundzustand: Schieber in Lage VOR
    g1, g2, a, pin_l, gear_l = gears[GEAR_DEFAULT]
    xm = -AXLE_X + a
    asm = {"deck": deck}
    for sx in (1, -1):
        for sy in (1, -1):
            asm[f"rad_{'v' if sx>0 else 'h'}{'l' if sy>0 else 'r'}"] = place_axis_y(wheel, sx * AXLE_X, sy * WHEEL_Y, AXLE_Z, sy)
            asm[f"lager_{sx}_{sy}"] = dummy_bearing_y(sx * AXLE_X, sy * (PYL_Y + PYL_T / 2 - BRG_W / 2))
        asm[f"achse_{sx}"] = CY(sx * AXLE_X, AXLE_Z, AXLE_D, -WHEEL_Y - 3, WHEEL_Y + 3)
        asm[f"fuehrungsrolle_{sx}"], asm[f"fuehrungsschraube_{sx}"] = dummy_guide(sx)
        asm[f"distanzhuelse_{sx}"] = spacer.translate((sx * GUIDE_X, 0, 0))
    asm["abtriebsrad"] = place_axis_y(gear_l, -AXLE_X, GEAR_Y - GEAR_W / 2, AXLE_Z, 1)
    pin_rot = pin_l.rotate((0, 0, 0), (0, 0, 1), 180.0 / g1.z if g1.z % 2 == 0 else 0.0)
    asm["ritzel"] = place_axis_y(pin_rot, xm, GEAR_Y - PINION_W / 2, AXLE_Z, 1)
    asm["motor"] = dummy_motor_ff130(a)
    asm["traeger_v"], asm["traeger_h"] = bracket, rot_z180(bracket)
    asm["puffer_v"], asm["puffer_h"] = make_pad(), rot_z180(make_pad())
    asm["stange_v"], asm["stange_h"] = rod, rot_z180(rod)
    asm["federteller_v"], asm["federteller_h"] = collar, rot_z180(collar)
    asm["schaltbasis"] = base
    asm["schieber"] = slider.translate((0, -SLIDE_H, 0))
    asm["schalter_R"], asm["schalter_V"] = dummy_switches()
    for i, m in enumerate(dummy_modules()):
        asm[f"modul_{i+1}"] = m
    k = 0
    for sx in (1, -1):
        for sy in (1, -1):
            for cx in (20, 58):
                c = clip if sy > 0 else clip.mirror("XZ")
                asm[f"klammer_{k}"] = c.translate((sx * cx, sy * MOD_W, Z_TOP))
                k += 1

    print("== Pruefungen ==")
    # 1 Reglement-Huellmasse
    veh = [v for n, v in asm.items()]
    xs = [bbox(v) for v in veh]
    L = max(b[1] for b in xs) - min(b[0] for b in xs)
    W = max(b[3] for b in xs) - min(b[2] for b in xs)
    Hh = max(b[5] for b in xs)
    zmin = min(b[4] for b in xs)
    check("Länge über alles <= 300 mm", L <= MAX_LEN, f"{L:.1f} mm (Stangenspitzen in Ruhelage; max. je Seite {X_TIP:.1f} mm)")
    check("Breite <= 140 mm", W <= MAX_WID, f"{W:.1f} mm")
    check("Führungsrolle <= 8 mm (DM-Reglement)", BRG_OD <= PIN_MAX, f"d = {BRG_OD} mm in Schiene innen {RAIL_W-2*RAIL_T:.0f} mm")
    report["huelle"] = {"Laenge_mm": round(L, 1), "Breite_mm": round(W, 1), "Hoehe_mm": round(Hh, 1), "tiefster_Punkt_mm": round(zmin, 2)}
    print(f"   Höhe über Fahrbahn: {Hh:.1f} mm (Tunnelhöhe im Reglement nicht angegeben!)")

    # 2 Schiene (Annahme: auf der Bahn aufliegend)
    rail = dummy_rail()
    worst = max(((n, inter_vol(v, rail)) for n, v in asm.items()), key=lambda t: t[1])
    check("keine Durchdringung mit Führungsschiene", worst[1] < 0.01, f"größte Überschneidung: {worst[0]} = {worst[1]:.3f} mm³")
    low = min((bbox(v)[4], n) for n, v in asm.items() if not n.startswith(("rad", "fuehrung")))
    check("Bodenfreiheit aller Teile außer Rad/Führung >= 2,5 mm", low[0] >= 2.5, f"{low[1]}: {low[0]:.2f} mm")
    # Huellraum der Schiene: seitliches Fuehrungsspiel +-2,4 mm und 2 mm nach oben
    worst_env = ("-", 0.0)
    for shift in ((0, 2.4, 0), (0, -2.4, 0), (0, 0, 2.0)):
        r2 = rail.translate(shift)
        for n, v in asm.items():
            iv = inter_vol(v, r2)
            if iv > worst_env[1]:
                worst_env = (f"{n} bei Versatz {shift}", iv)
    check("Freiraum zur Schiene (seitlich ±2,4 mm, 2 mm nach oben)", worst_env[1] < 0.05,
          f"größte Überschneidung mit verschobener Schiene: {worst_env[0]} = {worst_env[1]:.3f} mm³")

    # 3 Kollisionen im Zusammenbau (mehrere Schaltzustaende)
    press_ok = {("deck", "lager"), ("achse", "rad"), ("achse", "lager"), ("abtriebsrad", "achse"), ("motor", "ritzel"),
                ("fuehrungsrolle", "fuehrungsschraube"), ("distanzhuelse", "fuehrungsschraube"), ("deck", "fuehrungsschraube"),
                ("federteller", "stange"), ("puffer", "stange")}

    def allowed(n1, n2):
        k1, k2 = sorted((n1.split("_")[0], n2.split("_")[0]))
        return (k1, k2) in press_ok

    def collide(state_name, a_dict):
        names = list(a_dict)
        bad = []
        for n1, n2 in itertools.combinations(names, 2):
            if allowed(n1, n2):
                continue
            v = inter_vol(a_dict[n1], a_dict[n2])
            if v > 0.05:
                bad.append(f"{n1}/{n2}: {v:.2f} mm³")
        check(f"Kollisionsfrei – {state_name}", not bad, "keine Durchdringung > 0,05 mm³" if not bad else "; ".join(bad[:8]))

    collide("Grundzustand (Stangen aus, Schieber VOR)", asm)
    mech_keys = ["deck", "schaltbasis", "schalter_R", "schalter_V", "traeger_v", "traeger_h", "puffer_v", "puffer_h",
                 "modul_1", "modul_2", "modul_3", "modul_4", "motor", "abtriebsrad"]
    travel_max = ROD_PROTRUDE + PAD_COMPRESS * PAD_T
    for label, d_v, d_h in (("Stange vorn 4,5 mm (Rampe)", 4.5, 0.0), ("Stange vorn 10 mm (Pufferkontakt)", 10.0, 0.0),
                            (f"Stange vorn {travel_max:.0f} mm (Puffer voll gestaucht)", travel_max, 0.0),
                            ("Ruhe, Schieber RÜCK", 0.0, 0.0, ), ("Stange hinten 10 mm", 0.0, 10.0),
                            (f"Stange hinten {travel_max:.0f} mm", 0.0, travel_max)):
        st = {k_: asm[k_] for k_ in mech_keys}
        if label.startswith("Ruhe"):
            ys = SLIDE_H
        elif d_v > 0:
            ys = slider_y_for_rod_travel(d_v)
        else:
            ys = -slider_y_for_rod_travel(d_h)
        st["schieber"] = slider.translate((0, ys, 0))
        st["stange_v"] = rod.translate((-d_v, 0, 0))
        st["federteller_v"] = collar.translate((-d_v, 0, 0))
        st["stange_h"] = rot_z180(rod).translate((d_h, 0, 0))
        st["federteller_h"] = rot_z180(collar).translate((d_h, 0, 0))
        if d_v >= 10:
            st.pop("puffer_v")           # Schaumstoff wird gestaucht
        if d_h >= 10:
            st.pop("puffer_h")
        collide(label + f" [Schieber y = {ys:+.2f}]", st)

    spring_seat_x = AXLE_X + T_RIB / 2
    spring_min = (BRK_PLATE_X0 - COLLAR_L - travel_max) - spring_seat_x
    check("Rückstellfeder geht bei voller Pufferstauchung nicht auf Block", spring_min >= 4.5,
          f"Einbauraum Feder {BRK_PLATE_X0 - COLLAR_L - spring_seat_x:.1f} mm, bei {travel_max:.0f} mm Stangenweg noch {spring_min:.1f} mm (Blocklänge 14 Wdg. x 0,25 = 3,5 mm)")
    check("Rastfläche der Stange lang genug für vollen Stangenweg", X_R0 + RAMP_RUN + DWELL_LEN - travel_max >= PIN_X + PIN_D / 2 + 1.0,
          f"Rastende bei x = {X_R0 + RAMP_RUN + DWELL_LEN - travel_max:.1f} mm, Stift bis x = {PIN_X + PIN_D/2:.1f} mm")
    check("Schieber vollständig umgelegt, bevor der Puffer anliegt", ROD_SWITCH_TRAVEL < ROD_PROTRUDE - 1.0,
          f"Umschaltweg {ROD_SWITCH_TRAVEL:.2f} mm < Überstand {ROD_PROTRUDE:.1f} mm")
    # Mikroschalter: Betaetigungsweg um den Schaltpunkt (D2F-L: OP 6,8 +-1,5, Differenzweg max 0,5)
    press_pos = SW_HOLE_Y - (SLIDER_LY / 2 + SLIDE_H)
    free_pos = SW_HOLE_Y - (SLIDER_LY / 2 - SLIDE_H)
    check("Mikroschalter: gedrückt jenseits OP, frei jenseits Rückschaltpunkt (Nennlage)",
          press_pos <= 6.8 - 0.2 and free_pos >= 6.8 + 0.5 + 0.5,
          f"Hebel gedrückt bei {press_pos:.1f} mm, frei bei {free_pos:.1f} mm ab Lochlinie; OP-Toleranz ±1,5 mm über Langlöcher ±1,7 mm")

    # 4 Verzahnung
    for name, (g1_, g2_, a_, pin_, gear_) in gears.items():
        eps = gg.contact_ratio(g1_, g2_, a_)
        c1, c2 = gg.tip_root_clearance(g1_, g2_, a_)
        gp = place_axis_y(gear_, -AXLE_X, GEAR_Y - GEAR_W / 2, AXLE_Z, 1)
        pr = pin_.rotate((0, 0, 0), (0, 0, 1), 180.0 / g1_.z if g1_.z % 2 == 0 else 0.0)
        pp = place_axis_y(pr, -AXLE_X + a_, GEAR_Y - PINION_W / 2, AXLE_Z, 1)
        iv = inter_vol(gp, pp)
        clear = AXLE_Z - g2_.da / 2
        ok = eps >= 1.15 and min(c1, c2) >= 0.15 and iv < 0.02 and A_MIN <= a_ <= A_MAX and clear >= 2.5 and g1_.sa >= 0.39
        check(f"Zahnradpaar {name} z={g1_.z}/{g2_.z}", ok,
              f"i={g2_.z/g1_.z:.2f}, a={a_:.2f} mm, Überdeckung {eps:.2f}, Kopfspiel {min(c1,c2):.2f} mm, "
              f"Durchdringung {iv:.3f} mm³, Bodenfreiheit Rad {clear:.1f} mm, Zahnkopf Ritzel {g1_.sa:.2f} mm")
    check("Motorwelle erreicht Ritzelbreite", MOTOR_PLATE_Y + FF_SHAFT_L >= GEAR_Y + PINION_W / 2 - 0.5,
          f"Wellenende y = {MOTOR_PLATE_Y + FF_SHAFT_L:.2f}, Ritzel bis y = {GEAR_Y + PINION_W/2:.2f}")

    # 5 Wandstaerken / Druckbarkeit (konstruktive Mindestwerte)
    check("Mindestwandstärken >= 1,0 mm (0,4-mm-Düse: >= 2 Bahnen)", min(T_PLATE, T_RIB, 1.2) >= 1.0,
          f"Deckplatte {T_PLATE} mm, Rippen {T_RIB} mm, Lagerbock {PYL_T} mm, Motorplatte {MOTOR_PLATE_T} mm")
    bd = bbox(printed[0][1])
    check("Deck passt auf 256 x 256 mm Druckbett", bd[1] - bd[0] <= 250 and bd[3] - bd[2] <= 250,
          f"{bd[1]-bd[0]:.0f} x {bd[3]-bd[2]:.0f} x {bd[5]-bd[4]:.0f} mm (für 180-mm-Betten: im Slicer bei x = 0 teilen)")

    # 6 Masse, Schwerpunkt, Traegheiten
    dens = {"deck": DENSITY["ASA"], "rad": DENSITY["PLA Basic"], "abtriebsrad": DENSITY["PLA Basic"], "ritzel": DENSITY["PLA Basic"]}
    fixed = {"motor": 24.0, "schalter": 0.5, "lager": 0.2, "achse": 2.3, "modul": MOD_MASS_G, "puffer": 0.25,
             "fuehrungsrolle": 0.2, "fuehrungsschraube": 1.1}
    m_tot, mx, mz, parts_m = 0.0, 0.0, 0.0, {}
    for n, v in asm.items():
        key = n.split("_")[0]
        if key in fixed:
            m = fixed[key]
        else:
            m = vol(v) / 1000.0 * dens.get(key, DENSITY["PETG HF"])
        c = cq.Shape.centerOfMass(solid(v))
        m_tot += m; mx += m * c.x; mz += m * c.z
        parts_m[key] = parts_m.get(key, 0.0) + m
    extra = {"O-Ringe 4x": 4 * 0.37, "Schrauben/Muttern": 6.0, "Kabel, Lötzinn, Stiftleiste": 6.0, "Federn 2x": 0.4,
             "Magnete 2x": 0.4, "Klebeband/Kleber": 2.0}
    m_all = m_tot + sum(extra.values())
    xs_cg, zs_cg = mx / m_tot, mz / m_tot
    rear_frac = (AXLE_X - xs_cg) / (2 * AXLE_X)
    wl = solid(wheel)
    j_wheel = vol(wheel) / 1e9 * DENSITY["PLA Basic"] * 1000 * (cq.Shape.matrixOfInertia(wl)[2][2] / wl.Volume()) / 1e6 \
        + 0.37e-3 * (0.024) ** 2
    gl = solid(gear_l)
    j_gear = vol(gear_l) / 1e9 * DENSITY["PLA Basic"] * 1000 * (cq.Shape.matrixOfInertia(gl)[2][2] / gl.Volume()) / 1e6
    pl = solid(pin_l)
    j_pin = vol(pin_l) / 1e9 * DENSITY["PLA Basic"] * 1000 * (cq.Shape.matrixOfInertia(pl)[2][2] / pl.Volume()) / 1e6
    report["masse"] = {"Baugruppen_g": {k_: round(v, 2) for k_, v in sorted(parts_m.items())},
                       "Kleinteile_Annahme_g": extra, "Gesamtmasse_g": round(m_all, 1),
                       "davon_Solarmodule_Annahme_g": 4 * MOD_MASS_G,
                       "Schwerpunkt_x_mm": round(xs_cg, 1), "Schwerpunkt_z_mm": round(zs_cg, 1),
                       "Achslastanteil_Antriebsachse": round(rear_frac, 3),
                       "J_Rad_kgm2": float(f"{j_wheel:.3e}"), "J_Abtriebsrad_kgm2": float(f"{j_gear:.3e}"),
                       "J_Ritzel_kgm2": float(f"{j_pin:.3e}")}
    print(f"   Gesamtmasse {m_all:.1f} g (davon Module {4*MOD_MASS_G:.0f} g Annahme), Schwerpunkt x = {xs_cg:.1f} mm, "
          f"z = {zs_cg:.1f} mm, Antriebsachslast {rear_frac*100:.0f} %")
    print(f"   J Rad = {j_wheel:.2e}, J Abtriebsrad = {j_gear:.2e}, J Ritzel = {j_pin:.2e} kg·m²")
    pad_z = ROD_Z - 0.5
    check("Pufferhöhe nahe Schwerpunkthöhe (Kippmoment beim Aufprall)", abs(pad_z - zs_cg) <= 6.0,
          f"Puffermitte z = {pad_z:.1f} mm, Schwerpunkt z = {zs_cg:.1f} mm")

    report["kennwerte"] = {"Umschaltweg_Stange_mm": round(ROD_SWITCH_TRAVEL, 2), "Stangenueberstand_mm": ROD_PROTRUDE,
                           "Laenge_ueber_alles_mm": round(LEN_OVER_ALL, 1), "Achsabstand_Getriebe_mm": round(a, 2),
                           "Radstand_mm": 2 * AXLE_X, "Spurweite_mm": 2 * WHEEL_Y}
    n_bad = sum(1 for c in report["checks"] if c["Ergebnis"] != "OK")
    report["zusammenfassung"] = f"{len(report['checks']) - n_bad} von {len(report['checks'])} Prüfungen OK"
    (ASM / "pruefbericht.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md = ["# Prüfbericht CAD (automatisch erzeugt von cad/source/build_all.py)", "",
          "Geprüft wird ausschließlich die Geometrie des CAD-Modells. Kein Ersatz für Praxistests.", "",
          "| Prüfung | Ergebnis | Detail |", "|---|---|---|"]
    md += [f"| {c['Pruefung']} | {c['Ergebnis']} | {c['Detail']} |" for c in report["checks"]]
    md += ["", "## Hüllmaße", "", "```json", json.dumps(report["huelle"], indent=2, ensure_ascii=False), "```", "",
           "## Masse und Schwerpunkt", "", "```json", json.dumps(report["masse"], indent=2, ensure_ascii=False), "```", "",
           "## Kennwerte", "", "```json", json.dumps(report["kennwerte"], indent=2, ensure_ascii=False), "```"]
    (ASM / "pruefbericht.md").write_text("\n".join(md), encoding="utf-8")
    print("==", report["zusammenfassung"], "==")

    # ---- Zusammenbau-STEP
    colors = {"deck": (0.85, 0.85, 0.9), "rad": (0.15, 0.15, 0.15), "modul": (0.1, 0.15, 0.45), "motor": (0.6, 0.6, 0.6),
              "abtriebsrad": (0.95, 0.75, 0.1), "ritzel": (0.95, 0.5, 0.1), "stange": (0.9, 0.2, 0.2),
              "schieber": (0.1, 0.7, 0.2), "schaltbasis": (0.3, 0.6, 0.9), "schalter": (0.1, 0.1, 0.1),
              "traeger": (0.9, 0.4, 0.1), "puffer": (0.3, 0.3, 0.3)}
    assy = cq.Assembly(name="SolarMobil_Expert")
    for n, v in asm.items():
        c = colors.get(n.split("_")[0], (0.7, 0.7, 0.7))
        assy.add(v, name=n, color=cq.Color(*c))
    assy.export(str(STEP / "00_zusammenbau_solarmobil.step"))
    mech = cq.Assembly(name="Umkehrmechanismus")
    for n in ("schaltbasis", "schieber", "stange_v", "stange_h", "federteller_v", "federteller_h", "schalter_R",
              "schalter_V", "traeger_v", "traeger_h"):
        mech.add(asm[n], name=n, color=cq.Color(*colors.get(n.split("_")[0], (0.7, 0.7, 0.7))))
    mech.export(str(STEP / "00_baugruppe_umkehrmechanismus.step"))

    print("== Vorschaubilder ==")
    render_png(asm, colors, ASM / "vorschau_gesamt.png", 24, -58, "SolarMobil – Gesamtansicht (CAD-Vorschau)")
    render_png({n: v for n, v in asm.items() if not n.startswith(("modul", "klammer"))}, colors,
               ASM / "vorschau_unterseite.png", -38, -60, "Ansicht von unten (Module ausgeblendet)")
    render_png({n: v for n, v in asm.items() if not n.startswith(("modul", "klammer", "deck"))}, colors,
               ASM / "vorschau_ohne_deck.png", 38, -62, "Antrieb und Umkehrmechanismus (Deck und Module ausgeblendet)")
    render_png({n: asm[n] for n in ("schaltbasis", "schieber", "schalter_R", "schalter_V")} |
               {"stange_v": rod.intersect(B(-40, 45, -30, 30, 0, 99)), "stange_h": rot_z180(rod).intersect(B(-45, 40, -30, 30, 0, 99))},
               colors, ASM / "vorschau_schalteinheit.png", 58, -70, "Schalteinheit: Basis, Schieber, Nockenenden der Schaltstangen, Mikroschalter", tol=0.1)
    if args.fast:
        return n_bad
    print("== Zeichnungen ==")
    g1, g2, a, pin_l, gear_l = gears[GEAR_DEFAULT]
    notes = {
        "01_deck_hauptrahmen": [f"Deck {DECK_L:.0f} x {DECK_W:.0f}, Platte {T_PLATE}, Rippen {T_RIB} x {H_RIB}; Auflage z = {Z_TOP}",
                                f"Lagersitze d{BRG_OD+FIT:.2f} x {BRG_W+0.1:.1f} (MR63ZZ), Achshöhe {AXLE_Z:.0f}, Radstand {2*AXLE_X:.0f}",
                                f"Motorplatte: Langloch Bund d{FF_BOSS_D+0.4:.2f}, Achsabstand {A_MIN}…{A_MAX} einstellbar",
                                "Kernlöcher d1,6 für M2 selbstschneidend; Führungssäule Kernloch d2,5 (M3)",
                                "Werkstoff ASA (alternativ PETG HF); Drucklage: Oberseite auf der Platte, ohne Stützen"],
        "02_rad": [f"Außen-d mit O-Ring {WHEEL_D:.0f}; Nutgrund d{ORING_ID+1:.1f}; Breite {WHEEL_W}", f"Bohrung d{AXLE_D-PRESS:.2f} (Presssitz auf d3-Achse, mit Sekundenkleber sichern)",
                   "5 Speichen 1,4 x 3; Nabe d8", "Werkstoff PLA Basic, 4 Stück"],
        "03_stossfaengertraeger": ["Pufferplatte 44 x 21,1 x 2; Durchbruch 3,6 x 3,6 für Schaltstange", "2 x d2,3 für M2 in Deck-Dome; Lippe hält Modulenden nieder",
                                   f"Schaumstoffpuffer {PAD_W:.0f} x {PAD_H:.0f} x {PAD_T:.0f} außen aufkleben", "Werkstoff PETG HF, 2 Stück (hinten um 180° gedreht)"],
        "04_schaltstange": [f"Schaft {ROD_S} x {ROD_S}; Rampe {RAMP_DEG:.0f}°, Hub {2*SLIDE_H:.1f}, Rast {DWELL_LEN:.0f} lang",
                            f"Umschaltweg {ROD_SWITCH_TRAVEL:.2f} < Überstand {ROD_PROTRUDE:.0f}", "Gleitflächen entgraten, nicht schmieren (PETG auf PETG trocken)",
                            "Werkstoff PETG HF, 2 Stück identisch"],
        "05_federteller": ["6 x 6 x 3, Vierkant 3,16; nach Aufschieben der Feder mit Sekundenkleber fixieren", "Anschlag der Stange nach außen (an Trägerplatte)"],
        "06_schaltbasis": ["Grundplatte 36 x 52 x 2 + Lasche für Stiftleiste 1x4", "Langlöcher 2,3 x 3,4 zum Justieren der Mikroschalter (D2F-L)",
                           "Wände mit Kernloch d2,6 für M3-Stahlschraube (Anschlag + Magnet-Gegenpol)", "4 x d2,3 für M2 in Deck-Dome; Werkstoff PETG HF"],
        "07_schaltschieber": [f"Weg ±{SLIDE_H} mm; Stifte d{PIN_D} bei (±{PIN_X}, ∓{PIN_Y})", f"Magnettaschen d{MAG_D+0.1:.1f} x {MAG_T+0.1:.1f} in den Stirnwänden", "Werkstoff PETG HF"],
        "08_modulklammer": [f"für Moduldicke {MOD_T} mm (Parameter MOD_T!)", "M2 x 8 selbstschneidend in Deck-Dom"],
        "09_distanzhuelse_fuehrung": ["d5 / d3,3 x 7,75; zwischen Führungslager und Säule"],
    }
    for name, body, mat, qty, hint in printed[:9]:
        src = {"01_deck_hauptrahmen": deck, "02_rad": wheel, "03_stossfaengertraeger": bracket, "04_schaltstange": rod,
               "05_federteller": collar, "06_schaltbasis": base, "07_schaltschieber": slider, "08_modulklammer": clip,
               "09_distanzhuelse_fuehrung": spacer}[name]
        drawing(src, name, f"{name}  –  {mat}  –  {qty} Stück", notes.get(name, []) + [f"Drucklage: {hint}"])
        print("   Zeichnung", name)
    for name, (g1_, g2_, a_, pin_, gear_) in gears.items():
        rep = gg.pair_report(GEAR_M, g1_.z, g2_.z, backlash=GEAR_BACKLASH_A)
        both = gear_.union(pin_.translate((a_, 0, 0)), clean=False)
        drawing(both, f"10_zahnradpaar_{name}", f"Zahnradpaar {name}: z = {g1_.z} / {g2_.z}, Modul {GEAR_M}, i = {g2_.z/g1_.z:.2f}  –  PLA Basic",
                [f"Achsabstand {a_:.2f} (inkl. {GEAR_BACKLASH_A} Spiel); Profilverschiebung x = {g1_.x:+.2f} / {g2_.x:+.2f}",
                 f"Ritzel: d = {rep['d1_mm']}, da = {rep['da1_mm']}, df = {rep['df1_mm']}, Bohrung d{2-PRESS:.2f}, Breite {PINION_W}",
                 f"Rad: d = {rep['d2_mm']}, da = {rep['da2_mm']}, df = {rep['df2_mm']}, Bohrung d{AXLE_D-PRESS:.2f}, Breite {GEAR_W}",
                 f"Überdeckung {rep['Ueberdeckung']}; Flankenrückzug {GEAR_FLANK_COMP} je Flanke; Eingriffswinkel 20°",
                 "Druck mit 0,2-mm-Düse, 0,1 mm Schicht, 100 % Füllung"],
                views=[("Ansicht in Achsrichtung", "oben"), ("Seitenansicht", "seite"), ("Seitenansicht 2", "stirn"), ("Isometrie", "iso")])
        print("   Zeichnung Zahnradpaar", name)
    # Zusammenbau: Gesamtfahrzeug (ohne Module in der Untersicht) und Mechanik
    comp_all = cq.Workplane("XY").add(cq.Compound.makeCompound([solid(v) for v in asm.values()]))
    drawing(comp_all, "zusammenbau_gesamt", "Zusammenbau SolarMobil Ultraleicht-Expert",
            [f"Länge über alles {L:.0f} (max. 300) · Breite {W:.0f} (max. 140) · Höhe {Hh:.0f}",
             f"Radstand {2*AXLE_X:.0f} · Spurweite {2*WHEEL_Y:.0f} · Rad d{WHEEL_D:.0f} · Achshöhe {AXLE_Z:.0f}",
             f"Getriebe {g1.z}:{g2.z} (i = {g2.z/g1.z:.1f}), Achsabstand {a:.2f}",
             f"Gesamtmasse ca. {m_all:.0f} g (Module {4*MOD_MASS_G:.0f} g = Annahme)", "Schiene 15 x 15 x 2 nicht dargestellt"])
    comp_under = cq.Workplane("XY").add(cq.Compound.makeCompound([solid(v) for n, v in asm.items() if not n.startswith(("modul", "klammer"))]))
    drawing(comp_under, "zusammenbau_fahrwerk_ohne_module", "Fahrwerk und Umkehrmechanismus (Module ausgeblendet)",
            ["Ansicht von unten zeigt Schaltbasis, Schieber, Mikroschalter und beide Schaltstangen",
             "Stange vorn (rot im STEP) bei y = -7,2; Stange hinten bei y = +7,2", "Elektrik von unten und von der Seite vollständig einsehbar"],
            views=[("Untersicht", "unten"), ("Seitenansicht (von links)", "seite"), ("Stirnansicht (von vorn)", "stirn"), ("Isometrie von unten", "iso_unten")])
    mech_keys2 = ["schaltbasis", "schieber", "stange_v", "stange_h", "schalter_R", "schalter_V", "federteller_v", "federteller_h"]
    comp_m = cq.Workplane("XY").add(cq.Compound.makeCompound([solid(asm[n]) for n in mech_keys2]))
    drawing(comp_m, "zusammenbau_umkehrmechanismus", "Montagezeichnung Umkehrmechanismus (Grundzustand: Schieber in Lage VOR)",
            [f"Stange drückt Stift über {RAMP_DEG:.0f}°-Rampe: Schieberhub {2*SLIDE_H:.0f} mm nach {ROD_SWITCH_TRAVEL:.1f} mm Stangenweg",
             "Rastfläche der gedrückten Stange verriegelt den Schieber formschlüssig", "Magnet im Schieber + M3-Stahlschraube = Endanschlag und Halt",
             "Je Lage ist genau ein Mikroschalter (D2F-L) betätigt"],
            views=[("Draufsicht (von oben)", "oben"), ("Seitenansicht (von links)", "seite"), ("Stirnansicht (von vorn)", "stirn"), ("Isometrie", "iso")])
    # Explosionsdarstellung
    off = {"modul": 45, "klammer": 60, "deck": 20, "stange": 0, "federteller": 0, "schieber": -14, "schaltbasis": -26,
           "schalter": -20, "motor": -30, "abtriebsrad": -40, "ritzel": -40, "rad": -40, "achse": -40, "lager": -40,
           "traeger": 0, "puffer": 0, "fuehrungsrolle": -55, "fuehrungsschraube": -70, "distanzhuelse": -45}
    ex = []
    for n, v in asm.items():
        key = n.split("_")[0]
        dx = 0
        if key in ("traeger", "puffer"):
            dx = 25 if bbox(v)[0] > 0 else -25
        dy = 0
        if key == "rad":
            dy = 22 if bbox(v)[2] > 0 else -22
        ex.append(solid(v.translate((dx, dy, off.get(key, 0)))))
    drawing(cq.Workplane("XY").add(cq.Compound.makeCompound(ex)), "zusammenbau_explosion", "Explosionsdarstellung",
            ["Von oben nach unten: Modulklammern, Solarmodule, Deck, Schaltstangen, Schieber, Schalter, Schaltbasis,",
             "Motor, Getriebe/Achsen/Räder, Führungsrollen"],
            views=[("Seitenansicht (von links)", "seite"), ("Stirnansicht (von vorn)", "stirn"), ("Isometrie von unten", "iso_unten"), ("Isometrie", "iso")])
    return n_bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
