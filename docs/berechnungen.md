# Berechnungen: Solargenerator, Motor, Getriebe, Fahrleistung

Kennzeichnung jeder Zahl: **[D]** Datenblatt · **[B]** berechnet · **[S]** simuliert · **[C]** aus CAD · **[A]** Annahme · **[R]** Reglement. **Gemessen wurde nichts.** Alle Tabellen lassen sich mit den Skripten in `simulation/` neu erzeugen; vollständige Ergebnislisten liegen in `results/`.

## 1. Solargenerator

### 1.1 Was bedeuten „2 V und 0,6 A“?

Die offizielle Seite nennt für das Starterkit „vier Solarzellen (jeweils 2 V Spannung und 0,6 A Stromstärke)“. Hersteller, Typ, Kennlinie, Maße und Masse sind nicht angegeben; eine Recherche nach einem Modul mit genau diesen Werten blieb ohne Treffer. Ob es Nenn-, Leerlauf- oder Messwerte sind, lässt sich aus den Quellen **nicht** entscheiden. Physikalische Eingrenzung:

- Eine Silizium-Zelle hat etwa 0,55–0,62 V Leerlaufspannung. „2 V“ kann daher keine Leerlaufspannung einer ganzzahligen Zellenzahl sein, wohl aber die übliche **Nennspannung von vier Zellen in Reihe** (4 × 0,5 V). Die Leerlaufspannung läge dann bei ca. 2,4 V.
- Ein Vergleichsmodul mit Datenblattangaben beim Händler (TRU Components POLY-PVZ-8080-2V) wird genau so bezeichnet: Nennwerte 2 V / 0,4 A, Leerlauf 2,4 V, Kurzschluss 0,42 A, 80 × 80 × 3,1 mm, 33 g.
- „0,6 A“ ist demnach wahrscheinlich der Strom bei voller Sonne nahe dem Kurzschlussstrom.

**Modellannahme je Modul [A]:** U_oc = 2,40 V, I_sc = 0,60 A bei 1000 W/m² und 25 °C, Füllfaktor 0,72 → P_mpp ≈ 1,04 W. Die Lesart „2 V × 0,6 A = 1,2 W im Arbeitspunkt“ wäre 15 % optimistischer. Entschieden wird das durch Test 1.

Die Schulunterlage `Grundlagen Solarmodule.pptx` liefert dazu die Messmethodik (Versuche V1/V2: U_0c, I_sc, R-U-Kennlinie für Reihen-, Parallel- und gemischte Schaltung; V3 Abschattung; V4 Neigung; V5 Temperatur; V1-Kennlinien bei verschiedenen Bestrahlungsstärken, Abstandsgesetz für Lampen) und den Wirkungsgrad-Richtwert 16–20 % für Siliziumzellen. Der Messplan in `docs/testplan.md` (Test 1) folgt diesen Versuchen.

### 1.2 Elektrisches Modell (`simulation/solar_model.py`)

Eindiodenmodell je Zelle; Serien- und Parallelwiderstand sind in einer effektiven Idealität n = 2,0 zusammengefasst (ergibt den Füllfaktor 0,72):

    I = I_ph − I_0 · (exp(U_Zelle / (n·U_T)) − 1)
    I_ph = I_sc · G/1000 · (1 + α·(T − 25 °C)),   α = +0,05 %/K        [Literaturwert]
    U_oc(T) = U_oc,25 + β·(T − 25 °C),            β = −2,2 mV/K je Zelle [Literaturwert]

Module dieser Größe haben in der Regel keine Bypassdioden: In einer Reihenschaltung begrenzt das am schwächsten beleuchtete Modul den Strom. Im Sperrbereich wird ein Leckwiderstand von 20 Ω je Zelle angesetzt [A].

### 1.3 Verschaltungen (4 Module) – Kennwerte [B], Modulwerte [A]

| Verschaltung | Szenario | U_oc V | I_sc A | U_mpp V | I_mpp A | P_mpp W | P_mpp, wenn ein Modulpaar im Tunnel ist |
|---|---|---|---|---|---|---|---|
| 4s (alle in Reihe) | Sonne 850 W/m², 50 °C | 8,58 | 0,516 | 6,67 | 0,456 | 3,04 | 0,06 W |
| 4s | bewölkt 150 W/m², 25 °C | 8,04 | 0,090 | 6,27 | 0,080 | 0,50 | 0,03 W |
| 4s | Kunstlicht 200 W/m², 35 °C | 7,88 | 0,121 | 6,09 | 0,106 | 0,65 | 0,03 W |
| 2s2p (zwei Paare parallel) | Sonne | 4,29 | 1,033 | 3,33 | 0,911 | 3,04 | 1,41 W |
| 2s2p | bewölkt | 4,02 | 0,180 | 3,14 | 0,159 | 0,50 | 0,23 W |
| 2s2p | Kunstlicht | 3,94 | 0,241 | 3,05 | 0,212 | 0,65 | 0,30 W |
| 4p (alle parallel) | Sonne | 2,14 | 2,066 | 1,67 | 1,823 | 3,04 | 1,41 W |
| 4p | bewölkt | 2,01 | 0,360 | 1,57 | 0,318 | 0,50 | 0,23 W |
| 4p | Kunstlicht | 1,97 | 0,482 | 1,52 | 0,424 | 0,65 | 0,30 W |

Diagramme: `results/diagrams/solar_kennlinien.png`, `solar_temperatur_teilabschattung.png`.

Folgerungen:

- **Die maximale Leistung ist bei gleichmäßigem Licht für alle Verschaltungen gleich.** Die Verschaltung entscheidet nur, bei welcher Spannung und welchem Strom sie anfällt – und damit, wie gut sie zum Motor passt (Abschnitt 3).
- **Temperatur:** Von 25 auf 50 °C sinkt die Leerlaufspannung um 4 × 4 × 2,2 mV × 25 K = 0,88 V (4s) und die Leistung um etwa 10 %. Module nicht unnötig in der Sonne stehen lassen.
- **Teilabschattung:** Wird ein Modulpaar abgeschattet (Tunnelein- und -ausfahrt), bricht 4s praktisch vollständig ein (0,06 W), 2s2p und 4p liefern noch knapp die Hälfte. Deshalb werden die Stränge als **Paar vorn** und **Paar hinten** gebildet, nicht links/rechts.
- **Schwaches und künstliches Licht:** Der Strom sinkt proportional zur Bestrahlung, die Spannung nur logarithmisch. Bei Halogenlicht ist das Spektrum rotlastig; das Si-Äquivalent von 200 W/m² ist eine Schätzung [A]. Unter Punktstrahlern schwankt die Bestrahlung längs der Bahn (Abstandsgesetz) – im Modell ±40 % mit 1,25 m Periode [A].
- **Tunnel (1,6 m):** Ohne Batterie und Kondensator rollt das Fahrzeug mit seinem Schwung durch. Der dunkle Generator wirkt dabei wie eine Diodenkette; der Motor wird zum Generator und bremst geringfügig, sobald seine Spannung die Durchlassspannung erreicht (im Modell enthalten).

## 2. Motoren

### 2.1 Datenblattwerte und identifizierte Modellparameter

Modell: U = R·I + k·ω und M = k·I − M_r. R, k und M_r wurden je Motor per Ausgleichsrechnung aus Leerlauf-, Wirkungsgradbestpunkt- und Blockierangaben bestimmt (`simulation/motor_model.py`). Die letzte Spalte zeigt, wie gut das Modell die Datenblattpunkte trifft.

| Motor | U-Bereich V [D] | U_nenn V [D] | R Ω [B] | k mNm/A [B] | M_r mNm [B] | Anlaufstrom mA [B] | n_0 1/min [B] | M_block mNm [B] | I_block A [B] | P_mech,max W [B] | η_max % [B] | Masse g [D] | Modellfehler % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RF300CA-14270 | 0,5–4 | 1,9 | 4,73 | 4,75 | 0,155 | 33 | 3513 | 1,75 | 0,40 | 0,16 | 51 | 22 | 5,9 |
| RF300CA-11400 | 0,7–5 / 1,2–6 | 3,0 | 10,36 | 7,19 | 0,131 | 18 | 3735 | 1,95 | 0,29 | 0,19 | 56 | 22 | 4,0 |
| RF300CA-10460 | 0,8–6 | 3,2 | 14,7 | 8,21 | 0,142 | 17 | 3425 | 1,65 | 0,22 | 0,15 | 52 | 22 | 3,6 |
| RF300CA-09550 | 1–6 | 3,0 | 20,9 | 9,65 | 0,117 | 12 | 2718 | 1,27 | 0,14 | 0,09 | 50 | 22 | 3,3 |
| RF300EA-1D390 | 2,8–7 | 3,9 | 12,15 | 7,82 | 0,166 | 21 | 4448 | 2,34 | 0,32 | 0,27 | 55 | 22 | 3,1 |
| RF300FA-11420 | 0,7–5 | 3,0 | 11,82 | 9,05 | 0,157 | 17 | 2950 | 2,14 | 0,25 | 0,17 | 55 | 22 | 6,0 |
| RF300FA-12350 | 1,5–6 | 3,0 | 8,36 | 7,51 | 0,168 | 22 | 3576 | 2,53 | 0,36 | 0,24 | 56 | 22 | 7,1 |
| RF300SA-12350 | 2–6 | 3,0 | 8,29 | 8,48 | 0,231 | 27 | 3125 | 2,84 | 0,36 | 0,23 | 53 | 22 | 2,2 |
| FF-130RH-15210 | 1–4 | 3,0 | 4,78 | 4,81 | 0,220 | 46 | 5522 | 2,80 | 0,63 | 0,41 | 53 | 24 | 3,6 |
| FF-130SH-11340 | 3–12 | 7,5 | 13,56 | 10,74 | 0,360 | 34 | 6266 | 5,58 | 0,55 | 0,92 | 57 | 24 | 4,9 |
| **FF-130SH-14230** | **2,5–10** | 3,0 | **5,73** | **7,32** | 0,273 | 37 | 3636 | 3,56 | 0,52 | 0,34 | 54 | 24 | 1,6 |

Quellen: `quellen/RF300 Motoren Datenblatt.pdf` (Nostop), `quellen/Mabuchi_FF-130RH-SH_Datenblatt.pdf`. Die Werte der Spalten n_0 bis η_max gelten bei der jeweiligen **konstanten** Nennspannung. Vergleich bei einheitlich 4 V: `results/comparisons/motorvergleich_bei_4V.csv`. Kennlinien: `results/diagrams/motor_drehmoment_drehzahl.png`, `motor_leistung_wirkungsgrad.png`.

Der auf der Starterkit-Seite genannte „maximale Anlaufstrom 0,008 A“ und „2200 U/min“ lassen sich keiner Datenblattzeile zuordnen; der Kit-Motor wird deshalb als RF300CA-11400 gerechnet (einzige Variante, für die das mitgelieferte Datenblatt Kennlinien zeigt) [A]. Die Rotorträgheit steht in keinem Datenblatt: 1,2·10⁻⁷ kg·m² (FF-130) bzw. 4·10⁻⁷ kg·m² (RF-300) [A].

### 2.2 Der Solargenerator ist keine Konstantspannungsquelle

Am Solargenerator gilt weder die Nennspannung noch die Blockierstromangabe. Der Arbeitspunkt ist der Schnittpunkt aus Generatorkennlinie I_G(U) und Motorgerade I = (U − k·ω)/(R + R_Leitung). Er wird für jede Geschwindigkeit numerisch gelöst (`solve_operating_point`). Zwei Bereiche:

1. **Strombegrenzt** (niedrige Drehzahl): Der Motor könnte mehr Strom aufnehmen, als der Generator liefert → I ≈ I_sc, das Moment ist **konstant** M = k·I_sc − M_r, unabhängig von der Drehzahl.
2. **Spannungsbegrenzt** (hohe Drehzahl): Die Gegenspannung nähert sich U_oc, der Strom fällt steil ab.

Der Übergang liegt dort, wo die Motorspannung U_mpp erreicht. Diagramm: `results/diagrams/arbeitspunkt_solar_motor.png`.

Beispiel FF-130SH-14230, 4s, Sonne [B]:

    Anlauf:     U_oc/(R+R_L) = 8,58/5,93 = 1,45 A > I_sc  →  I ≈ 0,515 A
                M = 7,32 mNm/A · 0,515 A − 0,273 mNm = 3,50 mNm
    Übergang:   U_i = U_mpp − I_mpp·(R+R_L) = 6,67 − 0,456·5,93 = 3,97 V  →  n = 5180 1/min
                P_Welle = (7,32·0,456 − 0,273) mNm · 542 rad/s = 1,66 W  (55 % der Generatorleistung)
    Leerlauf:   ω_0 = (8,58 − 0,21)/0,00732 = 1143 rad/s  →  10 900 1/min

### 2.3 Anlaufrisiko bei schwachem Licht

Der Motor läuft nur an, wenn k·I_sc größer ist als sein Reibmoment **und** die Radkraft den Losbrechwiderstand übersteigt. Kunstlicht-Szenario, i = 5 [B]:

| Verschaltung | I_sc | Motormoment im Stand | Anfahrkraft am Rad | Losbrechwiderstand (1,5 × Rollwiderstand) [A] | Reserve |
|---|---|---|---|---|---|
| 4s | 0,121 A | 0,61 mNm | 0,108 N | 0,092 N | 1,2 – **kritisch** |
| 2s2p | 0,241 A | 1,49 mNm | 0,262 N | 0,092 N | 2,9 |

Deshalb wird bei schwachem Licht auf 2s2p umgesteckt. In der Monte-Carlo-Rechnung erreicht 4s unter Kunstlicht je nach Übersetzung nur in etwa 2 bis 26 % der Fälle das Ziel, 2s2p bei i = 5 bis 6 in rund 90 % (`results/comparisons/uebersetzung_unsicherheit.csv`).

### 2.4 Motorempfehlung

Für jede Kombination aus Motor, Verschaltung und Licht wurde die Übersetzung optimiert und die Gesamtzeit simuliert (`results/comparisons/motor_verschaltung_matrix.csv`). Auszug [S]:

| Szenario | Motor | Verschaltung | i_opt | Zeit s | Motorspannung max. | im Datenblattbereich |
|---|---|---|---|---|---|---|
| Sonne | FF-130RH-15210 | 4s | 8,5 | 12,58 | 8,0 V | nein (max. 4 V) |
| Sonne | **FF-130SH-14230** | **4s** | **5,5** | **12,61** | 8,1 V | **ja** |
| Sonne | RF300CA-14270 | 4s | 8,5 | 12,78 | 8,0 V | nein (max. 4 V) |
| Sonne | RF300CA-11400 (Kit) | 4s | 5,5 | 13,90 | 8,1 V | nein (max. 6 V) |
| bewölkt | RF300CA-14270 | 2s2p | 8,5 | 28,21 | 3,6 V | ja |
| bewölkt | FF-130SH-14230 | 2s2p | 5,5 | 28,88 | 3,6 V | ja |
| Kunstlicht | RF300CA-14270 | 2s2p | 7,0 | 24,88 | 3,5 V | ja |
| Kunstlicht | FF-130SH-14230 | 2s2p | 4,5 | 25,63 | 3,5 V | ja |

**Empfehlung: Mabuchi FF-130SH-14230.** Er ist der einzige Motor, der in der Sonne bei voller Generatorspannung innerhalb seines Datenblattbereichs (bis 10 V) arbeitet, in der Sonne praktisch gleichauf mit dem Schnellsten liegt und bei schwachem Licht nur 3 % hinter dem jeweils Besten – und das mit **derselben** Übersetzung. Der RF300CA-14270 wäre bei schwachem Licht 0,7 s schneller, bräuchte aber i ≈ 7–8,5 und darf nur bis 4 V betrieben werden.

Vorbehalt: Die Verfügbarkeit genau dieser Wicklung (Code 14230) wurde nicht geprüft. Rückfalllösung ist der Starterkit-Motor: in der Sonne rechnerisch 1,3 s langsamer und oberhalb von 6 V außerhalb seiner Spezifikation; für ihn sollte in der Sonne 2s2p geprüft werden.

## 3. Getriebe

### 3.1 Gleichungen (`simulation/vehicle_model.py`)

    v       = π · d · n_Rad / 60                  n_Rad = n_Motor / i,   i = n_Motor / n_Rad
    F_an    = η · i · M_Motor / r                 (Schleppbetrieb: F = i · M / (η · r))
    M_Motor = k · I − M_r                         I aus dem gemeinsamen Arbeitspunkt
    F_an   ≤ μ · m · g · Achslastanteil           Traktionsgrenze
    F_w     = c_rr·m·g + F_konst + ½·ρ·c_W·A·v² + m·g·Steigung
    m_eff   = m + (J_Räder + J_Abtriebsrad)/r² + (J_Rotor + J_Ritzel)·i²/r²
    dv/dt   = (F_an − F_w) / m_eff
    P_el    = U·I ≤ P_mpp(G, T)                   elektrische Leistungsbegrenzung
    Wende:  v_nach = e · v_auf,  Totzeit t_schalt, Umschalten nur wenn v_auf ≥ v_min

Eingangswerte der Auslegung:

| Größe | Wert | Herkunft |
|---|---|---|
| Masse m | 0,260 kg | [C] 116 g Fahrzeug + [A] 144 g Module |
| Raddurchmesser d | 50 mm | [C] |
| Getriebewirkungsgrad η | 0,88 (Bereich 0,78–0,94) | [A] |
| Rollwiderstand c_rr inkl. Lager | 0,020 (0,010–0,035) | [A] |
| Führungsreibung F_konst | 0,01 N (0–0,03) | [A] |
| c_W·A | 0,005 m² (×0,7–1,4) | [A] |
| Haftreibung μ / Achslast hinten | 0,6 (0,4–0,8) / 55 % | [A] / [C] |
| J Räder (4) / Abtriebsrad / Ritzel | 4,4·10⁻⁶ / 8,0·10⁻⁷ / 3,8·10⁻⁹ kg·m² | [C] |
| Leitungs- und Kontaktwiderstand | 0,2 Ω (0,1–0,5) | [A] |
| Rückprallzahl e / Totzeit | 0,3 (0,1–0,5) / 0,03 s (0,01–0,08) | [A] |
| Bahn 10 m, Tunnel 1,6 m, 4 Durchfahrten | – | [R]; Tunnel in Bahnmitte [A] |
| Steigung | 0 (Bahn laut Reglement eben) | [R] |

Daraus [B]: Rollwiderstand 0,061 N; Luftwiderstand bei 4,4 m/s 0,058 N; Schleppwiderstand des Motors im Tunnel i·M_r/(η·r) = 0,062 N; m_eff = 0,273 kg (Räder +2,7 %, Abtriebsrad +0,5 %, Rotor und Ritzel +1,9 %). Eine Steigung von 0,5 % entspräche 0,013 N und wäre gegenüber dem Rollwiderstand spürbar – Bahn mit der Wasserwaage prüfen.

### 3.2 Raddurchmesser

Für die Fahrdynamik zählt fast nur das Verhältnis **i/r** (`results/diagrams/raddurchmesser_uebersetzung.png`) [S]:

| Rad d mm | 20 | 30 | 40 | 44 | 50 | 60 |
|---|---|---|---|---|---|---|
| i_opt Sonne (4s) | 2,0 | 3,5 | 4,5 | 5,0 | 5,5 | 6,5 |
| Zeit Sonne s | 12,71 | 12,64 | 12,60 | 12,61 | 12,61 | 12,61 |
| i_opt Kunstlicht (2s2p) | 2,0 | 3,0 | 4,0 | 4,0 | 4,5 | 5,5 |
| Zeit Kunstlicht s | 25,73 | 25,67 | 25,67 | 25,60 | 25,63 | 25,62 |
| durchgehende Achse über der Schiene möglich | nein | nein | ja | ja | ja | ja |

Der Raddurchmesser ändert die Zeit um weniger als 1 %. Er wird deshalb **geometrisch** festgelegt: Die Achse muss über die 15 mm hohe Schiene [R, Lage A-1] → Radius ≥ 15 + 3 (Luft) + 1,5 (Achse) ≈ 20 mm. Kleinere Räder bräuchten Portal- oder Stummelachsen. Gewählt **d = 50 mm** (8,5 mm Luft über der Schiene, Platz für ein Abtriebsrad bis 44 mm Kopfkreis).

Nebenbedingung: Abtriebsrad-Radius/Radradius = m·z_1·(i/r)/2. Bei i/r = 0,2 mm⁻¹ passt das Rad nur unter die Achse, wenn m·z_1 ≤ ca. 8,5 mm ist – also Ritzel mit 10–14 Zähnen bei Modul 0,7 oder kleiner.

### 3.3 Optimale Übersetzung

Sweep i = 2…10 (`results/comparisons/uebersetzung_sweep.csv`, `results/diagrams/streckenzeit_ueber_uebersetzung.png`) [S]:

| Licht, Verschaltung | i_opt | Zeit im Optimum | Zeit bei i = 4 | i = 5 | i = 6 |
|---|---|---|---|---|---|
| Sonne, 4s | 5,50 | 12,61 s | 13,44 s | 12,68 s | 12,69 s |
| Sonne, 2s2p | 3,25 | 17,85 s | – | – | – |
| bewölkt, 2s2p | 5,50 | 28,88 s | 33,09 s | 29,22 s | 29,19 s |
| Kunstlicht, 2s2p | 4,75 | 25,59 s | 26,21 s | 25,68 s | 27,11 s |
| Kunstlicht, 4s | 10,0 (Rasterrand) | 29,60 s | Stillstand | – | – |

Das Optimum ist flach und liegt für **beide** empfohlenen Betriebsarten zwischen 4,75 und 5,5. Das Umstecken der Module wirkt wie ein elektrisches Zweiganggetriebe: 4s liefert hohe Spannung für hohe Drehzahl, 2s2p doppelten Strom für doppeltes Moment.

Warum nicht „länger“ übersetzen? Auf 10 m mit Tunnel erreicht das Fahrzeug seine Beharrungsgeschwindigkeit nie (Sonne: 4,4 m/s im Rennen gegenüber 5,1 m/s Beharrung, 5,7 m/s theoretischem Leerlauf). Entscheidend ist die Beschleunigung nach Start, Wende und Tunnel.

### 3.4 Unsicherheiten (Monte-Carlo, 300 Stichproben je Punkt) [S]

Variiert wurden gleichzeitig Bestrahlung (−25…+20 %), Modulstrom, Füllfaktor, Masse (−10…+12 %), c_rr, η, Führungsreibung, c_W·A, μ, Leitungswiderstand, Motorkonstanten (±7 %), Motorreibung (−20…+40 %), Rückprallzahl, Totzeit, Tunnel-Restlicht (0–10 %) und Tunnellage (4–6 m).

| Licht, Verschaltung | i | Ausfallquote | Zeit Median | Zeit 90 %-Wert | Aufprall 90 %-Wert |
|---|---|---|---|---|---|
| Sonne, 4s | 4,0 | 0 % | 14,5 s | 16,7 s | 4,6 m/s |
| Sonne, 4s | **5,0** | 0 % | 13,5 s | 15,1 s | 4,5 m/s |
| Sonne, 4s | 5,5 | 0 % | 13,4 s | 14,7 s | 4,3 m/s |
| Sonne, 4s | 6,0 | 0 % | 13,4 s | 14,5 s | 4,2 m/s |
| Sonne, 4s | 7,0 | 0 % | 13,9 s | 14,8 s | 3,8 m/s |
| bewölkt, 2s2p | 4,0 | 48 % | 34,9 s | 44,8 s | 2,1 m/s |
| bewölkt, 2s2p | **5,0** | 31 % | 32,0 s | 39,5 s | 2,0 m/s |
| bewölkt, 2s2p | 6,0 | 24 % | 32,1 s | 37,7 s | 1,8 m/s |
| bewölkt, 2s2p | 7,0 | 36 % | 33,4 s | 38,0 s | 1,7 m/s |
| Kunstlicht, 2s2p | 4,0 | 17 % | 29,7 s | 36,8 s | 2,2 m/s |
| Kunstlicht, 2s2p | **5,0** | 10 % | 28,5 s | 34,7 s | 2,0 m/s |
| Kunstlicht, 2s2p | 6,0 | 10 % | 29,6 s | 34,8 s | 1,8 m/s |
| Kunstlicht, 2s2p | 7,0 | 26 % | 31,8 s | 36,0 s | 1,6 m/s |

„Ausfall“ heißt: kein Anlauf am Start oder Stillstand im Tunnel. Zu kurze Übersetzung (i ≥ 7) ist bei schwachem Licht **schlechter**, weil der Motor im Tunnel stärker bremst; zu lange (i ≤ 4), weil die Anfahrkraft fehlt. **Bei einer geschlossenen Wolkendecke von 150 W/m² ist ein Zieleinlauf mit den schweren Kit-Modulen nicht gesichert** – das ist ein Ergebnis der Annahmen, kein Messwert, aber das größte Einzelrisiko des Konzepts.

### 3.5 Drei Getriebevarianten

Gemeinsam: Stirnradpaar, Modul 0,7, Eingriffswinkel 20°, Zähnezahlsumme 72 → **ein** Achsabstand 25,30 mm (25,20 + 0,10 Spiel) für alle drei Paare; V-Null-Verzahnung (x_1 = −x_2) gegen Unterschnitt; Zahnbreite Rad 4 mm, Ritzel 5,4 mm. Geometrie [B] aus `simulation/gear_geometry.py`, als CAD-Teile vorhanden und im Eingriff auf Durchdringung geprüft.

| | V1 „Schnell“ | **V2 „Ausgewogen“** | V3 „Anfahrstark“ |
|---|---|---|---|
| Zähnezahlen z_1 : z_2 | 14 : 58 | **12 : 60** | 10 : 62 |
| Übersetzung i | 4,14 | **5,00** | 6,20 |
| Profilverschiebung x_1 / x_2 | +0,21 / −0,21 | +0,32 / −0,32 | +0,44 / −0,44 |
| Teilkreis d_1 / d_2 mm | 9,80 / 40,60 | 8,40 / 42,00 | 7,00 / 43,40 |
| Kopfkreis d_a1 / d_a2 mm | 11,45 / 41,71 | 10,11 / 42,95 | 8,76 / 44,18 |
| Profilüberdeckung | 1,41 | 1,32 | 1,20 |
| Zahnkopfdicke Ritzel mm | 0,40 | 0,40 | 0,41 |
| Bodenfreiheit Abtriebsrad mm | 4,1 | 3,5 | 2,9 |
| **Sonne, 4s** [S]: Anfahrkraft N | 0,51 | 0,62 | 0,76 |
| Anfahrbeschleunigung m/s² | 1,65 | 2,03 | 2,55 |
| theor. Leerlaufgeschwindigkeit m/s | 6,9 | 5,7 | 4,6 |
| Beharrungsgeschwindigkeit m/s | 5,8 | 5,1 | 4,3 |
| größte Geschwindigkeit im Rennen m/s | 4,4 | 4,4 | 4,0 |
| 1. Durchfahrt / gesamt s | 3,83 / **13,26** | 3,58 / **12,67** | 3,48 / **12,75** |
| **Kunstlicht, 2s2p** [S]: Anfahrkraft N / Reserve | 0,22 / 2,4 | 0,26 / 2,9 | 0,33 / 3,6 |
| Anfahrbeschleunigung m/s² | 0,57 | 0,74 | 0,96 |
| kleinste Geschwindigkeit im Tunnel m/s | 1,42 | 1,38 | 1,08 |
| gesamt s | 25,95 | **25,67** | 27,56 |
| **bewölkt, 2s2p** [S]: Anfahrreserve | 1,7 | 2,0 | 2,5 |
| kleinste Geschwindigkeit im Tunnel m/s | 1,01 | 1,16 | 1,03 |
| gesamt s | 32,16 | **29,21** | 29,47 |

Einordnung:

- **V2 (12 : 60)** ist in allen drei Szenarien die schnellste oder gleichauf – Standardgetriebe.
- **V1 (14 : 58)** hat die höchste Endgeschwindigkeit, ist auf 10 m aber langsamer. Sie lohnt sich erst mit einem leichteren Fahrzeug (unter ca. 180 g liegt das Optimum bei i ≈ 4, siehe `results/calculations/masseneinfluss.csv`) oder bei mehr als ca. 1000 W/m².
- **V3 (10 : 62)** hat 24 % mehr Anfahrkraft und die niedrigste Aufprallgeschwindigkeit (4,0 statt 4,4 m/s in der Sonne bei nur 0,08 s Zeitverlust). Sie ist die Wahl, wenn das Fahrzeug bei Test 3 nicht sicher anfährt oder der Aufprall zu hart ist. Nachteil: Im Tunnel bremst der Motor stärker.

### 3.6 Bauformen des Getriebes

| Bauform | Bewertung |
|---|---|
| **eine Stirnradstufe** (gewählt) | i bis ca. 6,2 unter der Achse möglich; ein Zahneingriff, η ≈ 0,88 [A]; 2 Druckteile |
| zweistufig (z. B. 12:30 × 12:30 = 6,25) | nötig erst ab i > 6,5; zweiter Eingriff kostet ca. 10 % Wirkungsgrad, Zwischenwelle mit zwei Lagern ca. +3 g; hier ohne Vorteil |
| Übersetzung ins Schnelle (i < 1) | im Sweep bis i = 1 gerechnet: bei 260 g kein Anlauf bzw. sehr lange Zeiten – ungeeignet |
| Zahnriemen (z. B. GT2) | kleinste Scheibe ca. 14 Zähne (d ≈ 9 mm) → für i = 5 bräuchte die große Scheibe d ≈ 45 mm, breiter und schwerer als das Stirnrad; Riemenvorspannung belastet die Motorlager; gedruckte Scheiben mit 2 mm Teilung sind unkritischer zu drucken als Modul 0,7 |
| Rundriemen/O-Ring | leise und druckunkritisch, aber Schlupf und Vorspannverluste; bei schwachem Licht kostet das die knappe Anfahrreserve |
| gekaufte Zahnräder Modul 0,5 | 12 : 60 bei 18 mm Achsabstand, Motorhalter dafür verstellbar; zuverlässigste Lösung, wenn keine 0,2-mm-Düse vorhanden ist |

FDM-Grenzen: Modul 0,7 → Zahndicke 1,10 mm am Teilkreis, 0,40 mm am Ritzelkopf → 0,2-mm-Düse und 0,1 mm Schichthöhe erforderlich. Mit 0,4-mm-Düse ist Modul ≥ 1,0 nötig; dann passt unter die Achse höchstens z_2 ≈ 43 (i ≈ 3,6 mit z_1 = 12).

Zahnfußbeanspruchung [B]: größte Umfangskraft am Abtriebsrad = Traktionsgrenze 0,84 N · 25 mm / 21 mm = 1,0 N → Lewis-Näherung σ ≈ F/(b·m·Y) = 1,0/(4·0,7·0,3) ≈ 1,2 MPa, weit unter der Zugfestigkeit von PLA (39 MPa [D]). Kritisch ist nicht die Festigkeit, sondern die Maßhaltigkeit des Drucks.

## 4. Fahrleistung der Auslegung (V2, FF-130SH-14230) [S]

| | Sonne, 4s | Kunstlicht, 2s2p | bewölkt, 2s2p |
|---|---|---|---|
| Bestrahlung (Si-Äquivalent) [A] | 850 W/m² | 200 W/m² ± 40 % | 150 W/m² |
| Anfahrkraft / Anfahrreserve | 0,62 N / 6,7 | 0,26 N / 2,9 | 0,18 N / 2,0 |
| Anfahrbeschleunigung | 2,0 m/s² | 0,74 m/s² | 0,45 m/s² |
| größte Geschwindigkeit im Rennen | 4,4 m/s | 2,0 m/s | 1,9 m/s |
| kleinste Geschwindigkeit im Tunnel | 3,3 m/s | 1,4 m/s | 1,2 m/s |
| Durchfahrt 1 / 2–4 | 3,58 / 3,03 s | 6,89 / 6,26 s | 8,14 / 7,03 s |
| **Gesamtzeit (Nennwerte)** | **12,7 s** | **25,7 s** | **29,2 s** |
| Gesamtzeit Monte-Carlo: 10 % / Median / 90 % | 12,1 / 13,4 / 15,2 s | 24,8 / 28,4 / 34,4 s | 26,3 / 31,5 / 39,4 s |
| Zieleinlauf in der Monte-Carlo-Rechnung | 100 % | 92,5 % | 67,5 % |
| Zeitverlust durch drei Wenden (gegenüber verlustfreiem Rückprall) | 2,9 s | 3,9 s | 5,8 s |
| Aufprallgeschwindigkeit | 4,4 m/s | 2,0 m/s | 1,9 m/s |

Diagramme je Szenario: `results/diagrams/rennen_sonne.png`, `rennen_kunstlicht.png`, `rennen_bewoelkt.png` (Geschwindigkeit über Zeit und Strecke, Beschleunigung, Solar- und Fahrleistung).

### Tunnel [B]

Im Dunkeln bremsen Rollwiderstand (0,061 N), Motor-Schleppmoment (0,062 N bei i = 5) und Luft. Bei 2 m/s ergibt das ca. 0,135 N bzw. 0,49 m/s². Für den Generator ist der Tunnel um die Länge eines Modulpaars länger (1,6 m + 0,24 m in 4s; in 2s2p liefert das jeweils freie Paar noch halbe Leistung). Näherung für 4s: v_aus² = v_ein² − 2·0,49·1,84 → **Mindest-Einfahrgeschwindigkeit ca. 1,3–1,4 m/s**. Darunter bleibt das Fahrzeug im Tunnel stehen. Das ist der Ausfallmechanismus bei schwachem Licht.

### Einfluss der Masse [S]

| Masse | 100 g | 140 g | 180 g | 220 g | 260 g | 300 g |
|---|---|---|---|---|---|---|
| Sonne: i_opt / Zeit | 3,0 / 10,5 s | 4,0 / 10,7 s | 4,5 / 11,3 s | 5,0 / 12,0 s | 5,5 / 12,6 s | 5,5 / 13,2 s |
| Kunstlicht: i_opt / Zeit | 3,5 / 18,3 s | 4,0 / 20,4 s | 4,0 / 22,2 s | 4,5 / 24,0 s | 4,5 / 25,6 s | 5,0 / 27,2 s |

Je 10 g weniger Masse: etwa 0,16 s in der Sonne und 0,4 s unter Kunstlicht. Die Solarmodule machen 55 % der Masse aus (Annahme!) – dort liegt der größte Hebel (siehe `docs/konzeptvergleich.md`, Variante E).

## 5. Plausibilitätsprüfungen

`python -m pytest tests -q` (30 Prüfungen, alle bestanden):

- Motormodell gibt alle Datenblattpunkte auf ≤ 8–10 % wieder.
- Generator: U_oc und I_sc skalieren korrekt mit der Verschaltung; P_mpp ist bei gleichmäßigem Licht unabhängig von der Verschaltung; Spannung sinkt mit der Temperatur; Teilabschattung trifft die Reihenschaltung härter.
- Arbeitspunkt liegt auf beiden Kennlinien; U·I überschreitet nie P_mpp; I nie I_sc.
- Im Dunkeln ist die Antriebskraft ≤ 0. Die Geschwindigkeit bleibt unter der theoretischen Leerlaufgrenze. Die kinetische Energie am Ende der ersten Durchfahrt ist kleiner als die in dieser Zeit maximal verfügbare elektrische Energie.
- Mehr Licht → schneller; mehr Masse → langsamer. Ergebnis ändert sich bei viertel Zeitschritt um < 1 %.
- Zahnradpaare: Überdeckung ≥ 1,15, kein Unterschnitt, Kopfspiel ≥ 0,15 mm.
- CAD-Prüfbericht und STL-Validierung fehlerfrei; Simulationsmasse = CAD-Masse.

**Grenzen des Modells:** quasistatische Elektrik (Motorinduktivität vernachlässigt), Radschlupf nur als Kraftgrenze, Aufprall als Stoßzahl, keine Querdynamik und keine Führungsstöße, keine Erwärmung des Motors, Kunstlicht stark vereinfacht. Die Rennzeiten sind deshalb Erwartungswerte unter Annahmen – keine bestätigte Leistung.
