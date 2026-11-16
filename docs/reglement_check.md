# Regelkonformitätsmatrix – Ultraleicht-Expert

Stand der Prüfung: 14.11.2026

## 1. Quellen und Aktualität

| Kürzel | Quelle | Stand | Rolle |
|---|---|---|---|
| AUG | `quellen/SolarMobil_Augsburg_Reglement_2026.pdf` – SolarMobil Augsburg, Bayerische Meisterschaft 2026 | 28.01.2026 | **maßgebliche Planungsgrundlage** |
| WEB | https://solarmobil-augsburg.de/infos-und-teilnahme/ (abgerufen 14.11.2026) | – | Aktualitätsprüfung, Starterkit-Angaben |
| DM | `quellen/Reglement_SolarMobil_DM_2026.pdf` – SolarMobil Deutschland, Reglement zur DM 2026 | 13.01.2026 | Zusatzinformation (Bundesfinale), **keine** Augsburger Regel |

**Ergebnis der Aktualitätsprüfung:** Auf der offiziellen Seite ist kein neueres Reglement als 2026 verlinkt. Die Seite nennt als Termin den 09.07.2026 und verweist im Text noch auf das „Reglement 2025“ bzw. kündigt das neue Reglement für den 01.02.2026 an – ein Reglement für 2027 existiert dort noch nicht. Der Wettbewerb 2026 ist zum Prüfzeitpunkt bereits vorbei.

**Folge:** Das Reglement 2026 ist die Planungsgrundlage. Die Konformität für spätere Wettbewerbsjahre ist **vorläufig**; vor dem Bau das dann gültige Reglement gegen diese Matrix prüfen (alle Maße sind Parameter in `cad/source/params_cad.py`).

**Unterschiede DM 2026 gegenüber Augsburg 2026 (nur soweit konstruktionsrelevant):**

| Thema | Augsburg | DM (Bundesfinale) | Berücksichtigt |
|---|---|---|---|
| Beleuchtung 10-m-Bahn | Sonne angestrebt, Kunstlicht bei Regen/Wind (ohne nähere Angabe) | Kunstlicht: 500-W-Halogenstrahler in ca. 80 cm Höhe | Szenario „kunstlicht“ |
| CFK | nicht erwähnt | **verboten** (z. B. Carbon-Achsen) | kein CFK, kein PAHT-CF |
| Führungsdorn | nicht bemaßt | max. 8 mm (für 9-mm-Nut der Übungsbahn) | Führungsrolle d = 6 mm |
| Rennen 2 (Übungsbahn, Energy-Stick, Kurvenradius 500 mm) | für Expert nicht vorgesehen | für Expert vorgesehen | **nicht** Teil dieser Konstruktion |
| Parc fermé | – | Fahrzeug offen, Stromkreis zum Motor unterbrechen | Steckbrücke ziehen |

## 2. Matrix

Spalte „Art“: **V** = verbindliche Vorgabe (wörtlich aus AUG), **A** = technische Annahme dieser Konstruktion, **O** = offene Frage an die Rennleitung.

| Nr. | Art | Anforderung / Sachverhalt | Quelle | Umsetzung im Entwurf | Nachweis | Status |
|---|---|---|---|---|---|---|
| 1 | V | Breite bis 14 cm | AUG §3.3 | 128 mm | CAD-Prüfbericht | erfüllt (Geometrie) |
| 2 | V | Länge bis 30 cm „über Alles“ | AUG §3.3 | 296 mm mit ausgefahrenen Schaltstangen | CAD-Prüfbericht; am Fahrzeug nachmessen | erfüllt (Geometrie) |
| 3 | V | Motoren nur RF-300er- bzw. FF-130er-Serie, Anzahl beliebig | AUG §3.3 | 1 × Mabuchi FF-130SH-14230; Alternative Starterkit-RF300 | Datenblatt in `quellen/` mitführen | erfüllt |
| 4 | V | Antrieb ohne Batterie und ohne Kondensator | AUG §3.3 | Stromkreis: Solarmodule – Stiftleiste – 2 Mikroschalter – Motor | `electronics/schaltplan/schaltplan.png` | erfüllt |
| 5 | V | Elektrik jederzeit problemlos einsehbar | AUG §3.3 | Schalteinheit und Verdrahtung offen unter dem Deck, von unten und von der Seite sichtbar | Sichtprüfung | erfüllt, siehe O-3 |
| 6 | V | Fahrzeug selbst gebaut, optimiert oder neu konstruiert | AUG §3.3 | Neukonstruktion; Druck, Montage und Abstimmung durch das Team | – | durch Team zu erfüllen |
| 7 | V | Material Karosserie/Fahrgestell frei wählbar | AUG §3.3 | 3D-Druck (ASA, PETG HF, PLA) | – | erfüllt |
| 8 | V | Spurführung: U-Profil 15 mm hoch/breit, 2 mm Wandstärke | AUG §3.3 | 2 Führungsrollen d 6 mm in der Schiene | CAD-Prüfung Schiene | erfüllt unter A-1 |
| 9 | V | Solarzellen beliebig, Fläche frei wählbar | AUG §3.3 | 4 Starterkit-Module, umsteckbar 4s / 2s2p | – | erfüllt |
| 10 | V | Rennen: 10-m-Bahn 4-mal, 3 automatische Richtungswechsel ohne Eingriff von außen | AUG §3.3 | Schaltstangen + Schieber + Polwender aus 2 Mikroschaltern | `docs/umkehrmechanismus.md` | konstruiert, **nicht getestet** |
| 11 | V | Je Durchfahrt ein 1,6 m langer Tunnel | AUG §3.3 | Durchrollen mit Schwung, kein Speicher | Simulation | simuliert, siehe O-1 |
| 12 | V | Anschlagbrett am Streckenanfang und -ende, ca. 10 cm hoch | AUG §5.3 | Stangenspitze bei z = 48 mm, Puffer z = 37,5…57,5 mm | CAD | erfüllt |
| 13 | V | Bahn eben, ca. 10 m; zwei Führungsschienen im Abstand ca. 24,5 cm | AUG §5.3 | Fahrzeugbreite 128 mm → ca. 117 mm Abstand zum Nachbarfahrzeug | Rechnung | erfüllt |
| 14 | V | Start: Dorn in der Schiene, alle Räder berühren die Bahn und drehen nicht, kein Anschieben | AUG §5.5 | Fahrzeug wird festgehalten; Anfahren aus eigener Kraft (Anfahrreserve siehe Simulation) | Test 3 | simuliert |
| 15 | V | Nach der Fahrzeugabnahme keine Modifikationen | AUG §5.2 | Getriebevariante und Verschaltung **vor** der Abnahme festlegen | – | organisatorisch, siehe O-5 |
| 16 | V | Maximalzeit je Lauf wird am Wettbewerbstag bekannt gegeben | AUG §5.4 | simulierte Zeiten 13 s (Sonne) bis ca. 30 s (schwaches Licht) | Simulation | offen bis zum Renntag |
| 17 | V | Bei Regen/Wind Kunstlicht | AUG §5.8 | zweite Verschaltung 2s2p für schwaches Licht | Simulation | simuliert |
| 18 | V | Aus der Schiene gesprungenes Fahrzeug darf wieder aufgesetzt werden | AUG §5.6 | – | – | – |
| A-1 | A | Die Schiene liegt **auf** der Fahrbahn, Öffnung nach oben; Innenmaß 11 × 13 mm (aus 15 − 2·2 bzw. 15 − 2 berechnet) | – | Bodenfreiheit über der Schiene ≥ 2,5 mm, Führungsrolle in 8,5 mm Höhe | CAD | **vor dem Bau klären** |
| A-2 | A | Tunnel in Bahnmitte, Restlicht im Tunnel 0…10 % | – | Simulation variiert Lage 4…6 m | Monte-Carlo | Annahme |
| A-3 | A | Tunnel ist höher als 60 mm und breiter als 130 mm | – | Fahrzeughöhe 58,6 mm, Breite 128 mm | – | **vor dem Bau klären** |
| A-4 | A | Starterkit-Modul: 4 Zellen in Reihe, 2,4 V Leerlauf, 0,6 A Kurzschluss bei 1000 W/m², 120 × 60 × 3,1 mm, 36 g | WEB nennt nur „2 V, 0,6 A“ | Parameter `MOD_*`, `BASE_MODULE` | Test 1 und 5 | **messen** |
| A-5 | A | Kunstlicht entspricht ca. 200 W/m² Sonnenäquivalent mit ±40 % Ortswelligkeit | DM nennt nur Lampentyp und Höhe | Szenario „kunstlicht“ | Kurzschlussstrom vor Ort messen | Annahme |
| O-1 | O | Tunnel: Höhe, Breite, Lage auf der Bahn, lichtdicht oder durchscheinend? | – | – | – | Rennleitung fragen |
| O-2 | O | Schiene: aufliegend oder eingelassen? Stoßstellen, Schraubenköpfe im Profil? Abstand Schienenende – Anschlagbrett? | – | Führungshöhe über Schraubenlänge einstellbar | – | Rennleitung fragen |
| O-3 | O | Genügt für „einsehbar“ die Sicht von unten/seitlich, wenn die Module das Deck von oben abdecken? | – | notfalls Schaltplan am Fahrzeug mitführen | – | Rennleitung fragen |
| O-4 | O | Sind Dauermagnete (Rastung), Rückstellfedern und ein elastischer Schaumstoffpuffer zulässig? (Kein elektrischer Speicher; der Puffer gibt einen Teil der Aufprallenergie als Rückprall zurück.) | AUG verbietet nur Batterie und Kondensator | Rückprallzahl in der Simulation 0,3 (Annahme) | – | Rennleitung fragen |
| O-5 | O | Gilt das Umstecken der Steckbrücke (4s ↔ 2s2p) zwischen zwei Läufen als unzulässige Modifikation? | AUG §5.2 | im Zweifel vor der Abnahme festlegen | – | Rennleitung fragen |
| O-6 | O | Startposition: mit dem Heck am Anschlagbrett oder an einer Startlinie? Wo endet die Zeitmessung? | – | Simulation: Start am Brett, Ziel = Berührung des Bretts nach der 4. Durchfahrt | – | Rennleitung fragen |

## 3. Sicherheitsrelevante Punkte

Das Reglement enthält für die Expert-Klasse keine eigenen Sicherheitsvorschriften (der Explosionshinweis betrifft den Superkondensator der Solar-E-Klasse, der hier nicht verwendet wird). Aus der Konstruktion ergeben sich:

- **Aufprallenergie:** in der Sonnen-Simulation bis ca. 4,4 m/s bzw. 2,5 J am Anschlagbrett. Erstfahrten mit der langsamen Verschaltung 2s2p durchführen, Augen- und Fingerabstand zur Bahn halten (siehe `docs/testplan.md`, Test 8).
- **Motorspannung:** bei 4s bis ca. 8,1 V am Motor; der FF-130SH-14230 ist bis 10 V spezifiziert. Der Starterkit-RF300 (bis 6 V) wäre in dieser Verschaltung außerhalb seines Datenblattbereichs.
- **Löten und Sekundenkleber:** Lötdämpfe absaugen, Schutzbrille.
- **Neodym-Magnete:** klein (d 4 × 2 mm), von Kindern unter 14 Jahren fernhalten (Verschluckgefahr).

## 4. Nicht abgeleitete Maße

Folgende Größen stehen **nicht** im Reglement und werden deshalb ausdrücklich nicht als Regel behandelt: Tunnelhöhe und -breite, Tunnelposition, Fahrzeughöhe, Schienenlage (aufliegend/eingelassen), Beleuchtungsstärke, Maximalzeit, Bahnoberfläche.
