# Konzeptvergleich: Fahrzeug, Antrieb, Fahrgestell

Zahlen mit **[S]** stammen aus `simulation/gear_optimizer.py` (Studie 5, `results/comparisons/konzeptvergleich_simulation.csv`): je Konzept wurde die Übersetzung optimiert und die bessere Verschaltung gewählt. **[A]** = Annahme, **[C]** = CAD. Zielgröße ist die Gesamtzeit für vier Durchfahrten einschließlich dreier Richtungswechsel.

## 1. Untersuchte Fahrzeugkonzepte

| | Konzept | Masse | Annahmen |
|---|---|---|---|
| A | 1 Motor FF-130SH-14230, Heckantrieb, eine Stirnradstufe (**konstruiert**) | 260 g [C]+[A] | η = 0,88 |
| A' | wie A, aber Starterkit-Motor RF300CA-11400 | 258 g | – |
| B | 1 Motor, besonders leichtes Fahrgestell (−15 g), Riemen oder Feinverzahnung | 245 g [A] | η = 0,92 [A] |
| C | 2 Motoren FF-130SH-14230, beide Achsen angetrieben | 290 g [A] | +30 g, doppelte Motorreibung, volle Achslast für Traktion |
| D | wie A, aber nur 2 Solarmodule | 188 g | −72 g, halbe Leistung |
| E | wie A, aber Leichtbau-Solarzellen statt Kit-Module (laminierte Einzelzellen, 8 g je „Modul“ statt 36 g) | 148 g [A] | gleiche elektrische Werte |

### Simulationsergebnisse [S]

| Konzept | Sonne: Verschaltung / i_opt / Zeit / a_Start / Aufprall | Kunstlicht: Verschaltung / i_opt / Zeit / Anfahrreserve | bewölkt: Zeit / Anfahrreserve |
|---|---|---|---|
| **A** | 4s / 5,5 / **12,6 s** / 2,3 m/s² / 4,2 m/s | 2s2p / 4,5 / **25,6 s** / 2,6 | 28,9 s / 2,2 |
| A' | 4s / 5,5 / 13,9 s / 2,2 m/s² / 3,9 m/s (Motor > 6 V!) | 4s / 10 / 25,5 s / 2,9 (Motor > 6 V!) | 29,6 s / 2,5 |
| B | 4s / 5,5 / 12,2 s / 2,5 m/s² / 4,3 m/s | 2s2p / 4,5 / 24,4 s / 2,8 | 27,4 s / 2,4 |
| C | 4s / 6,0 / 13,0 s / 2,0 m/s² / 4,1 m/s | 2s2p / 5,5 / 29,7 s / 2,2 | **kein Zieleinlauf** |
| D | 2s / 3,5 / 17,2 s / 1,8 m/s² / 3,0 m/s | 2p / 3,0 / 45,1 s / 2,1 | **kein Zieleinlauf** |
| E | 4s / 4,0 / **10,8 s** / 2,8 m/s² / 5,2 m/s | 2s2p / 4,0 / **20,8 s** / 3,6 | 23,1 s / 2,8 |

### Einzelkriterien

| Kriterium | A (1 Motor, Stirnrad) | B (Leichtbau, Riemen) | C (2 Motoren) |
|---|---|---|---|
| Gesamtmasse | 260 g | 245 g | 290 g |
| Beschleunigung (Sonne / Kunstlicht) | 2,3 / 0,64 m/s² | 2,5 / 0,73 m/s² | 2,0 / 0,53 m/s² |
| Endgeschwindigkeit im Rennen (Sonne) | 4,2 m/s | 4,3 m/s | 4,1 m/s |
| Anfahren bei schwachem Licht | Reserve 2,2–2,6 | 2,4–2,8 | 2,2 und Ausfall bei „bewölkt“: zwei Motoren teilen sich den knappen Strom und haben doppelte Leerlaufverluste |
| Wirkungsgrad der Übertragung | 0,88 [A] | 0,92 [A], bei Riemen abhängig von der Vorspannung | 0,88, aber doppeltes Reibmoment |
| Rollwiderstand | 0,061 N | 0,058 N | 0,072 N (mehr Masse, zweites Getriebe) |
| mechanische Verluste | 1 Zahneingriff | 1 Riemen oder 1 Eingriff | 2 Zahneingriffe, 2 Motoren im Tunnel als Bremse |
| Fertigungskomplexität | niedrig: 1 Motorhalter, 2 Zahnräder | mittel: Riemenspannung, dünnwandiges Fahrgestell | hoch: zwei Antriebe, Gleichlauf |
| Zuverlässigkeit Richtungswechsel | gleich (Polwender) | gleich | gleich; zwei Motoren parallel am Polwender, doppelter Schaltstrom |
| Einfluss der Solarzellenmasse | Module = 55 % der Masse | 59 % | 50 % |
| Trägheit Räder/Zahnräder/Rotor | +5,1 % der Masse | ähnlich | ca. +8 % (zweiter Rotor, zweites Abtriebsrad, i höher) |

### Gewichtete Bewertung

Punkte 1 (schlecht) bis 5 (sehr gut). Die Rennzeit ist am höchsten gewichtet; sie enthält Beschleunigung, Endgeschwindigkeit und die Wendeverluste bereits.

| Kriterium | Gewicht | A | B | C |
|---|---|---|---|---|
| Simulierte Rennzeit Sonne | 25 % | 4 | 5 | 3 |
| Simulierte Rennzeit / Zieleinlauf schwaches Licht | 20 % | 4 | 5 | 1 |
| Anfahrverhalten schwaches Licht, Tunnel | 15 % | 4 | 4 | 2 |
| Zuverlässigkeit (Getriebe, Richtungswechsel) | 15 % | 5 | 3 | 3 |
| Fertigungs- und Abstimmaufwand | 10 % | 5 | 3 | 2 |
| Masse und Trägheiten | 10 % | 3 | 4 | 2 |
| Wartung, Reparierbarkeit am Renntag | 5 % | 5 | 3 | 3 |
| **Summe** | 100 % | **4,20** | **4,15** | **2,25** |

A liegt knapp vor B. B ist rechnerisch 0,4 s (Sonne) bis 1,2 s (Kunstlicht) schneller, sofern die 15 g Ersparnis und der höhere Wirkungsgrad tatsächlich erreicht werden – beides sind Annahmen. **Gewählt wird A**, weil es mit geringerem Risiko baubar ist und der Weg zu B offen bleibt (leichteres Deck, siehe Abschnitt 3). C scheidet aus: Die Leistung wird vom Solargenerator begrenzt, nicht vom Motor und nicht von der Traktion (Anfahrkraft 0,62 N bei 0,84 N Traktionsgrenze); ein zweiter Motor bringt nur Masse und Reibung.

**Wichtigster Befund außerhalb der drei Antriebskonzepte:** Die Solarmodule sind mit angenommenen 144 g der mit Abstand größte Massenanteil. Leichtere Zellen (Variante E) brächten rechnerisch 1,8 s in der Sonne und knapp 5 s unter Kunstlicht – mehr als jede Antriebsänderung. Nur zwei Module mitzunehmen (D) ist dagegen deutlich schlechter: Die halbe Masse der Module wiegt den Verlust der halben Leistung und der halben Spannung nicht auf. Variante E setzt voraus, dass das Team Einzelzellen bricht- und kurzschlussfrei verlöten und laminieren kann; die 8 g je Modul sind ein Schätzwert ohne Lieferantenangabe. Bei 148 g steigt außerdem die Aufprallgeschwindigkeit auf über 5 m/s.

## 2. Verschaltung der Solarmodule

Siehe `docs/berechnungen.md`, Abschnitt 1 und 2.3. Ergebnis: **4s bei Sonne, 2s2p bei schwachem oder künstlichem Licht**, umsteckbar über eine Stiftleiste. 4p ist in allen Szenarien deutlich langsamer (etwa 35 bis 45 s), weil rund 2 V für den Motor zu wenig sind. Als Stränge werden das vordere und das hintere Modulpaar verschaltet.

Alternative Solarzellen sind nach Reglement zulässig („Solarzellen beliebig“, „Solarzellenfläche frei wählbar“). Kriterien für einen Tausch: mindestens gleiche Fläche, Spannung im Bereich 6–9 V bei Reihenschaltung, möglichst geringes Flächengewicht. Konkrete Produkte wurden nicht recherchiert.

## 3. Fahrgestell: Leichtbaustrukturen

Lastfälle: Eigengewicht (2,6 N, davon 1,4 N Module), Antriebskraft bis 0,8 N, Aufprall mit im Mittel bis 210 N über den Stoßfängerträger [B], Führungskräfte quer unter 2 N [A].

| Struktur | Bewertung für dieses Fahrzeug |
|---|---|
| ebenes Fachwerk (Stäbe mit Diagonalen) | sehr gutes Steifigkeits-Masse-Verhältnis in der Ebene; dünne Diagonalen sind im FDM-Druck knick- und rissempfindlich; die Module steifen das Deck ohnehin aus |
| **verrippte Gitterplatte** (gewählt) | 1,0 mm Platte mit 1,2 × 5 mm Rippen; Lagerböcke, Motorplatte, Dome und Säulen wachsen ohne Stützen aus der Platte; Deck 33 g in ASA [C] |
| Hohlprofile | beste Torsionssteifigkeit; im FDM-Druck nur mit Stützen oder zweiteilig, Wandstärke ≥ 0,8 mm → kein Massevorteil bei dieser Größe |
| dünnwandige Schale | aerodynamisch günstig (c_W·A ist bei 4,4 m/s gleich groß wie der Rollwiderstand), aber die Elektrik muss einsehbar bleiben und eine Schale bringt Masse; nicht verfolgt |
| Hybrid 3D-Druck + Balsaholz | Balsa hat etwa die zehnfache spezifische Steifigkeit von PLA (E/ρ ≈ 20 gegenüber 2,2 GPa·cm³/g [Literaturwerte]); Längsträger aus Balsa 5 × 5 mm mit gedruckten Knoten könnten das Deck um geschätzt 10–15 g erleichtern [A] |

Vergleich vollständig gedruckt gegen Hybrid:

| | vollständig gedruckt (gewählt) | Hybrid Balsa + Druckknoten |
|---|---|---|
| Masse Deck | 33 g (ASA) [C] | ca. 18–23 g [A] |
| Zeitgewinn laut Simulation | – | ca. 0,2 s (Sonne), 0,4–0,6 s (Kunstlicht) [S über Massenstudie] |
| Fertigung | ein Druckteil | Zuschnitt, Klebelehre, viele Klebestellen |
| Montagegenauigkeit | Achsabstand des Getriebes und Lage der Schalteinheit durch das Druckteil festgelegt | hängt von der Klebelehre ab; Achsparallelität kritisch |
| Steifigkeit | ausreichend mit aufgeklebten Modulen | höher in Längsrichtung, Knoten sind Schwachstellen |
| Reparatur am Renntag | Ersatzteil mitbringen | Sekundenkleber, schnell |
| Nachhaltigkeitsbewertung der Jury | neutral | positiv (nachwachsender Rohstoff) |

Entscheidung: gedrucktes Deck für den ersten Prototyp, weil Getriebe und Umkehrmechanismus auf genaue Lagebeziehungen angewiesen sind. Das Hybriddeck ist der naheliegende zweite Entwicklungsschritt.

### Auslegung der Hauptmaße [C]

| Größe | Wert | Begründung |
|---|---|---|
| Länge über alles | 296 mm | Deck 240 + 2 × (Träger 3 + Puffer 15 + Stangenüberstand 10) |
| Breite | 128 mm | 2 Module + 8 mm Rand |
| Höhe | 58,6 mm | Räder (50 mm) unter dem Deck, Module obenauf: kein Schattenwurf der Räder auf die Zellen |
| Radstand / Spurweite | 180 / 114 mm | Achsen bei ±90 mm; breite Spur gegen Kippen um die Führung |
| Schwerpunkt | 8,8 mm hinter der Mitte, 47,7 mm hoch | Motor hinten → 55 % Achslast auf der Antriebsachse |
| Achsen | Alu d 3 mm in Kugellagern MR63ZZ | Biegespannung unter Radlast ca. 2 MPa [B]; Stahl wäre 9 g schwerer |
| Motorlage | hinten links, Welle parallel zur Achse, Achsabstand 17,5–26,5 mm einstellbar | deckt gedruckte Räder (Modul 0,7) und gekaufte (Modul 0,5) ab |
| Führung | 2 Rollen d 6 mm im Abstand 216 mm, vor und hinter den Achsen | langer Führungsabstand gegen Gieren; seitliches Spiel ±2,5 mm in 11 mm Schieneninnenweite |
| Puffer | Mitte 47,5 mm über der Bahn | auf Schwerpunkthöhe, damit der Aufprall das Fahrzeug nicht aufstellt |
| Kabel | offen unter dem Deck, Stiftleiste an der Schaltbasis | einsehbar, Steckbrücke als Hauptschalter |

Die Bauteile sind für diese Lasten überschlägig dimensioniert (Zahnfuß, Achse, Flächenpressung am Puffer, siehe `docs/berechnungen.md` und `docs/umkehrmechanismus.md`). Eine Festigkeitsberechnung des Decks für den Aufprall (z. B. FEM) wurde **nicht** durchgeführt; sie wird durch den gestuften Aufprallversuch (Test 8) ersetzt.
