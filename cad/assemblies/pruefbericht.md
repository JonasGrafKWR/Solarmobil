# Prüfbericht CAD (automatisch erzeugt von cad/source/build_all.py)

Geprüft wird ausschließlich die Geometrie des CAD-Modells. Kein Ersatz für Praxistests.

| Prüfung | Ergebnis | Detail |
|---|---|---|
| Länge über alles <= 300 mm | OK | 296.0 mm (Stangenspitzen in Ruhelage; max. je Seite 148.0 mm) |
| Breite <= 140 mm | OK | 128.0 mm |
| Führungsrolle <= 8 mm (DM-Reglement) | OK | d = 6.0 mm in Schiene innen 11 mm |
| keine Durchdringung mit Führungsschiene | OK | größte Überschneidung: deck = 0.000 mm³ |
| Bodenfreiheit aller Teile außer Rad/Führung >= 2,5 mm | OK | abtriebsrad: 3.53 mm |
| Freiraum zur Schiene (seitlich ±2,4 mm, 2 mm nach oben) | OK | größte Überschneidung mit verschobener Schiene: - = 0.000 mm³ |
| Kollisionsfrei – Grundzustand (Stangen aus, Schieber VOR) | OK | keine Durchdringung > 0,05 mm³ |
| Kollisionsfrei – Stange vorn 4,5 mm (Rampe) [Schieber y = -0.05] | OK | keine Durchdringung > 0,05 mm³ |
| Kollisionsfrei – Stange vorn 10 mm (Pufferkontakt) [Schieber y = +2.50] | OK | keine Durchdringung > 0,05 mm³ |
| Kollisionsfrei – Stange vorn 22 mm (Puffer voll gestaucht) [Schieber y = +2.50] | OK | keine Durchdringung > 0,05 mm³ |
| Kollisionsfrei – Ruhe, Schieber RÜCK [Schieber y = +2.50] | OK | keine Durchdringung > 0,05 mm³ |
| Kollisionsfrei – Stange hinten 10 mm [Schieber y = -2.50] | OK | keine Durchdringung > 0,05 mm³ |
| Kollisionsfrei – Stange hinten 22 mm [Schieber y = -2.50] | OK | keine Durchdringung > 0,05 mm³ |
| Rückstellfeder geht bei voller Pufferstauchung nicht auf Block | OK | Einbauraum Feder 27.4 mm, bei 22 mm Stangenweg noch 5.4 mm (Blocklänge 14 Wdg. x 0,25 = 3,5 mm) |
| Rastfläche der Stange lang genug für vollen Stangenweg | OK | Rastende bei x = 13.6 mm, Stift bis x = 6.5 mm |
| Schieber vollständig umgelegt, bevor der Puffer anliegt | OK | Umschaltweg 8.14 mm < Überstand 10.0 mm |
| Mikroschalter: gedrückt jenseits OP, frei jenseits Rückschaltpunkt (Nennlage) | OK | Hebel gedrückt bei 6.5 mm, frei bei 11.5 mm ab Lochlinie; OP-Toleranz ±1,5 mm über Langlöcher ±1,7 mm |
| Zahnradpaar V1_schnell z=14/58 | OK | i=4.14, a=25.30 mm, Überdeckung 1.41, Kopfspiel 0.28 mm, Durchdringung 0.000 mm³, Bodenfreiheit Rad 4.1 mm, Zahnkopf Ritzel 0.40 mm |
| Zahnradpaar V2_ausgewogen z=12/60 | OK | i=5.00, a=25.30 mm, Überdeckung 1.32, Kopfspiel 0.28 mm, Durchdringung 0.000 mm³, Bodenfreiheit Rad 3.5 mm, Zahnkopf Ritzel 0.40 mm |
| Zahnradpaar V3_anfahrstark z=10/62 | OK | i=6.20, a=25.30 mm, Überdeckung 1.20, Kopfspiel 0.28 mm, Durchdringung 0.000 mm³, Bodenfreiheit Rad 2.9 mm, Zahnkopf Ritzel 0.41 mm |
| Motorwelle erreicht Ritzelbreite | OK | Wellenende y = 45.55, Ritzel bis y = 43.70 |
| Mindestwandstärken >= 1,0 mm (0,4-mm-Düse: >= 2 Bahnen) | OK | Deckplatte 1.0 mm, Rippen 1.2 mm, Lagerbock 3.0 mm, Motorplatte 2.5 mm |
| Deck passt auf 256 x 256 mm Druckbett | OK | 240 x 128 x 39 mm (für 180-mm-Betten: im Slicer bei x = 0 teilen) |
| Pufferhöhe nahe Schwerpunkthöhe (Kippmoment beim Aufprall) | OK | Puffermitte z = 47.5 mm, Schwerpunkt z = 47.7 mm |

## Hüllmaße

```json
{
  "Laenge_mm": 296.0,
  "Breite_mm": 128.0,
  "Hoehe_mm": 58.6,
  "tiefster_Punkt_mm": 1.2
}
```

## Masse und Schwerpunkt

```json
{
  "Baugruppen_g": {
    "abtriebsrad": 3.12,
    "achse": 4.6,
    "deck": 33.35,
    "distanzhuelse": 0.22,
    "federteller": 0.2,
    "fuehrungsrolle": 0.4,
    "fuehrungsschraube": 2.2,
    "klammer": 1.49,
    "lager": 0.8,
    "modul": 144.0,
    "motor": 24.0,
    "puffer": 0.5,
    "rad": 9.45,
    "ritzel": 0.36,
    "schaltbasis": 4.87,
    "schalter": 1.0,
    "schieber": 2.18,
    "stange": 4.48,
    "traeger": 6.91
  },
  "Kleinteile_Annahme_g": {
    "O-Ringe 4x": 1.48,
    "Schrauben/Muttern": 6.0,
    "Kabel, Lötzinn, Stiftleiste": 6.0,
    "Federn 2x": 0.4,
    "Magnete 2x": 0.4,
    "Klebeband/Kleber": 2.0
  },
  "Gesamtmasse_g": 260.4,
  "davon_Solarmodule_Annahme_g": 144.0,
  "Schwerpunkt_x_mm": -8.8,
  "Schwerpunkt_z_mm": 47.7,
  "Achslastanteil_Antriebsachse": 0.549,
  "J_Rad_kgm2": 1.095e-06,
  "J_Abtriebsrad_kgm2": 8.017e-07,
  "J_Ritzel_kgm2": 3.75e-09
}
```

## Kennwerte

```json
{
  "Umschaltweg_Stange_mm": 8.14,
  "Stangenueberstand_mm": 10.0,
  "Laenge_ueber_alles_mm": 296.0,
  "Achsabstand_Getriebe_mm": 25.3,
  "Radstand_mm": 180.0,
  "Spurweite_mm": 114.0
}
```