#!/usr/bin/env python3
"""
Bilder von crazy-geese.at herunterladen
"""

import os
import requests
from pathlib import Path
from urllib.parse import urlparse

# Zielordner
SCRIPT_DIR = Path(__file__).parent
IMAGES_DIR = SCRIPT_DIR.parent / "data" / "alte-website-bilder"

# Bild-URLs von crazy-geese.at
IMAGE_URLS = {
    "logos": [
        "https://www.crazy-geese.at/wp-content/uploads/2018/02/R.png",
        "https://www.crazy-geese.at/wp-content/uploads/2016/04/cropped-logo_720_316.png",
        "https://www.crazy-geese.at/wp-content/uploads/2013/04/cropped-cropped-HP-Logo-Final.jpg",
    ],
    "sponsoren": [
        ("kutro.png", "https://www.crazy-geese.at/wp-content/uploads/2017/05/kutro.png"),
        ("fielders-choice.png", "https://www.crazy-geese.at/wp-content/uploads/2019/08/fc.png"),
        ("wstv.jpg", "https://www.crazy-geese.at/wp-content/uploads/2024/10/1_WSTV_Logo-300x186.jpg"),
        ("energy3000.png", "https://www.crazy-geese.at/wp-content/uploads/2023/05/9737.png"),
        ("ehrnhoefer.png", "https://www.crazy-geese.at/wp-content/uploads/2023/05/ernhoefer.png"),
        ("sipconnect.jpeg", "https://www.crazy-geese.at/wp-content/uploads/2023/05/sipconnect.jpeg"),
        ("arteks.png", "https://www.crazy-geese.at/wp-content/uploads/2017/05/arteks.png"),
        ("zeus.jpeg", "https://www.crazy-geese.at/wp-content/uploads/2021/09/zeus-300x182.jpeg"),
        ("pannonia-eagles.jpg", "https://www.crazy-geese.at/wp-content/uploads/2016/11/eagles.jpg"),
        ("pusitz-bau.jpg", "https://www.crazy-geese.at/wp-content/uploads/2013/03/pusitz-bau.jpg"),
        ("bank-burgenland.jpg", "https://www.crazy-geese.at/wp-content/uploads/2013/03/bank-burgenland.jpg"),
        ("generali.jpg", "https://www.crazy-geese.at/wp-content/uploads/2013/03/generali.jpg"),
    ],
    "sonstige": [
        "https://www.crazy-geese.at/wp-content/uploads/2013/03/lust_auf_baseball_neu1.jpg",
        "https://www.crazy-geese.at/wp-content/uploads/2024/06/images.jpg",
        "https://www.crazy-geese.at/wp-content/uploads/2013/04/FacebookLogo-300x99.png",
    ],
    "news": [
        "https://www.crazy-geese.at/wp-content/uploads/2023/05/WhatsApp-Image-2023-05-21-at-15.47.21-1140x1612.jpeg",
        "https://www.crazy-geese.at/wp-content/uploads/2023/04/Auswahl_018.png",
        "https://www.crazy-geese.at/wp-content/uploads/2022/07/slide_baseball-1140x855.jpeg",
        "https://www.crazy-geese.at/wp-content/uploads/2022/07/2022_07_30_metrostars-1140x769.png",
        "https://www.crazy-geese.at/wp-content/uploads/2022/07/2022_07_09_wandereres-1140x769.png",
        "https://www.crazy-geese.at/wp-content/uploads/2022/06/banner-1140x387.png",
        "https://www.crazy-geese.at/wp-content/uploads/2022/06/2022_06_12_cubs-1140x769.png",
    ],
}


def download_image(url, target_path):
    """Lädt ein Bild von einer URL herunter"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        with open(target_path, "wb") as f:
            f.write(response.content)

        print(f"  [OK] {target_path.name}")
        return True
    except Exception as e:
        print(f"  [FEHLER] {url}: {e}")
        return False


def main():
    print("=" * 50)
    print("Bilder von crazy-geese.at herunterladen")
    print("=" * 50)

    # Ordner erstellen
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    success = 0

    for category, urls in IMAGE_URLS.items():
        print(f"\n[{category.upper()}]")
        category_dir = IMAGES_DIR / category
        category_dir.mkdir(exist_ok=True)

        for item in urls:
            total += 1

            # Falls Tuple (name, url), sonst URL parsen
            if isinstance(item, tuple):
                filename, url = item
            else:
                url = item
                filename = os.path.basename(urlparse(url).path)

            target = category_dir / filename

            if target.exists():
                print(f"  - {filename} (existiert bereits)")
                success += 1
                continue

            if download_image(url, target):
                success += 1

    print("\n" + "=" * 50)
    print(f"Fertig: {success}/{total} Bilder heruntergeladen")
    print(f"Ordner: {IMAGES_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()
