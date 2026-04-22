#!/usr/bin/env python3
"""
Generates an A6 two-sided flyer PDF for the Rohrbach Crazy Geese.

Heimspiele und Trainingszeiten werden aus data/data.json gelesen, damit der
Flyer nicht bei jeder Spielplan-Aenderung stale wird.

Run:    python generate-flyer.py
Output: flyer-a6.pdf
"""

import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# A6 dimensions
WIDTH, HEIGHT = A6  # 105mm x 148mm = 297.64 x 419.53 points

# Colors (from style.css)
NAVY = HexColor("#1e2d4d")
BLUE = HexColor("#2563eb")
LIGHT_BG = HexColor("#f0f4ff")
GRAY = HexColor("#6b7280")
ORANGE = HexColor("#ea580c")
MUTED = HexColor("#94a3b8")

SCRIPT_DIR = Path(__file__).parent
LOGO_PATH = SCRIPT_DIR / "geese_logo.png"
DATA_PATH = SCRIPT_DIR / "data" / "data.json"
OUTPUT_PATH = SCRIPT_DIR / "flyer-a6.pdf"

TEAM_FULL_NAME = "Rohrbach Crazy Geese"
HOME_LOCATION_KEYWORD = "rohrbach"

WEEKDAYS_DE = ["MO", "DI", "MI", "DO", "FR", "SA", "SO"]
MONTHS_DE = ["JAN", "FEB", "MÄR", "APR", "MAI", "JUN", "JUL", "AUG", "SEP", "OKT", "NOV", "DEZ"]

# Trainingszeiten – Quelle: CLAUDE.md (bei Aenderung dort UND hier anpassen).
TRAININGS = [
    ("Baseball", "So 15:00 · Mi 18:00", "Erwachsene, Anfänger willkommen"),
    ("Kindertraining", "Mo & Do 17:00", "Ab ca. 6 Jahren"),
    ("Slowpitch Softball", "Termine tba", "Gemischte Teams, Männer & Frauen"),
]


def load_home_games(max_days=3):
    """Liest Heimspiele aus data.json und gruppiert sie nach Datum.

    Heimspiel = Ort enthaelt 'Rohrbach' UND Rohrbach Crazy Geese ist 'heim'.
    Sortiert nach Datum aufsteigend, gibt die naechsten max_days Spieltage zurueck.
    """
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    games = (
        list(data.get("spiele", {}).get("naechste", []))
        + list(data.get("spiele", {}).get("vergangene", []))
    )
    home = [
        g for g in games
        if HOME_LOCATION_KEYWORD in (g.get("ort") or "").lower()
        and TEAM_FULL_NAME in (g.get("heim") or "")
        and g.get("datum")
    ]

    by_date = {}
    for g in home:
        by_date.setdefault(g["datum"], []).append(g)

    sorted_days = sorted(by_date.items())
    result = []
    for datum, day_games in sorted_days[:max_days]:
        day_games.sort(key=lambda g: g.get("zeit", ""))
        result.append((datum, day_games))
    return result


def format_date(datum_iso):
    d = datetime.strptime(datum_iso, "%Y-%m-%d")
    return f"{WEEKDAYS_DE[d.weekday()]} {d.day}. {MONTHS_DE[d.month - 1]}"


def opponent_label(game):
    """Kurzer Gegnername fuer den Flyer."""
    return (game.get("gast") or "").strip()


def draw_page1(c, home_days):
    """Front page: Logo, headline, home games, CTA"""
    w, h = WIDTH, HEIGHT

    # === NAVY HEADER BACKGROUND ===
    header_h = 52 * mm
    c.setFillColor(NAVY)
    c.rect(0, h - header_h, w, header_h, fill=1, stroke=0)

    # Logo
    if LOGO_PATH.exists():
        logo = ImageReader(str(LOGO_PATH))
        logo_size = 24 * mm
        c.drawImage(logo, (w - logo_size) / 2, h - 30 * mm,
                    width=logo_size, height=logo_size,
                    preserveAspectRatio=True, mask='auto')

    # Team name
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(w / 2, h - 38 * mm, "CRAZY GEESE")

    # Subtitle
    c.setFont("Helvetica", 8)
    c.drawCentredString(w / 2, h - 42 * mm, "BASEBALL IN ROHRBACH BEI MATTERSBURG")

    # === BLUE BADGE: Titelverteidiger ===
    badge_h = 8 * mm
    badge_y = h - header_h - badge_h
    c.setFillColor(BLUE)
    c.rect(0, badge_y, w, badge_h, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(w / 2, badge_y + 2.2 * mm, "MEISTER 2025  –  TITELVERTEIDIGER!")

    # === HOME GAMES SECTION ===
    games_top = badge_y - 4 * mm
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(w / 2, games_top, "HEIMSPIELE")

    c.setFont("Helvetica", 7)
    c.setFillColor(GRAY)
    c.drawCentredString(w / 2, games_top - 4 * mm, "Geese Ballpark, Rohrbach")

    y = games_top - 12 * mm
    card_w = w - 10 * mm
    card_x = 5 * mm
    card_h = 17 * mm

    if not home_days:
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 8)
        c.drawCentredString(w / 2, y - 5 * mm, "Aktueller Spielplan auf crazy-geese.at")
        y -= 10 * mm
    else:
        for datum, day_games in home_days:
            # Card background
            c.setFillColor(LIGHT_BG)
            c.roundRect(card_x, y - card_h + 2 * mm, card_w, card_h, 2 * mm, fill=1, stroke=0)

            # Date – big and bold
            c.setFillColor(NAVY)
            c.setFont("Helvetica-Bold", 13)
            c.drawString(card_x + 3 * mm, y - 3 * mm, format_date(datum))

            # Up to 2 games per day
            for slot, game in enumerate(day_games[:2]):
                row_y = y - (8.5 + 4.5 * slot) * mm
                zeit = game.get("zeit") or ""
                opp = opponent_label(game)

                c.setFillColor(BLUE)
                c.setFont("Helvetica-Bold", 7)
                c.drawString(card_x + 3 * mm, row_y, zeit)

                c.setFillColor(NAVY)
                c.setFont("Helvetica", 8)
                c.drawString(card_x + 16 * mm, row_y, f"vs {opp}")

            y -= card_h + 2 * mm

    # === EINTRITT FREI ===
    free_y = y - 2 * mm
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(w / 2, free_y, "EINTRITT FREI!")

    # === FOOTER ===
    footer_h = 7 * mm
    c.setFillColor(NAVY)
    c.rect(0, 0, w, footer_h, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica", 6.5)
    c.drawString(4 * mm, 2.5 * mm, "@rohrbachcrazygeese")
    c.drawRightString(w - 4 * mm, 2.5 * mm, "crazy-geese.at")


def draw_page2(c):
    """Back page: About, Training, Mitmachen, Contact"""
    w, h = WIDTH, HEIGHT

    # === NAVY HEADER ===
    header_h = 14 * mm
    c.setFillColor(NAVY)
    c.rect(0, h - header_h, w, header_h, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w / 2, h - 9.5 * mm, "MITMACHEN!")

    margin = 5 * mm
    y = h - header_h - 6 * mm

    # === UBER UNS ===
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, y, "Wer sind wir?")
    y -= 4 * mm

    c.setFillColor(NAVY)
    c.setFont("Helvetica", 7)
    lines = [
        "Die Crazy Geese sind ein Baseballverein aus",
        "Rohrbach bei Mattersburg im Burgenland.",
        "Wir spielen in der Landesliga Ost und wurden",
        "2025 ungeschlagen Meister (13-0)!",
    ]
    for line in lines:
        c.drawString(margin, y, line)
        y -= 3.3 * mm

    y -= 2 * mm

    # === TRAINING SECTION ===
    section_h = 33 * mm
    c.setFillColor(LIGHT_BG)
    c.rect(0, y - section_h + 5 * mm, w, section_h, fill=1, stroke=0)

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, y, "Training")
    y -= 5 * mm

    for name, zeit, desc in TRAININGS:
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(margin, y, name)
        c.setFillColor(BLUE)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawRightString(w - margin, y, zeit)
        y -= 3.5 * mm
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 6.5)
        c.drawString(margin, y, desc)
        y -= 5 * mm

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin, y, "Geese Ballpark, Rohrbach")
    y -= 6 * mm

    # === KEINE VORANMELDUNG ===
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, y, "Einfach vorbeikommen!")
    y -= 4.5 * mm

    c.setFillColor(NAVY)
    c.setFont("Helvetica", 7)
    infos = [
        "✔  Keine Voranmeldung nötig",
        "✔  Ausrüstung wird vom Verein gestellt",
        "✔  Nur Sportgewand mitbringen",
        "✔  Kinder & Erwachsene willkommen",
    ]
    for info in infos:
        c.drawString(margin, y, info)
        y -= 3.8 * mm

    y -= 1 * mm

    # === SCHULKOOPERATIONEN ===
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, y, "Schulkooperationen")
    y -= 4 * mm
    c.setFillColor(NAVY)
    c.setFont("Helvetica", 7)
    c.drawString(margin, y, "Baseball-Training in Schulen – alle Altersgruppen.")
    y -= 3.3 * mm
    c.drawString(margin, y, "Einzel-Schnupperstunden oder regelmäßig.")
    y -= 3.3 * mm
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin, y, "Kontakt: crazygeese93@gmail.com")

    # === FOOTER ===
    footer_h = 14 * mm
    c.setFillColor(NAVY)
    c.rect(0, 0, w, footer_h, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(w / 2, footer_h - 4 * mm, "crazy-geese.at")

    c.setFont("Helvetica", 6.5)
    c.drawCentredString(w / 2, footer_h - 8 * mm, "crazygeese93@gmail.com  |  @rohrbachcrazygeese")

    c.setFont("Helvetica", 6)
    c.setFillColor(MUTED)
    c.drawCentredString(w / 2, footer_h - 11.5 * mm, "Instagram  •  Facebook")


def main():
    home_days = load_home_games(max_days=3)
    print(f"Heimspiele aus data.json: {len(home_days)} Spieltage")
    for datum, day_games in home_days:
        gegner = ", ".join(opponent_label(g) for g in day_games)
        print(f"  {format_date(datum)} – {gegner}")

    c = canvas.Canvas(str(OUTPUT_PATH), pagesize=A6)
    c.setTitle("Rohrbach Crazy Geese – Flyer")
    c.setAuthor("Rohrbach Crazy Geese")

    draw_page1(c, home_days)
    c.showPage()

    draw_page2(c)
    c.showPage()

    c.save()
    print(f"PDF erstellt: {OUTPUT_PATH}")
    print(f"Format: A6 (105mm x 148mm), 2 Seiten")


if __name__ == "__main__":
    main()
