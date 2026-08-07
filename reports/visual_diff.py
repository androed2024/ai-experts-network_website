#!/usr/bin/env python3
"""Create pixel-diff images and a machine-readable visual summary."""

from __future__ import annotations

import csv
import json
import re
import urllib.parse
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance


REPORTS = Path(__file__).resolve().parent
SCREENSHOTS = REPORTS / "screenshots"
VIEWS = ("desktop", "tablet", "mobile")


def screenshot_name(url: str) -> str:
    path = urllib.parse.urlsplit(url).path
    value = re.sub(r"[^a-zA-Z0-9._-]+", "__", path.strip("/"))
    return (value or "root") + ".png"


def compare_pair(original_path: Path, clone_path: Path, diff_path: Path) -> dict:
    with Image.open(original_path).convert("RGB") as original:
        with Image.open(clone_path).convert("RGB") as clone:
            width = max(original.width, clone.width)
            height = max(original.height, clone.height)
            original_canvas = Image.new("RGB", (width, height), "white")
            clone_canvas = Image.new("RGB", (width, height), "white")
            original_canvas.paste(original, (0, 0))
            clone_canvas.paste(clone, (0, 0))
            raw_diff = ImageChops.difference(original_canvas, clone_canvas)
            grayscale = raw_diff.convert("L")
            histogram = grayscale.histogram()
            total_pixels = width * height
            changed_pixels = sum(histogram[12:])
            changed_ratio = changed_pixels / total_pixels if total_pixels else 0
            mean_abs_difference = (
                sum(value * count for value, count in enumerate(histogram))
                / total_pixels
                / 255
                if total_pixels
                else 0
            )

            highlighted = Image.new("RGB", (width, height), (255, 255, 255))
            red = Image.new("RGB", (width, height), (220, 30, 45))
            mask = ImageEnhance.Contrast(grayscale).enhance(2.5)
            highlighted.paste(red, mask=mask)
            context = Image.blend(original_canvas, clone_canvas, 0.5)
            output = Image.blend(context, highlighted, 0.55)
            diff_path.parent.mkdir(parents=True, exist_ok=True)
            output.save(diff_path, optimize=True)

    if changed_ratio >= 0.35 or mean_abs_difference >= 0.20:
        severity = "kritisch"
    elif changed_ratio >= 0.12 or mean_abs_difference >= 0.07:
        severity = "mittel"
    elif changed_ratio >= 0.01 or mean_abs_difference >= 0.01:
        severity = "niedrig"
    else:
        severity = "identisch/vernachlässigbar"
    return {
        "width": width,
        "height": height,
        "changed_pixels": changed_pixels,
        "changed_ratio": changed_ratio,
        "mean_abs_difference": mean_abs_difference,
        "severity": severity,
    }


def main() -> None:
    rows: list[dict] = []
    payload = json.loads((REPORTS / "original-pages.json").read_text(encoding="utf-8"))
    expected_files = {screenshot_name(page["requested_url"]) for page in payload["pages"]}
    for view in VIEWS:
        original_dir = SCREENSHOTS / "original" / view
        clone_dir = SCREENSHOTS / "clone" / view
        diff_dir = SCREENSHOTS / "diff" / view
        original_files = {path.name: path for path in original_dir.glob("*.png")}
        clone_files = {path.name: path for path in clone_dir.glob("*.png")}
        for filename in sorted(expected_files | set(original_files) | set(clone_files)):
            original_path = original_files.get(filename)
            clone_path = clone_files.get(filename)
            base = {
                "viewport": view,
                "page_key": filename.removesuffix(".png"),
                "original_screenshot": str(original_path.relative_to(REPORTS))
                if original_path
                else "",
                "clone_screenshot": str(clone_path.relative_to(REPORTS))
                if clone_path
                else "",
                "diff_screenshot": "",
                "width": "",
                "height": "",
                "changed_pixels": "",
                "changed_ratio": "",
                "mean_abs_difference": "",
                "severity": "",
            }
            if not original_path or not clone_path:
                base["severity"] = "nicht auswertbar: Screenshot fehlt"
                rows.append(base)
                continue
            diff_path = diff_dir / filename
            metrics = compare_pair(original_path, clone_path, diff_path)
            base.update(metrics)
            base["changed_ratio"] = f"{metrics['changed_ratio']:.6f}"
            base["mean_abs_difference"] = f"{metrics['mean_abs_difference']:.6f}"
            base["diff_screenshot"] = str(diff_path.relative_to(REPORTS))
            rows.append(base)

    fieldnames = [
        "viewport", "page_key", "original_screenshot", "clone_screenshot",
        "diff_screenshot", "width", "height", "changed_pixels", "changed_ratio",
        "mean_abs_difference", "severity",
    ]
    with (REPORTS / "visual-comparison.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"visual rows={len(rows)} diffs={sum(bool(r['diff_screenshot']) for r in rows)}")


if __name__ == "__main__":
    main()
