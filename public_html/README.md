# AI-Experts Network – Local Static Clone

Cloned from: https://ai-experts.network/de/
Generated:   2026-04-18 21:39 UTC

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
