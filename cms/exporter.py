import argparse
import json
import tempfile
from dataclasses import replace
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError

from . import render
from .builder import Builder
from .config import DEFAULT_CONFIG, Settings, load_settings
from .repository import Repository


MANIFEST = "index.json"
RENDERED_SUFFIXES = (".pdf", ".webp")


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

    def export_all(self) -> list[dict]:
        """Render every collage to PDF and WebP, write the manifest, drop stale renders."""
        export_dir = self.settings.export_dir
        export_dir.mkdir(parents=True, exist_ok=True)
        collages = self.repository.list_collages()

        # Standalone HTML goes to a scratch directory so the editor previews stay intact.
        with tempfile.TemporaryDirectory() as scratch:
            builder = Builder(replace(self.settings, site_dir=Path(scratch)), self.repository)
            try:
                with render.open_browser() as browser:
                    for collage in collages:
                        pdf, full, thumbnail = (
                            export_dir / name for name in rendered_files(collage)
                        )
                        render.render_pdf(browser, builder.build_collage(collage), pdf)
                        render.render_full(pdf, full)
                        render.render_thumbnail(pdf, thumbnail)
            except PlaywrightError as error:
                raise ExportError(f"Rendering failed: {error.message}") from error

        manifest = [
            {"name": collage, **self.repository.get_metadata(collage).as_json()}
            for collage in collages
        ]
        (export_dir / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")
        self._remove_stale(collages)
        return manifest

    def _remove_stale(self, collages: list[str]) -> None:
        current = {name for collage in collages for name in rendered_files(collage)}
        for path in self.settings.export_dir.iterdir():
            if path.is_file() and path.suffix in RENDERED_SUFFIXES and path.name not in current:
                path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render every collage to PDF and WebP.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    settings = load_settings(args.config)
    for entry in Exporter(settings).export_all():
        print(f"exported {settings.export_dir / entry['name']}.pdf")


if __name__ == "__main__":
    main()
