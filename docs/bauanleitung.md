# Bauanleitung: Werkstoffe, 3D-Druck, Montage

Alle Geometriedaten stammen aus dem parametrischen CAD (`cad/source/`). Die Druckteile wurden geometrisch geprüft (Kollision, Wandstärken, wasserdichte Netze), aber **noch nie gedruckt oder montiert**. Passungen deshalb zuerst an einem Probestück prüfen.

## 0. Vor dem ersten Druck: drei Maße nehmen

Die Abmessungen der Starterkit-Solarmodule sind nicht dokumentiert. In `cad/source/params_cad.py` stehen dafür Annahmen:

```python
MOD_L, MOD_W, MOD_T = 120.0, 60.0, 3.1   # Länge, Breite, Dicke eines Moduls in mm
MOD_MASS_G = 36.0                        # Masse eines Moduls in g
```

1. Ein Modul mit dem Messschieber messen und wiegen, Werte eintragen.
2. `python cad/source/build_all.py` und `python cad/source/validate_stl.py` ausführen. Das Deck wird automatisch auf 2 × Modullänge und 2 × Modulbreite + 8 mm ausgelegt.
3. Prüfbericht `cad/assemblies/pruefbericht.md` lesen. Meldet er „Breite > 140 mm“ oder „Deck passt nicht auf das Druckbett“, passen die vier Module nicht in 2 × 2-Anordnung auf das Fahrzeug – dann zuerst die Anordnung klären.

## 1. Werkstoffwahl

Kennwerte aus den Bambu-Lab-Datenblättern (TDS) in `quellen/`, soweit dort vorhanden. „n. v.“ = Datenblatt konnte nicht abgerufen werden; diese Werte vor Verwendung beim Hersteller nachschlagen.

| Werkstoff | Dichte g/cm³ | Zugfestigkeit XY / Z MPa | Biegemodul XY MPa | Biegefestigkeit XY MPa | Wärmeformbeständigkeit 0,45 MPa | Quelle |
|---|---|---|---|---|---|---|
| PLA Basic | 1,24 | 39 / 35 | 2750 | 76 | 57 °C | TDS geprüft |
| PLA Aero (geschäumt gedruckt) | 1,21 (Filament), Bauteil je nach Aufschäumung deutlich weniger | 24 / 18 | 1690 | 45 (Z: 17) | 53 °C | TDS geprüft |
| PETG HF | n. v. (typ. ca. 1,28) | n. v. | n. v. | 64 | n. v. (typ. knapp 70 °C) | nur Biegefestigkeit aus Hersteller-Shopseite |
| ASA | n. v. (typ. ca. 1,05) | n. v. | n. v. | n. v. | n. v. (typ. ca. 100 °C) | **nicht verifiziert** |
| PAHT-CF | 1,06 | 88 / 64 | 4120 | 140 | 194 °C | TDS geprüft |

Bewertung für dieses Fahrzeug:

| Kriterium | PLA Basic | PLA Aero | PETG HF | ASA | PAHT-CF |
|---|---|---|---|---|---|
| Steifigkeit | hoch | niedrig | mittel | mittel | sehr hoch |
| Schlagzähigkeit / Rissverhalten bei Aufprall | spröde | spröde, schwache Schichthaftung | zäh | zäh | zäh |
| Wärme unter dunklen Modulen in der Sonne (50–60 °C) | kritisch | kritisch | grenzwertig | gut | sehr gut |
| Maßhaltigkeit | sehr gut | schlecht (Aufschäumen) | gut | mittel (Verzug, Einhausung nötig) | gut |
| Reibung/Verschleiß an Gleitflächen und Zähnen | gut, für Zahnräder bewährt | ungeeignet | Gleitflächen gut | mittel | abrasiv gegen Gegenlauffläche |
| Druckbarkeit | sehr einfach | anspruchsvoll | einfach | Einhausung, Geruch | gehärtete Düse, Trocknung |
| Zulässigkeit | ja | ja | ja | ja | **Kohlefaser – beim Bundesfinale ist CFK verboten** |

Entscheidung je Bauteil:

- **Deck:** ASA. Es liegt direkt unter den dunklen Modulen und trägt alle Lager; PLA würde in praller Sonne kriechen. Ohne Einhausung: PETG HF (ca. 7 g schwerer).
- **Stoßfängerträger, Schaltstangen, Schieber, Basis, Klammern:** PETG HF – zäh, gleitet gut auf sich selbst.
- **Zahnräder, Räder:** PLA Basic – höchste Steifigkeit und Maßhaltigkeit; liegen im Schatten des Decks.
- **PLA Aero** bringt beim Deck rechnerisch ca. 8 g Ersparnis (3 % der Fahrzeugmasse), kostet aber Steifigkeit, Schichthaftung an den Lagerböcken und Wärmefestigkeit. Für tragende Teile und Zahnräder nicht verwendet. Sinnvoll wäre es höchstens für nichttragende Verkleidungen, die dieses Fahrzeug nicht hat.
- **PAHT-CF** wird nicht verwendet (CFK-Verbot der DM, kein Bedarf).

## 2. Druckteile

Massen aus dem CAD-Volumen (`bom/druckteile_massen.csv`). Drucklage = Lage der STL-Datei. Düse 0,4 mm, Schichthöhe 0,2 mm, sofern nicht anders angegeben.

| Datei (exports/STL) | Werkstoff | Masse je Stück | Stück | Drucklage | Wandlinien / Füllung | Stützen | Passungen und Hinweise |
|---|---|---|---|---|---|---|---|
| 01_deck_hauptrahmen | ASA | 33,4 g | 1 | Oberseite auf der Platte, 240 × 128 × 39 mm | Stege 1,0–1,2 mm = massiv; Lagerböcke/Motorplatte 100 % | keine | Lagersitz d 6,15 × 2,6; Kernlöcher d 1,6 (M2) und d 2,5 (M3); 5 mm Brim gegen Verzug; Betten < 250 mm: im Slicer bei x = 0 teilen und mit Lasche verkleben |
| 02_rad | PLA Basic | 2,4 g | 4 | Außenseite auf der Platte | 3 / 100 % | keine | Bohrung d 2,95 (Presssitz auf 3-mm-Achse, ggf. mit 3-mm-Bohrer von Hand aufreiben) |
| 03_stossfaengertraeger | PETG HF | 3,5 g | 2 | Pufferfläche auf der Platte | 4 / 100 % | keine | Durchbruch 3,6 × 3,6 für die Stange entgraten |
| 04_schaltstange | PETG HF | 2,2 g | 2 | flach | 100 % | keine | Elefantenfuß-Kompensation 0,15 mm einschalten; Rampe und Rastfläche glätten |
| 05_federteller | PETG HF | 0,1 g | 2 | Vierkantloch senkrecht | 100 % | keine | Vierkant 3,16 mm, Schiebesitz |
| 06_schaltbasis | PETG HF | 4,9 g | 1 | Grundplatte unten | 3 / 100 % | keine | Kernloch d 2,6 für M3 (waagrecht), Langlöcher 2,3 × 3,4 |
| 07_schaltschieber | PETG HF | 2,2 g | 1 | Platte unten, Stifte oben | 100 % | keine | Stifte d 3: Mindestschichtzeit 8 s; Magnettaschen d 4,1 |
| 08_modulklammer | PETG HF | 0,2 g | 8 | Lippe auf der Platte | 100 % | keine | Höhe folgt `MOD_T` |
| 09_distanzhuelse_fuehrung | PETG HF | 0,1 g | 2 | stehend | 100 % | keine | – |
| 10_ritzel_z10 / z12 / z14 | PLA Basic | 0,3–0,5 g | je 1 | flach | 100 % | keine | **Düse 0,2 mm, Schicht 0,1 mm**; Bohrung d 1,95 (Presssitz auf 2-mm-Welle) |
| 11_abtriebsrad_z58 / z60 / z62 | PLA Basic | 3,0–3,3 g | je 1 | Stegseite auf der Platte | 100 % | keine | **Düse 0,2 mm, Schicht 0,1 mm**; Bohrung d 2,95 |

Allgemeine Drucktoleranzen im Modell: Bohrungen +0,15 mm, Presssitze −0,05 mm, Zahnflanken je 0,04 mm zurückgenommen, Achsabstand +0,10 mm. Fallen Bohrungen an Ihrem Drucker enger aus, im Slicer die „XY-Lochkompensation“ erhöhen statt am CAD zu drehen.

**Zahnräder mit 0,4-mm-Düse?** Modul 0,7 hat 1,1 mm Zahndicke am Teilkreis und 0,4 mm am Ritzelkopf – das ist mit 0,4 mm Düse nicht sauber druckbar. Alternativen: Parameter `GEAR_M = 1.0` (dann nur Übersetzungen bis ca. 3,6 unter der Achse möglich) oder gekaufte Zahnräder Modul 0,5 (z. B. 12 und 60 Zähne, Achsabstand 18 mm – der Motorhalter deckt 17,5 bis 26,5 mm ab).

## 3. Kaufteile

Siehe `bom/stueckliste.csv`. Geschätzte Materialkosten ohne Starterkit: ca. 30 € (Schätzwerte, keine Angebote).

## 4. Montage

Werkzeug: Lötkolben, Seitenschneider, Schraubendreher PH0/PH00, 3-mm- und 2-mm-Bohrer (von Hand), Messschieber, Multimeter mit Durchgangsprüfer, Sekundenkleber, Federwaage oder Briefwaage.

### Schritt 1 – Achsen und Räder
1. Vier Lager MR63ZZ von außen in die Lagerböcke drücken (bündig).
2. Achsen (Alu d 3 × 122 mm) entgraten. Hinterachse: zuerst durch das linke Lager stecken, Abtriebsrad aufschieben (Nabe zeigt zum Lager, Zahnkranz zur Motorplatte), dann durch das rechte Lager.
3. Räder mit O-Ring aufpressen. Der schmale Nabenbund zeigt zum Lager und soll 0,2–0,4 mm Luft zum Lagerinnenring haben. Sitz mit einem Tropfen Sekundenkleber sichern.
4. Abtriebsrad auf y = 41 mm (Mitte Zahnkranz) setzen: 2,5 mm Abstand zur Motorplatte. Mit Sekundenkleber sichern.
5. Prüfen: Fahrzeug auf den Kopf legen, Rad anstoßen – es muss mehrere Sekunden frei auslaufen.

### Schritt 2 – Motor und Getriebe
1. Ritzel auf die Motorwelle pressen (bündig mit dem Wellenende).
2. Motor von innen an die Motorplatte setzen, Bund im Langloch, zwei Schrauben M2 × 4 leicht anziehen. **Die Schrauben dürfen höchstens 2 mm in den Motor ragen** (Datenblatt).
3. Achsabstand einstellen: Papierstreifen (ca. 0,1 mm) zwischen die Zähne, Motor andrücken, festziehen, Papier herausdrehen. Sollwert 25,3 mm.
4. Prüfen: Das Rad muss sich ohne Haken durchdrehen lassen; leichtes Zahnspiel fühlbar.

### Schritt 3 – Schalteinheit vormontieren
1. Magnete in die beiden Taschen des Schiebers kleben (Polung beliebig).
2. Mikroschalter mit M2 × 10, Scheibe und Mutter auf die Basis setzen, Hebel zeigen zur Mitte; noch nicht festziehen.
3. Stahlschrauben M3 × 8 in die beiden Wände drehen, bis die Spitze 2,5 mm vorsteht.
4. Schieber einlegen. Er muss von Hand ±2,5 mm laufen und an beiden Enden vom Magneten gehalten werden.
5. **Schalter justieren:** Durchgangsprüfer an COM und NO. Schieber in die Endlage bringen; den Schalter so weit an den Schieber schieben, dass er ca. 0,5 mm vor der Endlage schaltet. Festziehen. Für den zweiten Schalter wiederholen.
6. **Haltekraft messen:** Schieber mit der Federwaage aus der Endlage ziehen. Soll: 1,2–2,0 N. Über die Einschraubtiefe der M3-Schraube einstellen.

### Schritt 4 – Schaltstangen
1. Schaltbasis mit 4 × M2 × 8 unter das Deck schrauben.
2. Vordere Stange von der Mitte her nach vorn durch die Kerbe der Achsrippe schieben (Nocken liegt auf dem Führungsbock, Rampe zeigt zur Fahrzeugmitte).
3. Feder über die Stangenspitze schieben, dann den Federteller. Stoßfängerträger aufstecken und mit 2 × M2 × 8 anschrauben.
4. Stange so weit herausziehen, bis die Rampe 1 mm vor dem Stift steht (Schieber in Lage VOR), Federteller an die Trägerplatte schieben und mit Sekundenkleber auf der Stange fixieren.
5. Hintere Stange genauso (um 180° gedreht).
6. Prüfen: Jede Stange 9 mm eindrücken → Schieber springt um und bleibt; Stange federt zurück. Stange bis 22 mm eindrücken → kein Klemmen.
7. Schaumstoffpuffer (40 × 20 × 15 mm, Loch für die Stange) auf die Träger kleben. Stangenspitze muss 10 mm überstehen.

### Schritt 5 – Führung
M3 × 20 von unten durch Lager MR63ZZ und Distanzhülse in die Führungssäule drehen, bis das Lager spielfrei, aber leicht drehbar sitzt. Sollhöhe Rollenmitte 8,5 mm über der Bahn.

### Schritt 6 – Module und Verdrahtung
1. Module mit doppelseitigem Klebeband auf das Deck setzen (Anschlüsse nach innen), Klammern anschrauben. Die Lippen der Stoßfängerträger halten die Modulenden.
2. Vorderes Modulpaar in Reihe löten, hinteres Modulpaar in Reihe löten. **Reihenfolge der Paare beachten:** Beide vorderen Module bilden einen Strang, beide hinteren den anderen – nur so liefert beim Ein- und Ausfahren in den Tunnel ein Strang weiter Strom.
3. Stiftleiste 1 × 4 in die Lasche der Basis kleben. Anschlüsse von links nach rechts: V+, H+, V−, H−.
4. Nach Schaltplan verdrahten (`electronics/schaltplan/schaltplan.png`): V+ → NC beider Schalter (PLUS), H− → NO beider Schalter (MINUS), COM von S_R → Motoranschluss A, COM von S_V → Motoranschluss B. Leitungen offen und sichtbar verlegen.
5. Steckbrücke: **4s** = eine Brücke auf den mittleren Stiften (H+/V−). **2s2p** = zwei Brücken (V+/H+ und V−/H−). Keine Brücke = aus.
6. Prüfen ohne Sonne: Durchgang von V+ zu Motor A in Lage VOR, zu Motor B in Lage RÜCK. Kein Durchgang zwischen PLUS und MINUS bei abgeklemmtem Motor in jeder Schieberlage.
7. Prüfen in der Sonne (Räder frei): Drehrichtung muss zur Schieberlage passen – in Lage VOR fährt das Fahrzeug nach vorn. Sonst Motoranschlüsse tauschen.

### Schritt 7 – Endkontrolle
- Länge über alles mit ausgefahrenen Stangen ≤ 300 mm (Soll 296), Breite ≤ 140 mm (Soll 128).
- Masse wiegen und in `simulation/kalibrierung.py --masse` eintragen.
- Danach Testplan (`docs/testplan.md`) abarbeiten.

## 5. Wartung

| Was | Wann | Wie |
|---|---|---|
| Zahnräder | nach jedem Renntag | Zähne auf Ausbrüche prüfen, Ersatzsatz mitführen |
| Lager | bei rauem Lauf | mit Waschbenzin spülen, ein Tropfen dünnes Öl |
| Schaumstoffpuffer | wenn er sich nicht mehr vollständig zurückstellt | ersetzen |
| Schaltereinstellung | nach hartem Aufprall | Schritt 3.5 wiederholen |
| Stangen und Schieber | wöchentlich | Abrieb entfernen, trocken lassen |
