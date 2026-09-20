set dotenv-load := false

# Run Flask and Vite development servers; Ctrl-C stops both.
dev:
    #!/usr/bin/env bash
    set -euo pipefail

    uv run --project cms flask --app 'cms.app:create_app()' run --debug --port 8000 &
    backend_pid=$!
    npm --prefix cms/frontend run dev &
    frontend_pid=$!

    cleanup() {
        kill "$backend_pid" "$frontend_pid" 2>/dev/null || true
        wait "$backend_pid" "$frontend_pid" 2>/dev/null || true
    }
    trap cleanup EXIT INT TERM
    wait -n "$backend_pid" "$frontend_pid"

# Generate standalone collages in site_dir.
generate:
    uv run --project cms python -m cms.builder
