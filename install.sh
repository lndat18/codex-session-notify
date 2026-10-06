#!/usr/bin/env bash
set -euo pipefail
plugin_source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
    echo 'Python 3.11+ is required / Cần Python 3.11 trở lên.' >&2
    exit 1
fi
exec python3 "$plugin_source_dir/bootstrap.py" --interactive
