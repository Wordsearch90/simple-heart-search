"""
Scrapes every post from The Simple Heart Substack at
https://blog.simpleheart.org

Substack sites run on a public JSON API — the same one that loads posts
into the archive page's list. We can call it directly with plain HTTP
requests instead of using a headless browser, which is what the DxE
scraper needed (that site's pagination was harder to work with).

Output: docs/posts.json — consumed by docs/index.html (the search page).
"""

import json
import re
import time
from pathlib import Path

import requests

BASE_URL = "https://blog.simpleheart.org"
OUTPUT_PATH = Path(__file__).parent / "docs" / "posts.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ArchiveIndexer/1.0)"}


def get_all_post_stubs() -> list[dict]:
    """Page through the archive API to collect every post's basic metadata."""
    stubs = []
    offset = 0
    limit = 50
    while True:
        url = f"{BASE_URL}/api/v1/archive?sort=new&search=&offset={offset}&limit={limit}"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        stubs.extend(batch)
        print(f"  fetched {len(stubs)} post stubs so far...")
        if len(batch) < limit:
            break
        offset += limit
        time.sleep(0.3)
    return stubs


def get_author_names(stub: dict) -> str:
    # Substack's API has used a couple of different field names for this
    # over time, so check a few variants defensively.
    bylines = stub.get("publishedBylines") or stub.get("published_bylines") or []
    names = [b.get("name") for b in bylines if isinstance(b, dict) and b.get("name")]
    if names:
        return ", ".join(names)
    if stub.get("author"):
        return str(stub["author"])
    return ""


def get_full_post(slug: str) -> dict:
    """Fetch a single post's full data (including body) via the API."""
    url = f"{BASE_URL}/api/v1/posts/{slug}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def html_to_text(html: str) -> str:
    """Strip HTML tags down to plain text for searching."""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&#39;|&rsquo;|&apos;", "'", text)
    text = re.sub(r"&quot;|&rdquo;|&ldquo;", '"', text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print("Collecting post list from archive API...")
    stubs = get_all_post_stubs()
    print(f"Found {len(stubs)} total posts.")

    posts = []
    for i, stub in enumerate(stubs, 1):
        slug = stub.get("slug")
        title = stub.get("title", "")
        print(f"[{i}/{len(stubs)}] {title}")
        body = ""
        try:
            full = get_full_post(slug)
            body_html = full.get("body_html", "") or ""
            body = html_to_text(body_html)
        except Exception as e:
            print(f"  couldn't fetch full body ({e}), falling back to subtitle")
        if not body:
            body = stub.get("subtitle", "") or stub.get("description", "") or ""

        posts.append({
            "title": title,
            "author": get_author_names(stub),
            "date": (stub.get("post_date") or "")[:10],
            "url": stub.get("canonical_url") or f"{BASE_URL}/p/{slug}",
            "body": body,
        })
        time.sleep(0.2)

    OUTPUT_PATH.write_text(json.dumps(posts, indent=2, ensure_ascii=False))
    print(f"Saved {len(posts)} posts to {OUTPUT_PATH}")

    # Sanity check: fail loudly rather than silently "succeeding" with an
    # empty or near-empty dataset if the API shape ever changes.
    if len(posts) < 5:
        raise RuntimeError(
            f"Only scraped {len(posts)} posts — that seems too low. "
            "Failing the job so this doesn't look like a clean success."
        )


if __name__ == "__main__":
    main()
