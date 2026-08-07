#!/usr/bin/env python3
"""Read-only comparison crawler for ai-experts.network and its static clone."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher, unified_diff
from pathlib import Path
from typing import Any

from lxml import etree, html
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
ARCHIVE = REPORTS / "original-archive"
ORIGINAL_HOST = "ai-experts.network"
CLONE_HOST = "ai-experts.11mind.com"
ORIGINAL_BASE = f"https://{ORIGINAL_HOST}"
CLONE_BASE = f"https://{CLONE_HOST}"
START_PATHS = ["/de/", "/en/", "/kontakt/"]
MAX_PAGES = 200
TIMEOUT = 25
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
    "AI-Experts-Clone-Audit/1.0"
)
ASSET_EXTENSIONS = {
    ".avif", ".css", ".eot", ".gif", ".ico", ".jpeg", ".jpg", ".js", ".json",
    ".map", ".mp4", ".otf", ".pdf", ".png", ".svg", ".ttf", ".webm", ".webp",
    ".woff", ".woff2", ".xml", ".zip",
}
TRACKING_TEXT_PATTERNS = (
    "cookie", "cookies", "datenschutz-einstellungen", "privacy settings",
    "consent", "marketing", "funktional", "functional", "statistiken",
    "statistics",
)


class RecordingRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self) -> None:
        self.chain: list[dict[str, Any]] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.chain.append({"status": code, "from": req.full_url, "to": newurl})
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@dataclass
class FetchResult:
    requested_url: str
    final_url: str
    status: int
    headers: dict[str, str]
    body: bytes
    redirects: list[dict[str, Any]]
    error: str = ""


def fetch(url: str, method: str = "GET") -> FetchResult:
    redirect_handler = RecordingRedirectHandler()
    opener = urllib.request.build_opener(redirect_handler)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        method=method,
    )
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            body = b"" if method == "HEAD" else response.read()
            return FetchResult(
                requested_url=url,
                final_url=response.geturl(),
                status=response.status,
                headers={k.lower(): v for k, v in response.headers.items()},
                body=body,
                redirects=redirect_handler.chain,
            )
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return FetchResult(
            requested_url=url,
            final_url=exc.geturl(),
            status=exc.code,
            headers={k.lower(): v for k, v in exc.headers.items()},
            body=body,
            redirects=redirect_handler.chain,
            error=str(exc),
        )
    except Exception as exc:
        return FetchResult(
            requested_url=url,
            final_url=url,
            status=0,
            headers={},
            body=b"",
            redirects=redirect_handler.chain,
            error=f"{type(exc).__name__}: {exc}",
        )


def canonicalize_url(url: str, base: str | None = None) -> str:
    resolved = urllib.parse.urljoin(base or "", url)
    parsed = urllib.parse.urlsplit(resolved)
    scheme = parsed.scheme.lower()
    host = parsed.netloc.lower()
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if not Path(path).suffix and not path.endswith("/"):
        path += "/"
    query = parsed.query
    return urllib.parse.urlunsplit((scheme, host, path, query, ""))


def normalize_internal_page_url(raw: str, base: str, host: str) -> str | None:
    if not raw:
        return None
    raw = raw.strip()
    if raw.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    absolute = canonicalize_url(raw, base)
    parsed = urllib.parse.urlsplit(absolute)
    if parsed.scheme not in ("http", "https") or parsed.netloc.lower() != host:
        return None
    if Path(parsed.path).suffix.lower() in ASSET_EXTENSIONS:
        return None
    if parsed.query and any(
        key in urllib.parse.parse_qs(parsed.query)
        for key in ("s", "replytocom", "preview", "rest_route")
    ):
        return None
    return absolute


def clean_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("\u00ad", "").replace("\u200b", "").replace("\ufeff", "")
    return re.sub(r"\s+", " ", value).strip()


def selector_texts(doc, xpath: str) -> list[str]:
    result = []
    for element in doc.xpath(xpath):
        text = clean_text(" ".join(element.itertext()))
        if text:
            result.append(text)
    return result


def visible_text_blocks(doc) -> list[str]:
    for bad in doc.xpath("//script|//style|//noscript|//template|//svg|//canvas"):
        parent = bad.getparent()
        if parent is not None:
            parent.remove(bad)
    for bad in doc.xpath(
        "//*[@hidden or @aria-hidden='true' or "
        "contains(translate(@style,' ',''),'display:none') or "
        "contains(translate(@style,' ',''),'visibility:hidden')]"
    ):
        parent = bad.getparent()
        if parent is not None:
            parent.remove(bad)
    blocks: list[str] = []
    block_tags = "p|h1|h2|h3|h4|h5|h6|li|blockquote|figcaption|label|button|address|td|th"
    for element in doc.xpath(f"//*[self::{block_tags.replace('|', ' or self::')}]"):
        text = clean_text(" ".join(element.itertext()))
        if len(text) < 2:
            continue
        lower = text.lower()
        if any(pattern in lower for pattern in TRACKING_TEXT_PATTERNS) and len(text) < 180:
            continue
        if not blocks or blocks[-1] != text:
            blocks.append(text)
    return blocks


def attr_urls(doc, xpath: str, attr: str, base_url: str) -> list[str]:
    values: list[str] = []
    for node in doc.xpath(xpath):
        raw = node.get(attr)
        if raw:
            values.append(urllib.parse.urljoin(base_url, raw.strip()))
    return values


def image_dimensions(body: bytes, content_type: str) -> tuple[int | None, int | None]:
    if "svg" in content_type:
        try:
            root = etree.fromstring(body)
            width = re.sub(r"[^0-9.]", "", root.get("width") or "")
            height = re.sub(r"[^0-9.]", "", root.get("height") or "")
            if width and height:
                return int(float(width)), int(float(height))
            view_box = root.get("viewBox")
            if view_box:
                parts = [float(part) for part in view_box.replace(",", " ").split()]
                if len(parts) == 4:
                    return int(parts[2]), int(parts[3])
        except Exception:
            return None, None
        return None, None
    try:
        with Image.open(io.BytesIO(body)) as image:
            return image.size
    except Exception:
        return None, None


def fetch_asset(url: str, cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if url in cache:
        return cache[url]
    result = fetch(url)
    content_type = result.headers.get("content-type", "").split(";")[0]
    width, height = image_dimensions(result.body, content_type)
    record = {
        "url": url,
        "final_url": result.final_url,
        "status": result.status,
        "redirects": result.redirects,
        "content_type": content_type,
        "bytes": len(result.body),
        "sha256": hashlib.sha256(result.body).hexdigest() if result.body else "",
        "width": width,
        "height": height,
        "error": result.error,
    }
    cache[url] = record
    time.sleep(0.03)
    return record


def parse_srcset(value: str, base_url: str) -> list[str]:
    urls = []
    for part in value.split(","):
        candidate = part.strip().split()[0] if part.strip() else ""
        if candidate:
            urls.append(urllib.parse.urljoin(base_url, candidate))
    return urls


def extract_page(result: FetchResult, host: str, asset_cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    content_type = result.headers.get("content-type", "")
    page: dict[str, Any] = {
        "requested_url": result.requested_url,
        "url": result.final_url,
        "status": result.status,
        "redirects": result.redirects,
        "content_type": content_type,
        "error": result.error,
        "title": "",
        "meta_description": "",
        "h1": [],
        "h2": [],
        "canonical": "",
        "language_links": [],
        "navigation_links": [],
        "footer_links": [],
        "internal_links": [],
        "external_links": [],
        "forms": [],
        "images": [],
        "assets": [],
        "text_blocks": [],
        "normalized_text": "",
    }
    if result.status == 0 or "html" not in content_type.lower() or not result.body:
        return page
    try:
        doc = html.fromstring(result.body, base_url=result.final_url)
    except Exception as exc:
        page["error"] = f"HTML parse error: {exc}"
        return page

    titles = selector_texts(doc, "//title")
    page["title"] = titles[0] if titles else ""
    descriptions = doc.xpath(
        "//meta[translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='description']/@content"
    )
    page["meta_description"] = clean_text(descriptions[0]) if descriptions else ""
    page["h1"] = selector_texts(doc, "//h1")
    page["h2"] = selector_texts(doc, "//h2")
    canonicals = doc.xpath(
        "//link[contains(concat(' ',normalize-space(@rel),' '),' canonical ')]/@href"
    )
    page["canonical"] = (
        urllib.parse.urljoin(result.final_url, canonicals[0]) if canonicals else ""
    )
    for node in doc.xpath("//link[@hreflang and @href]"):
        page["language_links"].append(
            {
                "hreflang": node.get("hreflang"),
                "url": urllib.parse.urljoin(result.final_url, node.get("href")),
            }
        )

    links = []
    for node in doc.xpath("//a[@href]"):
        href = node.get("href", "").strip()
        absolute = urllib.parse.urljoin(result.final_url, href)
        text = clean_text(" ".join(node.itertext()))
        parsed = urllib.parse.urlsplit(absolute)
        link = {
            "href": href,
            "url": absolute,
            "text": text,
            "target": node.get("target", ""),
            "rel": node.get("rel", ""),
        }
        links.append(link)
        in_nav = bool(node.xpath("ancestor::nav|ancestor::*[contains(@class,'menu')]"))
        in_footer = bool(node.xpath("ancestor::footer|ancestor::*[contains(@class,'footer')]"))
        if in_nav:
            page["navigation_links"].append(link)
        if in_footer:
            page["footer_links"].append(link)
        if parsed.scheme in ("http", "https") and parsed.netloc.lower() == host:
            page["internal_links"].append(link)
        elif parsed.scheme in ("http", "https"):
            page["external_links"].append(link)

    for form in doc.xpath("//form"):
        fields = []
        for field in form.xpath(".//input|.//textarea|.//select|.//button"):
            fields.append(
                {
                    "tag": field.tag,
                    "type": field.get("type", ""),
                    "name": field.get("name", ""),
                    "required": field.get("required") is not None
                    or field.get("aria-required") == "true",
                    "label": field.get("aria-label", "")
                    or field.get("placeholder", "")
                    or field.get("value", ""),
                }
            )
        page["forms"].append(
            {
                "action": urllib.parse.urljoin(result.final_url, form.get("action", "")),
                "method": (form.get("method") or "get").upper(),
                "id": form.get("id", ""),
                "class": form.get("class", ""),
                "fields": fields,
            }
        )

    image_urls: set[str] = set()
    for node in doc.xpath("//img"):
        candidates = []
        for attr in ("src", "data-src", "data-lazy-src"):
            if node.get(attr):
                candidates.append(urllib.parse.urljoin(result.final_url, node.get(attr)))
        for attr in ("srcset", "data-srcset"):
            if node.get(attr):
                candidates.extend(parse_srcset(node.get(attr), result.final_url))
        if not candidates:
            continue
        primary = candidates[0]
        asset = fetch_asset(primary, asset_cache)
        image_urls.update(candidates)
        page["images"].append(
            {
                **asset,
                "src": node.get("src", ""),
                "alt": node.get("alt", ""),
                "filename": Path(urllib.parse.urlsplit(primary).path).name,
                "declared_width": node.get("width"),
                "declared_height": node.get("height"),
                "candidates": candidates,
            }
        )

    assets: set[tuple[str, str]] = set()
    for node in doc.xpath("//link[@href]"):
        rel = " ".join(node.get("rel", "").split()).lower()
        href = urllib.parse.urljoin(result.final_url, node.get("href"))
        if any(token in rel for token in ("stylesheet", "icon", "preload")):
            assets.add((href, rel or "link"))
    for node in doc.xpath("//script[@src]"):
        assets.add((urllib.parse.urljoin(result.final_url, node.get("src")), "script"))
    for url in image_urls:
        assets.add((url, "image"))
    for asset_url, kind in sorted(assets):
        page["assets"].append({"kind": kind, **fetch_asset(asset_url, asset_cache)})

    page["text_blocks"] = visible_text_blocks(doc)
    page["normalized_text"] = "\n".join(page["text_blocks"])
    page["all_links"] = links
    return page


def archive_original_html(result: FetchResult) -> None:
    if result.status == 0 or not result.body:
        return
    parsed = urllib.parse.urlsplit(result.final_url)
    path = parsed.path.strip("/")
    if not path or parsed.path.endswith("/"):
        target = ARCHIVE / "html" / path / "index.html"
    else:
        target = ARCHIVE / "html" / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(result.body)


def crawl_site(base: str, host: str, archive: bool = False) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    queue = deque(canonicalize_url(path, base) for path in START_PATHS)
    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    asset_cache: dict[str, dict[str, Any]] = {}
    while queue and len(visited) < MAX_PAGES:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        print(f"[{host}] {len(visited):03d} {url}", flush=True)
        result = fetch(url)
        if archive:
            archive_original_html(result)
        page = extract_page(result, host, asset_cache)
        pages.append(page)
        for link in page.get("internal_links", []):
            normalized = normalize_internal_page_url(link["url"], page["url"], host)
            if normalized and normalized not in visited and normalized not in queue:
                queue.append(normalized)
        time.sleep(0.08)
    return pages, asset_cache


def path_key(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    elif path == "/index.html":
        path = "/"
    if not Path(path).suffix and not path.endswith("/"):
        path += "/"
    return path


def page_map(pages: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for page in pages:
        mapped[path_key(page["requested_url"])] = page
    for page in pages:
        mapped.setdefault(path_key(page["url"]), page)
    return mapped


def block_diff(original: list[str], clone: list[str]) -> dict[str, list[str]]:
    original_set = set(original)
    clone_set = set(clone)
    return {
        "missing": [block for block in original if block not in clone_set],
        "additional": [block for block in clone if block not in original_set],
    }


def severity_for(original: dict[str, Any], clone: dict[str, Any] | None, ratio: float) -> str:
    if clone is None or clone.get("status") != 200:
        return "kritisch"
    if original.get("status") != 200:
        return "mittel"
    if ratio < 0.65:
        return "kritisch"
    if ratio < 0.97:
        return "mittel"
    if ratio < 0.999:
        return "niedrig"
    return "identisch"


def csv_write(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def compare_assets(
    original_pages: list[dict[str, Any]], clone_pages: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    clone_by_hash: dict[str, list[dict[str, Any]]] = {}
    clone_by_name: dict[str, list[dict[str, Any]]] = {}
    for page in clone_pages:
        for asset in page.get("assets", []):
            if asset.get("sha256"):
                clone_by_hash.setdefault(asset["sha256"], []).append(asset)
            name = Path(urllib.parse.urlsplit(asset["url"]).path).name.lower()
            clone_by_name.setdefault(name, []).append(asset)
    rows = []
    seen = set()
    for page in original_pages:
        for asset in page.get("assets", []):
            key = (page["requested_url"], asset["url"], asset["kind"])
            if key in seen:
                continue
            seen.add(key)
            matches = clone_by_hash.get(asset.get("sha256", ""), [])
            match_type = "sha256" if matches else ""
            if not matches:
                name = Path(urllib.parse.urlsplit(asset["url"]).path).name.lower()
                matches = clone_by_name.get(name, [])
                match_type = "filename" if matches else ""
            if not matches:
                name = Path(urllib.parse.urlsplit(asset["url"]).path).name.lower()
                suffix_matches = []
                for clone_name, candidates in clone_by_name.items():
                    if clone_name.endswith(name):
                        suffix_matches.extend(candidates)
                matches = suffix_matches
                match_type = "flattened-path suffix" if matches else ""
            clone_asset = matches[0] if matches else {}
            if asset["status"] != 200:
                rating = "Original-Asset nicht ladbar"
            elif not clone_asset:
                rating = "Fehlt im Klon"
            elif clone_asset.get("status") != 200:
                rating = "Klon-Asset nicht ladbar"
            elif match_type == "sha256":
                rating = "Identisch"
            elif (
                asset["kind"] == "image"
                and clone_asset.get("bytes") == asset.get("bytes")
                and clone_asset.get("width") == asset.get("width")
                and clone_asset.get("height") == asset.get("height")
            ):
                rating = "Äquivalentes lokales Bild (Maße/Dateigröße gleich)"
            else:
                rating = "Dateiname/Pfad äquivalent, Inhalt abweichend"
            rows.append(
                {
                    "page": page["requested_url"],
                    "kind": asset["kind"],
                    "original_url": asset["url"],
                    "original_status": asset["status"],
                    "original_bytes": asset["bytes"],
                    "original_sha256": asset["sha256"],
                    "clone_url": clone_asset.get("url", ""),
                    "clone_status": clone_asset.get("status", ""),
                    "clone_bytes": clone_asset.get("bytes", ""),
                    "clone_sha256": clone_asset.get("sha256", ""),
                    "match_type": match_type,
                    "rating": rating,
                }
            )
    return rows


def build_link_rows(clone_pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    checked: dict[str, FetchResult] = {}
    for page in clone_pages:
        for link in page.get("all_links", []):
            absolute = link["url"]
            parsed = urllib.parse.urlsplit(absolute)
            if parsed.scheme not in ("http", "https"):
                continue
            is_clone_internal = parsed.netloc.lower() == CLONE_HOST
            points_to_original = parsed.netloc.lower() == ORIGINAL_HOST
            if is_clone_internal:
                target = canonicalize_url(absolute)
                if target not in checked:
                    checked[target] = fetch(target, method="GET")
                result = checked[target]
                status = result.status
                final_url = result.final_url
            else:
                status = ""
                final_url = ""
            if points_to_original:
                rating = "kritisch: interner Link zeigt auf Original-Domain"
            elif is_clone_internal and (not isinstance(status, int) or status >= 400 or status == 0):
                rating = "kritisch: kaputter interner Link"
            elif is_clone_internal:
                rating = "OK"
            else:
                rating = "extern (nicht für Inhaltsgleichheit gewertet)"
            rows.append(
                {
                    "source_url": page["requested_url"],
                    "link_text": link["text"],
                    "href": link["href"],
                    "resolved_url": absolute,
                    "type": (
                        "original-domain"
                        if points_to_original
                        else "internal"
                        if is_clone_internal
                        else "external"
                    ),
                    "status": status,
                    "final_url": final_url,
                    "rating": rating,
                }
            )
    return rows


def write_text_diff_report(comparisons: list[dict[str, Any]]) -> None:
    lines = [
        "# Text-Diff-Zusammenfassung",
        "",
        "Normalisierung: Unicode NFKC, Whitespace-Kollaps, Entfernung unsichtbarer "
        "Zeichen sowie kurzer Cookie-/Tracking-Texte.",
        "",
    ]
    for item in comparisons:
        if item["severity"] == "identisch":
            continue
        lines.extend(
            [
                f"## {item['path']} — {item['severity']}",
                "",
                f"- Ähnlichkeit: {item['ratio']:.2%}",
                f"- Fehlende Textblöcke: {len(item['missing_blocks'])}",
                f"- Zusätzliche Textblöcke: {len(item['additional_blocks'])}",
                "",
            ]
        )
        if item["missing_blocks"]:
            lines.append("### Im Klon fehlend")
            lines.append("")
            for block in item["missing_blocks"][:30]:
                lines.append(f"- {block}")
            lines.append("")
        if item["additional_blocks"]:
            lines.append("### Im Klon zusätzlich/abweichend")
            lines.append("")
            for block in item["additional_blocks"][:30]:
                lines.append(f"- {block}")
            lines.append("")
    (REPORTS / "text-diff-summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).isoformat()

    reuse = "--reuse" in sys.argv
    if reuse:
        original_payload = json.loads(
            (REPORTS / "original-pages.json").read_text(encoding="utf-8")
        )
        clone_payload = json.loads(
            (REPORTS / "clone-pages.json").read_text(encoding="utf-8")
        )
        original_pages = original_payload["pages"]
        clone_pages = clone_payload["pages"]
        original_assets = original_payload["asset_index"]
        clone_assets = clone_payload["asset_index"]
    else:
        original_pages, original_assets = crawl_site(
            ORIGINAL_BASE, ORIGINAL_HOST, archive=True
        )
        clone_pages, clone_assets = crawl_site(CLONE_BASE, CLONE_HOST)

    if not reuse:
        original_payload = {
            "generated": generated,
            "base_url": ORIGINAL_BASE,
            "start_urls": [urllib.parse.urljoin(ORIGINAL_BASE, p) for p in START_PATHS],
            "pages": original_pages,
            "asset_index": original_assets,
        }
        clone_payload = {
            "generated": generated,
            "base_url": CLONE_BASE,
            "start_urls": [urllib.parse.urljoin(CLONE_BASE, p) for p in START_PATHS],
            "pages": clone_pages,
            "asset_index": clone_assets,
        }
        (REPORTS / "original-pages.json").write_text(
            json.dumps(original_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (REPORTS / "clone-pages.json").write_text(
            json.dumps(clone_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    original_by_path = page_map(original_pages)
    clone_by_path = page_map(clone_pages)
    all_paths = sorted(set(original_by_path) | set(clone_by_path))
    url_rows = []
    text_comparisons = []
    for path in all_paths:
        original = original_by_path.get(path)
        clone = clone_by_path.get(path)
        if original and clone:
            ratio = SequenceMatcher(
                None, original["normalized_text"], clone["normalized_text"]
            ).ratio()
            diffs = block_diff(original["text_blocks"], clone["text_blocks"])
            severity = severity_for(original, clone, ratio)
        elif original:
            ratio = 0.0
            diffs = {"missing": original["text_blocks"], "additional": []}
            severity = "kritisch"
        else:
            ratio = 0.0
            diffs = {"missing": [], "additional": clone["text_blocks"] if clone else []}
            severity = "mittel"
        assessment = {
            "identisch": "OK",
            "niedrig": "Niedrige Abweichung",
            "mittel": "Mittlere Abweichung",
            "kritisch": "Kritische Abweichung",
        }[severity]
        url_rows.append(
            {
                "Original-URL": original["requested_url"] if original else "",
                "Clone-URL": clone["requested_url"] if clone else "",
                "Status Original": original["status"] if original else "",
                "Status Clone": clone["status"] if clone else "",
                "Bewertung": assessment,
                "Textähnlichkeit": f"{ratio:.4f}",
            }
        )
        if original:
            text_comparisons.append(
                {
                    "path": path,
                    "original_url": original["requested_url"],
                    "clone_url": clone["requested_url"] if clone else "",
                    "ratio": ratio,
                    "severity": severity,
                    "missing_blocks": diffs["missing"],
                    "additional_blocks": diffs["additional"],
                }
            )

    csv_write(
        REPORTS / "url-comparison.csv",
        url_rows,
        [
            "Original-URL", "Clone-URL", "Status Original", "Status Clone",
            "Bewertung", "Textähnlichkeit",
        ],
    )
    write_text_diff_report(text_comparisons)

    prior_audit = {}
    if reuse and (REPORTS / "audit-data.json").exists():
        prior_audit = json.loads(
            (REPORTS / "audit-data.json").read_text(encoding="utf-8")
        )
    refresh_assets = "--refresh-assets" in sys.argv
    asset_rows = (
        prior_audit.get("asset_rows")
        if prior_audit.get("asset_rows") and not refresh_assets
        else compare_assets(original_pages, clone_pages)
    )
    csv_write(
        REPORTS / "assets-comparison.csv",
        asset_rows,
        [
            "page", "kind", "original_url", "original_status", "original_bytes",
            "original_sha256", "clone_url", "clone_status", "clone_bytes",
            "clone_sha256", "match_type", "rating",
        ],
    )
    link_rows = (
        prior_audit.get("link_rows")
        if prior_audit.get("link_rows")
        else build_link_rows(clone_pages)
    )
    csv_write(
        REPORTS / "link-check.csv",
        link_rows,
        [
            "source_url", "link_text", "href", "resolved_url", "type", "status",
            "final_url", "rating",
        ],
    )
    (REPORTS / "audit-data.json").write_text(
        json.dumps(
            {
                "generated": generated,
                "text_comparisons": text_comparisons,
                "url_rows": url_rows,
                "asset_rows": asset_rows,
                "link_rows": link_rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (ARCHIVE / "README.md").write_text(
        "# Original-Archiv\n\n"
        f"Automatisch am {generated} erstellt. Enthält die beim Audit abgerufenen "
        "HTML-Dokumente in der Original-Pfadstruktur. Vollständige Metadaten, Links, "
        "Texte und Asset-Hashes stehen in `../original-pages.json`.\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "original_pages": len(original_pages),
                "clone_pages": len(clone_pages),
                "original_assets": len(original_assets),
                "clone_assets": len(clone_assets),
                "url_rows": len(url_rows),
                "text_comparisons": len(text_comparisons),
                "asset_rows": len(asset_rows),
                "link_rows": len(link_rows),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
