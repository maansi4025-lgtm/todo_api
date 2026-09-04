import os
import time
import requests
import json
import re
from pydantic import BaseModel, HttpUrl, ValidationError
from datetime import datetime, timezone
from urllib.parse import urljoin
from bs4 import BeautifulSoup

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/maansi4025-lgtm/todo_api)"
TIMEOUT_SECONDS = 10
CACHE_DIR = "cache"


def fetch_page(url: str, cache_filename: str) -> str:
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)

    if response.status_code != 200:
        raise RuntimeError(f"Fetch failed: {url} returned status {response.status_code}")

    response.encoding = "utf-8"
    html = response.text
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"FETCH: {cache_filename} ({len(html)} bytes)")
    return html


def discover_book_urls():
    all_book_urls = []
    page_num = 1
    page_url = "https://books.toscrape.com/catalogue/page-1.html"

    while True:
        cache_filename = f"catalogue-page-{page_num}.html"
        was_cached = os.path.exists(os.path.join(CACHE_DIR, cache_filename))

        html = fetch_page(page_url, cache_filename)
        soup = BeautifulSoup(html, "html.parser")

        book_links = soup.select("article.product_pod h3 a")
        for link in book_links:
            relative_url = link["href"]
            absolute_url = urljoin(page_url, relative_url)
            all_book_urls.append(absolute_url)

        if not was_cached:
            time.sleep(0.5)

        next_link = soup.select_one("li.next a")
        if next_link is None or page_num >= 3:
            break

        page_num += 1
        page_url = urljoin(page_url, next_link["href"])

    unique_urls = list(dict.fromkeys(all_book_urls))

    print(f"catalogue_pages={page_num}")
    print(f"discovered={len(all_book_urls)}")
    print(f"unique_urls={len(unique_urls)}")

    return unique_urls


def extract_book(book_url: str, source_page: str) -> dict:
    cache_filename = book_url.rstrip("/").split("/")[-2] + ".html"

    html = fetch_page(book_url, cache_filename)
    soup = BeautifulSoup(html, "html.parser")

    product_main = soup.select_one("div.product_main")
    title = product_main.select_one("h1").get_text(strip=True)

    price_text = product_main.select_one("p.price_color").get_text(strip=True)

    availability_text = product_main.select_one("p.availability").get_text(strip=True)

    rating_tag = product_main.select_one("p.star-rating")
    rating_text = rating_tag["class"][1] if rating_tag else None

    description_tag = soup.select_one("#product_description ~ p")
    description = description_tag.get_text(strip=True) if description_tag else None

    return {
        "title": title,
        "product_url": book_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }
class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_gbp: float
    price_text: str
    availability_text: str
    rating_text: str | None
    description: str | None
    source_page: str
    fetched_at: str


def normalize_price(price_text: str) -> float:
    # "£51.77" -> 51.77
    cleaned = re.sub(r"[^\d.]", "", price_text)
    return float(cleaned)


def clean_and_validate(raw_records: list[dict]) -> tuple[list[dict], list[dict]]:
    valid_records = []
    invalid_records = []
    seen_urls = set()

    for raw in raw_records:
        if raw["product_url"] in seen_urls:
            continue
        seen_urls.add(raw["product_url"])

        try:
            price_gbp = normalize_price(raw["price_text"])
            record = BookRecord(
                title=raw["title"],
                product_url=raw["product_url"],
                price_gbp=price_gbp,
                price_text=raw["price_text"],
                availability_text=raw["availability_text"],
                rating_text=raw["rating_text"],
                description=raw["description"],
                source_page=raw["source_page"],
                fetched_at=raw["fetched_at"]
            )
            valid_records.append(json.loads(record.model_dump_json()))
        except (ValidationError, ValueError) as e:
            invalid_records.append({"record": raw, "error": str(e)})

    return valid_records, invalid_records
if __name__ == "__main__":
    run_start = datetime.now(timezone.utc)

    urls = discover_book_urls()

    # Stage 5 checkpoint: deliberately add one fake URL to prove failure handling
    

    raw_records = []
    failed_pages = 0
    cache_hits = 0
    fetches = 0

    for url in urls:
        cache_filename = url.rstrip("/").split("/")[-2] + ".html"
        was_cached = os.path.exists(os.path.join(CACHE_DIR, cache_filename))

        try:
            record = extract_book(url, source_page="catalogue")
            raw_records.append(record)
            if was_cached:
                cache_hits += 1
            else:
                fetches += 1
                time.sleep(0.5)
        except RuntimeError as e:
            print(f"FAILED: {url} — {e}")
            failed_pages += 1

    valid_records, invalid_records = clean_and_validate(raw_records)

    os.makedirs("output", exist_ok=True)
    with open("output/books.json", "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2)

    if invalid_records:
        with open("output/errors.json", "w", encoding="utf-8") as f:
            json.dump(invalid_records, f, indent=2)

    run_end = datetime.now(timezone.utc)
    duration_seconds = (run_end - run_start).total_seconds()

    report = {
        "start_time": run_start.isoformat(),
        "duration_seconds": duration_seconds,
        "pages_fetched": fetches,
        "cache_hits": cache_hits,
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
        "failed_pages": failed_pages
    }

    with open("output/run-report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"valid_records={len(valid_records)}")
    print(f"invalid_records={len(invalid_records)}")
    print(f"failed_pages={failed_pages}")