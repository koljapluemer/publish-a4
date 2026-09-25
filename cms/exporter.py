import argparse
import json
import os
import tempfile
import threading
from dataclasses import replace
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError

from . import render
from .builder import CMS_DIR, Builder
from .config import DEFAULT_CONFIG, Settings, load_settings
from .repository import Repository


MANIFEST = "index.json"
RENDERED_SUFFIXES = (".pdf", ".webp")
# Application files that affect every render.
SHARED_SOURCES = tuple(CMS_DIR / name for name in ("collage.html.j2", "normalize.css", "style.css"))


def rendered_files(collage: str) -> tuple[str, str, str]:
    """PDF, full-size WebP and thumbnail WebP file names."""
    return f"{collage}.pdf", f"{collage}.webp", f"{collage}-thumbnail.webp"


class ExportError(Exception):
    code = "export_failed"
    status = 500


class Exporter:
    def __init__(self, settings: Settings, repository: Repository | None = None):
        self.settings = settings
        self.repository = repository or Repository(settings)
        self._lock = threading.Lock()

    def export_all(self, force: bool = False) -> tuple[list[dict], list[str]]:
        """Render outdated collages to PDF and WebP, write the manifest, drop stale renders.

        Returns the manifest and the names of the collages that were rendered.
        """
        with self._lock:
            return self._export_all(force)

    def _export_all(self, force: bool) -> tuple[list[dict], list[str]]:
        export_dir = self.settings.export_dir
        export_dir.mkdir(parents=True, exist_ok=True)
        collages = self.repository.list_collages()
        outdated = {
            collage: self._source_mtime(collage)
            for collage in collages
            if force or self._is_outdated(collage)
        }

        if outdated:
            # Standalone HTML goes to a scratch directory so the editor previews stay intact.
            with tempfile.TemporaryDirectory() as scratch:
                builder = Builder(replace(self.settings, site_dir=Path(scratch)), self.repository)
                try:
                    with render.open_browser() as browser:
                        for collage, source_mtime in outdated.items():
                            paths = [export_dir / name for name in rendered_files(collage)]
                            pdf, full, thumbnail = paths
                            render.render_pdf(browser, builder.build_collage(collage), pdf)
                            render.render_full(pdf, full)
                            render.render_thumbnail(pdf, thumbnail)
                            # Stamp renders with the source time read before building, so edits
                            # made during the render still count as newer next time.
                            for path in paths:
                                os.utime(path, ns=(source_mtime, source_mtime))
                except PlaywrightError as error:
                    raise ExportError(f"Rendering failed: {error.message}") from error

        manifest = [
            {"name": collage, **self.repository.get_metadata(collage).as_json()}
            for collage in collages
        ]
        (export_dir / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")
        self._remove_stale(collages)
        return manifest, list(outdated)

    def _source_mtime(self, collage: str) -> int:
        """Newest modification time (ns) of the collage's files and the shared templates."""
        collage_dir = self.settings.data_dir / collage
        paths = [collage_dir, *collage_dir.rglob("*"), *SHARED_SOURCES]
        return max(path.stat().st_mtime_ns for path in paths)

    def _is_outdated(self, collage: str) -> bool:
        paths = [self.settings.export_dir / name for name in rendered_files(collage)]
        if not all(path.is_file() for path in paths):
            return True
        rendered = min(path.stat().st_mtime_ns for path in paths)
        return self._source_mtime(collage) > rendered

    def _remove_stale(self, collages: list[str]) -> None:
        current = {name for collage in collages for name in rendered_files(collage)}
        for path in self.settings.export_dir.iterdir():
            if path.is_file() and path.suffix in RENDERED_SUFFIXES and path.name not in current:
                path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render outdated collages to PDF and WebP.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--force", action="store_true", help="re-render every collage")
    args = parser.parse_args()
    settings = load_settings(args.config)
    manifest, rendered = Exporter(settings).export_all(force=args.force)
    for collage in rendered:
        print(f"exported {settings.export_dir / collage}.pdf")
    print(f"{len(rendered)} of {len(manifest)} collages rendered")


if __name__ == "__main__":
    main()
