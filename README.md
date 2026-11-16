# SolarMobil Expert – Ultraleicht-Expert-Klasse, SolarMobil Augsburg

Parametrisch konstruiertes, simuliertes Solarmodellfahrzeug mit automatischem Richtungswechsel.

**Stand:** konstruiert, exportiert, geometrisch geprüft und simuliert. **Nicht gebaut, nicht getestet.** Alle Fahrleistungen sind Simulationswerte unter gekennzeichneten Annahmen.

Einstieg: [docs/abschlussbericht.md](docs/abschlussbericht.md)

## Ergebnis in Kürze

| | |
|---|---|
| Konzept | 1 Motor Mabuchi FF-130SH-14230, Heckantrieb, Stirnradstufe 12 : 60 (i = 5), Räder d 50 mm |
| Solar | 4 Starterkit-Module, umsteckbar: 4 in Reihe (Sonne) / 2s2p (schwaches Licht) |
| Richtungswechsel | 2 Schaltstangen → Querschieber mit Magnetrastung → 2 Mikroschalter als Polwender |
| Maße / Masse | 296 × 128 × 59 mm (zulässig 300 × 140) / 260 g (davon 144 g Module = Annahme) |
| Simulierte Rennzeit | 12,7 s Sonne · 25,7 s Kunstlicht · 29,2 s bewölkt |
| Größte offene Punkte | Modulkennlinie und -masse unbekannt; Aufprall bis 4,4 m/s; Anfahren und Tunnel bei schwachem Licht |

## Ordner

| Ordner | Inhalt |
|---|---|
| `docs/` | Abschlussbericht, Regelkonformitätsmatrix, Konzeptvergleich, Berechnungen, Umkehrmechanismus, Bauanleitung (Werkstoffe, Druck, Montage), Testplan |
| `simulation/` | Motor-, Solar-, Fahrzeugmodell, Getriebeoptimierung, Rennsimulation, Kalibrierung, Auslegung des Umkehrmechanismus |
| `cad/source/` | parametrische CAD-Quellen (`params_cad.py` = alle Maße), Build- und Validierungsskript |
| `cad/drawings/`, `cad/assemblies/` | Maßblätter (SVG), Zusammenbau- und Explosionsdarstellung, Vorschaubilder, CAD-Prüfbericht |
| `exports/STL/`, `exports/STEP/` | Druckdateien in Drucklage, STEP-Einzelteile und Zusammenbau |
| `electronics/schaltplan/` | Schaltplan (PNG/SVG) und erzeugendes Skript |
| `results/` | Diagramme, Vergleichstabellen (CSV), Rechenprotokolle |
| `tests/` | Plausibilitätstests (pytest), Vorlagen für Messprotokolle |
| `bom/` | Stückliste, Massen der Druckteile, Prüfskript |
| `quellen/` | Reglements, Datenblätter, Unterrichtsmaterial |

## Ausführen

Voraussetzung: Python 3.12.

```bash
python -m venv .venv
```

```bash
.venv\Scripts\python -m pip install -r requirements.txt
```

Danach (jeweils mit `.venv\Scripts\python`):

| Befehl | Zweck | Dauer |
|---|---|---|
| `python simulation/race_simulation.py` | Rennablauf für alle Szenarien, Diagramme, Monte-Carlo | ca. 1 min |
| `python simulation/race_simulation.py --szenario sonne --i 6.2 --masse 0.22` | einzelne Variante; `--help` zeigt alle Parameter | Sekunden |
| `python simulation/gear_optimizer.py` | Motor-, Verschaltungs-, Übersetzungs-, Rad- und Konzeptstudien | ca. 4 min |
| `python simulation/motor_model.py` / `solar_model.py` | Kennlinien und Vergleichstabellen | Sekunden |
| `python simulation/umkehr_berechnung.py` | Kräfte und Energien am Umkehrmechanismus | Sekunden |
| `python simulation/kalibrierung.py --help` | Messwerte in die Simulation übernehmen | – |
| `python cad/source/build_all.py` | alle CAD-Daten, Zeichnungen und Prüfbericht neu erzeugen | ca. 1 min |
| `python cad/source/validate_stl.py` | STL-Netze prüfen | Sekunden |
| `python electronics/schaltplan/schaltplan_zeichnen.py` | Schaltplan und Funktionsdiagramm | Sekunden |
| `python bom/stueckliste_pruefen.py` | Stückliste mit CAD-Massen abgleichen | Sekunden |
| `python -m pytest tests -q` | 30 Plausibilitätsprüfungen | ca. 10 s |

## Erste Schritte vor dem Bau

1. Ein Solarmodul messen und wiegen, `MOD_L`, `MOD_W`, `MOD_T`, `MOD_MASS_G` in `cad/source/params_cad.py` eintragen, CAD neu erzeugen.
2. Offene Fragen aus `docs/reglement_check.md` mit der Rennleitung klären (Tunnel, Schiene).
3. Kennlinie eines Moduls aufnehmen (Testplan, Test 1) und mit `kalibrierung.py` übernehmen.
4. Zahnradpaar und Schalteinheit als Probe drucken, erst dann das Deck.

## Werkzeuge

FreeCAD und OpenSCAD waren auf dem Entwicklungsrechner nicht installiert. Die Konstruktion nutzt CadQuery (Python, OpenCASCADE-Kern wie FreeCAD). Die STEP-Dateien lassen sich in FreeCAD öffnen und weiterbearbeiten; das wurde dort nicht geprüft.
