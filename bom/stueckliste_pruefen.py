"""Prueft und aktualisiert bom/stueckliste.csv.

    python stueckliste_pruefen.py

* uebernimmt die Massen der Druckteile aus bom/druckteile_massen.csv (CAD)
* rechnet Masse_gesamt = Stueck x Masse_je_Stueck neu
* schreibt die Summenzeile neu und vergleicht mit dem CAD-Pruefbericht
"""
import csv
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
cad = {}
with open(HERE / "druckteile_massen.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter=";"):
        cad[r["Teil"] + ".stl"] = float(r["Masse_je_Stueck_g"])

with open(HERE / "stueckliste.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter=";"))
fields = list(rows[0].keys())
assert all(None not in r and len(r) == len(fields) for r in rows), "Spaltenzahl pruefen (Semikolon im Text?)"
body = [r for r in rows if r["Pos"]]
m_cad = m_other = price = 0.0
for r in body:
    stl = r["Spezifikation"].split(",")[0].strip()
    if r["Baugruppe"] == "Druckteil" and stl in cad:
        r["Masse_je_Stueck_g"] = f"{cad[stl]:.2f}"
        r["Herkunft_Masse"] = "CAD"
    tot = int(r["Stueck"]) * float(r["Masse_je_Stueck_g"])
    r["Masse_gesamt_g"] = f"{tot:.2f}"
    if r["Herkunft_Masse"] == "CAD":
        m_cad += tot
    else:
        m_other += tot
    price += float(r["Preis_gesamt_EUR_Schaetzung"])
total = {k: "" for k in fields}
total.update({"Bezeichnung": "SUMME", "Masse_gesamt_g": f"{m_cad + m_other:.2f}",
              "Herkunft_Masse": f"CAD {m_cad:.2f} g + Kaufteile/Annahmen {m_other:.2f} g",
              "Preis_gesamt_EUR_Schaetzung": f"{price:.2f}",
              "Bezug_Bemerkung": "ohne Starterkit (Module, ggf. Motor) und ohne Versand - Preise sind Schaetzwerte"})
with open(HERE / "stueckliste.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter=";")
    w.writeheader()
    w.writerows(body + [total])
print(f"Summe {m_cad + m_other:.1f} g  (CAD {m_cad:.1f} g, Kaufteile/Annahmen {m_other:.1f} g), Material ca. {price:.2f} EUR")
rep = HERE.parent / "cad" / "assemblies" / "pruefbericht.json"
if rep.exists():
    g = json.loads(rep.read_text(encoding="utf-8"))["masse"]["Gesamtmasse_g"]
    print(f"CAD-Pruefbericht: {g} g  -> Abweichung {m_cad + m_other - g:+.1f} g")
