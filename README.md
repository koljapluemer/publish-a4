# a4

Collages of HTML "cards" on a landscape A4 page. Managed with [uv](https://docs.astral.sh/uv/); dependencies are PyYAML and Jinja2.

## Config

Copy `config.example.yml` to `config.yml` (untracked) and set `data_dir` and `site_dir`.
Paths can be absolute, `~`-prefixed, or relative to `config.yml`.

## Data layout

Inside `data_dir`:

```
<collage>/
  index.jsonl    one line per card: {"card": "<name>", "top": <mm>, "left": <mm>}
  cards/<name>.html
  assets/        optional; reference from cards as ../assets/<file>
```

## Template

`cms/collage.html.j2` is the page wrapper (CSS, card markup, drag script for `--serve`).
Variables: `title`, `edit`, `cards` (each with `name`, `top`, `left`, `html`).

## Commands

Build every collage to `<site_dir>/<collage>/index.html`:

```
uv run --project cms cms/demo_ssg.py
```

Edit card positions by dragging (writes back to `<data_dir>/<collage>/index.jsonl`):

```
uv run --project cms cms/demo_ssg.py --serve
```

then open http://localhost:8000 and pick a collage.

Print: open `<site_dir>/<collage>/index.html` from a build without `--serve`, print with
margins "None". The page is exactly A4 landscape (297 x 210 mm).
