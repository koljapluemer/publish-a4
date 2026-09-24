# Filesystem layout

The filesystem is the application's source of truth. There is no database. Two configured
Three configured directories hold mutable state: `data_dir` contains the editable source data,
`site_dir` contains generated HTML, and `export_dir` contains rendered PDFs and images.

## Configuration

By default, the app reads `config.yml` in the repository root:

```yaml
data_dir: ~/collages/data
site_dir: ~/collages/_site
export_dir: ~/collages/export
```

All three values are required. Absolute paths are used as written, `~` is expanded, and relative
paths are resolved relative to the configuration file. A different configuration file can be
passed to the builder with `--config`; `create_app()` also accepts a configuration path.

The app reads the configuration file but does not modify it.

## Editable source data (`data_dir`)

Each direct child containing an `index.jsonl` file is treated as a collage:

```text
<data_dir>/
  <collage>/
    index.jsonl
    cards/
      <card>.html
    assets/                 # optional
      <files>
```

Collage and card names may contain only ASCII letters, numbers, underscores, and hyphens.
The collage name is its directory name. Renaming a collage moves the complete directory,
including its cards and assets.

### `index.jsonl`

`index.jsonl` contains one compact JSON object per line. The app writes records in this order:

```json
{"timestamps":{"createdAt":"2026-09-22T10:15:30Z","updatedAt":"2026-09-22T10:20:00Z"}}
{"meta":{"displayTitle":"Week 12","publish":true,"tags":["weekly"]}}
{"card":"weather","top":10,"left":14}
{"card":"notes","top":35,"left":14}
```

- `timestamps` is always written for new collages. Values are UTC RFC 3339 timestamps. Existing
  timestamp-less collages remain readable and receive both values on their next mutation.
- `meta` is omitted when `displayTitle`, `publish`, and `tags` all have their default values.
- Each `card` record identifies a card file and stores its position in millimetres.
- Placement order is preserved and determines card order in generated HTML.

Creating, editing, moving, or deleting a card, editing metadata, or renaming the collage updates
`updatedAt`. `createdAt` is preserved.

### `cards/<card>.html`

Each placement must have a corresponding HTML file. Its contents are the card source edited by
the UI and inserted into generated output. The first rendered HTML element is given the stored
position during generation; the source file itself is not changed by that transformation.

Card source may refer to a collage asset as `../assets/<file>` (the older
`./../assets/<file>` form is also accepted during generation).

Deleting a card removes its placement and HTML file. It does not remove files from `assets/`,
because an asset may be referenced by another card.

### `assets/`

The directory is created when the first image card is uploaded. Uploaded images are stored as
`<card>.png`, `.jpg`, `.gif`, or `.webp`, based on their MIME type. Other files placed in this
directory manually are also copied to generated output unchanged.

### Write behaviour

Writes to `index.jsonl`, card HTML, and uploaded image files use a temporary file in the target
directory followed by an atomic replace. Temporary names start with `.<target-name>.` and are
removed after a failed write when possible.

## Generated output (`site_dir`)

Each collage is generated into a matching directory:

```text
<site_dir>/
  <collage>/
    index.html
    normalize.css
    style.css
    assets/                 # present when the source collage has assets
      <copied files>
```

This directory is derived output, not durable source data. On every build of a collage, the app
deletes the entire existing `<site_dir>/<collage>/` directory and recreates it. Any files added
there manually are lost.

Generation reads the collage's `index.jsonl`, card HTML files, and complete `assets/` tree. It
also reads `cms/collage.html.j2`, `cms/normalize.css`, and `cms/style.css` from the application
source. Assets and stylesheets are copied; `index.html` is rendered from the template and cards.

Starting the Flask app rebuilds all collages in editor-preview mode. Mutations made through the
API rebuild the affected collage. Renaming also removes the old generated directory. Running
`python -m cms.builder` rebuilds all collages as standalone output without editor hooks.

Only known collages are rebuilt. If a source collage is removed manually, a matching stale
directory in `site_dir` is not cleaned up automatically. There is no collage-deletion endpoint.

## Exported renders (`export_dir`)

An export ("Export all" in the editor, `POST /api/export`, or `python -m cms.exporter`) covers
every collage regardless of `publish`:

```text
<export_dir>/
  index.json
  <collage>.pdf
  <collage>.webp
  <collage>-thumbnail.webp
```

Each collage is built as standalone HTML (no editor hooks) in a temporary directory, which is
deleted afterwards; `site_dir` is not touched. Chromium prints it to PDF using the page's
`@page` size; the first PDF page is rendered to a 144 DPI WebP and a 600 px wide thumbnail.
Existing files are overwritten in place.

`index.json` is written after all renders succeed. It is an array in collage-name order:

```json
[{"name": "weekly", "displayTitle": "Week 12", "publish": true, "tags": ["weekly"]}]
```

After writing the manifest, `.pdf` and `.webp` files in `export_dir` that do not belong to a
current collage (for example after a rename) are deleted. Other files are left alone.

## Frontend files

At runtime Flask reads and serves the prebuilt editor from:

```text
cms/frontend/dist/
  index.html
  favicon.ico
  assets/
```

The Flask app never writes this directory. It is produced separately by
`npm --prefix cms/frontend run build`. If `dist/index.html` is absent, the editor route returns
an error explaining that the frontend must be built; API and builder filesystem behaviour is
otherwise unchanged.

## Files not managed by the app

The app does not create logs, caches, lock files, a database, or backups. Python, uv, npm, Vite,
and Playwright may maintain their own environments and caches, but those are tooling files
and are not read as collage data.
