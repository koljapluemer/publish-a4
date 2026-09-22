# a4

Local editor and static-site generator for HTML cards arranged on an A4 landscape page.
The editor is Vue, Vite, TypeScript, and CodeMirror; Flask provides a small filesystem API.
Generated collages are standalone HTML and do not depend on the editor.

## Initial setup

Requirements: Python 3.13, [uv](https://docs.astral.sh/uv/),
[just](https://just.systems/), and a current Node.js/npm.

```bash
cp config.example.yml config.yml
# Edit config.yml.
uv sync --project cms --dev
npm --prefix cms/frontend install
npm --prefix cms/frontend run build
```

`config.yml` accepts absolute, `~`-prefixed, or repository-relative paths:

```yaml
data_dir: ~/collages/data
site_dir: ~/collages/_site
```

## Data layout

Each subdirectory containing an `index.jsonl` file is a collage:

```text
<data_dir>/
  weekly/
    index.jsonl
    cards/
      weather.html
      notes.html
    assets/
      chart.png
```

Each placement is one JSON object per line:

```json
{"card":"weather","top":10,"left":14}
```

Each collage also has an internal timestamp line. The editor maintains these UTC timestamps
automatically; they are not shown in its interface:

```json
{"timestamps":{"createdAt":"2026-09-22T10:15:30Z","updatedAt":"2026-09-22T10:15:30Z"}}
```

Collage metadata (`displayTitle`, `publish`) is an optional `{"meta":...}` line, edited in the
sidebar below the card editor. Without it the defaults are `""` and `false`:

```json
{"meta":{"displayTitle":"Week 12","publish":true}}
```

Card files may contain arbitrary HTML and embedded `<style>` elements. From a card file,
reference collage assets as `../assets/chart.png`. Card and collage names are restricted to
letters, numbers, underscores, and hyphens.

## Run the editor

Build the frontend after frontend changes, then start the local server:

```bash
npm --prefix cms/frontend run build
uv run --project cms python -m cms.app
```

Open <http://localhost:8000>. Starting the server generates editor-mode previews. In the
editor, click a card to load its source, drag it to update its placement, and use `Ctrl+S`
or `Cmd+S` to save source changes.

The server has no authentication and is intended to remain bound to localhost.

## Frontend development

Run both development servers:

```bash
just dev
```

Open the Vite URL, normally <http://localhost:5173>. Vite proxies `/api` and `/preview` to
Flask. `Ctrl-C` stops both processes.

Checks:

```bash
uv run --project cms python -m pytest cms/tests
npm --prefix cms/frontend run typecheck
npm --prefix cms/frontend run build
```

## Generate standalone output

```bash
just generate
```

This rebuilds every collage at `<site_dir>/<collage>/index.html`. Open or serve those files
and print with margins set to "None". The page is exactly 297 × 210 mm.

Running the editor and generating standalone output intentionally use the same site directory.
Run the standalone build when the desired final state should contain no editor hooks.

## Code map

- `cms/app.py`: Flask routes and JSON translation.
- `cms/repository.py`: validated, atomic filesystem operations.
- `cms/builder.py`: standalone and editor-preview generation.
- `cms/collage.html.j2`: generated page wrapper.
- `cms/frontend/`: Vue editor.

The filesystem remains the source of truth. There is no database, asset manager, card rename,
or collage CRUD layer. See [Filesystem layout](docs/filesystem.md) for the complete on-disk
structure and read/write behaviour.
