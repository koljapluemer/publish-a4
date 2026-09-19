# a4

Collages of HTML "cards" on a landscape A4 page. Managed with [uv](https://docs.astral.sh/uv/); no third-party dependencies.

## Data layout

```
data/<collage>/
  index.jsonl    one line per card: {"card": "<name>", "top": <mm>, "left": <mm>}
  cards/<name>.html
  assets/        optional; reference from cards as ../assets/<file>
```

## Commands

Build every collage to `_site/<collage>/index.html`:

```
uv run --project cms cms/demo_ssg.py
```

Edit card positions by dragging (writes back to `data/<collage>/index.jsonl`):

```
uv run --project cms cms/demo_ssg.py --serve
```

then open http://localhost:8000 and pick a collage.

Print: open `_site/<collage>/index.html` from a build without `--serve`, print with
margins "None". The page is exactly A4 landscape (297 x 210 mm).
