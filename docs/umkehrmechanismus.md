# Automatischer Umkehrmechanismus

Aufgabe: Das Fahrzeug muss an beiden Anschlagbrettern selbstständig die Fahrtrichtung wechseln, dreimal hintereinander, ohne Berührung von außen.

Herkunft der Zahlen: **[D]** Datenblatt, **[C]** aus CAD, **[B]** berechnet (`simulation/umkehr_berechnung.py`), **[S]** simuliert, **[A]** Annahme. Nichts in diesem Dokument ist gemessen.

## 1. Drei untersuchte Lösungen

### Konzept A – Mechanisch betätigter Polwendeschalter

Eine bewegliche Stange wird vom Anschlagbrett eingedrückt und stellt einen zweipoligen Umschalter um, der die Motoranschlüsse vertauscht.

Untersuchte Ausführungen:

| Ausführung | Beschreibung | Befund |
|---|---|---|
| A1 | durchgehende Schaltstange, schiebt DPDT-Schiebeschalter | einfach, aber: (1) kleine Schiebeschalter sind nur für 0,3 A / 6 V DC ausgelegt [D, C&K JS202011: Händlerangaben], hier fließen bis ca. 0,5 A bei bis zu 8,6 V (4s) bzw. 1,0 A (2s2p in der Sonne); (2) beim Rückprall will die Stange „stehen bleiben“ und zieht den Schalter zurück – die Haltekraft muss größer sein als Stangenmasse × Verzögerung; (3) harte Endanschläge der Stange vertragen sich nicht mit einem nachgiebigen Puffer |
| A2 | zwei federnd rückgestellte Halbstangen mit Keilnocken, Querschieber, **2 Mikroschalter (Wechsler) als Polwender**, Magnetrastung | **gewählt** – siehe Abschnitt 2 |
| A3 | wie A2, aber der Knopf eines quer eingebauten DPDT-Schiebeschalters ist selbst der Schieber | leichteste Variante (ein Kaufteil statt Schieber + 2 Schalter), elektrisch außerhalb der Nenndaten kleiner Schiebeschalter; als Rückfalllösung dokumentiert |

**Ist ein handelsüblicher DPDT-Schalter mit mechanischer Betätigung geeignet?** Ja, mit Einschränkungen:

- *Elektrisch:* Der Schalter muss den Kurzschlussstrom des Generators führen: 0,52 A (4s, 850 W/m²) bzw. 1,03 A (2s2p, 850 W/m²) [B]. Subminiatur-Schiebeschalter (0,3 A / 6 V DC) liegen darunter. Ein DPDT-Kippschalter (z. B. Baureihe MTS-202, mehrere Ampere) wäre elektrisch ausreichend, braucht aber typisch mehrere Newton Schaltkraft und wiegt ca. 5 g – Kraft- und Massewerte konnten nicht aus einem geprüften Datenblatt belegt werden.
- *Mechanisch:* Schiebeschalter haben eine stromlose Mittelstellung. Bleibt die Stange bei schwachem Aufprall dort stehen, steht das Fahrzeug.
- *Deshalb:* zwei Mikroschalter Omron D2F-L [D]: 2 A / 30 V DC (ohmsche Last), Betätigungskraft max. 0,78 N, Sprungkontakt ohne Mittelstellung, je 0,5 g, mechanische Lebensdauer ≥ 1 Mio. Schaltspiele. Für Motorlast verweist das Datenblatt auf Rückfrage beim Hersteller; die Belastung beträgt hier höchstens die Hälfte des ohmschen Nennstroms bei weniger als einem Drittel der Nennspannung.

### Konzept B – Mechanische Getriebeumkehr

Der Motor dreht immer gleich, ein Schwenkrad oder Wendegetriebe kehrt die Drehrichtung am Rad um.

- zusätzliches Zwischenrad samt Lagerung und Schwenkhebel: geschätzt +6…10 g [A]
- in einer Fahrtrichtung eine Zahnradstufe mehr: Wirkungsgrad × ca. 0,88 [A] – das Fahrzeug wäre in zwei von vier Durchfahrten langsamer
- Umschalten unter Last: Die Zähne müssen bei drehendem Motor außer und wieder in Eingriff gebracht werden; an gedruckten Zähnen mit Modul 0,7 ist das verschleiß- und klemmanfällig
- Vorteil: keine elektrischen Kontakte

Bewertung: realisierbar, aber schwerer, verlustreicher und unzuverlässiger als A2. Nicht weiterverfolgt.

### Konzept C – Bistabiles Relais mit Tastfühlern

Zwei sehr leichtgängige Tastschalter (vorn/hinten) geben einen Stromimpuls auf die Setz- bzw. Rücksetzspule eines bistabilen 2-Spulen-Relais (2 Wechsler, ca. 2 g), das den Motor umpolt. Kein Kondensator nötig.

- Vorteil: kleinste Betätigungskraft (ca. 0,25 N), praktisch keine Mindestgeschwindigkeit, definierte Kontakte
- **Schwachstelle:** Der am Brett blockierte Motor zieht die Generatorspannung auf I_sc · R_Motor herunter: bei schwachem Licht in 4s-Schaltung 0,12 A × 5,7 Ω ≈ 0,7 V [B]. Damit zieht ein 3-V-Relais nicht an. Trennt der Tastschalter stattdessen den Motor ab, solange er gedrückt ist, bleibt das Fahrzeug stromlos am Brett stehen, wenn es nicht von selbst zurückprallt.
- zusätzliches Risiko: Die Jury könnte ein Relais als „versteckte“ Elektrik werten.

Bewertung: elegant, aber bei schwachem Licht nicht eigensicher. Als Entwicklungsoption für später notiert.

### Bewertung

Punkte 1 (schlecht) bis 5 (sehr gut); Gewichtung nach Bedeutung für einen gültigen Lauf.

| Kriterium | Gewicht | A1 Schiebeschalter | **A2 Halbstangen + Mikroschalter** | B Getriebeumkehr | C Relais |
|---|---|---|---|---|---|
| Auslösen bei geringer Aufprallgeschwindigkeit | 15 % | 3 | 4 | 3 | 5 |
| Betätigungskraft | 10 % | 2 | 4 | 3 | 5 |
| Zusatzmasse | 10 % | 5 | 3 | 2 | 4 |
| Sichere Verrastung / Unempfindlichkeit gegen Rückprall | 20 % | 2 | 5 | 3 | 4 |
| Kontaktsicherheit, kein Kurzschluss beim Polwechsel | 10 % | 3 | 5 | 5 | 5 |
| Reproduzierbare Schaltpositionen | 10 % | 3 | 4 | 2 | 5 |
| Kein Verklemmen am Brett, verträgt nachgiebigen Puffer | 10 % | 2 | 5 | 3 | 4 |
| Funktion bei schwachem Licht | 10 % | 4 | 4 | 4 | 1 |
| Fertigungsaufwand | 5 % | 5 | 3 | 2 | 4 |
| **Summe (gewichtet)** | 100 % | **3,00** | **4,25** | **3,05** | **4,15** |

Gewählt: **A2**. Konzept C liegt nach Punkten knapp dahinter, scheidet aber am K.-o.-Kriterium „Funktion bei schwachem Licht“ aus: Ein Fahrzeug, das stromlos am Brett stehen bleibt, verliert den Lauf.

## 2. Aufbau des gewählten Mechanismus

Zeichnungen: `cad/assemblies/zusammenbau_umkehrmechanismus.svg` (Montagezeichnung), `cad/assemblies/vorschau_schalteinheit.png`, Funktionsdiagramm `results/diagrams/umkehr_funktionsdiagramm.png`, Schaltplan `electronics/schaltplan/schaltplan.png`.

| Pos. | Teil | Funktion |
|---|---|---|
| 1 | Schaltstange vorn / hinten (2 identische Druckteile) | ragt 10 mm über den Puffer hinaus; Keilnocken (35°) am inneren Ende |
| 2 | Rückstellfeder + Federteller | drückt die Stange nach außen (0,26 N Vorspannung [B]); Federteller = Außenanschlag |
| 3 | Schaltschieber | bewegt sich **quer** zur Fahrtrichtung um ±2,5 mm; zwei Mitnehmerstifte, zwei Magnete |
| 4 | Schaltbasis | führt Schieber und Stangen, trägt Mikroschalter (in Langlöchern justierbar) und zwei M3-Stahlschrauben als Endanschlag und Magnet-Gegenpol |
| 5 | 2 Mikroschalter Omron D2F-L | je Schieberlage ist genau einer betätigt → Polwender |
| 6 | Stoßfängerträger mit Schaumstoffpuffer 40 × 20 × 15 mm | nimmt die Aufprallenergie auf; sitzt auf Schwerpunkthöhe |

### Ablauf beim Auftreffen (vorn)

1. **0–1 mm:** Die Stangenspitze berührt das Brett, Leerweg.
2. **1–8,1 mm:** Die Rampe drückt den Stift und damit den Schieber von −2,5 nach +2,5 mm. Kurz nach Beginn löst S_V (beide Schalter frei → Motor kurzgeschlossen, bremst), kurz vor Ende schaltet S_R → Motor rückwärts gepolt. [C]
3. **8,1–10 mm:** Der Stift liegt an der geraden Rastfläche der Stange. Der Schieber ist jetzt **formschlüssig verriegelt**, solange die Stange gedrückt ist.
4. **10–22 mm:** Der Puffer liegt am Brett an und wird gestaucht; die Stange läuft auf der Rastfläche einfach weiter (kein harter Anschlag). In dieser Phase wirken die großen Verzögerungen. Die hintere Stange wird dabei von ihrer Trägheit nach vorn gedrückt (0,4…1,8 N [B]) – sie stößt gegen den verriegelten Schieber und kann nichts umschalten.
5. **Rückprall/Abfahrt:** Die Feder schiebt die vordere Stange wieder heraus. Der Schieber bleibt durch den Magneten in Lage RÜCK. Die hintere Stange ist bereit für das andere Brett.

Am hinteren Brett läuft derselbe Vorgang spiegelbildlich ab.

### Warum diese Anordnung

| Forderung | Lösung |
|---|---|
| Auslösen bei geringer Geschwindigkeit | Schaltarbeit 6,4 mJ [B] → Mindestgeschwindigkeit 0,22 m/s, mit Faktor 2 auf die Arbeit 0,31 m/s. Simulierte Aufprallgeschwindigkeiten: 1,8…4,4 m/s [S], Energiereserve 70- bis 390-fach |
| Niedrige Betätigungskraft | größte Stangenkraft 2,1 N beim Lösen des Magneten, danach 1,1 N [B] |
| Geringe Zusatzmasse | Druckteile ca. 11,4 g [C] + Schalter, Federn, Magnete, Schrauben ca. 4 g [A]; Stoßfängerträger 2 × 3,5 g [C] |
| Sichere Verrastung | Magnet (Soll 1,5 N [A]) gegen Hebelkraft 0,78 N [D]; während des Aufpralls zusätzlich Formschluss durch die Rastfläche |
| Kontaktprellen | Sprungkontakte; während des Umschaltens ist der Motor kurzgeschlossen, Prellen ändert die Polarität nicht |
| Rückprall, Mehrfachbetätigung | „Setzen/Rücksetzen“ statt „Umschalten“: ein zweiter Stoß am selben Brett ändert nichts |
| Kein Kurzschluss beim Polwechsel | jeder Motoranschluss liegt über einen Wechsler entweder an PLUS oder an MINUS; der Generator kann in keiner Stellung kurzgeschlossen werden |
| Reproduzierbare Schaltpositionen | Endlagen durch M3-Anschlagschrauben einstellbar, Schalter in Langlöchern ±1,7 mm justierbar (OP-Toleranz laut Datenblatt ±1,5 mm) |
| Kein Verklemmen am Brett | Stange und Puffer sind getrennt; Stangenweg 22 mm frei [C] |
| Rückwärts-Anfahrkraft | Antrieb ist symmetrisch; Anfahrkraft wie vorwärts (0,18…0,62 N je nach Licht [S]) |
| Kurze Stillstandszeit | Polwechsel schon 8 mm vor dem Fahrzeugkontakt; in der Simulation 0,03 s Totzeit [A] |
| Kippen beim Aufprall | Puffermitte 47,5 mm, Schwerpunkt 47,7 mm über der Bahn [C] |

### Elektrische Grenzwerte

| Größe | Wert | Herkunft |
|---|---|---|
| Schaltvermögen D2F-L | 2 A bei 30 V DC, ohmsche Last | [D] |
| Kontaktwiderstand | ≤ 30 mΩ (Neuzustand) | [D] |
| größter Strom, 4s, 850 W/m² | 0,52 A | [B] |
| größter Strom, 2s2p, 850 W/m² | 1,03 A | [B] |
| größte Spannung (Leerlauf 4s, 25 °C, 1000 W/m²) | 9,6 V | [B], Modulwerte [A] |
| Betätigungskraft / Rückstellkraft | max. 0,78 N / min. 0,05 N | [D] |
| Schaltpunkt OP ab Lochlinie | 6,8 ± 1,5 mm, Ruhelage max. 10 mm | [D] |

## 3. Offene Punkte dieses Mechanismus

1. **Magnet-Haltekraft** ist nicht berechnet, sondern als Sollwert 1,5 N angenommen. Mit Federwaage messen (Test 8) und über den Abstand der M3-Schraube einstellen. Zu schwach → Schieber fällt zurück; zu stark → höhere Mindestgeschwindigkeit.
2. **Reibwert PETG auf PETG** (0,25 angenommen). Bei 0,4 steigt die Losbrechkraft auf ca. 2,6 N.
3. **Schaumstoff:** Für 4,4 m/s wird ein Druckplateau von ca. 0,26 MPa über 12 mm Weg benötigt [B], für 2 m/s nur 0,05 MPa. Ein Schaum kann nicht beides optimal; die Auswahl erfolgt im Fallversuch (Test 8).
4. **Festigkeit beim Aufprall:** mittlere Pufferkraft bis 210 N, Verzögerung bis ca. 80 g [B]. Die Befestigung der Träger (je 2 × M2 in ASA-Domen) und die Modulbefestigung sind dafür nur überschlägig ausgelegt.
5. **Federdaten:** Die Feder ist über Abmessungen spezifiziert (Draht 0,25 mm, Außen-d 4,5–5 mm, ungespannte Länge ca. 36 mm, ca. 14 Windungen, Rate ca. 0,03–0,04 N/mm), nicht über eine geprüfte Bestellnummer.

Die Selbstständigkeit des Richtungswechsels ist damit **konstruktiv und rechnerisch begründet, aber nicht experimentell nachgewiesen**.
