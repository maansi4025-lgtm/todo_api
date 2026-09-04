# Scraper — Books to Scrape

A polite scraping pipeline that downloads the first 3 catalogue pages of Books to Scrape, visits all 60 book detail pages, and turns the messy HTML into clean, schema-validated JSON — surviving broken pages and reporting exactly what happened on every run.

## Target classification

- **Site:** https://books.toscrape.com
- **Why this target:** Books to Scrape is a sandbox site explicitly built for people to practice web scraping, with no real business behind it — the safest possible target for learning this skill.
- **Scope:** the first 3 catalogue pages only (60 books total), plus each book's own detail page.
- **Data collected:** publicly visible book metadata already present in the page's HTML — title, price, availability, star rating, and description.
- **robots.txt result:** requested `https://books.toscrape.com/robots.txt` — returned `404 Not Found`. No robots file exists. Treated as "no explicit rules found," not as blanket permission — the site's own stated purpose as a scraping sandbox is what actually justifies scraping it here.
- **Why this is appropriate:** the site exists specifically for this purpose, no login or paywall is bypassed, and only a small, bounded slice of public data is collected.

I will not reuse this code on another site without checking its rules and terms first.

## How to run it

```bash
cd scraper
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

This produces `output/books.json` (60 validated records) and `output/run-report.json` (a summary of the run).

## Politeness rules

- **User-agent:** every real request identifies itself as `FlyRankInternshipA9/1.0`, with a link back to this repo.
- **Timeout:** every request gives up after 10 seconds rather than hanging forever.
- **Delay:** at least 0.5 seconds between real requests to the site. Cached pages need no delay — they never leave the machine.
- **Cache:** every page is saved to `cache/` on first fetch; all later runs during development read from disk instead of hitting the site again.
- **Status check:** only a `200` response is treated as a successful fetch. Anything else is logged and skipped, never parsed.

## Record schema

Each validated record in `books.json`:

| Field | Type | Notes |
|---|---|---|
| `title` | string | |
| `product_url` | string (URL) | canonical identity of the record |
| `price_gbp` | number | normalized from `price_text` |
| `price_text` | string | raw text as scraped, e.g. `"£51.77"` |
| `availability_text` | string | raw text as scraped |
| `rating_text` | string or null | e.g. `"Three"` |
| `description` | string or null | `null` when the page has no description — never invented |
| `source_page` | string | which catalogue page this book was discovered on |
| `fetched_at` | string (ISO timestamp) | when this record was fetched |

## Sample run report

```json
{
  "start_time": "2026-09-04T09:18:01.897083+00:00",
  "duration_seconds": 2.401879,
  "pages_fetched": 0,
  "cache_hits": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}
```

(This particular run includes one deliberately broken test URL, added on purpose to prove the pipeline survives a bad page — see Stage 5 of the assignment. The 60 real books were unaffected.)

## Why no browser was needed

All the data collected here — title, price, availability, rating, description — is already present in the plain HTML the server sends back. There is no JavaScript rendering step hiding this data behind an API call, so a full browser (e.g. Playwright) would only add cost and complexity with no benefit over a plain HTTP request.

## Ethics note

This scraper only touches a public sandbox built for practice. In general: prefer an official API when one exists, never bypass logins, paywalls, or explicit blocks, and only collect the minimum data actually needed. This code is not reused against any other site without re-checking that site's own rules first.

## Honest limitation

Some book descriptions on this site appear to repeat their own opening sentence within the scraped text — likely a quirk of how the source page itself renders "read more" content, not a bug in the extraction logic, but worth knowing before trusting `description` values downstream.