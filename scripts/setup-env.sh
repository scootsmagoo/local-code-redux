#!/usr/bin/env bash
# Local Code dev environment: Node 22.22.1 (fnm) + pnpm via corepack.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v fnm >/dev/null 2>&1; then
  echo "fnm is required. Install with: brew install fnm"
  echo "Then add to ~/.zshrc:"
  echo '  eval "$(fnm env)"'
  exit 1
fi

eval "$(fnm env)"
fnm install 22.22.1
fnm use 22.22.1

corepack enable
corepack prepare pnpm@10.12.1 --activate

echo "Node:  $(node --version)"
echo "pnpm:  $(pnpm --version)"

if [[ -d /Applications/Xcode.app/Contents/Developer ]]; then
  export DEVELOPER_DIR="/Applications/Xcode.app/Contents/Developer"
  echo "DEVELOPER_DIR=$DEVELOPER_DIR"
fi

echo ""
echo "Next: cd vscodium && export OS_NAME=osx VSCODE_QUALITY=stable && bash prepare_vscode.sh"
echo "Or compile: cd vscodium/vscode && pnpm run compile"
