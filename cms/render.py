from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pymupdf
from PIL import Image
from playwright.sync_api import Browser, sync_playwright


THUMBNAIL_WIDTH_PX = 600
FULL_SIZE_SCALE = 2  # 144 DPI


@contextmanager
def open_browser() -> Iterator[Browser]:
    """One headless Chromium shared by all PDF renders (install: `playwright install chromium`)."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            yield browser
        finally:
            browser.close()


def render_pdf(browser: Browser, html_path: Path, pdf_path: Path) -> None:
    """Print the page to PDF using its own `@page` size (A4 landscape).

    Loaded from disk, so relative assets resolve next to the HTML file.
    """
    page = browser.new_page()
    try:
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        page.pdf(path=str(pdf_path), prefer_css_page_size=True, print_background=True)
    finally:
        page.close()


def render_full(pdf_path: Path, webp_path: Path) -> None:
    """Save the first PDF page as a full-size webp."""
    _render_webp(pdf_path, webp_path, pymupdf.Matrix(FULL_SIZE_SCALE, FULL_SIZE_SCALE))


def render_thumbnail(pdf_path: Path, webp_path: Path) -> None:
    """Save the first PDF page as a downscaled webp."""
    with pymupdf.open(pdf_path) as document:
        scale = THUMBNAIL_WIDTH_PX / document[0].rect.width
    _render_webp(pdf_path, webp_path, pymupdf.Matrix(scale, scale))


def _render_webp(pdf_path: Path, webp_path: Path, matrix: pymupdf.Matrix) -> None:
    with pymupdf.open(pdf_path) as document:
        pixmap = document[0].get_pixmap(matrix=matrix)
        image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    image.save(webp_path, "WEBP", quality=80)
