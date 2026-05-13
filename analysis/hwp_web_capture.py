# Copyright (c) 2024 S. Leclerc (sle118@hotmail.com)
#
# This file is part of the Pool Heater Controller component project.
#
# @project Pool Heater Controller Component
# @developer S. Leclerc (sle118@hotmail.com)
# @license MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import argparse
import struct
import sys
import time
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SIZES = "phone=390x844,tablet=768x1024,desktop=1280x800"
DEFAULT_README_SIZE = "tablet"


@dataclass(frozen=True)
class ViewportSize:
    name: str
    width: int
    height: int

    @property
    def filename(self) -> str:
        return f"hwp-web-{self.name}.png"


def parse_size_spec(spec: str) -> tuple[ViewportSize, ...]:
    sizes: list[ViewportSize] = []
    for raw_part in spec.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "=" not in part or "x" not in part:
            raise ValueError(f"Bad size {part!r}; use name=WIDTHxHEIGHT")
        name, dims = part.split("=", 1)
        width_text, height_text = dims.lower().split("x", 1)
        name = name.strip()
        if not name:
            raise ValueError("Viewport size name cannot be empty")
        width = int(width_text)
        height = int(height_text)
        if width < 120 or height < 120:
            raise ValueError(f"Viewport {name!r} is too small")
        sizes.append(ViewportSize(name=name, width=width, height=height))
    if not sizes:
        raise ValueError("At least one viewport size is required")
    names = [size.name for size in sizes]
    if len(set(names)) != len(names):
        raise ValueError("Viewport size names must be unique")
    return tuple(sizes)


def screenshot_path(out_dir: Path, size: ViewportSize) -> Path:
    return out_dir / size.filename


def selected_readme_path(out_dir: Path, sizes: tuple[ViewportSize, ...], readme_size: str) -> Path:
    for size in sizes:
        if size.name == readme_size:
            return screenshot_path(out_dir, size)
    raise ValueError(f"readme size {readme_size!r} is not in --sizes")


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as png_file:
        header = png_file.read(24)
    if len(header) < 24 or not header.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"{path} is not a PNG file")
    return struct.unpack(">II", header[16:24])


def validate_png(path: Path, expected_width: int, expected_height: int) -> None:
    if path.stat().st_size < 1024:
        raise ValueError(f"{path} is unexpectedly small")
    width, height = png_dimensions(path)
    if width != expected_width or height != expected_height:
        raise ValueError(
            f"{path} is {width}x{height}, expected {expected_width}x{expected_height}"
        )


def capture_screenshots(
    *,
    base_url: str,
    out_dir: Path,
    sizes: tuple[ViewportSize, ...],
    wait_ms: int,
    dry_run: bool = False,
) -> tuple[Path, ...]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = tuple(screenshot_path(out_dir, size) for size in sizes)
    if dry_run:
        return outputs

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required for capture. Install with "
            "`python -m pip install playwright` and ensure a Chromium browser is available."
        ) from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=_chromium_path(),
            headless=True,
        )
        try:
            for size, output in zip(sizes, outputs):
                page = browser.new_page(viewport={"width": size.width, "height": size.height})
                page.goto(base_url, wait_until="networkidle")
                if wait_ms > 0:
                    page.wait_for_timeout(wait_ms)
                page.screenshot(path=str(output), full_page=False)
                page.close()
                validate_png(output, size.width, size.height)
        finally:
            browser.close()
    return outputs


def _chromium_path() -> str | None:
    for candidate in (
        Path("/usr/bin/chromium"),
        Path("/usr/bin/chromium-browser"),
        Path("/usr/bin/google-chrome"),
    ):
        if candidate.exists():
            return str(candidate)
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture firmware-served HWP web dashboard screenshots."
    )
    parser.add_argument("--base-url", required=True, help="HWP dashboard URL, for example http://pool.local/hwp")
    parser.add_argument("--out-dir", default="analysis/screenshots", help="Directory for regenerated screenshots")
    parser.add_argument("--sizes", default=DEFAULT_SIZES, help="Comma-separated name=WIDTHxHEIGHT viewports")
    parser.add_argument("--wait-ms", type=int, default=1500, help="Delay after page load before capture")
    parser.add_argument("--readme-size", default=DEFAULT_README_SIZE, help="Viewport name used by analysis/README.md")
    parser.add_argument("--dry-run", action="store_true", help="Print target paths without launching a browser")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        sizes = parse_size_spec(args.sizes)
        out_dir = Path(args.out_dir)
        outputs = capture_screenshots(
            base_url=args.base_url,
            out_dir=out_dir,
            sizes=sizes,
            wait_ms=max(0, args.wait_ms),
            dry_run=args.dry_run,
        )
        readme_capture = selected_readme_path(out_dir, sizes, args.readme_size)
    except (OSError, RuntimeError, ValueError) as exc:
        parser.error(str(exc))
        return 2

    for output in outputs:
        print(output)
    print(f"README capture: {readme_capture}")
    print(f"Captured at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
