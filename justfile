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

# Rebuild the frontend, (re)write the a4 user service and restart it.
reinstall:
    #!/usr/bin/env bash
    set -euo pipefail
    npm --prefix cms/frontend run build
    unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
    mkdir -p "$unit_dir"
    cat > "$unit_dir/a4.service" <<EOF
    [Unit]
    Description=a4 CMS

    [Service]
    WorkingDirectory={{justfile_directory()}}
    ExecStart=$(command -v uv) run --project cms flask --app 'cms.app:create_app()' run --port 8000
    Restart=on-failure

    [Install]
    WantedBy=default.target
    EOF
    systemctl --user daemon-reload
    systemctl --user enable a4.service
    systemctl --user restart a4.service
