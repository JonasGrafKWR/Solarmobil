"""Parametrische Bauteile des SolarMobils (CadQuery / OpenCASCADE-Kern).

Alle Bauteile werden in Fahrzeugkoordinaten (Einbaulage) erzeugt.
Druckteile: deck, wheel, gear/pinion, bracket, rod, collar, base, slider,
            clip, spacer.
Kaufteile (nur als Huellkoerper fuer Einbauraum- und Kollisionspruefung):
            motor, switches, bearings, axles, modules, pads, rail.
"""
from __future__ import annotations

import math
import pathlib
import sys

import cadquery as cq

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "simulation"))
import gear_geometry as gg  # noqa: E402
from params_cad import *    # noqa: E402,F401,F403


# ---------------------------------------------------------------- Hilfsfunktionen
def B(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def CZ(x, y, d, z0, z1):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, y, z0))


def CY(x, z, d, y0, y1):
    return cq.Workplane("XY").add(cq.Solid.makeCylinder(d / 2, y1 - y0, cq.Vector(x, y0, z), cq.Vector(0, 1, 0)))


def CX(y, z, d, x0, x1):
    return cq.Workplane("XY").add(cq.Solid.makeCylinder(d / 2, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0)))


def PXY(pts, z0, z1):
    return cq.Workplane("XY").polyline(pts).close().extrude(z1 - z0).translate((0, 0, z0))


def PYZ(pts, x0, x1):
    return cq.Workplane("YZ").polyline(pts).close().extrude(x1 - x0).translate((x0, 0, 0))


def PXZ(pts, y0, y1):
    return cq.Workplane("XZ").polyline(pts).close().extrude(-(y1 - y0)).translate((0, y0, 0))


def U(*parts):
    r = parts[0]
    for p in parts[1:]:
        r = r.union(p, clean=False)
    return r


def rot_z180(wp):
    return wp.rotate((0, 0, 0), (0, 0, 1), 180)


# ---------------------------------------------------------------- abgeleitete Masse
ROD_Z0, ROD_Z1 = ROD_Z - ROD_S / 2, ROD_Z + ROD_S / 2
_T = math.tan(math.radians(RAMP_DEG))
Y_OUT = -ROD_Y - ROD_S / 2                 # Aussenflanke Stange V
Y_LOW = -ROD_Y + ROD_S / 2                 # Schaftflanke (Schieber in Lage VOR)
Y_DW = -PIN_Y + SLIDE_H - PIN_D / 2        # Rastflanke (Schieber in Lage RUECK)
_YC0 = -PIN_Y - SLIDE_H                    # Stiftmitte in Lage VOR
X_R0 = (PIN_D / 2 * math.sqrt(1 + _T**2) - (_YC0 - Y_LOW) + _T * PIN_X) / _T + ROD_LEAD
RAMP_RUN = (Y_DW - Y_LOW) / _T
X_PAD0 = BRK_PLATE_X0 + BRK_PLATE_T
X_TIP = X_PAD0 + PAD_T + ROD_PROTRUDE
ROD_SWITCH_TRAVEL = ROD_LEAD + 2 * SLIDE_H / _T   # Stangenweg bis Schieber umgelegt
LEN_OVER_ALL = 2 * X_TIP
BASE_Z1 = BASE_Z0 + BASE_T
SLIDER_ZTOP = ROD_Z0 - 0.3


def slider_y_for_rod_travel(d: float) -> float:
    """Schieberlage (Mitte) in Abhaengigkeit vom Weg der vorderen Stange."""
    return min(SLIDE_H, max(-SLIDE_H, -SLIDE_H + _T * (d - ROD_LEAD)))


def gear_pair(name=GEAR_DEFAULT):
    z1, z2 = GEAR_PAIRS[name]
    return gg.make_pair(GEAR_M, z1, z2, backlash=GEAR_BACKLASH_A)


# ---------------------------------------------------------------- Deck
def make_deck():
    hl, hw = DECK_L / 2, DECK_W / 2
    zr = Z_PB - H_RIB
    body = B(-hl, hl, -hw, hw, Z_PB, Z_TOP)

    # Aussparungen der Deckplatte (Gitterrahmen)
    xs = [(-hl + 5, -AXLE_X - 3), (-AXLE_X + 3, -18), (-12, 12), (18, AXLE_X - 3), (AXLE_X + 3, hl - 5)]
    for (xa, xb) in xs:
        for sy in (1, -1):
            ys = [(5.0, hw - 8.0)]
            if sy == 1 and xa == -AXLE_X + 3:          # Steg fuer die Motorplatte
                ys = [(5.0, 32.5), (38.0, hw - 8.0)]
            for (ya, yb) in ys:
                cut = (cq.Workplane("XY").rect(xb - xa, yb - ya).extrude(T_PLATE + 2).edges("|Z").fillet(2.0)
                       .translate(((xa + xb) / 2, sy * (ya + yb) / 2, Z_PB - 1)))
                body = body.cut(cut, clean=False)

    ribs = [
        B(-hl, hl, hw - T_RIB, hw, zr, Z_PB), B(-hl, hl, -hw, -hw + T_RIB, zr, Z_PB),          # Laengsrand
        B(hl - T_RIB, hl, -hw, hw, zr, Z_PB), B(-hl, -hl + T_RIB, -hw, hw, zr, Z_PB),          # Stirnrand
        B(30, hl, -T_RIB / 2, T_RIB / 2, zr, Z_PB), B(-hl, -30, -T_RIB / 2, T_RIB / 2, zr, Z_PB),  # Mittelrippe
        B(15 - T_RIB / 2, 15 + T_RIB / 2, -hw, hw, zr, Z_PB), B(-15 - T_RIB / 2, -15 + T_RIB / 2, -hw, hw, zr, Z_PB),
        B(AXLE_X - T_RIB / 2, AXLE_X + T_RIB / 2, -PYL_Y + PYL_T / 2, PYL_Y - PYL_T / 2, zr, Z_PB),
        B(-AXLE_X - T_RIB / 2, -AXLE_X + T_RIB / 2, -PYL_Y + PYL_T / 2, PYL_Y - PYL_T / 2, zr, Z_PB),
        B(-AXLE_X, -15, 35.25 - T_RIB / 2, 35.25 + T_RIB / 2, zr, Z_PB),                       # Rippe ueber Motorplatte
    ]
    body = U(body, *ribs)

    # Lagerboecke
    for sx in (1, -1):
        for sy in (1, -1):
            x = sx * AXLE_X
            yi, yo = sy * (PYL_Y - PYL_T / 2), sy * (PYL_Y + PYL_T / 2)
            blade = B(x - PYL_LX / 2, x + PYL_LX / 2, min(yi, yo), max(yi, yo), AXLE_Z - BRG_OD / 2 - 1.5, Z_PB)
            fins = [B(x + s * PYL_LX / 2 - (T_RIB if s > 0 else 0), x + s * PYL_LX / 2 + (0 if s > 0 else T_RIB),
                      min(yi, yi - sy * 5), max(yi, yi - sy * 5), AXLE_Z + 5, Z_PB) for s in (1, -1)]
            body = U(body, blade, *fins)
            pocket = CY(x, AXLE_Z, BRG_OD + FIT, min(yo, yo - sy * (BRG_W + 0.1)), max(yo, yo - sy * (BRG_W + 0.1)))
            bore = CY(x, AXLE_Z, 4.6, min(yi, yo) - 0.1, max(yi, yo) + 0.1)
            body = body.cut(pocket, clean=False).cut(bore, clean=False)

    # Motorplatte (hinten links) mit Langloechern fuer FF-130 (+-6,2) und RF-300 (+-8,25)
    y0, y1 = MOTOR_PLATE_Y, MOTOR_PLATE_Y + MOTOR_PLATE_T
    zb = AXLE_Z - 9.5
    plate = U(B(-85, -44, y0, y1, zb, Z_PB), B(-AXLE_X, -85, y0, y1, 40, Z_PB),
              PYZ([(y0, Z_PB), (y0 - 10, Z_PB), (y0, 30)], -45.2, -44),
              PYZ([(y1, Z_PB), (y1 + 10, Z_PB), (y1, 30)], -45.2, -44))
    xm0, xm1 = -AXLE_X + A_MIN, -AXLE_X + A_MAX
    rb = (FF_BOSS_D + 0.4) / 2
    slots = U(B(xm0, xm1, y0 - 1, y1 + 1, AXLE_Z - rb, AXLE_Z + rb),
              CY(xm0, AXLE_Z, 2 * rb, y0 - 1, y1 + 1), CY(xm1, AXLE_Z, 2 * rb, y0 - 1, y1 + 1),
              B(xm0 - RF_PCD / 2, xm1 + RF_PCD / 2, y0 - 1, y1 + 1, AXLE_Z - 1.15, AXLE_Z + 1.15),
              CY(xm0 - RF_PCD / 2, AXLE_Z, 2.3, y0 - 1, y1 + 1), CY(xm1 + RF_PCD / 2, AXLE_Z, 2.3, y0 - 1, y1 + 1))
    body = U(body, plate).cut(slots, clean=False)

    # Fuehrungssaeulen mit Laengsfinnen
    for sx in (1, -1):
        x = sx * GUIDE_X
        col = U(CZ(x, 0, GUIDE_COL_D, GUIDE_COL_Z0, Z_PB),
                PXZ([(x + sx * 3, Z_PB), (x + sx * 7, Z_PB), (x + sx * 3, 45.5)], -T_RIB / 2, T_RIB / 2),   # aussen kurz
                PXZ([(x - sx * 3, Z_PB), (x - sx * 11, Z_PB), (x - sx * 3, 36)], -T_RIB / 2, T_RIB / 2))    # innen lang
        body = U(body, col).cut(CZ(x, 0, 2.5, GUIDE_COL_Z0 - 0.1, GUIDE_COL_Z0 + 14), clean=False)

    # Anschraubdome (M2 selbstschneidend, Kernloch 1,6)
    for sx in (1, -1):
        for sy in (1, -1):
            for (bx, by, d, zlo, through) in ((15, 23, 6, BASE_Z1, False), (116.5, 14, 6, 44.9, False),
                                              (20, 62, 4, zr, True), (58, 62, 4, zr, True)):
                dome = CZ(sx * bx, sy * by, d, zlo, Z_PB)
                hole = CZ(sx * bx, sy * by, 1.6, zlo - 0.1, Z_TOP + 0.1 if through else min(Z_PB - 0.6, zlo + 9))
                body = U(body, dome).cut(hole, clean=False)

    # Freischnitte: Schaltstangen, Federteller, Nocken, Abtriebsrad
    zn = ROD_Z1 + 0.4
    for (sy, xa, xb) in ((-1, 80, hl + 1), (1, -hl - 1, -80)):
        body = body.cut(B(xa, xb, sy * ROD_Y - 1.9, sy * ROD_Y + 1.9, zr - 0.1, zn), clean=False)
        xe = hl if xa > 0 else -hl
        body = body.cut(B(min(xe, xe - (1 if xa > 0 else -1) * (T_RIB + 0.1)) - 0.05,
                          max(xe, xe - (1 if xa > 0 else -1) * (T_RIB + 0.1)) + 0.05,
                          sy * ROD_Y - 3.6, sy * ROD_Y + 3.6, zr - 0.1, ROD_Z + 3.5), clean=False)
    for sx in (1, -1):
        body = body.cut(B(sx * 15 - 1, sx * 15 + 1, -10.9, 10.9, zr - 0.1, zn), clean=False)
    _, g2, _ = gear_pair("V3_anfahrstark")                       # groesstes Rad
    body = body.cut(CY(-AXLE_X, AXLE_Z, g2.da + 2.4, GEAR_Y - GEAR_W / 2 - 1.5, GEAR_Y + GEAR_W / 2 + 1.5), clean=False)
    return body.clean()


# ---------------------------------------------------------------- Rad
def make_wheel_local():
    """Rad um die z-Achse; +z = Fahrzeugaussenseite."""
    r_g = ORING_ID / 2 + 0.5            # Nutgrund: O-Ring leicht gedehnt -> Aussen-d = WHEEL_D
    r_f = r_g + 0.8
    r_i = r_g - 1.2
    w = WHEEL_W / 2
    prof = [(r_i, -w), (r_f, -w), (r_f, -1.1), (r_g, -0.6), (r_g, 0.6), (r_f, 1.1), (r_f, w), (r_i, w)]
    rim = cq.Workplane("XZ").polyline(prof).close().revolve(360, (0, 0, 0), (0, 1, 0))
    zin = -(WHEEL_Y - (PYL_Y + PYL_T / 2) - 0.3)       # Nabenbund laeuft mit 0,3 mm Spiel am Lagerinnenring an
    hub = U(CZ(0, 0, 8.0, zin + 1.0, w), CZ(0, 0, 4.4, zin, zin + 1.0))
    spokes = None
    for k in range(5):
        s = B(3.0, r_i + 0.3, -0.7, 0.7, w - 3.0, w).rotate((0, 0, 0), (0, 0, 1), 72 * k)
        spokes = s if spokes is None else spokes.union(s, clean=False)
    wheel = U(rim, hub, spokes).cut(CZ(0, 0, AXLE_D - PRESS, zin - 1, 4), clean=False)
    return wheel.clean()


def place_axis_y(wp, x, y, z, outward=1):
    """Dreht ein um z aufgebautes Teil so, dass lokale +z-Achse nach +-y zeigt."""
    r = wp.rotate((0, 0, 0), (1, 0, 0), -90 if outward > 0 else 90)
    return r.translate((x, y, z))


# ---------------------------------------------------------------- Zahnraeder
def gear_profile(g: gg.Gear, flank_comp=GEAR_FLANK_COMP, n=7):
    rb, ra, rf, rp = g.db / 2, g.da / 2, g.df / 2, g.d / 2
    half_p = g.s / (2 * rp) - flank_comp / rp
    r0 = max(rb, rf)
    flank = []
    for j in range(n + 1):
        r = r0 + (ra - r0) * j / n
        flank.append((r, half_p + gg.inv(gg.ALPHA) - gg.inv(math.acos(min(1.0, rb / r)))))
    pts = []
    for k in range(g.z):
        c = 2 * math.pi * k / g.z
        seq = []
        if rf < rb:
            seq.append((rf, c - flank[0][1]))
        seq += [(r, c - th) for r, th in flank]
        seq += [(r, c + th) for r, th in reversed(flank)]
        if rf < rb:
            seq.append((rf, c + flank[0][1]))
        pts += [(r * math.cos(a), r * math.sin(a)) for r, a in seq]
    return pts


def make_gear_local(g: gg.Gear):
    """Abtriebsrad um z; Zahnbreite GEAR_W, Nabe 0 ... GEAR_W+4 (Stegseite plan)."""
    body = PXY(gear_profile(g), 0, GEAR_W)
    r_in = g.df / 2 - 2.0
    web = cq.Workplane("XY").circle(r_in).circle(5.2).extrude(GEAR_W - 1.4).translate((0, 0, 1.4))
    body = body.cut(web, clean=False)                                  # Steg 1,4 mm
    for k in range(6):
        a = math.radians(60 * k + 30)
        rm = (r_in + 5.2) / 2
        body = body.cut(CZ(rm * math.cos(a), rm * math.sin(a), min(9.5, r_in - 5.2 - 2.5), -1, GEAR_W + 1), clean=False)
    body = U(body, CZ(0, 0, 8.0, 0.0, GEAR_W + 4.0)).cut(CZ(0, 0, AXLE_D - PRESS, -1, GEAR_W + 5), clean=False)
    return body.clean()


def make_pinion_local(g: gg.Gear):
    body = PXY(gear_profile(g), 0, PINION_W).cut(CZ(0, 0, 2.0 - PRESS, -1, PINION_W + 1), clean=False)
    return body.clean()


# ---------------------------------------------------------------- Stossfaengertraeger (vorn)
def make_bracket():
    x0, x1 = BRK_PLATE_X0, BRK_PLATE_X0 + BRK_PLATE_T
    z_mod = Z_TOP + MOD_T + 0.3
    zc = ROD_Z - 0.5                                   # Puffermitte ~ Schwerpunkthoehe
    plate = B(x0, x1, -22, 22, zc - PAD_H / 2, z_mod + 1.2)
    lip = B(x0 - 3.5, x0, -22, 22, z_mod, z_mod + 1.2)                 # Niederhalter ueber Modulenden
    flange = B(112, x0, -18, 18, 42.9, 44.9)
    gus = [PXZ([(x0, 42.9), (113, 42.9), (x0, zc - PAD_H / 2)], sy * 12 - 0.6, sy * 12 + 0.6) for sy in (1, -1)]
    body = U(plate, lip, flange, *gus)
    for sy in (1, -1):
        body = body.cut(CZ(116.5, sy * 14, 2.3, 42, 46), clean=False)
    body = body.cut(B(x0 - 1, x1 + 1, -ROD_Y - 1.8, -ROD_Y + 1.8, ROD_Z - 1.8, ROD_Z + 1.8), clean=False)
    return body.clean()


def make_pad():
    zc = ROD_Z - 0.5
    return B(X_PAD0, X_PAD0 + PAD_T, -PAD_W / 2, PAD_W / 2, zc - PAD_H / 2, zc + PAD_H / 2).cut(
        CX(-ROD_Y, ROD_Z, 5.5, X_PAD0 - 1, X_PAD0 + PAD_T + 1))


# ---------------------------------------------------------------- Schaltstange (vorn, Ruhelage)
def make_rod():
    x_in = X_R0 - 2.0
    xd0 = X_R0 + RAMP_RUN
    xd1 = xd0 + DWELL_LEN
    xt = xd1 + (Y_DW - Y_LOW) / math.tan(math.radians(30))
    pts = [(x_in, Y_OUT), (x_in, Y_LOW), (X_R0, Y_LOW), (xd0, Y_DW), (xd1, Y_DW), (xt, Y_LOW),
           (X_TIP - 1.0, Y_LOW), (X_TIP, Y_LOW - 1.0), (X_TIP, Y_OUT + 1.0), (X_TIP - 1.0, Y_OUT)]
    return PXY(pts, ROD_Z0, ROD_Z1)


def make_collar():
    """Federteller: wird nach dem Aufschieben der Feder auf die Stange geklebt."""
    s = 6.0
    return B(BRK_PLATE_X0 - COLLAR_L, BRK_PLATE_X0, -ROD_Y - s / 2, -ROD_Y + s / 2, ROD_Z - s / 2, ROD_Z + s / 2).cut(
        B(115, 122, -ROD_Y - ROD_S / 2 - 0.08, -ROD_Y + ROD_S / 2 + 0.08, ROD_Z0 - 0.08, ROD_Z1 + 0.08))


# ---------------------------------------------------------------- Schaltbasis
def make_base():
    z0, z1 = BASE_Z0, BASE_Z1
    hx = SLIDER_LX / 2 + 0.25
    body = U(B(-18, 18, -26, 26, z0, z1), B(18, 24.5, -7, 7, z0, z1))
    zb = ROD_Z0 - 0.1
    for sx in (1, -1):
        xa, xb = (hx, 17.0) if sx > 0 else (-17.0, -hx)
        block = U(B(xa, xb, -10.5, 10.5, z1, zb), B(xa, xb, 8.9, 10.5, zb, ROD_Z1 + 0.2),
                  B(xa, xb, -10.5, -8.9, zb, ROD_Z1 + 0.2))
        block = block.cut(B(xa + 1.2, xb - 1.2, -7.6, 7.6, z1 + 1.2, zb + 1), clean=False)
        body = U(body, block)
    zk = z1 + 3.1                                                       # Hoehe Magnet / Anschlagschraube
    body = U(body, B(-12, -7, 16, 19, z1, z1 + 5.6), B(7, 12, -19, -16, z1, z1 + 5.6))
    body = body.cut(CY(-9.5, zk, 2.6, 15.5, 19.5), clean=False).cut(CY(9.5, zk, 2.6, -19.5, -15.5), clean=False)
    for (cx, hy) in ((SW_CX, SW_HOLE_Y), (-SW_CX, -SW_HOLE_Y)):         # Langloecher zum Justieren der Schalter
        for dx in (-SW_HOLE_PITCH / 2, SW_HOLE_PITCH / 2):
            body = body.cut(B(cx + dx - 1.15, cx + dx + 1.15, hy - 1.7, hy + 1.7, z0 - 1, z1 + 1), clean=False)
    for sx in (1, -1):
        for sy in (1, -1):
            body = body.cut(CZ(sx * 15, sy * 23, 2.3, z0 - 1, z1 + 1), clean=False)
    body = body.cut(B(-8, 8, -7, 7, z0 - 1, z1 + 1), clean=False)       # Fenster unter dem Schieber
    body = body.cut(B(19.9, 22.6, -5.2, 5.2, z0 - 1, z1 + 1), clean=False)  # Stiftleiste 1x4 (Steckbruecken)
    return body.clean()


# ---------------------------------------------------------------- Schieber (Mittellage y = 0)
def make_slider():
    z1 = BASE_Z1
    hx, hy = SLIDER_LX / 2, SLIDER_LY / 2
    zt = SLIDER_ZTOP
    body = U(B(-hx, hx, -hy, hy, z1, z1 + 2.0), B(-hx, hx, hy - 3, hy, z1 + 2, zt), B(-hx, hx, -hy, -hy + 3, z1 + 2, zt),
             CZ(PIN_X, -PIN_Y, 6.0, z1 + 2, zt), CZ(-PIN_X, PIN_Y, 6.0, z1 + 2, zt),
             CZ(PIN_X, -PIN_Y, PIN_D, zt, ROD_Z1 - 0.2), CZ(-PIN_X, PIN_Y, PIN_D, zt, ROD_Z1 - 0.2))
    zk = z1 + 3.1
    body = body.cut(CY(-9.5, zk, MAG_D + 0.1, hy - MAG_T - 0.1, hy + 0.1), clean=False)
    body = body.cut(CY(9.5, zk, MAG_D + 0.1, -hy - 0.1, -hy + MAG_T + 0.1), clean=False)
    body = body.cut(B(-10.5, 0.5, -6.5, -2.3, z1 - 1, z1 + 3), clean=False)
    body = body.cut(B(-0.5, 10.5, 2.3, 6.5, z1 - 1, z1 + 3), clean=False)
    return body.clean()


# ---------------------------------------------------------------- Kleinteile
def make_clip():
    """Modulklammer, Ursprung = Modulkante (y) / Deckoberseite (z); +y nach aussen."""
    h = MOD_T + 0.3
    body = U(B(-4, 4, 0.2, 4.0, 0, h + 1.2), B(-4, 4, -2.4, 0.2, h, h + 1.2))
    return body.cut(CZ(0, 2.0, 2.3, -1, h + 2), clean=False)


def make_spacer():
    z0 = GUIDE_ROLL_Z + BRG_W / 2
    return CZ(0, 0, 5.0, z0, GUIDE_COL_Z0).cut(CZ(0, 0, 3.3, z0 - 1, GUIDE_COL_Z0 + 1))


# ---------------------------------------------------------------- Kaufteile (Huellkoerper)
def dummy_motor_ff130(a):
    xm = -AXLE_X + a
    yf = MOTOR_PLATE_Y
    body = CY(xm, AXLE_Z, FF_W, yf - FF_L, yf).intersect(B(xm - 20, xm + 20, yf - FF_L - 1, yf + 1,
                                                           AXLE_Z - FF_H / 2, AXLE_Z + FF_H / 2))
    return U(body, CY(xm, AXLE_Z, FF_BOSS_D, yf, yf + FF_BOSS_H), CY(xm, AXLE_Z, 2.0, yf, yf + FF_SHAFT_L),
             CY(xm, AXLE_Z, 10.0, yf - FF_L - 2.1, yf - FF_L))


def dummy_switches():
    hl = SW_L / 2
    r = B(SW_CX - hl, SW_CX + hl, SW_HOLE_Y - SW_ABOVE, SW_HOLE_Y + SW_BELOW, BASE_Z1, BASE_Z1 + SW_T)
    return r, rot_z180(r)


def dummy_bearing_y(x, y_c):
    return CY(x, AXLE_Z, BRG_OD, y_c - BRG_W / 2, y_c + BRG_W / 2).cut(CY(x, AXLE_Z, BRG_ID, y_c - 2, y_c + 2))


def dummy_modules():
    return [B(min(0, sx * MOD_L), max(0, sx * MOD_L), min(0, sy * MOD_W), max(0, sy * MOD_W), Z_TOP, Z_TOP + MOD_T)
            for sx in (1, -1) for sy in (1, -1)]


def dummy_rail(length=340):
    return B(-length / 2, length / 2, -RAIL_W / 2, RAIL_W / 2, 0, RAIL_H).cut(
        B(-length / 2 - 1, length / 2 + 1, -RAIL_W / 2 + RAIL_T, RAIL_W / 2 - RAIL_T, RAIL_T, RAIL_H + 1))


def dummy_guide(sx):
    x = sx * GUIDE_X
    roller = CZ(x, 0, BRG_OD, GUIDE_ROLL_Z - BRG_W / 2, GUIDE_ROLL_Z + BRG_W / 2)
    screw = U(CZ(x, 0, 3.0, GUIDE_ROLL_Z - BRG_W / 2, GUIDE_COL_Z0 + 9), CZ(x, 0, 5.5, GUIDE_ROLL_Z - BRG_W / 2 - 2.4,
                                                                           GUIDE_ROLL_Z - BRG_W / 2))
    return roller, screw
