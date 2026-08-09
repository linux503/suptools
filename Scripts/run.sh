#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
USER_SITE="$(python3 -c 'import site; print(site.getusersitepackages())' 2>/dev/null || true)"
export PYTHONPATH="$ROOT${USER_SITE:+:$USER_SITE}${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$ROOT/main.py"
