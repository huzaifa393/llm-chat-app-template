import requests
from bs4 import BeautifulSoup
import json
import time

BASE = "https://sunnah.com"

all_duas = []

# categories page
url = BASE + "/hisn"

html = requests.get(url).text
soup = BeautifulSoup(html, "lxml")

links = soup.select("a")

seen = set()

for a in links:
    href = a.get("href", "")

    if href.startswith("/hisn/") and href.count("/") == 2:
        full = BASE + href

        if full not in seen:
            seen.add(full)

print("TOTAL PAGES:", len(seen))

for link in seen:

    print("SCRAPING:", link)

    try:
        html = requests.get(link).text
        soup = BeautifulSoup(html, "lxml")

        title = soup.find("h1")

        title = title.text.strip() if title else "Unknown"

        arabics = soup.select(".arabic_text_details")
        english = soup.select(".english_hadith_full")
        refs = soup.select(".hadith_reference")

        for i in range(min(len(arabics), len(english))):

            item = {
                "category": title,
                "arabic": arabics[i].get_text(" ", strip=True),
                "english": english[i].get_text(" ", strip=True),
                "reference": refs[i].get_text(" ", strip=True) if i < len(refs) else ""
            }

            all_duas.append(item)

        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)

print("TOTAL DUAS:", len(all_duas))

with open("hisn_sunnah.json", "w", encoding="utf-8") as f:
    json.dump(all_duas, f, ensure_ascii=False, indent=2)

print("DONE")
