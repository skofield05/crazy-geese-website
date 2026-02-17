#!/usr/bin/env python3
"""
Generates an A6 two-sided flyer PDF for the Rohrbach Crazy Geese.
Run: python generate-flyer.py
Output: flyer-a6.pdf
"""

from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pathlib import Path
import os

# A6 dimensions
WIDTH, HEIGHT = A6  # 105mm x 148mm = 297.64 x 419.53 points

# Colors (from style.css)
NAVY = HexColor("#1e2d4d")
BLUE = HexColor("#2563eb")
LIGHT_BG = HexColor("#f0f4ff")
LIGHT_BORDER = HexColor("#dbeafe")
GRAY = HexColor("#6b7280")
DARK = HexColor("#1e2d4d")
ORANGE = HexColor("#ea580c")

SCRIPT_DIR = Path(__file__).parent
LOGO_PATH = SCRIPT_DIR / "geese_logo.png"
OUTPUT_PATH = SCRIPT_DIR / "flyer-a6.pdf"


def draw_page1(c):
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
    c.drawCentredString(w / 2, badge_y + 2.2 * mm, "MEISTER 2025  \u2013  TITELVERTEIDIGER!")

    # === HOME GAMES SECTION ===
    games_top = badge_y - 4 * mm

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(w / 2, games_top, "HEIMSPIELE 2026")

    c.setFont("Helvetica", 7)
    c.setFillColor(GRAY)
    c.drawCentredString(w / 2, games_top - 4 * mm, "Geese Ballpark, Rohrbach")

    # Game entries - big and prominent
    games = [
        ("SA 16. MAI", "11:00", "Schremser Beers", "16:00", "Graz Dirty Sox"),
        ("SA 13. JUNI", "11:00", "Danube Titans", "16:00", "Vienna Metrostars"),
        ("SA 15. AUG", "11:00", "Vienna Bucks", "16:00", "Vienna Lawnmowers"),
    ]

    y = games_top - 12 * mm
    card_w = w - 10 * mm
    card_x = 5 * mm
    card_h = 17 * mm

    for date_str, time1, opp1, time2, opp2 in games:
        # Card background
        c.setFillColor(LIGHT_BG)
        c.roundRect(card_x, y - card_h + 2 * mm, card_w, card_h, 2 * mm, fill=1, stroke=0)

        # Date - big and bold
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(card_x + 3 * mm, y - 3 * mm, date_str)

        # Game 1
        c.setFillColor(BLUE)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(card_x + 3 * mm, y - 8.5 * mm, time1)
        c.setFillColor(DARK)
        c.setFont("Helvetica", 8)
        c.drawString(card_x + 16 * mm, y - 8.5 * mm, f"vs {opp1}")

        # Game 2
        c.setFillColor(BLUE)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(card_x + 3 * mm, y - 13 * mm, time2)
        c.setFillColor(DARK)
        c.setFont("Helvetica", 8)
        c.drawString(card_x + 16 * mm, y - 13 * mm, f"vs {opp2}")

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
    content_w = w - 2 * margin
    y = h - header_h - 6 * mm

    # === UBER UNS ===
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, y, "Wer sind wir?")
    y -= 4 * mm

    c.setFillColor(DARK)
    c.setFont("Helvetica", 7)
    lines = [
        "Die Crazy Geese sind ein Baseballverein aus",
        "Rohrbach im Burgenland. Wir",
        "spielen in der Landesliga Ost und wurden 2025",
        "ungeschlagen Meister (13-0)!",
    ]
    for line in lines:
        c.drawString(margin, y, line)
        y -= 3.3 * mm

    y -= 2 * mm

    # === TRAINING SECTION ===
    # Blue section background
    section_h = 33 * mm
    c.setFillColor(LIGHT_BG)
    c.rect(0, y - section_h + 5 * mm, w, section_h, fill=1, stroke=0)

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, y, "Training")
    y -= 5 * mm

    trainings = [
        ("Kindertraining", "Di 17:00\u201318:00", "Ab 6 Jahren"),
        ("Baseball", "Di ab 18:00", "Erwachsene, Anf\u00e4nger willkommen!"),
        ("Slowpitch Softball", "Di 18:00\u201320:00", "Gemischte Teams, M\u00e4nner & Frauen"),
    ]

    for name, time, desc in trainings:
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(margin, y, name)
        c.setFillColor(BLUE)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawRightString(w - margin, y, time)
        y -= 3.5 * mm
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 6.5)
        c.drawString(margin, y, desc)
        y -= 5 * mm

    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin, y, "Geese Ballpark, Rohrbach")
    y -= 6 * mm

    # === KEINE VORANMELDUNG ===
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin, y, "Einfach vorbeikommen!")
    y -= 4.5 * mm

    c.setFillColor(DARK)
    c.setFont("Helvetica", 7)
    infos = [
        "\u2714  Keine Voranmeldung n\u00f6tig",
        "\u2714  Ausr\u00fcstung wird vom Verein gestellt",
        "\u2714  Nur Sportgewand mitbringen",
        "\u2714  Kinder & Erwachsene willkommen",
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
    c.setFillColor(DARK)
    c.setFont("Helvetica", 7)
    c.drawString(margin, y, "Baseball-Training in Schulen \u2013 Sport & Englisch")
    y -= 3.3 * mm
    c.drawString(margin, y, "mit unserem US-Coach! Alle Altersgruppen.")
    y -= 3.3 * mm
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin, y, "Kontakt: joergdorner@gmx.net")

    # === FOOTER ===
    footer_h = 14 * mm
    c.setFillColor(NAVY)
    c.rect(0, 0, w, footer_h, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(w / 2, footer_h - 4 * mm, "crazy-geese.at")

    c.setFont("Helvetica", 6.5)
    c.drawCentredString(w / 2, footer_h - 8 * mm, "office@crazy-geese.at  |  @rohrbachcrazygeese")

    c.setFont("Helvetica", 6)
    c.setFillColor(HexColor("#94a3b8"))
    c.drawCentredString(w / 2, footer_h - 11.5 * mm, "Instagram  \u2022  Facebook")


def main():
    c = canvas.Canvas(str(OUTPUT_PATH), pagesize=A6)
    c.setTitle("Rohrbach Crazy Geese - Flyer 2026")
    c.setAuthor("Rohrbach Crazy Geese")

    # Page 1: Front
    draw_page1(c)
    c.showPage()

    # Page 2: Back
    draw_page2(c)
    c.showPage()

    c.save()
    print(f"PDF erstellt: {OUTPUT_PATH}")
    print(f"Format: A6 (105mm x 148mm), 2 Seiten")


if __name__ == "__main__":
    main()
