import os
import time
import requests
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
            time.sleep(0.5)  # politeness delay — only for real requests

        next_link = soup.select_one("li.next a")
        if next_link is None or page_num >= 3:
            break

        page_num += 1
        page_url = urljoin(page_url, next_link["href"])

    unique_urls = list(dict.fromkeys(all_book_urls))  # removes duplicates, keeps order

    print(f"catalogue_pages={page_num}")
    print(f"discovered={len(all_book_urls)}")
    print(f"unique_urls={len(unique_urls)}")

    return unique_urls


if __name__ == "__main__":
    urls = discover_book_urls()