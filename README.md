# Local Code

Local-LLM-first IDE based on VSCodium. See **[PROJECT.md](PROJECT.md)** for goals and roadmap; **[implementation-notes.md](implementation-notes.md)** for build status and decisions.

## Prerequisites

- **fnm** (Node version manager) — `brew install fnm`
- **pnpm** — activated via corepack (see setup script)
- **macOS:** Xcode or current Command Line Tools with a working C++ SDK (see implementation notes if native builds fail)

`nvm` is not required; this repo uses **fnm** and **`.node-version`** (22.22.1).

## Setup

```bash
# One-time: add fnm to your shell (~/.zshrc)
eval "$(fnm env)"

# From repo root
./scripts/setup-env.sh
```

## Build VS Code tree

```bash
eval "$(fnm env)" && fnm use 22.22.1

cd vscodium
export VSCODE_QUALITY=stable OS_NAME=osx
bash get_repo.sh          # if vscode/ missing
bash prepare_vscode.sh    # patches + pnpm install
```

Installs inside `vscodium/vscode/` use **pnpm**, not npm (`prepare_vscode.sh`).

## Package manager policy

| Area | Manager |
|------|---------|
| Local Code repo root | **pnpm** (`package.json` → `packageManager`) |
| `vscodium/vscode/` (upstream) | **pnpm** (lockfile from `pnpm import` of `package-lock.json`) |

We do not use `npm ci` / `npm install` for dependency installs in this project.
