#!/usr/bin/env python3
"""Update critical clone page content from the archived original HTML."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

from lxml import html


ROOT = Path(__file__).resolve().parents[1]
CLONE = ROOT / "ai-experts-clone"
ARCHIVE = ROOT / "reports" / "original-archive" / "html"
REPORTS = ROOT / "reports"

CRITICAL_PATHS = [
    "de/faq",
    "de/team/andreas-rodenbeck",
    "de/team/kristin-goas-oses",
    "de/team/mario-levenhagen",
    "de/team/meike-quentin",
    "de/team/rene-goebels",
    "de/team/stephan-grandy",
    "en/faq",
    "en/leistungen",
    "en/team/kristin-goas-oses",
    "en/team/mario-levenhagen",
    "en/team/meike-quentin",
    "en/team/rene-goebels",
    "en/team/stephan-grandy",
]

ASSET_SUBDIRS = {
    ".css": "css",
    ".js": "js",
    ".woff": "fonts",
    ".woff2": "fonts",
    ".ttf": "fonts",
    ".eot": "fonts",
    ".otf": "fonts",
    ".png": "images",
    ".jpg": "images",
    ".jpeg": "images",
    ".gif": "images",
    ".svg": "images",
    ".webp": "images",
    ".ico": "images",
    ".avif": "images",
    ".pdf": "downloads",
}


def local_page_for_path(path: str) -> Path:
    clean = urllib.parse.unquote(path).lstrip("/")
    if not clean:
        return CLONE / "index.html"
    candidate = Path(clean)
    if candidate.suffix:
        return CLONE / candidate
    return CLONE / candidate / "index.html"


def local_asset_for_url(url: str) -> Path | None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.netloc and parsed.netloc != "ai-experts.network":
        return None
    remote_path = parsed.path.lstrip("/")
    if not remote_path:
        return None
    suffix = Path(remote_path).suffix.lower()
    subdir = ASSET_SUBDIRS.get(suffix, "misc")
    candidate = CLONE / "assets" / subdir / remote_path.replace("/", "_")
    if candidate.is_file():
        return candidate
    basename = Path(remote_path).name
    matches = list((CLONE / "assets" / subdir).glob(f"*{basename}"))
    if len(matches) == 1:
        return matches[0]
    return None


def relative_url(target: Path, page_file: Path, query: str = "", fragment: str = "") -> str:
    value = os.path.relpath(target, page_file.parent).replace(os.sep, "/")
    if query:
        value += "?" + query
    if fragment:
        value += "#" + fragment
    return value


def rewrite_reference(value: str, page_file: Path, *, page_link: bool) -> tuple[str, str | None]:
    if not value or value.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return value, None
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme in ("http", "https") and parsed.netloc not in ("", "ai-experts.network"):
        return value, None

    absolute = urllib.parse.urljoin("https://ai-experts.network/", value)
    absolute_parsed = urllib.parse.urlsplit(absolute)
    asset = local_asset_for_url(absolute)
    if asset is not None:
        return relative_url(asset, page_file, absolute_parsed.query, absolute_parsed.fragment), None

    if page_link:
        page_target = local_page_for_path(absolute_parsed.path)
        if page_target.is_file():
            return relative_url(
                page_target,
                page_file,
                absolute_parsed.query,
                absolute_parsed.fragment,
            ), None
        return value, f"missing internal page: {absolute_parsed.path}"

    if absolute_parsed.netloc == "ai-experts.network":
        return value, f"missing local asset: {absolute}"
    return value, None


def rewrite_srcset(value: str, page_file: Path) -> tuple[str, list[str]]:
    rewritten: list[str] = []
    issues: list[str] = []
    for entry in value.split(","):
        parts = entry.strip().split()
        if not parts:
            continue
        parts[0], issue = rewrite_reference(parts[0], page_file, page_link=False)
        if issue:
            issues.append(issue)
        rewritten.append(" ".join(parts))
    return ", ".join(rewritten), issues


def rewrite_main(main, page_file: Path) -> list[str]:
    issues: list[str] = []
    for element in main.iter():
        if element.get("href"):
            rewritten, issue = rewrite_reference(
                element.get("href"), page_file, page_link=True
            )
            element.set("href", rewritten)
            if issue:
                issues.append(issue)
        for attribute in ("src", "data-src", "data-lazy-src"):
            if element.get(attribute):
                rewritten, issue = rewrite_reference(
                    element.get(attribute), page_file, page_link=False
                )
                element.set(attribute, rewritten)
                if issue:
                    issues.append(issue)
        for attribute in ("srcset", "data-srcset"):
            if element.get(attribute):
                rewritten, found_issues = rewrite_srcset(element.get(attribute), page_file)
                element.set(attribute, rewritten)
                issues.extend(found_issues)
        if element.get("style") and "url(" in element.get("style"):
            def replace_style(match: re.Match[str]) -> str:
                quote = match.group(1) or "'"
                rewritten, issue = rewrite_reference(
                    match.group(2), page_file, page_link=False
                )
                if issue:
                    issues.append(issue)
                return f"url({quote}{rewritten}{quote})"

            element.set(
                "style",
                re.sub(
                    r"url\(\s*(['\"]?)([^)'\"\s]+)\1\s*\)",
                    replace_style,
                    element.get("style"),
                ),
            )
    return sorted(set(issues))


def replace_main(target_html: str, serialized_main: str) -> str:
    pattern = re.compile(r"<main\b.*?</main>", re.DOTALL | re.IGNORECASE)
    updated, count = pattern.subn(lambda _match: serialized_main, target_html, count=1)
    if count != 1:
        raise RuntimeError(f"Expected one <main>, replaced {count}")
    return updated


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    apply_changes = "--apply" in sys.argv
    records = []
    all_issues: list[str] = []
    for relative in CRITICAL_PATHS:
        source_file = ARCHIVE / relative / "index.html"
        target_file = CLONE / relative / "index.html"
        if not source_file.is_file() or not target_file.is_file():
            raise FileNotFoundError(f"Missing source or target for {relative}")

        source_doc = html.fromstring(source_file.read_bytes())
        mains = source_doc.xpath("//main")
        if len(mains) != 1:
            raise RuntimeError(f"Expected one source <main> for {relative}")
        source_main = copy.deepcopy(mains[0])
        issues = rewrite_main(source_main, target_file)
        all_issues.extend(f"{relative}: {issue}" for issue in issues)
        serialized_main = html.tostring(
            source_main, encoding="unicode", method="html", with_tail=False
        )
        target_html = target_file.read_text(encoding="utf-8")
        updated_html = replace_main(target_html, serialized_main)
        before_hash = sha256(target_file)
        after_hash = hashlib.sha256(updated_html.encode("utf-8")).hexdigest()
        records.append(
            {
                "path": "/" + relative + "/",
                "source": str(source_file.relative_to(ROOT)),
                "target": str(target_file.relative_to(ROOT)),
                "before_sha256": before_hash,
                "after_sha256": after_hash,
                "changed": before_hash != after_hash,
                "issues": issues,
            }
        )
        if apply_changes:
            target_file.write_text(updated_html, encoding="utf-8")

    payload = {
        "mode": "apply" if apply_changes else "dry-run",
        "updated_pages": len(records),
        "issues": sorted(set(all_issues)),
        "pages": records,
    }
    output = REPORTS / "critical-content-update.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if all_issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
