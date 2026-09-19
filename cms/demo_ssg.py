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

import yaml
from jinja2 import Environment, FileSystemLoader

CONFIG = Path(__file__).resolve().parent.parent / "config.yml"


def load_config() -> tuple[Path, Path]:
    """Return (data_dir, site_dir); relative paths are relative to config.yml."""
    if not CONFIG.is_file():
        sys.exit(f"missing {CONFIG}; copy config.example.yml to config.yml and edit it")
    cfg = yaml.safe_load(CONFIG.read_text())
    return tuple(
        (CONFIG.parent / Path(cfg[key]).expanduser()).resolve()
        for key in ("data_dir", "site_dir")
    )


DATA, SITE = load_config()

TEMPLATE = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parent),
    trim_blocks=True,
    lstrip_blocks=True,
).get_template("collage.html.j2")


def build(collage: Path, edit: bool = False) -> None:
    lines = (collage / "index.jsonl").read_text().splitlines()
    cards = []
    for line in filter(str.strip, lines):
        spec = json.loads(line)
        html = (collage / "cards" / f"{spec['card']}.html").read_text()
        # cards live in cards/, but are emitted into the page next to assets/
        html = html.replace("./../assets/", "assets/").replace("../assets/", "assets/")
        cards.append({"name": spec["card"], "top": spec["top"], "left": spec["left"], "html": html})

    out = SITE / collage.name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    if (collage / "assets").is_dir():
        shutil.copytree(collage / "assets", out / "assets")
    (out / "index.html").write_text(
        TEMPLATE.render(title=collage.name, cards=cards, edit=edit)
    )
    print(f"built {out / 'index.html'}")


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
