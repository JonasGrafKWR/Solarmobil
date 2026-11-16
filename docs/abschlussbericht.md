# Technischer Abschlussbericht – SolarMobil Ultraleicht-Expert

Stand 14.11.2026 · Planungsgrundlage: Reglement SolarMobil Augsburg 2026 (Stand 28.01.2026); Konformität für spätere Jahre vorläufig.

**Status in einem Satz:** Das Fahrzeug ist vollständig parametrisch konstruiert, als STL/STEP exportiert, geometrisch geprüft und simuliert – es ist **nicht gebaut und nicht getestet**. Alle Fahrleistungen sind Simulationswerte auf Basis von Datenblättern und gekennzeichneten Annahmen.

Herkunftskennzeichen: **[D]** Datenblatt · **[R]** Reglement · **[C]** aus CAD · **[B]** berechnet · **[S]** simuliert · **[A]** Annahme · gemessen: nichts.

## 1. Empfohlenes Gesamtkonzept

Ein Motor, Heckantrieb über eine Stirnradstufe, vier Räder d 50 mm, einteiliges gedrucktes Gitterdeck, auf dem die vier Starterkit-Module liegen und unter dem Antrieb, Führung und Umkehrmechanismus hängen. Die Module sind über Steckbrücken umsteckbar (alle in Reihe für Sonne, zwei Paare parallel für schwaches Licht). Zwei federnd rückgestellte Schaltstangen legen am Anschlagbrett einen Querschieber um, der über zwei Mikroschalter den Motor umpolt.

Bilder: `cad/assemblies/vorschau_gesamt.png`, `vorschau_ohne_deck.png`, `vorschau_schalteinheit.png`; Zeichnungen in `cad/assemblies/` und `cad/drawings/`.

## 2. Kernergebnisse

| Thema | Ergebnis | Herkunft |
|---|---|---|
| Motor | **Mabuchi FF-130SH-14230** (2,5–10 V; R = 5,7 Ω, k = 7,3 mNm/A, 24 g) | [D] + [B] |
| Begründung | einziger zugelassener Motor, der in der Sonne die volle Generatorspannung (ca. 8 V) innerhalb seines Datenblattbereichs nutzt; gleichauf mit dem Schnellsten in der Sonne, 3 % hinter dem Besten bei schwachem Licht – mit derselben Übersetzung | [S] |
| Rückfall | Starterkit-Motor RF300 (gerechnet als RF300CA-11400): ca. 1,3 s langsamer in der Sonne, über 6 V außerhalb seiner Spezifikation | [S], Typzuordnung [A] |
| Solarkonfiguration | **4s** bei Sonne (8,6 V / 0,52 A / 3,0 W bei 850 W/m², 50 °C); **2s2p** bei bewölktem Himmel und Kunstlicht (doppelter Strom → doppeltes Anfahrmoment); Stränge = vorderes und hinteres Modulpaar | [B], Modulwerte [A] |
| Optimale Übersetzung | i = 4,75…5,5 für beide Betriebsarten; gewählt **i = 5,0** | [S] |
| Zähnezahlen | **V2 12 : 60** (Standard) · V1 14 : 58 (i = 4,14) · V3 10 : 62 (i = 6,2); Modul 0,7, Achsabstand 25,3 mm für alle | [B], [C] |
| Raddurchmesser | **50 mm** (mit O-Ring 45 × 2); die Zeit hängt kaum vom Durchmesser ab (< 1 %), er folgt aus der Schienenhöhe und dem Platz für das Abtriebsrad | [S], [C] |
| Fahrzeugmasse | **260 g**, davon 116 g Fahrzeug [C] und 144 g Solarmodule [A] | [C] + [A] |
| Anfahrbeschleunigung | 2,0 m/s² (Sonne) · 0,74 m/s² (Kunstlicht) · 0,45 m/s² (bewölkt) | [S] |
| Höchstgeschwindigkeit | im Rennen 4,4 m/s (Sonne), 2,0 m/s (Kunstlicht), 1,9 m/s (bewölkt); Beharrung 5,1 m/s, theoretischer Leerlauf 5,7 m/s (Sonne) | [S] / [B] |
| **Rennzeit 4 Durchfahrten** | **12,7 s** Sonne · **25,7 s** Kunstlicht · **29,2 s** bewölkt (Nennannahmen) | [S] |
| Streubereich (10 % / Median / 90 %) | 12,1 / 13,4 / 15,2 s · 24,8 / 28,4 / 34,4 s · 26,3 / 31,5 / 39,4 s | [S] Monte-Carlo |
| Zieleinlauf-Wahrscheinlichkeit unter den Annahmen | 100 % Sonne · 92,5 % Kunstlicht · 67,5 % bewölkt (150 W/m²) | [S] Monte-Carlo |
| Länge × Breite × Höhe | 296 × 128 × 59 mm (zulässig 300 × 140) | [C] |
| Materialkosten Kaufteile | ca. 30 € ohne Starterkit, zuzüglich ca. 70 g Filament | Schätzung |

Die drei Rennzeiten sind **keine experimentell bestätigten Leistungen**. Sie reagieren am stärksten auf die unbekannte Modulkennlinie und -masse.

## 3. Solargenerator

Die Kit-Angabe „2 V, 0,6 A“ ist nicht eindeutig. Sie wird als Nennspannung eines 4-Zellen-Moduls (Leerlauf ca. 2,4 V) und Strom nahe Kurzschluss bei voller Sonne gedeutet; begründet in `docs/berechnungen.md`, Abschnitt 1.1. Das Modell, die Kennlinien für Reihen-, Parallel- und gemischte Schaltung, Temperatur- und Teilabschattungseinfluss sowie die drei Beleuchtungsszenarien stehen in Abschnitt 1 dort; der Messplan in `docs/testplan.md`, Test 1.

Tunnel: ohne Speicher rollt das Fahrzeug durch. Rechnerische Mindest-Einfahrgeschwindigkeit ca. 1,3–1,4 m/s [B]; in der Sonne kostet der Tunnel etwa 0,3 m/s, bei schwachem Licht ist er die häufigste Ausfallursache [S].

## 4. Getriebe

| Variante | z_1 : z_2 | i | Sonne 4s: Zeit / Aufprall | Kunstlicht 2s2p: Zeit / Anfahrreserve | Einsatz |
|---|---|---|---|---|---|
| V1 Schnell | 14 : 58 | 4,14 | 13,3 s / 4,4 m/s | 26,0 s / 2,4 | erst bei leichterem Fahrzeug (< ca. 180 g) oder sehr starker Sonne im Vorteil |
| **V2 Ausgewogen** | **12 : 60** | **5,00** | **12,7 s** / 4,4 m/s | **25,7 s** / 2,9 | Standard |
| V3 Anfahrstark | 10 : 62 | 6,20 | 12,8 s / 4,0 m/s | 27,6 s / 3,6 | wenn das Anfahren unsicher ist oder der Aufprall zu hart |

Alle drei Paare sind als Druckteile vorhanden und passen auf denselben Achsabstand. Vollständige Verzahnungsdaten, Riemen- und Mehrstufenvergleich: `docs/berechnungen.md`, Abschnitt 3.

## 5. Umkehrmechanismus

Gewählt aus drei Konzepten (mechanischer Polwender / Getriebeumkehr / bistabiles Relais): zwei Schaltstangen mit 35°-Keilnocken → Querschieber (±2,5 mm, Magnetrastung) → zwei Mikroschalter Omron D2F-L als Polwender. Kennwerte:

| Größe | Wert | Herkunft |
|---|---|---|
| Stangenweg bis zum vollständigen Umschalten | 8,1 mm bei 10 mm Überstand vor dem Puffer | [C] |
| Schaltarbeit / Mindest-Aufprallgeschwindigkeit | 6,4 mJ / 0,22 m/s (0,31 m/s mit Faktor 2 auf die Arbeit) | [B] |
| simulierte Aufprallgeschwindigkeiten | 1,9…4,4 m/s | [S] |
| größte Stangenkraft | 2,1 N | [B], Magnetkraft 1,5 N [A] |
| Schaltvermögen der Mikroschalter | 2 A / 30 V DC; Bedarf max. 1,0 A / 9,6 V | [D] / [B] |
| Aufprallenergie / mittlere Pufferkraft bei 4,4 m/s | 2,5 J / 210 N über 12 mm | [B] |

Kein Kurzschluss beim Polwechsel möglich; während des Aufpralls ist der Schieber durch die gedrückte Stange formschlüssig verriegelt; die Aufprallkräfte wirken längs, der Schieber bewegt sich quer. Einzelheiten, Bewertungsmatrix, Funktionsdiagramm und Schaltplan: `docs/umkehrmechanismus.md`, `results/diagrams/umkehr_funktionsdiagramm.png`, `electronics/schaltplan/schaltplan.png`.

## 6. Konstruktion und Fertigungsdaten

| Ergebnis | Ort | Prüfstand |
|---|---|---|
| parametrische Quellen (CadQuery, OpenCASCADE-Kern) | `cad/source/params_cad.py`, `parts.py`, `build_all.py` | laufen fehlerfrei |
| 15 STL-Dateien in Drucklage | `exports/STL/` | 15 von 15 wasserdicht, Volumenabweichung zum CAD < 0,3 % |
| STEP-Dateien der Teile, des Mechanismus und des Gesamtfahrzeugs | `exports/STEP/` | in FreeCAD zu öffnen (dort nicht geprüft) |
| Maßblätter und Zusammenbauzeichnungen | `cad/drawings/`, `cad/assemblies/` | Dreiseitenansichten mit Haupt- und Funktionsmaßen; **keine normgerechte Einzelbemaßung** |
| CAD-Prüfbericht | `cad/assemblies/pruefbericht.md` | 24 von 24: Hüllmaße, Schienenfreiraum, Kollision in 7 Schaltzuständen, Verzahnung, Federweg, Schwerpunkt |

**Abweichung vom Auftrag:** FreeCAD und OpenSCAD sind auf diesem Rechner nicht installiert. Verwendet wurde CadQuery, das denselben Geometriekern wie FreeCAD nutzt; die Quellen sind reine Python-Dateien und die STEP-Dateien lassen sich in FreeCAD weiterbearbeiten. Eine FreeCAD-Datei (.FCStd) wurde nicht erzeugt.

Werkstoffe: Deck ASA, Mechanik und Halter PETG HF, Zahnräder und Räder PLA Basic; PLA Aero und PAHT-CF begründet nicht verwendet. Teiletabelle mit Masse, Drucklage, Füllung, Stützen, Toleranzen und Stückzahl sowie die Montage in sieben Schritten: `docs/bauanleitung.md`. Stückliste: `bom/stueckliste.csv` (259 g, davon 67 g Druckteile).

## 7. Regelkonformität

Alle bemaßten Vorgaben des Reglements sind im CAD eingehalten (Breite 128 ≤ 140 mm, Länge 296 ≤ 300 mm, Motorserie, keine Batterie, kein Kondensator, Führung im U-Profil 15 × 15 × 2). Die vollständige Matrix mit 18 verbindlichen Vorgaben, 5 Annahmen und 6 offenen Fragen steht in `docs/reglement_check.md`.

Vor dem Bau mit der Rennleitung zu klären: Tunnelhöhe, -breite und -lage; Lage der Schiene (aufliegend oder eingelassen); ob Einsicht von unten als „einsehbar“ genügt; Zulässigkeit von Magnetrastung und elastischem Puffer; ob das Umstecken der Module zwischen Läufen erlaubt ist.

## 8. Offene Risiken

| Nr. | Risiko | Auswirkung | Maßnahme |
|---|---|---|---|
| 1 | Kennlinie, Maße und Masse der Kit-Module unbekannt | alle Zeiten, Deckgröße, ggf. passen 4 Module nicht in 2 × 2 auf 140 mm Breite | Test 1 und 5 vor dem ersten Druck; Parameter eintragen, neu erzeugen |
| 2 | Schwaches Licht: Anfahren und Tunnel | Stillstand; unter den Annahmen bis zu einem Drittel Ausfälle bei 150 W/m² | 2s2p, V3 bereithalten, Reibung minimieren (Test 3, 6, 9); mittelfristig leichtere Zellen |
| 3 | Aufprall mit bis zu 4,4 m/s (2,5 J) | Bruch von Trägern, Domen, Modulen; unkontrollierter Rückprall | gestufter Aufprallversuch (Test 8); Schaum auswählen; notfalls V3 (4,0 m/s) oder 2s2p in der Sonne (2,4 m/s, dafür ca. 20 s statt 12,7 s) |
| 4 | Umkehrmechanismus ungetestet (Reibwert, Magnetkraft, Federn, Drucktoleranzen) | kein Umschalten oder Zurückschalten | Test 8, Einstellanleitung in der Bauanleitung |
| 5 | Verzahnung Modul 0,7 braucht 0,2-mm-Düse | rauer Lauf, niedriger Wirkungsgrad | Probedruck; Ausweichlösung gekaufte Zahnräder Modul 0,5 (Halter dafür verstellbar) |
| 6 | Verfügbarkeit FF-130SH-14230 nicht geprüft | anderer Motor, andere optimale Übersetzung | vor Bestellung Wicklungscode prüfen; Simulation mit `--motor` neu rechnen |
| 7 | Tunnel- und Schienengeometrie unbekannt | Fahrzeug passt nicht, Führung greift nicht | Rückfrage; Höhe 59 mm und Führungshöhe sind Parameter |
| 8 | Deck aus ASA verzieht sich ohne Einhausung | Lager fluchten nicht | PETG HF verwenden oder Deck teilen |
| 9 | Kunstlicht-Annahme (200 W/m² Äquivalent) | Zeiten unter Kunstlicht können um ein Mehrfaches abweichen | Kurzschlussstrom am Wettbewerbsort messen, `--licht` anpassen |
| 10 | Simulationsmodell vereinfacht (Aufprall, Schlupf, Führung) | Abweichung der realen Zeiten | Kalibrierung nach Testplan |

Erforderliche Praxistests: alle zehn in `docs/testplan.md`; zwingend vor dem ersten Lauf in der Sonne sind Test 1, 5, 3 und 8.

## 9. Herkunft der wichtigsten Zahlen

| Ergebnis | gemessen | berechnet | simuliert | Datenblatt | angenommen |
|---|---|---|---|---|---|
| Motorkennwerte R, k, M_r | | × | | × | |
| Rotorträgheit | | | | | × |
| Modulwerte U_oc, I_sc, Füllfaktor | | | | | × |
| Modulmaße und -masse | | | | | × |
| Generatorkennlinien, MPP | | × | | | (aus Modulwerten) |
| Masse der Druckteile, Schwerpunkt, Trägheiten | | × (CAD) | | | |
| Gesamtmasse 260 g | | × | | × (Motor, Schalter) | × (Module, Kleinteile) |
| Rollwiderstand, Getriebewirkungsgrad, c_W·A, Haftreibung | | | | | × |
| Beleuchtungsszenarien, Tunnellage | | | | | × |
| optimale Übersetzung, Rennzeiten, Aufprallgeschwindigkeit | | | × | | |
| Verzahnungsgeometrie | | × | | | |
| Schaltarbeit, Mindestgeschwindigkeit, Pufferkräfte | | × | | × (Schalter) | × (Reibwert, Magnet) |
| Hüllmaße, Kollisionsfreiheit | | × (CAD) | | | |
| Funktion des Umkehrmechanismus, Festigkeit beim Aufprall | **nicht nachgewiesen** | überschlägig | | | |
