# Implementation notes (Local Code)

Running log of decisions, tradeoffs, and changes not spelled out in [`PROJECT.md`](PROJECT.md). Newest entries at the **top**.

---

## 2026-05-20 — Phase 2: Ollama language model provider

### Shipped in repo

| Item | Location |
|------|----------|
| Ollama client | `vscodium/vscode/src/vs/workbench/contrib/localLLM/browser/ollamaClient.ts` — `/api/tags`, streaming `/api/chat` (NDJSON) |
| LM provider | `ollamaLanguageModelProvider.ts` — `ILanguageModelChatProvider`, vendor `ollama`, identifiers `ollama/<model>` |
| Workbench registration | `localLLM.contribution.ts` + import from `chat/electron-browser/chat.contribution.ts` |
| Patch | [`vscodium/patches/user/92-local-code-phase2-ollama.patch`](vscodium/patches/user/92-local-code-phase2-ollama.patch) |
| Extra settings | `localCode.ollama.requestTimeoutMs`, `localCode.ollama.maxOutputTokens` |

### Verify locally

1. Start Ollama (`ollama serve`) and pull at least one model.
2. `pnpm run compile` in `vscodium/vscode`, then `./scripts/run-dev.sh`.
3. Open Chat → model picker → **Local (Ollama)** group; send a prompt.

### Phase 2 limits (by design)

- Text-only messages (no images/tools yet).
- Desktop Electron only (contribution loaded from `electron-browser/chat.contribution.ts`).
### Connect to Ollama (dev tree only, patch pending)

In `vscodium/vscode/` (not yet a separate patch): `ollamaConnect.ts`, `localCode.connectOllama` command, startup probe, chat link runs local `/api/tags` instead of GitHub. Re-apply from dev tree after clean `prepare_vscode.sh` until patch `94` lands.

### Fix: “Failed to sign in to Ollama” (2026-05-20)

Chat setup was still running the Copilot **sign-in** path because `defaultChatAgent.provider.default` is named “Ollama”. Local Code has no `chatExtensionId` and no auth.

| Patch | Change |
|-------|--------|
| [`93-local-code-skip-chat-signin.patch`](vscodium/patches/user/93-local-code-skip-chat-signin.patch) | On startup (no `chatExtensionId`): mark setup `completed`, entitlement `Free`, skip install/sign-in; fix “Connect to Ollama” precondition |

After recompile + relaunch, chat should forward to the built-in `ollama` LM provider without a sign-in dialog.

---

## 2026-05-20 — Phase 1: Local Code product identity

### Shipped in repo

| Item | Location |
|------|----------|
| Product overlay | [`vscodium/product-local-code.json`](vscodium/product-local-code.json) — neutered `defaultChatAgent` (Ollama provider, no GitHub extension ids) |
| Prepare hook | [`vscodium/prepare_vscode.sh`](vscodium/prepare_vscode.sh) — when overlay exists: `APP_NAME=Local Code`, `applicationName=localcode`, `dataFolderName=.local-code`, merge overlay |
| Branding + chat copy patch | [`vscodium/patches/user/91-local-code-phase1-branding.patch`](vscodium/patches/user/91-local-code-phase1-branding.patch) |
| Ollama settings (stubs) | `localCode.ollama.endpoint` / `localCode.ollama.defaultModel` in `chat.contribution.ts` (Phase 2 provider reads these) |

### Dev tree (already prepared)

`vscodium/vscode/product.json` and chat sources were updated in-place for `./scripts/run-dev.sh`. After a clean `prepare_vscode.sh`, patches re-apply the same edits.

### Rebuild / relaunch

```bash
cd vscodium/vscode
eval "$(fnm env)" && fnm use 22.22.1
pnpm run compile   # required for .ts string / config changes
cd ../..
./scripts/run-dev.sh
```

Electron app folder name follows `product.nameLong` (expect **Local Code Dev.app** under `.build/electron/` after `preLaunch`).

### Phase 1 follow-ups

- [ ] Custom icons (still VSCodium assets until overlay)
- [ ] `defaultChatAgent` participant → Local Code agent (needs chat participant wiring)
- [ ] Wire **Connect to Ollama** command to `OllamaClient.listModels` health-check

---

## 2026-05-20 — Windows / locked-down work PC (build not viable here)

### Context

Attempted Phase 0 on a **corporate Windows 10** machine with limited install permissions. Goal: `get_repo.sh` → `prepare_vscode.sh` → `pnpm install` → `pnpm run compile`.

### What worked (no admin)

| Step | Result |
|------|--------|
| Node **22.22.0** | Already in `Program Files\nodejs`; close enough to `.nvmrc` **22.22.1** |
| **pnpm** | `npm install -g pnpm@10.12.1` to user profile (`%AppData%\Roaming\npm`) — **corepack** failed (`EPERM` writing under `Program Files\nodejs`) |
| **jq**, **Rust** | `winget install` succeeded |
| **Git Bash** | Required for `get_repo.sh` / `prepare_vscode.sh` |
| `get_repo.sh` | VS Code **1.116.0** @ `560a9dba` cloned to `vscodium/vscode/` |
| `git config core.longpaths true` | Needed after two long-path snapshot files failed on first checkout |
| `prepare_vscode.sh` (patches) | All VSCodium patches + `90-local-code-enable-ai-default.patch` applied |
| Helper script | [`scripts/win-build-env.sh`](scripts/win-build-env.sh) — Git Bash `PATH` for pnpm, jq, cargo, Python |

### Blocker: MSVC / VC++ toolset (admin or IT)

`pnpm install --frozen-lockfile` fails in `build/npm/postinstall.ts` when **node-gyp** rebuilds native modules (e.g. `@vscode/deviceid`, `@vscode/spdlog` under `remote/`).

```
VS 2022 Community found at ...\2022\Community
- found "Visual Studio C++ core features"
- missing any VC++ toolset
```

- **Visual Studio Installer → Modify → Desktop development with C++** is the fix; often requires elevation or an IT ticket.
- `winget install Microsoft.VisualStudio.2022.BuildTools` with `--add Microsoft.VisualStudio.Workload.VCTools` exited **1602** (cancelled / policy / UAC).
- **WSL2** not installed; would also typically need admin for first-time setup.

### Re-running `prepare_vscode.sh`

If `vscode/` already has patches applied, a second `prepare_vscode.sh` fails on the first patch (`patch does not apply`). Reset before re-preparing:

```bash
source scripts/win-build-env.sh
cd vscodium/vscode
git reset --hard HEAD
git clean -fdx   # drops node_modules; omit or narrow if you only need a patch retry
cd ..
bash prepare_vscode.sh
```

After VC++ is available, a full prepare may not be needed—**`pnpm install --frozen-lockfile`** in `vscodium/vscode/` may suffice if patches are already applied.

### Recommendation: split dev vs build machines

| Machine | Role |
|---------|------|
| **Locked-down Windows (work)** | Patches, docs, `PROJECT.md`, git; **do not expect compile** without VC++ workload |
| **macOS (home / prior progress)** | `pnpm install`, `pnpm run compile`, run IDE — see [2026-05-19 Xcode fix](#2026-05-19--xcode-fix-pnpm-install-succeeded) |

Stock **VSCodium + Ollama** on Windows is still useful for UX spikes; it does not replace building this fork.

### Follow-ups

- [ ] IT: add **Desktop development with C++** to VS 2022 Community, or install **Build Tools 2022 + VC++ workload**
- [ ] On Mac: `cd vscodium/vscode && pnpm run compile` (install already succeeded there)
- [ ] Optional: shorten clone path on Windows (e.g. `C:\lc\`) if long-path issues return

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
