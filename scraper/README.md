# Scraper — Books to Scrape

## Target classification

- **Site:** https://books.toscrape.com
- **Why this target:** Books to Scrape is a sandbox site explicitly built for people to practice web scraping, with no real business behind it — the safest possible target for learning this skill.
- **Scope:** the first 3 catalogue pages only (60 books total), plus each book's own detail page.
- **Data collected:** publicly visible book metadata already present in the page's HTML — title, price, availability, star rating, and description.
- **robots.txt result:** requested `https://books.toscrape.com/robots.txt` — returned `404 Not Found`. No robots file exists. This is treated as "no explicit rules found," not as blanket permission — the site's own stated purpose as a scraping sandbox is what actually justifies scraping it here.
- **Why this is appropriate:** the site exists specifically for this purpose, no login or paywall is bypassed, and only a small, bounded slice of public data is collected.

I will not reuse this code on another site without checking its rules and terms first.