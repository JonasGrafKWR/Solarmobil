"""Konstruktionsparameter des SolarMobils (alle Laengen in mm).

Koordinatensystem des Fahrzeugs:  x = Fahrtrichtung "vorwaerts", y = links,
z = oben, Ursprung = Fahrzeugmitte auf der Fahrbahn.

Kennzeichnung:  [R] Reglement   [D] Datenblatt   [B] berechnet/konstruiert
                [A] ANNAHME -> am realen Teil messen und hier eintragen,
                    danach `python build_all.py` neu ausfuehren.
"""
# --- Reglement ------------------------------------------------------------------
MAX_LEN, MAX_WID = 300.0, 140.0        # [R] "ueber Alles"
RAIL_W, RAIL_H, RAIL_T = 15.0, 15.0, 2.0  # [R] U-Profil; [A] liegt auf der Bahn, Oeffnung oben
PIN_MAX = 8.0                          # [R] DM-Reglement: Fuehrungsdorn max. 8 mm

# --- Solarmodule (Starterkit) ---------------------------------------------------
MOD_L, MOD_W, MOD_T = 120.0, 60.0, 3.1  # [A] !!! unbekannt - messen !!!
MOD_MASS_G = 36.0                       # [A]

# --- Deck (Hauptrahmen) -----------------------------------------------------------
DECK_L = 2 * MOD_L                 # 240
DECK_W = 2 * MOD_W + 8.0           # 128
Z_TOP = 54.0                       # Oberseite Deck = Auflage der Module
T_PLATE = 1.0
H_RIB, T_RIB = 5.0, 1.2
Z_PB = Z_TOP - T_PLATE             # Unterseite Deckplatte

# --- Fahrwerk -----------------------------------------------------------------------
WHEEL_D = 50.0                     # [B] mit O-Ring 45x2
ORING_ID, ORING_CS = 45.0, 2.0     # Kaufteil
AXLE_Z = WHEEL_D / 2
AXLE_X = 90.0                      # Radstand 180
AXLE_D = 3.0                       # Kaufteil Alu-/Stahlstab
BRG_OD, BRG_ID, BRG_W = 6.0, 3.0, 2.5   # [D] Rillenkugellager MR63ZZ
PYL_Y, PYL_T, PYL_LX = 50.0, 3.0, 10.0  # Lagerbock: Mitte y, Dicke, Laenge in x
WHEEL_Y, WHEEL_W = 57.0, 5.0
FIT = 0.15                         # allgemeines FDM-Spiel (Bohrung groesser)
PRESS = 0.05                       # Presssitz-Untermass fuer 3-mm-Achse / 2-mm-Welle

# --- Antrieb ------------------------------------------------------------------------
GEAR_M = 0.7                       # [B] Modul
GEAR_PAIRS = {"V1_schnell": (14, 58), "V2_ausgewogen": (12, 60), "V3_anfahrstark": (10, 62)}
GEAR_DEFAULT = "V2_ausgewogen"
GEAR_BACKLASH_A = 0.10             # Achsabstandszugabe
GEAR_FLANK_COMP = 0.04             # Zahnflanken-Rueckzug je Flanke (FDM)
GEAR_Y, GEAR_W, PINION_W = 41.0, 4.0, 5.4
MOTOR_PLATE_Y, MOTOR_PLATE_T = 34.0, 2.5      # Innenflaeche (Motoranlage), Dicke
A_MIN, A_MAX = 17.5, 26.5          # einstellbarer Achsabstand (m0,5-Kaufzahnraeder ... m0,7 gedruckt)
# FF-130 [D]: Gehaeuse 20,4 x 15,4 x 25,1; Bund d6,15 x 1,6; Welle d2 bis 11,55; 2 x M2 im Abstand 12,4
FF_W, FF_H, FF_L, FF_BOSS_D, FF_BOSS_H, FF_SHAFT_L, FF_HOLE = 20.4, 15.4, 25.1, 6.15, 1.6, 11.55, 12.4
# RF-300 [D]: d24,4 x 12,3; Bund d6,1; 6 x M1,7 auf Teilkreis 16,5
RF_D, RF_L, RF_PCD = 24.4, 12.3, 16.5

# --- Spurfuehrung -------------------------------------------------------------------
GUIDE_X = 108.0
GUIDE_COL_D = 7.0
GUIDE_COL_Z0 = 17.5                # Unterkante Saeule (2,5 mm ueber Schienenoberkante)
GUIDE_ROLL_Z = 8.5                 # Mitte Fuehrungsrolle (MR63ZZ, d6 < 8 mm zulaessig)

# --- Umkehrmechanismus ----------------------------------------------------------------
ROD_Y, ROD_Z, ROD_S = 7.2, 48.0, 3.0     # Schaltstange: Versatz, Hoehe (Mitte), Querschnitt
PIN_X, PIN_Y, PIN_D = 5.0, 1.6, 3.0      # Mitnehmerstifte am Schieber (lokal)
SLIDE_H = 2.5                            # Schieberweg +-h
RAMP_DEG = 35.0
ROD_LEAD = 1.0                           # Leerweg der Stange bis Rampenbeginn
DWELL_LEN = 22.0
ROD_PROTRUDE = 10.0                      # Ueberstand Stangenspitze vor dem Puffer
PAD_T, PAD_W, PAD_H = 15.0, 40.0, 20.0   # Schaumstoff-Puffer (Kaufteil, zuschneiden)
PAD_COMPRESS = 0.8                       # nutzbare Stauchung des Puffers (Annahme)
COLLAR_L = 3.0                           # Laenge Federteller
BRK_PLATE_X0, BRK_PLATE_T = 121.0, 2.0   # Stossfaengertraeger: senkrechte Platte
BASE_Z0, BASE_T = 38.4, 1.6              # Schaltbasis
SLIDER_LX, SLIDER_LY = 24.0, 22.0
SW_HOLE_Y = 20.0                         # Lochlinie Mikroschalter (D2F-L)
SW_CX = 3.5
# Omron D2F-L [D]: 12,8 x 5,8 x 6,5; Loecher d2 im Abstand 6,5; OP 6,8 +-1,5; FP max 10; OF max 0,78 N
SW_L, SW_T, SW_ABOVE, SW_BELOW, SW_HOLE_PITCH = 12.8, 5.8, 5.0, 1.5, 6.5
MAG_D, MAG_T = 4.0, 2.0                  # Neodym-Scheibenmagnet (Kaufteil)

# --- Werkstoffe (Dichte g/cm^3) -------------------------------------------------------
DENSITY = {"ASA": 1.05, "PETG HF": 1.28, "PLA Basic": 1.24, "PLA Aero": 0.80}
