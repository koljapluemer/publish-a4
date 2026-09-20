import argparse
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import DEFAULT_CONFIG, Settings, load_settings
from .repository import Repository


CMS_DIR = Path(__file__).resolve().parent
TEMPLATE = Environment(
    loader=FileSystemLoader(CMS_DIR),
    autoescape=select_autoescape(("html", "xml")),
    trim_blocks=True,
    lstrip_blocks=True,
).get_template("collage.html.j2")


class Builder:
    def __init__(self, settings: Settings, repository: Repository | None = None):
        self.settings = settings
        self.repository = repository or Repository(settings)

    def build_collage(self, collage: str, edit: bool = False) -> Path:
        source_dir = self.settings.data_dir / collage
        cards = []
        for placement in self.repository.list_cards(collage):
            card = self.repository.get_card(collage, placement.name)
            html = card.source.replace("./../assets/", "assets/").replace(
                "../assets/", "assets/"
            )
            cards.append({**placement.as_json(), "html": html})

        output_dir = self.settings.site_dir / collage
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)
        assets = source_dir / "assets"
        if assets.is_dir():
            shutil.copytree(assets, output_dir / "assets")
        for stylesheet in ("normalize.css", "style.css"):
            shutil.copy2(CMS_DIR / stylesheet, output_dir / stylesheet)
        output = output_dir / "index.html"
        output.write_text(TEMPLATE.render(title=collage, cards=cards, edit=edit))
        return output

    def build_all(self, edit: bool = False) -> list[Path]:
        return [
            self.build_collage(collage, edit=edit)
            for collage in self.repository.list_collages()
        ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build standalone A4 collages.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    builder = Builder(load_settings(args.config))
    for output in builder.build_all():
        print(f"built {output}")


if __name__ == "__main__":
    main()
