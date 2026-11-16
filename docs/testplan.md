# Testplan

Zweck: Die Annahmen der Simulation durch Messwerte ersetzen und die Funktion des Fahrzeugs nachweisen. Bisher ist **nichts** gemessen.

Reihenfolge: 1 → 5 → 2 → 3 → 6 → 4 → 7 → 8 → 9 → 10. Nach jedem Test die Werte mit `simulation/kalibrierung.py` übernehmen und `python simulation/race_simulation.py` neu rechnen. Vorlagen für Messprotokolle: `tests/messprotokolle/`.

Allgemeine Messmittel: Multimeter (Spannung, Strom bis 2 A), Küchen- oder Briefwaage (0,1 g), Maßband, Smartphone mit Zeitlupe (≥ 120 Bilder/s), ebenes Brett mit U-Profil 15 × 15 × 2 mm (mindestens 3 m, besser 10 m).

---

## Test 1 – Kennlinie der Solarmodule

| | |
|---|---|
| Messgeräte | Multimeter, Festwiderstände 1 / 2,2 / 3,3 / 4,7 / 10 / 22 / 47 / 100 Ω (≥ 2 W), optional zweites Multimeter als Amperemeter, Thermometer |
| Aufbau | Ein Modul waagrecht in voller Sonne (wolkenlos, Mittag) bzw. unter der späteren Rennbeleuchtung. Modultemperatur auf der Rückseite messen. |
| Vorgehen | a) Leerlaufspannung U_oc messen. b) Kurzschlussstrom I_sc messen (Multimeter im 10-A-Bereich direkt an das Modul). c) Nacheinander jeden Widerstand anschließen, Spannung notieren. d) Für alle vier Module I_sc und U_oc vergleichen. e) Wiederholen bei bedecktem Himmel und unter Kunstlicht. |
| Messwerte | R, U je Laststufe; U_oc, I_sc; Temperatur; Uhrzeit, Wetter |
| Berechnung | I = U/R, P = U²/R; MPP = größtes P; Füllfaktor FF = P_mpp/(U_oc·I_sc). Übernahme: `python simulation/kalibrierung.py --solar tests/messprotokolle/solar_kennlinie.csv --g-mess <W/m²> --t-mess <°C>`. Ohne Bestrahlungsmessgerät: klare Mittagssonne im Sommer ≈ 900 W/m² ansetzen und als Schätzung kennzeichnen. |
| Erfolgskriterium | Kennlinie mit ≥ 8 Punkten; Anpassungsfehler < 5 % von I_sc; die vier Module weichen in I_sc um < 10 % voneinander ab (sonst das schwächste Modul nicht in Reihe mit den anderen betreiben). |
| Klärt | Sind „2 V / 0,6 A“ Nenn-, Leerlauf- oder Kurzschlusswerte? |

## Test 2 – Motordrehzahl unter Last

| | |
|---|---|
| Messgeräte | regelbares Netzteil 0–10 V, Multimeter (Strom), Drehzahlmessung: Smartphone-Zeitlupe auf eine Markierung am Abtriebsrad oder Reflex-Drehzahlmesser; Schnurrolle d 10 mm auf der Radachse, Gewichte 5 / 10 / 20 g |
| Aufbau | Motor mit Getriebe im Fahrzeug, Fahrzeug aufgebockt. Schnur über die Rolle, Gewicht wird gehoben. |
| Vorgehen | Bei 2, 4, 6 V: a) Leerlauf: Strom und Drehzahl. b) Mit jedem Gewicht: Strom und Drehzahl während des Hebens. c) Blockierstrom (Rad 1 s festhalten). |
| Messwerte | U, I, n_Rad je Laststufe |
| Berechnung | n_Motor = n_Rad · i; M_Rad = m·g·r_Rolle; R = U/I_block; k = (U − I·R)/ω; Reibmoment = k·I_0. Vergleich mit `results/comparisons/motorvergleich_nennspannung.csv`. |
| Erfolgskriterium | R und k weichen < 10 % vom Datenblattmodell ab; sonst Werte in `motor_model.py` als neue Motorzeile eintragen. |

## Test 3 – Anlaufverhalten

| | |
|---|---|
| Messgeräte | Multimeter (I_sc eines Moduls als Lichtmaß), Abdeckkarton, Stoppuhr |
| Aufbau | Fahrzeug fahrbereit auf der Bahn, Führung in der Schiene. |
| Vorgehen | a) Fahrzeug festhalten, loslassen – fährt es ohne Anschieben los? b) Module schrittweise abdecken bzw. Licht verringern, bis es nicht mehr anfährt; dabei I_sc eines frei liegenden Referenzmoduls notieren. c) Für 4s und 2s2p und alle drei Getriebevarianten. d) Auch rückwärts. |
| Messwerte | kleinster I_sc, bei dem das Fahrzeug sicher anfährt (5 von 5 Versuchen) |
| Berechnung | Anlauf-Bestrahlung G_min ≈ I_sc,min / I_sc,1000 · 1000 W/m². Vergleich mit der simulierten Anfahrreserve (`rennsimulation_auslegung.csv`). |
| Erfolgskriterium | Anfahren in beiden Richtungen bei höchstens 60 % des am Renntag gemessenen I_sc (Reserve Faktor ≥ 1,7). |

## Test 4 – Getriebewirkungsgrad

| | |
|---|---|
| Messgeräte | wie Test 2 |
| Aufbau | wie Test 2, mit Gewicht |
| Vorgehen | Bei 4 V Gewichte heben; Strom, Hubgeschwindigkeit messen. Motorkennwerte aus Test 2 (Leerlaufmessung ohne Ritzel) verwenden. |
| Messwerte | U, I, Hubgeschwindigkeit v_h, Masse m |
| Berechnung | P_ab = m·g·v_h; P_Motorwelle = (k·I − M_r)·ω; η_Getriebe = P_ab / P_Motorwelle. Übernahme: `kalibrierung.py --eta <Wert>`. |
| Erfolgskriterium | η ≥ 0,80. Darunter: Achsabstand, Zahnflanken und Fluchtung prüfen. |

## Test 5 – Fahrzeugmasse

| | |
|---|---|
| Messgeräte | Waage 0,1 g |
| Vorgehen | Jedes Modul einzeln, alle Druckteile, das fertige Fahrzeug; Achslasten (jeweils eine Achse auf der Waage, die andere auf gleich hoher Unterlage). |
| Berechnung | Vergleich mit `bom/stueckliste.csv`; Achslastanteil hinten = m_hinten/m_gesamt. Übernahme: `kalibrierung.py --masse <kg> --modulmasse <kg>`. |
| Erfolgskriterium | Abweichung der Druckteile vom CAD < 10 %; Gesamtmasse dokumentiert. |

## Test 6 – Rollwiderstand

| | |
|---|---|
| Messgeräte | Bahn mit Schiene, Maßband, Smartphone-Zeitlupe, zwei Markierungen im Abstand 0,20 m |
| Aufbau | **Ritzel von der Welle abziehen oder Motor zurücksetzen**, damit nur Räder, Lager und Führung gemessen werden. |
| Vorgehen | Fahrzeug von Hand auf ca. 1 m/s anschieben und loslassen. Zeit zwischen den Markierungen (→ v0) und Ausrollweg ab der zweiten Markierung messen. 10 Wiederholungen, beide Richtungen. Danach mit eingerücktem Getriebe wiederholen. |
| Messwerte | v0, Ausrollweg s |
| Berechnung | c_rr = v0²/(2·g·s). Mit Getriebe: Zusatzwiderstand ΔF = m·(a_mit − a_ohne) → Vergleich mit i·M_r/(η·r) aus dem Motormodell. Übernahme: `kalibrierung.py --ausroll tests/messprotokolle/ausrollversuch.csv`. |
| Erfolgskriterium | c_rr ≤ 0,03; Unterschied vorwärts/rückwärts < 20 % (sonst ist die Bahn nicht eben oder ein Lager schleift). |

## Test 7 – Geradeauslauf und Spurführung

| | |
|---|---|
| Messgeräte | Bahn mit Schiene, Kreide oder Papierstreifen an den Schieneninnenwänden |
| Vorgehen | a) Ohne Schiene 2 m frei rollen lassen: seitliche Abweichung messen. b) Mit Schiene 10 Fahrten: Anlaufspuren an den Rollen, Geräusch, Aushebeln beobachten. c) Schienenstoß mit 1 mm Versatz nachstellen. |
| Messwerte | Abdrift in mm/m; Zahl der Entgleisungen |
| Berechnung | Abdrift > 10 mm/m deutet auf nicht parallele Achsen oder ungleiche Raddurchmesser. |
| Erfolgskriterium | 0 Entgleisungen in 20 Fahrten; Rollen laufen nicht dauerhaft an einer Wand. |

## Test 8 – Umkehrmechanismus

| | |
|---|---|
| Messgeräte | Federwaage 0–5 N, Durchgangsprüfer, schiefe Ebene oder Pendelaufhängung zum Einstellen definierter Aufprallgeschwindigkeiten, Smartphone-Zeitlupe, festes Brett 100 mm hoch |
| Aufbau | a) Standprüfung auf dem Tisch. b) Fahrzeug ohne Sonne (Module abgedeckt) von einer Rampe gegen das Brett rollen lassen; Höhe h → v = √(2·g·h) (0,5 m/s ≙ 13 mm; 1 m/s ≙ 51 mm; 2 m/s ≙ 204 mm; 3 m/s ≙ 459 mm). |
| Vorgehen | 1. Haltekraft des Schiebers und Eindrückkraft der Stange messen. 2. Je 20 Aufpralle bei 0,3 / 0,5 / 1 / 2 m/s, vorn und hinten, unter identischen Bedingungen. 3. Erst wenn 2 m/s fehlerfrei ist: 3 m/s und 4 m/s, nach jedem Stoß Sichtprüfung auf Risse (Träger, Dome, Lagerböcke, Module). 4. Verschiedene Schaumstoffe vergleichen. 5. Zeitlupe: Schaltet der Schieber vor dem Pufferkontakt? Prallt die hintere Stange hinein? 6. Mit Sonne: Dauerlauf 50 Wenden. |
| Messwerte | je Versuch: umgeschaltet ja/nein, Rückprallweg, Schäden (Protokoll `umkehrversuch_VORLAGE.csv`); Haltekraft, Eindrückkraft; Rückprallzahl e = v_nach/v_vor aus der Zeitlupe |
| Berechnung | Mindestgeschwindigkeit = kleinste Stufe mit 20/20 Erfolgen; Vergleich mit dem Rechenwert 0,22–0,31 m/s. Übernahme: `kalibrierung.py --rueckprall <e> --t-schalt <s>`. |
| Erfolgskriterium | 20 von 20 bei jeder Stufe ab 0,5 m/s; kein Zurückschalten; keine Schäden bis zur höchsten im Rennen erwarteten Geschwindigkeit + 20 %. |

## Test 9 – Tunneldurchfahrt

| | |
|---|---|
| Messgeräte | Karton-Tunnel 1,6 m lang (innen mindestens 150 mm breit, 80 mm hoch), Zeitlupe, Markierungen am Ein- und Ausgang |
| Vorgehen | a) Einfahrgeschwindigkeit variieren (Anlaufstrecke 1 / 2 / 4 m). b) Ein- und Ausfahrgeschwindigkeit messen. c) Kleinste Einfahrgeschwindigkeit bestimmen, bei der das Fahrzeug noch herausrollt. d) Mit 4s und 2s2p. e) Tunnel an verschiedenen Bahnpositionen. |
| Messwerte | v_ein, v_aus, Stillstand ja/nein |
| Berechnung | mittlere Verzögerung im Tunnel a = (v_ein² − v_aus²)/(2·1,6 m); Vergleich mit Simulation (`v_Tunnel_min`). Der Unterschied zum Ausrollversuch (Test 6) ist der Schleppwiderstand von Motor und Getriebe. |
| Erfolgskriterium | Durchfahrt bei der kleinsten am Renntag zu erwartenden Einfahrgeschwindigkeit mit ≥ 30 % Geschwindigkeitsreserve. |

## Test 10 – Vollständiger Rennablauf

| | |
|---|---|
| Messgeräte | 10-m-Bahn mit zwei Anschlagbrettern und Tunnel, Stoppuhr oder Videoauswertung, Multimeter für I_sc vor jedem Lauf |
| Vorgehen | Start nach Reglement (festhalten, loslassen). 4 Durchfahrten, 3 Wenden, ohne Berührung. Mindestens 10 Läufe je Lichtbedingung und Verschaltung; alle drei Getriebevarianten. |
| Messwerte | Zeit je Durchfahrt, Gesamtzeit, I_sc, Störungen (Protokoll `rennlauf_VORLAGE.csv`) |
| Berechnung | Mittelwert und Streuung; Vergleich mit `results/calculations/rennsimulation_auslegung.csv`. Abweichung > 15 % → Parameter aus Test 1–9 prüfen. |
| Erfolgskriterium | 10 von 10 Läufen ohne Eingriff; Streuung der Gesamtzeit < 10 %. |

---

## Kalibrierkette

| Test | liefert | Simulationsparameter |
|---|---|---|
| 1 | U_oc, I_sc, Füllfaktor | `module.u_oc`, `i_sc`, `n_ideal` |
| 2 | R, k, Reibmoment | Motorzeile in `motor_model.py` |
| 4 | η | `vehicle.eta_gear` |
| 5 | Masse, Achslast | `vehicle.mass`, `driven_load_frac`, `module.mass` |
| 6 | c_rr | `vehicle.crr`, `f_const` |
| 8 | Rückprallzahl, Totzeit, Mindestgeschwindigkeit | `reversal.restitution`, `t_switch`, `v_switch_min` |
| 9 | Tunnelverzögerung | Kontrolle von η, M_r, Tunnel-Restlicht |
| 10 | Rennzeit | Gesamtkontrolle |
