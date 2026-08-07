#!/usr/bin/env python3
"""Verify file-backed asset references in the static clone."""

from __future__ import annotations

import csv
import re
import urllib.parse
from pathlib import Path

from lxml import html


ROOT = Path(__file__).resolve().parents[1]
CLONE = ROOT / "ai-experts-clone"
OUTPUT = ROOT / "reports" / "local-asset-check.csv"
URL_PATTERN = re.compile(r"url\(\s*(['\"]?)([^)'\"\s]+)\1\s*\)", re.I)


def resolve_local(source: Path, reference: str) -> Path | None:
    reference = reference.strip()
    if not reference or reference.startswith(("data:", "#", "http://", "https://", "//")):
        return None
    clean = urllib.parse.unquote(urllib.parse.urlsplit(reference).path)
    if clean.startswith("/"):
        return (CLONE / clean.lstrip("/")).resolve()
    return (source.parent / clean).resolve()


def category(reference: str) -> str:
    suffix = Path(urllib.parse.urlsplit(reference).path).suffix.lower()
    if suffix in {".woff", ".woff2", ".ttf", ".otf", ".eot"}:
        return "font"
    if suffix == ".css":
        return "css"
    if suffix == ".js":
        return "js"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif", ".ico"}:
        return "image"
    return "other"


def add_row(rows: list[dict], source: Path, reference: str, context: str) -> None:
    target = resolve_local(source, reference)
    parsed = urllib.parse.urlsplit(reference)
    is_remote = parsed.scheme in ("http", "https") or reference.startswith("//")
    original_domain = "ai-experts.network" in reference
    if target is not None:
        exists = target.is_file()
        resolved = str(target)
        assessment = "OK" if exists else "Fehlt lokal"
    elif original_domain:
        exists = ""
        resolved = reference
        assessment = "Verweist auf Original-Domain"
    elif is_remote:
        exists = ""
        resolved = reference
        assessment = "Extern"
    else:
        exists = ""
        resolved = reference
        assessment = "Ignoriert (data/fragment)"
    rows.append(
        {
            "source_file": str(source.relative_to(ROOT)),
            "context": context,
            "category": category(reference),
            "reference": reference,
            "resolved": resolved,
            "exists": exists,
            "assessment": assessment,
        }
    )


def main() -> None:
    rows: list[dict] = []
    for source in CLONE.rglob("*.html"):
        try:
            doc = html.fromstring(source.read_bytes())
        except Exception:
            continue
        for node in doc.xpath("//*[@src]"):
            add_row(rows, source, node.get("src"), f"{node.tag}[src]")
        for node in doc.xpath("//link[@href]"):
            add_row(rows, source, node.get("href"), f"link[{node.get('rel', '')}]")
        for node in doc.xpath("//*[@srcset]"):
            for item in node.get("srcset").split(","):
                reference = item.strip().split()[0] if item.strip() else ""
                if reference:
                    add_row(rows, source, reference, f"{node.tag}[srcset]")
        for node in doc.xpath("//*[@data-src]"):
            add_row(rows, source, node.get("data-src"), f"{node.tag}[data-src]")
    for source in CLONE.rglob("*.css"):
        text = source.read_text(encoding="utf-8", errors="replace")
        for match in URL_PATTERN.finditer(text):
            add_row(rows, source, match.group(2), "css url()")

    fields = [
        "source_file", "context", "category", "reference", "resolved", "exists",
        "assessment",
    ]
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"references={len(rows)}")


if __name__ == "__main__":
    main()
