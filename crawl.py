#!/usr/bin/env python3
"""
AI-Experts Website Crawler
Crawls https://ai-experts.network/de/ and creates a local static copy.
Uses Playwright for rendering JavaScript-heavy pages.
"""

import asyncio
import json
import os
import re
import time
import urllib.parse
from pathlib import Path
from collections import defaultdict

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Track CSS files already processed to avoid double-patching
processed_css: set[str] = set()

# ─── Configuration ────────────────────────────────────────────────────────────
BASE_URL = "https://ai-experts.network"
START_URL = "https://ai-experts.network/de/"
START_URLS = [
    "https://ai-experts.network/de/",
    "https://ai-experts.network/en/",
]
OUTPUT_DIR = Path(__file__).parent / "ai-experts-clone"
ASSETS_DIR = OUTPUT_DIR / "assets"
MAX_PAGES = 100          # safety cap
DELAY_BETWEEN_REQUESTS = 1.0   # seconds, be polite
TIMEOUT = 30000          # ms for Playwright

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ─── Globals ──────────────────────────────────────────────────────────────────
visited_pages: set[str] = set()
queued_pages: list[str] = list(START_URLS)
downloaded_assets: dict[str, str] = {}   # remote URL → local relative path
failed_assets: list[dict] = []
failed_pages: list[dict] = []
crawled_pages: list[dict] = []

# ─── Helpers ──────────────────────────────────────────────────────────────────

def normalize_url(url: str, base: str = BASE_URL) -> str | None:
    """Resolve a possibly relative URL and return absolute if internal."""
    if not url or url.startswith(("mailto:", "tel:", "javascript:", "#")):
        return None
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme in ("http", "https"):
        if parsed.netloc and parsed.netloc != "ai-experts.network":
            return None  # external
        return url.split("#")[0].rstrip("/") + "/"
    # relative
    resolved = urllib.parse.urljoin(base, url)
    if "ai-experts.network" not in resolved:
        return None
    return resolved.split("#")[0].rstrip("/") + "/"


def url_to_local_path(url: str) -> Path:
    """Convert a page URL like /de/foo/ → OUTPUT_DIR/de/foo/index.html"""
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lstrip("/")
    if not path or path.endswith("/"):
        path = path + "index.html"
    elif "." not in Path(path).name:
        path = path + "/index.html"
    return OUTPUT_DIR / path


def asset_url_to_local(url: str) -> Path:
    """Map a remote asset URL to a local path under assets/."""
    parsed = urllib.parse.urlparse(url)
    # strip the wp-content / other path prefix
    remote_path = parsed.path.lstrip("/")

    # Categorise
    ext = Path(remote_path).suffix.lower()
    if ext in (".css",):
        sub = "css"
    elif ext in (".js",):
        sub = "js"
    elif ext in (".woff", ".woff2", ".ttf", ".eot", ".otf"):
        sub = "fonts"
    elif ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".avif"):
        sub = "images"
    elif ext in (".pdf",):
        sub = "downloads"
    else:
        sub = "misc"

    filename = Path(remote_path).name
    # keep the wp-content subdirectory structure to avoid collisions
    wp_sub = remote_path.replace("/", "_")
    return ASSETS_DIR / sub / wp_sub


def make_relative(from_path: Path, to_path: Path) -> str:
    """Return a relative path string from one file to another."""
    try:
        return os.path.relpath(to_path, from_path.parent)
    except ValueError:
        return str(to_path)


# ─── Asset downloading ─────────────────────────────────────────────────────────

def download_asset(url: str, session: requests.Session) -> Path | None:
    """Download a single asset and return its local path, or None on failure."""
    if url in downloaded_assets:
        return Path(downloaded_assets[url])

    # Only download from the same origin (or well-known CDN fonts we want)
    parsed = urllib.parse.urlparse(url)

    # Reject URLs that look like local file paths accidentally resolved as remote
    if not parsed.scheme:
        return None
    # Reject if path has no file extension and looks like a directory
    path_part = parsed.path.rstrip("/")
    if path_part and "." not in Path(path_part).name:
        return None

    if parsed.netloc and parsed.netloc not in (
        "ai-experts.network",
        "fonts.googleapis.com",
        "fonts.gstatic.com",
    ):
        return None

    local_path = asset_url_to_local(url)
    if local_path.exists():
        downloaded_assets[url] = str(local_path)
        return local_path

    local_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = session.get(url, timeout=20, headers=HEADERS)
        r.raise_for_status()
        local_path.write_bytes(r.content)
        downloaded_assets[url] = str(local_path)
        print(f"  ✓ asset  {url}")
        return local_path
    except Exception as e:
        print(f"  ✗ asset  {url}  →  {e}")
        failed_assets.append({"url": url, "error": str(e)})
        return None


def download_css_assets(css_text: str, css_url: str, session: requests.Session) -> str:
    """Parse a CSS file, download url() references, return patched CSS."""
    css_local = asset_url_to_local(css_url)

    def replace_url(match):
        raw = match.group(1).strip("'\"")
        if raw.startswith("data:") or raw.startswith("#"):
            return match.group(0)
        abs_url = urllib.parse.urljoin(css_url, raw)
        # allow gstatic fonts from Google Fonts CSS
        parsed = urllib.parse.urlparse(abs_url)
        if parsed.netloc and parsed.netloc not in (
            "ai-experts.network", "fonts.googleapis.com", "fonts.gstatic.com"
        ):
            return match.group(0)
        local = download_asset(abs_url, session)
        if local:
            rel = make_relative(css_local, local)
            return f"url('{rel}')"
        return match.group(0)

    return re.sub(r'url\(([^)]+)\)', replace_url, css_text)


# ─── HTML rewriting ────────────────────────────────────────────────────────────

def rewrite_html(html: str, page_url: str, page_local: Path, session: requests.Session) -> str:
    """
    - Download all linked assets
    - Rewrite asset references to relative local paths
    - Rewrite internal page links to local relative paths
    - Strip WordPress admin bar / login links
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove WP admin bar
    for el in soup.select("#wpadminbar, .logged-in-only, #wp-toolbar"):
        el.decompose()

    # ── Stylesheets ──────────────────────────────────────────────────────
    for tag in soup.find_all("link", rel="stylesheet"):
        href = tag.get("href")
        if not href:
            continue
        abs_url = urllib.parse.urljoin(page_url, href)
        if "ai-experts.network" in abs_url or "fonts.googleapis.com" in abs_url or abs_url.startswith("/"):
            local = download_asset(abs_url, session)
            if local:
                # re-process CSS for nested assets, but only once per file
                if abs_url not in processed_css:
                    processed_css.add(abs_url)
                    try:
                        css_text = local.read_text(encoding="utf-8", errors="replace")
                        patched = download_css_assets(css_text, abs_url, session)
                        local.write_text(patched, encoding="utf-8")
                    except Exception:
                        pass
                rel = make_relative(page_local, local)
                tag["href"] = rel

    # ── Scripts ──────────────────────────────────────────────────────────
    for tag in soup.find_all("script", src=True):
        src = tag.get("src")
        if not src:
            continue
        abs_url = urllib.parse.urljoin(page_url, src)
        if "ai-experts.network" in abs_url:
            local = download_asset(abs_url, session)
            if local:
                rel = make_relative(page_local, local)
                tag["src"] = rel

    # ── Images ───────────────────────────────────────────────────────────
    for tag in soup.find_all(["img", "source"]):
        for attr in ("src", "srcset", "data-src", "data-srcset"):
            val = tag.get(attr)
            if not val:
                continue
            # handle srcset (comma-separated url w h pairs)
            if "," in val and attr in ("srcset", "data-srcset"):
                parts = []
                for entry in val.split(","):
                    entry = entry.strip()
                    bits = entry.split()
                    if bits:
                        abs_url = urllib.parse.urljoin(page_url, bits[0])
                        local = download_asset(abs_url, session)
                        if local:
                            rel = make_relative(page_local, local)
                            bits[0] = rel
                    parts.append(" ".join(bits))
                tag[attr] = ", ".join(parts)
            else:
                abs_url = urllib.parse.urljoin(page_url, val)
                local = download_asset(abs_url, session)
                if local:
                    rel = make_relative(page_local, local)
                    tag[attr] = rel

    # ── Background images in style attrs ─────────────────────────────────
    for tag in soup.find_all(style=True):
        style = tag["style"]
        def replace_bg(m):
            raw = m.group(1).strip("'\"")
            if raw.startswith("data:") or raw.startswith("#"):
                return m.group(0)
            abs_url = urllib.parse.urljoin(page_url, raw)
            local = download_asset(abs_url, session)
            if local:
                rel = make_relative(page_local, local)
                return f"url('{rel}')"
            return m.group(0)
        tag["style"] = re.sub(r'url\(([^)]+)\)', replace_bg, style)

    # ── Internal page links ───────────────────────────────────────────────
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        norm = normalize_url(href, page_url)
        if norm:
            target_local = url_to_local_path(norm)
            rel = make_relative(page_local, target_local)
            tag["href"] = rel
            # Queue for crawling if not yet seen
            if norm not in visited_pages and norm not in queued_pages:
                if "/de/" in norm or "/en/" in norm:
                    queued_pages.append(norm)

    return str(soup)


# ─── Playwright crawling ───────────────────────────────────────────────────────

async def fetch_page_playwright(url: str, browser) -> str | None:
    """Fetch a single page with Playwright, wait for network idle."""
    try:
        page = await browser.new_page()
        await page.set_extra_http_headers(HEADERS)
        await page.goto(url, wait_until="networkidle", timeout=TIMEOUT)
        # dismiss cookie banners
        for selector in [
            ".cmplz-accept", "#cookie-accept", ".cookie-accept-all",
            "[data-cc-action='accept-all']", ".cc-btn-accept-all"
        ]:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass
        html = await page.content()
        await page.close()
        return html
    except Exception as e:
        print(f"  ✗ playwright  {url}  →  {e}")
        return None


async def crawl():
    """Main crawl loop."""
    session = requests.Session()
    session.headers.update(HEADERS)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for sub in ("css", "js", "images", "fonts", "downloads", "misc"):
        (ASSETS_DIR / sub).mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        while queued_pages and len(visited_pages) < MAX_PAGES:
            url = queued_pages.pop(0)
            if url in visited_pages:
                continue
            visited_pages.add(url)

            print(f"\n[{len(visited_pages):03d}] Crawling: {url}")
            html = await fetch_page_playwright(url, browser)

            if not html:
                failed_pages.append({"url": url, "error": "fetch failed"})
                continue

            page_local = url_to_local_path(url)
            page_local.parent.mkdir(parents=True, exist_ok=True)

            # Rewrite HTML, download assets, queue new links
            rewritten = rewrite_html(html, url, page_local, session)
            page_local.write_text(rewritten, encoding="utf-8")
            print(f"  → saved  {page_local.relative_to(OUTPUT_DIR)}")

            crawled_pages.append({
                "url": url,
                "local": str(page_local.relative_to(OUTPUT_DIR))
            })

            time.sleep(DELAY_BETWEEN_REQUESTS)

        await browser.close()

    # ── Root redirect ─────────────────────────────────────────────────────
    root_html = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=de/index.html">
<title>AI-Experts Network</title></head>
<body><a href="de/index.html">Go to site</a></body></html>"""
    (OUTPUT_DIR / "index.html").write_text(root_html, encoding="utf-8")


# ─── Manifest & README ────────────────────────────────────────────────────────

def write_manifest():
    manifest = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": START_URL,
        "crawled_pages": crawled_pages,
        "downloaded_assets": [
            {"remote": k, "local": v} for k, v in downloaded_assets.items()
        ],
        "failed_pages": failed_pages,
        "failed_assets": failed_assets,
        "stats": {
            "pages_crawled": len(crawled_pages),
            "assets_downloaded": len(downloaded_assets),
            "pages_failed": len(failed_pages),
            "assets_failed": len(failed_assets),
        }
    }
    path = OUTPUT_DIR / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nManifest written: {path}")


def write_readme():
    content = f"""# AI-Experts Network – Local Static Clone

Cloned from: {START_URL}
Generated:   {time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}

## How to run locally

**Option A – Python built-in server (recommended):**
```bash
cd ai-experts-clone
python3 -m http.server 8080
# then open http://localhost:8080/de/
```

**Option B – Node.js:**
```bash
npx serve ai-experts-clone
```

**Option C – any static file server** pointing at the `ai-experts-clone/` folder.

## What was copied

- All pages under `/de/` and sub-paths (see `manifest.json` for full list)
- CSS, JS, images, fonts from `ai-experts.network`
- Internal links rewritten to relative local paths
- Asset references in HTML and CSS rewritten to local paths

## Known limitations / what could not be copied exactly

1. **Dynamic forms** – Contact Form 7 requires a WordPress backend.
   Forms render visually but submission will not work offline.
2. **Cookie consent** – Complianz plugin fires API calls to WordPress.
   The consent banner may appear but preferences won't persist.
3. **WordPress REST API calls** – Any AJAX-driven content (e.g. dynamic
   team filters) won't work without the backend.
4. **Google Tag Manager / Analytics** – Tracking scripts are included but
   won't fire correctly without the original domain.
5. **External fonts** – Google Fonts links are preserved as-is (remote).
   Download `assets/fonts/` manually if you need fully offline fonts.

## Re-running the crawler

```bash
cd /path/to/AI-Experts-Website
python3 crawl.py
```

The script will overwrite existing files and produce an updated `manifest.json`.

## Project structure

```
ai-experts-clone/
  index.html              ← redirect to /de/
  de/
    index.html            ← main German homepage
    unser-ansatz/
    leistungen/
    ki-workshops-kompetenzaufbau/
    ki-strategieberatung-bedarfsanalyse/
    ki-executive-coaching-change/
    ki-umsetzung-automatisierung/
    ki-keynotes/
    ki-expertinnen/
    faq/
    kontakt/
    impressum/
    datenschutz/
    ...
  assets/
    css/
    js/
    images/
    fonts/
    downloads/
  manifest.json
  README.md
```
"""
    path = OUTPUT_DIR / "README.md"
    path.write_text(content, encoding="utf-8")
    print(f"README written: {path}")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("AI-Experts Network Crawler")
    print(f"Target: {START_URL}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 60)
    asyncio.run(crawl())
    write_manifest()
    write_readme()

    print("\n" + "=" * 60)
    print("DONE")
    print(f"  Pages crawled  : {len(crawled_pages)}")
    print(f"  Assets saved   : {len(downloaded_assets)}")
    print(f"  Pages failed   : {len(failed_pages)}")
    print(f"  Assets failed  : {len(failed_assets)}")
    print(f"\nOpen: {OUTPUT_DIR / 'de' / 'index.html'}")
    print("Or run: python3 -m http.server 8080 --directory ai-experts-clone")
