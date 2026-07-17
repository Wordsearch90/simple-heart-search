# The Simple Heart — Blog Archive

Full-text search over every post at blog.simpleheart.org, with author and
date filters — same tool as the DxE blog archive, adapted for Substack.

## How it works
- `scrape.py` calls Substack's public JSON API directly (the same one
  that powers the "Archive" page you see in your browser) — no headless
  browser needed here, unlike the DxE version, since Substack's API
  returns clean structured data with plain HTTP requests.
  - `/api/v1/archive?sort=new&offset=N&limit=50` — pages through every
    post's title, slug, date, author, and URL.
  - `/api/v1/posts/{slug}` — fetches each post's full HTML body, which
    gets stripped down to plain text for searching.
- `docs/index.html` is the same static search page used for the DxE
  archive — loads `posts.json`, filters by search term / author / date
  range, all client-side.
- `.github/workflows/scrape.yml` runs the scraper on GitHub's servers
  (manually, or automatically every Monday) and commits the updated data.

## One-time setup
1. Create a new GitHub repo and add all these files (keep the folder
   structure — `.github/workflows/scrape.yml` must stay nested exactly
   like that, note the leading dot on `.github`).
2. **Settings → Pages** → Source: "Deploy from a branch" → Branch: `main`,
   folder: `/docs` → Save. GitHub gives you a live URL.
3. **Actions** tab → click "Scrape Simple Heart Blog" → **Run workflow**.
   This should be fast (a minute or two) — no browser to install, no
   pagination clicking, just direct API calls.
4. Once it finishes (green checkmark), refresh your Pages URL — the
   archive will be searchable.

## Updating later
Re-runs automatically every Monday, or trigger manually anytime from
the Actions tab.

## If Substack's API shape ever changes
If a run fails, check the log for the actual error — Substack hasn't
publicly documented this API, so field names have shifted before. The
scraper already checks a couple of fallback field names for the author
byline; if `body_html` or `post_date` ever come back empty/differently
named, that's the first place to look.
