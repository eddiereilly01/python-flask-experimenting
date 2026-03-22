import csv
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime

CSV_PATH = os.getenv("CSV_PATH", "data/data.csv")
def fetch():
    print("Fetching data...")
    all_artists = {}  # keyed by data-index to avoid duplicates

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://szigetfestival.com/en/programs-lineup-2026#/", wait_until="networkidle")

        page.wait_for_selector(".widgetArtistListItem", timeout=10000)

        prev_count = 0
        no_change_streak = 0

        while True:
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            for artist in soup.select(".widgetArtistListItem"):
                idx = artist.get("data-index", len(all_artists))
                if idx not in all_artists:
                    name_tag = artist.select_one(".artistData__name__inner")
                    country = artist.select_one(".artistData__country")
                    tags = [t.get_text(strip=True) for t in artist.select(".artistData__tag")]
                    img = artist.select_one("img")
                    link = artist.select_one("a")

                    all_artists[idx] = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "name": name_tag.get_text(strip=True).replace(country.get_text(strip=True), "").strip() if name_tag and country else name_tag.get_text(strip=True) if name_tag else "",
                        "country": country.get_text(strip=True) if country else "",
                        "tags": "|".join(tags),
                        "image": img["src"] if img else "",
                        "link": link["href"] if link else "",
                    }

            print(f"Captured {len(all_artists)} artists so far...")

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)

            if len(all_artists) == prev_count:
                no_change_streak += 1
            else:
                no_change_streak = 0
            prev_count = len(all_artists)

            if no_change_streak >= 3:  # 3 scrolls with no new artists = done
                break

        browser.close()

    print(f"Found {len(all_artists)} artists total")
    write_to_csv(list(all_artists.values()))

def write_to_csv(rows):
    if not rows:
        print("No rows found — page may not have loaded correctly")
        return
    file_exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)