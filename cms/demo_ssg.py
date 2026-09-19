"""Generate one A4 (landscape) collage HTML per subdir of data/ into _site/.

Run with --serve to also serve _site/ and drag cards around; positions are
written back to data/<collage>/index.jsonl.
"""

import json
import shutil
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
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
  @page {{ size: A4 landscape; margin: 0; }}
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
{edit_script}
</body>
</html>
"""

# Injected in --serve mode only. Drag a card; on drop, POST its new position in mm.
EDIT_SCRIPT = """<style>
  .card {{ cursor: move; user-select: none; touch-action: none; }}
  .card img {{ -webkit-user-drag: none; pointer-events: none; }}
</style>
<script>
const page = document.querySelector('.page');
document.querySelectorAll('.card').forEach(card => {{
  card.addEventListener('pointerdown', e => {{
    e.preventDefault();
    card.setPointerCapture(e.pointerId);
    card.style.zIndex = 1000;
    const pxPerMm = page.getBoundingClientRect().width / 297;
    const x0 = e.clientX, y0 = e.clientY;
    const left0 = parseFloat(card.style.left), top0 = parseFloat(card.style.top);
    const move = e => {{
      card.style.left = Math.round(left0 + (e.clientX - x0) / pxPerMm) + 'mm';
      card.style.top = Math.round(top0 + (e.clientY - y0) / pxPerMm) + 'mm';
    }};
    const up = () => {{
      card.removeEventListener('pointermove', move);
      card.removeEventListener('pointerup', up);
      card.style.zIndex = '';
      fetch('/save/{name}', {{
        method: 'POST',
        body: JSON.stringify({{card: card.dataset.card, top: parseInt(card.style.top), left: parseInt(card.style.left)}}),
      }});
    }};
    card.addEventListener('pointermove', move);
    card.addEventListener('pointerup', up);
  }});
}});
</script>"""


def build(collage: Path, edit: bool = False) -> None:
    lines = (collage / "index.jsonl").read_text().splitlines()
    cards = []
    for line in filter(str.strip, lines):
        spec = json.loads(line)
        html = (collage / "cards" / f"{spec['card']}.html").read_text()
        # cards live in cards/, but are emitted into the page next to assets/
        html = html.replace("./../assets/", "assets/").replace("../assets/", "assets/")
        cards.append(
            f'<div class="card" data-card="{spec["card"]}" style="top: {spec["top"]}mm; left: {spec["left"]}mm;">\n{html}\n</div>'
        )

    out = SITE / collage.name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    if (collage / "assets").is_dir():
        shutil.copytree(collage / "assets", out / "assets")
    (out / "index.html").write_text(
        TEMPLATE.format(
            title=collage.name,
            cards="\n".join(cards),
            edit_script=EDIT_SCRIPT.format(name=collage.name) if edit else "",
        )
    )
    print(f"built {out.relative_to(ROOT)}/index.html")


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        name = self.path.removeprefix("/save/")
        path = DATA / name / "index.jsonl"
        if "/" in name or not path.is_file():
            return self.send_error(404)
        move = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        specs = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
        for spec in specs:
            if spec["card"] == move["card"]:
                spec["top"], spec["left"] = move["top"], move["left"]
        path.write_text("\n".join(json.dumps(s) for s in specs) + "\n")
        build(path.parent, edit=True)
        self.send_response(204)
        self.end_headers()


def main() -> None:
    serve = "--serve" in sys.argv
    for collage in sorted(DATA.iterdir()):
        if (collage / "index.jsonl").is_file():
            build(collage, edit=serve)
    if serve:
        print("serving on http://localhost:8000")
        HTTPServer(("", 8000), partial(Handler, directory=SITE)).serve_forever()


if __name__ == "__main__":
    main()
