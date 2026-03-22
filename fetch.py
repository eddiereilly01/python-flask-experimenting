import csv
import os
import random

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
CSV_PATH = os.getenv("CSV_PATH", f"data/data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
def fetch():
    print("Fetching data...")
    all_artists = {}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://szigetfestival.com/en/programs-lineup-2026#/", wait_until="networkidle")
        page.wait_for_selector(".widgetArtistListItem", timeout=10000)

        scroll_step = 100
        scroll_position = 0

        while True:
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            for artist in soup.select(".widgetArtistListItem"):
                link = artist.select_one("a")
                idx = link["href"] if link else None
                if not idx or idx in all_artists:
                    continue

                name_tag = artist.select_one(".artistData__name__inner")
                country = artist.select_one(".artistData__country")
                tags = [t.get_text(strip=True) for t in artist.select(".artistData__tag")]
                img = artist.select_one("img")

                all_artists[idx] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "name": name_tag.get_text(strip=True).replace(country.get_text(strip=True), "").strip() if name_tag and country else name_tag.get_text(strip=True) if name_tag else "",
                    "country": country.get_text(strip=True) if country else "",
                    "tags": "|".join(tags),
                    "image": img["src"] if img else "",
                    "link": idx,
                }

            print(f"Captured {len(all_artists)} artists at scroll {scroll_position}...")

            scroll_position += scroll_step
            page.evaluate(f"window.scrollTo(0, {scroll_position})")
            page.wait_for_timeout(500)

            page_height = page.evaluate("document.body.scrollHeight")
            if scroll_position >= page_height:
                break

        browser.close()

    print(f"Found {len(all_artists)} artists total")
    write_to_csv(list(all_artists.values()))


def write_to_csv(rows):
    if not rows:
        print("No rows found — page may not have loaded correctly")
        return
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)