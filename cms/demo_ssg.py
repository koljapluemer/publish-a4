"""Generate one A4 collage HTML per subdir of data/ into _site/."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "_site"

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  @page {{ size: A4; margin: 0; }}
  * {{ box-sizing: border-box; print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
  html, body {{ margin: 0; background: #000; }}
  body {{ padding: 10mm 0; }}
  .page {{
    position: relative;
    height: 210mm;
    width: 297mm;
    margin: 0 auto;
    background: #fff;
    overflow: hidden;
  }}
  .card {{
    position: absolute;
    background: #fff;
    box-shadow: 1mm 1mm 3mm rgba(0, 0, 0, .25);
  }}
  .card img {{ display: block; max-width: 100%; }}
  @media print {{
    html, body {{ height: 210mm; width: 297mm; background: #fff; }}
    body {{ padding: 0; }}
    .page {{ margin: 0; break-after: avoid; }}
  }}
</style>
</head>
<body>
<div class="page">
{cards}
</div>
</body>
</html>
"""


def build(collage: Path) -> None:
    lines = (collage / "index.jsonl").read_text().splitlines()
    cards = []
    for line in filter(str.strip, lines):
        spec = json.loads(line)
        html = (collage / "cards" / f"{spec['card']}.html").read_text()
        # cards live in cards/, but are emitted into the page next to assets/
        html = html.replace("./../assets/", "assets/").replace("../assets/", "assets/")
        cards.append(
            f'<div class="card" style="top: {spec["top"]}mm; left: {spec["left"]}mm;">\n{html}\n</div>'
        )

    out = SITE / collage.name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    if (collage / "assets").is_dir():
        shutil.copytree(collage / "assets", out / "assets")
    (out / "index.html").write_text(
        TEMPLATE.format(title=collage.name, cards="\n".join(cards))
    )
    print(f"built {out.relative_to(ROOT)}/index.html")


def main() -> None:
    for collage in sorted(DATA.iterdir()):
        if (collage / "index.jsonl").is_file():
            build(collage)


if __name__ == "__main__":
    main()
