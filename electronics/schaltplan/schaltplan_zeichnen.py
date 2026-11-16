"""Zeichnet Schaltplan und Funktionsdiagramm des Umkehrmechanismus.

    python schaltplan_zeichnen.py

Ausgabe: schaltplan.png / .svg (dieser Ordner) und
         results/diagrams/umkehr_funktionsdiagramm.png

Die Geometriewerte des Funktionsdiagramms stammen direkt aus
cad/source/params_cad.py (gleiche Parameter wie das CAD-Modell).
"""
import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, FancyArrowPatch

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "cad" / "source"))
import params_cad as C  # noqa: E402


def wire(ax, pts, color="k", lw=1.6, ls="-"):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, solid_capstyle="round")


def dot(ax, x, y, c="k"):
    ax.add_patch(Circle((x, y), 0.07, color=c, zorder=5))


def module(ax, x, y, name):
    ax.add_patch(Rectangle((x, y), 1.5, 0.8, fc="#1f3b8a", ec="k"))
    ax.text(x + 0.75, y + 0.4, name, color="w", ha="center", va="center", fontsize=8)
    ax.text(x - 0.08, y + 0.4, "+", ha="right", va="center", fontsize=11, color="r")
    ax.text(x + 1.58, y + 0.4, "–", ha="left", va="center", fontsize=11, color="b")


def spdt(ax, x, y, name, pressed):
    """Wechsler: COM links (x,y), NC oben rechts, NO unten rechts."""
    dot(ax, x, y); dot(ax, x + 1.0, y + 0.45); dot(ax, x + 1.0, y - 0.45)
    tgt = (x + 0.95, y - 0.40) if pressed else (x + 0.95, y + 0.40)
    wire(ax, [(x, y), tgt], lw=2.4)
    ax.text(x - 0.08, y + 0.12, "COM", fontsize=7, ha="right")
    ax.text(x + 1.08, y + 0.45, "NC  (Ruhe)", fontsize=7, va="center")
    ax.text(x + 1.08, y - 0.45, "NO  (betätigt)", fontsize=7, va="center")
    ax.text(x + 0.5, y + 0.78, f"{name} (Omron D2F-L): " + ("BETÄTIGT" if pressed else "frei"), fontsize=8, ha="center")


def schematic(ax, state):
    """state: 'VOR' oder 'RUECK'."""
    ax.set_xlim(-0.6, 15.6); ax.set_ylim(-1.0, 9.0); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"Schieberlage {state}: {'S_V betätigt → Motor vorwärts' if state == 'VOR' else 'S_R betätigt → Motor rückwärts'}", fontsize=10)
    yv, yh, py, yp, ym = 7.6, 6.0, 6.9, 4.6, -0.5          # Modulreihen, Stiftleiste, PLUS- und MINUS-Schiene
    module(ax, 0.3, yv, "M1 vorn"); module(ax, 2.6, yv, "M2 vorn")
    module(ax, 0.3, yh, "M3 hinten"); module(ax, 2.6, yh, "M4 hinten")
    wire(ax, [(1.8, yv + 0.4), (2.6, yv + 0.4)]); wire(ax, [(1.8, yh + 0.4), (2.6, yh + 0.4)])
    px = [6.0, 6.7, 7.4, 8.1]
    for x, lab in zip(px, ("V+", "H+", "V–", "H–")):
        ax.add_patch(Rectangle((x - 0.13, py - 0.13), 0.26, 0.26, fc="gold", ec="k", zorder=4))
        ax.text(x, py + 0.3, lab, fontsize=8, ha="center")
    ax.text(7.05, py + 1.35, "Stiftleiste 1×4 (2,54 mm) mit Steckbrücken", fontsize=8, ha="center")
    ax.add_patch(Rectangle((px[1] - 0.2, py - 0.2), px[2] - px[1] + 0.4, 0.4, fc="none", ec="g", lw=2.2, zorder=6))
    ax.text(7.05, py + 0.85, "grün = Brücke H+/V–: 4s (Sonne)   |   2s2p: Brücken V+/H+ und V–/H–", fontsize=7, ha="center", color="g")
    wire(ax, [(0.3, yv + 0.4), (-0.2, yv + 0.4), (-0.2, 8.8), (5.2, 8.8), (5.2, py), (6.0, py)], "r")       # V+
    wire(ax, [(4.1, yv + 0.4), (4.5, yv + 0.4), (4.5, 5.6), (7.4, 5.6), (7.4, py)], "b")                 # V-
    wire(ax, [(0.3, yh + 0.4), (-0.2, yh + 0.4), (-0.2, 5.3), (6.7, 5.3), (6.7, py)], "r")               # H+
    wire(ax, [(4.1, yh + 0.4), (4.3, yh + 0.4), (4.3, 5.0), (8.1, 5.0), (8.1, py)], "b")                 # H-
    wire(ax, [(6.0, py), (6.0, yp), (14.8, yp)], "r", 2.0); ax.text(14.9, yp, "PLUS", color="r", fontsize=8, va="center")
    wire(ax, [(8.1, 5.0), (8.6, 5.0), (8.6, ym), (14.8, ym)], "b", 2.0); ax.text(14.9, ym, "MINUS", color="b", fontsize=8, va="center")
    sv, sr = (10.0, 3.2), (10.0, 0.9)
    spdt(ax, *sv, "S_V", state == "VOR")
    spdt(ax, *sr, "S_R", state == "RUECK")
    for (x, y) in (sv, sr):
        wire(ax, [(x + 1.0, y + 0.45), (x + 3.4, y + 0.45), (x + 3.4, yp)], "r"); dot(ax, x + 3.4, yp, "r")
        wire(ax, [(x + 1.0, y - 0.45), (x + 4.0, y - 0.45), (x + 4.0, ym)], "b"); dot(ax, x + 4.0, ym, "b")
    ax.add_patch(Circle((7.2, 2.05), 0.55, fc="w", ec="k", lw=1.8)); ax.text(7.2, 2.05, "M", ha="center", va="center", fontsize=14)
    ax.text(7.2, 1.25, "FF-130SH-14230", fontsize=7, ha="center")
    wire(ax, [sv, (9.3, sv[1]), (9.3, 3.6), (7.2, 3.6), (7.2, 2.6)])
    wire(ax, [sr, (9.3, sr[1]), (9.3, 0.3), (6.1, 0.3), (6.1, 2.05), (6.65, 2.05)])
    ax.text(7.35, 3.0, "B", fontsize=9); ax.text(6.25, 2.3, "A", fontsize=9)
    pol = "A = PLUS, B = MINUS" if state == "VOR" else "A = MINUS, B = PLUS"
    info = "\n".join([f"Motorklemmen: {pol}", "", "Übergang (kein oder beide Schalter betätigt):",
                      "A = B → Motor kurzgeschlossen (bremst),", "der Solargenerator wird NIE kurzgeschlossen.", "",
                      "Keine Batterie, kein Kondensator.", "Hauptschalter = Steckbrücke ziehen."])
    ax.text(-0.3, 3.9, info, fontsize=8, va="top", bbox=dict(fc="#f4f4f4", ec="gray"))


def function_diagram(path):
    t = math.tan(math.radians(C.RAMP_DEG))
    d = [x * 0.05 for x in range(0, int(19 / 0.05) + 1)]
    ys = [min(C.SLIDE_H, max(-C.SLIDE_H, -C.SLIDE_H + t * (x - C.ROD_LEAD))) for x in d]
    d_sw = C.ROD_LEAD + 2 * C.SLIDE_H / t
    op_r = C.SLIDE_H - (6.8 - (C.SW_HOLE_Y - C.SLIDER_LY / 2 - C.SLIDE_H))     # Schieberlage, bei der S_R schaltet (Nennlage)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8.6), sharex=True, gridspec_kw={"height_ratios": [2.2, 1.3, 1.3]})
    ax = axes[0]
    ax.plot(d, ys, lw=2.2, label="Schieberlage y (aus Rampengeometrie)")
    ax.axvspan(0, C.ROD_LEAD, color="gray", alpha=0.15); ax.text(C.ROD_LEAD / 2, 2.0, "Leerweg", rotation=90, ha="center", va="center", fontsize=8)
    ax.axvline(d_sw, color="g", ls="--"); ax.text(d_sw + 0.15, -2.2, f"Schieber umgelegt\nnach {d_sw:.2f} mm", color="g", fontsize=8)
    ax.axvline(C.ROD_PROTRUDE, color="r", ls="--"); ax.text(C.ROD_PROTRUDE + 0.15, -0.6, f"Puffer berührt Anschlagbrett\n({C.ROD_PROTRUDE:.0f} mm)", color="r", fontsize=8)
    ax.axhline(op_r, color="orange", ls=":"); ax.axhline(-op_r, color="orange", ls=":")
    ax.text(18.9, op_r + 0.12, "S_R schaltet (OP, Nennlage)", fontsize=7, ha="right", color="darkorange")
    ax.text(18.9, -op_r - 0.35, "S_V schaltet zurück", fontsize=7, ha="right", color="darkorange")
    ax.set_ylabel("Schieberlage y [mm]\n–2,5 = VOR, +2,5 = RÜCK"); ax.grid(alpha=0.3); ax.legend(loc="upper left", fontsize=8)
    ax.set_title("Funktionsdiagramm Umkehrmechanismus: vordere Schaltstange wird vom Anschlagbrett eingedrückt")
    sv = [1 if y < -op_r else 0 for y in ys]
    sr = [1 if y > op_r else 0 for y in ys]
    axes[1].step(d, sv, where="post", lw=2, label="S_V betätigt"); axes[1].step(d, [v + 1.3 for v in sr], where="post", lw=2, label="S_R betätigt (+1,3 versetzt)")
    axes[1].set_yticks([0, 1, 1.3, 2.3]); axes[1].set_yticklabels(["S_V frei", "S_V betätigt", "S_R frei", "S_R betätigt"], fontsize=8)
    axes[1].grid(alpha=0.3)
    mot = [1 if a and not b else (-1 if b and not a else 0) for a, b in zip(sv, sr)]
    axes[2].step(d, mot, where="post", lw=2.4, color="purple")
    axes[2].set_yticks([-1, 0, 1]); axes[2].set_yticklabels(["Motor RÜCKWÄRTS", "kurzgeschlossen\n(bremst)", "Motor VORWÄRTS"], fontsize=8)
    axes[2].set_xlabel("Weg der vorderen Schaltstange relativ zum Fahrzeug [mm]   (10–19 mm: Schaumstoffpuffer wird gestaucht, Stange läuft auf der Rastfläche weiter)")
    axes[2].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=125)
    plt.close(fig)


def main():
    fig, axes = plt.subplots(2, 1, figsize=(12.5, 12.5))
    schematic(axes[0], "VOR")
    schematic(axes[1], "RUECK")
    fig.suptitle("Schaltplan SolarMobil Ultraleicht-Expert – Polwender aus zwei Mikroschaltern (Wechsler), Verschaltung umsteckbar", fontsize=12)
    fig.tight_layout()
    fig.savefig(HERE / "schaltplan.png", dpi=120)
    fig.savefig(HERE / "schaltplan.svg")
    plt.close(fig)
    out = ROOT / "results" / "diagrams" / "umkehr_funktionsdiagramm.png"
    function_diagram(out)
    print("geschrieben:", HERE / "schaltplan.png", out)


if __name__ == "__main__":
    main()
