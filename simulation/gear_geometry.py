"""Evolventen-Stirnradgeometrie (DIN 867 Bezugsprofil, alpha = 20 Grad).

Wird von der Simulation (Zahnzahlwahl) UND von der CAD-Erzeugung
(cad/source/build_all.py) verwendet, damit beide dieselben Zahlen benutzen.

V-Null-Verzahnung: Profilverschiebung x1 = -x2, dadurch bleibt der
Achsabstand a = m*(z1+z2)/2.  Kleine Ritzel bekommen x > 0 gegen Unterschnitt;
der Kopfkreis wird so weit gekuerzt, dass die Zahnkopfdicke druckbar bleibt.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

ALPHA = math.radians(20.0)


def inv(a: float) -> float:
    return math.tan(a) - a


@dataclass(frozen=True)
class Gear:
    m: float          # Modul [mm]
    z: int            # Zaehnezahl
    x: float          # Profilverschiebungsfaktor
    tip_short: float  # Kopfkuerzung [mm] (>= 0)
    c: float = 0.25   # Kopfspielfaktor

    @property
    def d(self):       # Teilkreis
        return self.m * self.z

    @property
    def db(self):      # Grundkreis
        return self.d * math.cos(ALPHA)

    @property
    def da(self):      # Kopfkreis
        return self.d + 2 * self.m * (1 + self.x) - 2 * self.tip_short

    @property
    def df(self):      # Fusskreis
        return self.d - 2 * self.m * (1 + self.c - self.x)

    @property
    def s(self):       # Zahndicke am Teilkreis (ohne Flankenspiel)
        return self.m * (math.pi / 2 + 2 * self.x * math.tan(ALPHA))

    def thickness_at(self, dy: float) -> float:
        """Zahndicke auf Durchmesser dy (Bogen)."""
        ay = math.acos(min(1.0, self.db / dy))
        return dy * (self.s / self.d + inv(ALPHA) - inv(ay))

    @property
    def sa(self):      # Zahnkopfdicke
        return self.thickness_at(self.da)

    @property
    def x_min_undercut(self):
        return (17 - self.z) / 17.0


def make_pair(m: float, z1: int, z2: int, sa_min: float = 0.40, backlash: float = 0.10):
    """Erzeugt ein V-Null-Radpaar. backlash = Achsabstandszugabe [mm] fuer FDM."""
    x1 = max(0.0, round((17 - z1) / 17.0 + 0.03, 2)) if z1 < 17 else 0.0
    x1 = min(x1, 0.5)
    g1 = Gear(m, z1, x1, 0.0)
    # Kopfkuerzung des Ritzels, bis die Kopfdicke druckbar ist
    short = 0.0
    while Gear(m, z1, x1, short).sa < sa_min and short < 0.5 * m:
        short += 0.01
    g1 = Gear(m, z1, x1, round(short, 2))
    g2 = Gear(m, z2, -x1, 0.0)
    a = m * (z1 + z2) / 2.0
    return g1, g2, a + backlash


def contact_ratio(g1: Gear, g2: Gear, a: float) -> float:
    """Profilueberdeckung beim Betriebsachsabstand a."""
    a0 = (g1.d + g2.d) / 2
    aw = math.acos(min(1.0, a0 * math.cos(ALPHA) / a))
    ra1, ra2, rb1, rb2 = g1.da / 2, g2.da / 2, g1.db / 2, g2.db / 2
    ga = (math.sqrt(max(ra1**2 - rb1**2, 0)) + math.sqrt(max(ra2**2 - rb2**2, 0)) - a * math.sin(aw))
    return ga / (math.pi * g1.m * math.cos(ALPHA))


def tip_root_clearance(g1: Gear, g2: Gear, a: float) -> tuple[float, float]:
    """Kopfspiel Ritzelkopf/Radfuss und Radkopf/Ritzelfuss [mm]."""
    return a - g1.da / 2 - g2.df / 2, a - g2.da / 2 - g1.df / 2


def pair_report(m: float, z1: int, z2: int, **kw) -> dict:
    g1, g2, a = make_pair(m, z1, z2, **kw)
    c1, c2 = tip_root_clearance(g1, g2, a)
    return {
        "Modul": m, "z1": z1, "z2": z2, "i": round(z2 / z1, 3),
        "x1": g1.x, "x2": g2.x, "Kopfkuerzung1_mm": g1.tip_short,
        "d1_mm": round(g1.d, 2), "da1_mm": round(g1.da, 2), "df1_mm": round(g1.df, 2),
        "d2_mm": round(g2.d, 2), "da2_mm": round(g2.da, 2), "df2_mm": round(g2.df, 2),
        "Achsabstand_mm": round(a, 2), "Ueberdeckung": round(contact_ratio(g1, g2, a), 2),
        "Kopfspiel1_mm": round(c1, 2), "Kopfspiel2_mm": round(c2, 2),
        "Zahnkopfdicke1_mm": round(g1.sa, 2), "Zahnkopfdicke2_mm": round(g2.sa, 2),
        "Zahndicke_Teilkreis_mm": round(math.pi * m / 2, 2),
    }


if __name__ == "__main__":
    for z1, z2 in ((14, 58), (12, 60), (10, 62)):
        print(pair_report(0.7, z1, z2))
