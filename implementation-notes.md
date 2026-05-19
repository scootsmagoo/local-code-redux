# Implementation notes (Local Code)

Running log of decisions, tradeoffs, and changes not spelled out in [`PROJECT.md`](PROJECT.md). Newest entries at the **top**.

---

## 2026-05-19 — Xcode fix: pnpm install succeeded

### Resolution

- **Xcode** at `/Applications/Xcode.app` fixes C++ headers when `DEVELOPER_DIR` points there.
- `xcode-select` still defaults to CLT (`/Library/Developer/CommandLineTools`); **`sudo xcode-select -s /Applications/Xcode.app/Contents/Developer`** recommended so builds work without extra env vars.
- `pnpm install --frozen-lockfile` completed in ~43s with `DEVELOPER_DIR` set.
- Added `strict-dep-builds=false` to `vscodium/npmrc` for pnpm 10 native script approval.
- `prepare_vscode.sh` now exports `DEVELOPER_DIR` on macOS when Xcode.app exists.

### Follow-ups

- [ ] User: run `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` (optional but cleaner)
- [ ] `pnpm approve-builds` / `strict-dep-builds` — may need full rebuild of natives if runtime fails; `node-pty` uses prebuilds; `sqlite3` built manually once
- [ ] Next step: `cd vscodium/vscode && pnpm run compile` (or `./dev/build.sh` in vscodium)

---

## 2026-05-19 — Node/fnm, pnpm, install attempt

### Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Node version manager | **fnm** (not nvm) | `nvm` not installed on machine; `brew install fnm` succeeded |
| Node version | **22.22.1** via fnm | Matches `vscodium/.nvmrc`; required for `build/npm/*.ts` native execution |
| Package manager | **pnpm** only for installs | User request; `prepare_vscode.sh` uses `pnpm install --frozen-lockfile` |
| Lockfile | `pnpm import` → `vscode/pnpm-lock.yaml` | Generated from upstream `package-lock.json` when missing |
| macOS native builds | `CXX=clang++` for all osx installs | VSCodium only used this for CI; enabled for dev too |

### What ran successfully

- `brew install fnm`
- `fnm install 22.22.1` / `fnm use 22.22.1`
- `corepack prepare pnpm@10.12.1 --activate`
- `node build/npm/preinstall.ts` (Node 22.22.1)
- `pnpm import` in `vscodium/vscode/`

### Blocker: macOS C++ toolchain (not pnpm)

`pnpm install --frozen-lockfile` and `npm ci` both fail on native modules:

1. **`unordered_set` file not found** — even `clang++ -isysroot $(xcrun --show-sdk-path)` cannot compile `<unordered_set>` with current CLT SDK.
2. **node-gyp `CLTVersion()`** — `AttributeError` parsing CLT version on **Darwin 25.4.0**.

This points to **Command Line Tools / Xcode mismatch** on this macOS build (likely needs full **Xcode.app** from App Store, or updated CLT: `sudo xcode-select --install` / `xcode-select -s /Applications/Xcode.app/Contents/Developer`).

### Files added/changed

- `package.json`, `.node-version`, `.npmrc`, `README.md`, `scripts/setup-env.sh`
- `vscodium/prepare_vscode.sh` — pnpm + `pnpm import` + osx `CXX=clang++`
- `vscodium/vscode/pnpm-lock.yaml` — generated (large; consider gitignore vs commit — **TBD**)

### User shell setup

Add to `~/.zshrc`:

```bash
eval "$(fnm env)"
```

Then: `cd local-code && ./scripts/setup-env.sh`

---

## 2026-05-19 — Phase 0 progress (build)

### Status

| Step | Status |
|------|--------|
| `get_repo.sh` (VS Code 1.116.0 @ `560a9dba`) | Done |
| VSCodium patches + `90-local-code-enable-ai-default.patch` | Done |
| `npm ci` / compile | **Blocked** — see below |

### Blocker: Node version

`prepare_vscode.sh` failed at `node build/npm/preinstall.ts` with:

`ERR_UNKNOWN_FILE_EXTENSION` for `.ts`

- System Node: **v22.17.0**
- Required per `vscodium/.nvmrc`: **22.22.1**

**Action:** `nvm install 22.22.1 && nvm use 22.22.1`, then re-run `prepare_vscode.sh` from `vscodium/` (or `./dev/build.sh`).

### Verified patch outcome

In prepared `vscode/`, `chat.disableAIFeatures` now defaults to **`false`** and description no longer mentions Copilot:

```
description: ... "Disable and hide built-in AI features, including chat and inline suggestions."
default: false,
```

### Patch fix

First version of `90-local-code-enable-ai-default.patch` had a malformed hunk (`corrupt patch at line 14`). Replaced with a 4-line hunk against post–`00-copilot` state (`default: true` → `false`).

---

## 2026-05-19 — Project bootstrap

### Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Product name | **Local Code** | User choice; `applicationName` TBD (`localcode` vs `local-code`) |
| Base distribution | VSCodium build scripts @ VS Code **1.116.0** | Full chat/LM stack in core; Copilot already stripped |
| “Native” provider | Workbench contrib `localLLM` via patches | User rejected marketplace-extension-first; aligns with `ILanguageModelsService` |
| v1 backend | **Ollama** | Simple HTTP/SSE; LM Studio later via OpenAI-compatible URL |
| Context model | **Explicit default**; implicit later opt-in | Cursor-style implicit context is harness work, not free in OSS chat |
| Docs location | Repo root `PROJECT.md` + this file | `vscodium/` stays upstream-aligned; product spec is Local Code–owned |
| Spike path | May use echo provider in core before Ollama | De-risks patch/regression workflow before HTTP client work |

### Tradeoffs

- **Core patches vs bundled extension:** Core patches are harder to rebase but match “native” requirement; bundled `extensions/local-llm` was rejected as the long-term shape (acceptable only for a short spike).
- **Fork VSCodium scripts vs fork microsoft/vscode:** We patch through VSCodium’s `patches/` flow so we keep Open VSX, telemetry stripping, and Copilot removal; product branding changes go in `prepare_vscode.sh` + `patches/user/`.
- **Implicit context deferred:** Faster MVP; avoids shipping a bad auto-index that sends whole repos to the model.

### Not in spec / open questions

- [ ] Final `applicationName`, `dataFolderName`, bundle IDs (avoid collision with VSCodium if both installed)
- [ ] `defaultChatAgent` participant ID and manifest shape (needs vscode tree after clone)
- [ ] Whether to keep Open VSX as default gallery or curate a “local-first” extension set
- [ ] Icon/branding assets (reuse VSCodium overlays until custom assets exist)

### Changes made

- Added [`PROJECT.md`](PROJECT.md) (spec + roadmap)
- Added this file
- Added `vscodium/patches/user/90-local-code-enable-ai-default.patch` — sets `chat.disableAIFeatures` default back to `false` for Local Code (overrides VSCodium’s `true` default from `00-copilot-fix-action-condition.patch`)

### Next actions

1. Run `get_repo.sh` → populate `vscodium/vscode/`
2. Run `prepare_vscode.sh` with user patches applied
3. Dev compile + launch; verify Chat visible
4. Begin `90-local-code` branding patch + `contrib/localLLM` spike

---
