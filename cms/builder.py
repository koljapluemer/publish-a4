import argparse
import html
import re
import shutil
from html.parser import HTMLParser
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


NON_RENDERED_ELEMENTS = {"base", "link", "meta", "script", "style", "title"}


class _CardRootParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.root: tuple[int, int] | None = None
        self.start_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.root is None and tag not in NON_RENDERED_ELEMENTS:
            line, column = self.getpos()
            self.root = (line, column)
            self.start_tag = self.get_starttag_text()

    handle_startendtag = handle_starttag


def place_card(source: str, name: str, top: float, left: float) -> str:
    parser = _CardRootParser()
    parser.feed(source)
    if parser.root is None:
        raise ValueError(f"Card '{name}' must contain an HTML element.")

    line, column = parser.root
    start = sum(len(value) for value in source.splitlines(keepends=True)[: line - 1]) + column
    if parser.start_tag is None:
        raise ValueError(f"Card '{name}' has an invalid root element.")

    start_tag = parser.start_tag
    placement = f"top: {top}mm; left: {left}mm;"
    style_pattern = re.compile(r"(\sstyle\s*=\s*)(['\"])(.*?)\2", re.DOTALL | re.IGNORECASE)
    if style_pattern.search(start_tag):
        start_tag = style_pattern.sub(
            lambda match: f"{match.group(1)}{match.group(2)}{placement} {match.group(3)}{match.group(2)}",
            start_tag,
            count=1,
        )
        attributes = f' data-card="{html.escape(name, quote=True)}"'
    else:
        attributes = (
            f' data-card="{html.escape(name, quote=True)}"'
            f' style="{placement}"'
        )
    insertion = start_tag.rfind("/>")
    if insertion == -1:
        insertion = start_tag.rfind(">")
    placed_tag = start_tag[:insertion] + attributes + start_tag[insertion:]
    return source[:start] + placed_tag + source[start + len(parser.start_tag) :]


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
            cards.append(place_card(html, placement.name, placement.top, placement.left))

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
