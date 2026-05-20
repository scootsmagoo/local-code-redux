#!/usr/bin/env bash
# Launch VSCodium from a dev build (sources in vscodium/vscode/).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VSCODE="$ROOT/vscodium/vscode"

if ! command -v fnm >/dev/null 2>&1; then
  echo "fnm is required. Install: brew install fnm" >&2
  exit 1
fi

eval "$(fnm env)"
fnm use 22.22.1

# Cursor/CI sometimes sets this; Electron must not run as plain Node.
unset ELECTRON_RUN_AS_NODE

if [[ -d /Applications/Xcode.app ]]; then
  export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
fi

cd "$VSCODE"
exec bash scripts/code.sh "$@"
