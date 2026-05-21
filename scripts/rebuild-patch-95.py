#!/usr/bin/env python3
"""Rebuild patch 95 as incremental on top of patches 90-92 and 91 (for providers)."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VSCODE = ROOT / "vscodium/vscode"
PATCH_DIR = ROOT / "vscodium/patches/user"
OUT = PATCH_DIR / "95-local-code-phase3-ollama-chat-integration.patch"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def make_diff(rel: str, base: Path, final: Path) -> str | None:
    r = run("diff", "-u", str(base), str(final))
    if r.returncode != 1 or not r.stdout.strip():
        return None
    d = r.stdout.replace(f"--- {base}", f"--- a/{rel}").replace(f"+++ {final}", f"+++ b/{rel}")
    return f"diff --git a/{rel} b/{rel}\n" + d


def make_new(rel: str, final: Path) -> str | None:
    r = run("diff", "-u", "/dev/null", str(final))
    if r.returncode != 1:
        return None
    d = r.stdout.replace("--- /dev/null", f"--- a/{rel}").replace(f"+++ {final}", f"+++ b/{rel}")
    return f"diff --git a/{rel} b/{rel}\nnew file mode 100644\n" + d


def extract_p2_file(patch_path: Path, filename: str) -> str:
    lines = patch_path.read_text().splitlines()
    out: list[str] = []
    in_file = False
    for line in lines:
        if line.startswith(f"diff --git a/{filename}"):
            in_file = True
            continue
        if in_file and line.startswith("diff --git "):
            break
        if in_file and line.startswith("+") and not line.startswith("+++"):
            out.append(line[1:])
    return "\n".join(out) + "\n"


def git_head_file(rel: str) -> Path | None:
    r = subprocess.run(["git", "-C", str(VSCODE), "show", f"HEAD:{rel}"], capture_output=True)
    if r.returncode != 0:
        return None
    dest = Path(f"/tmp/lc_head_{Path(rel).name}")
    dest.write_bytes(r.stdout)
    return dest


def apply_patch_91(rel: str, marker: str) -> Path:
    """Apply patch 91 in a minimal tree containing files the patch touches."""
    head = git_head_file(rel)
    if not head:
        raise SystemExit(f"missing HEAD file for {rel}")

    tmp = Path(f"/tmp/lc91_{Path(rel).name}")
    if tmp.exists():
        shutil.rmtree(tmp)

    for p in [
        "src/vs/workbench/contrib/chat/browser/chat.contribution.ts",
        "src/vs/workbench/contrib/chat/browser/chatSetup/chatSetupContributions.ts",
        "src/vs/workbench/contrib/chat/browser/chatSetup/chatSetupProviders.ts",
        "src/vs/workbench/contrib/chat/browser/chatSetup/chatSetupRunner.ts",
        "src/vs/workbench/contrib/chat/browser/widget/chatWidget.ts",
    ]:
        h = git_head_file(p)
        if h:
            dest = tmp / p
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(h, dest)

    subprocess.run(
        ["patch", "-p1", "-d", str(tmp), "-i", str(PATCH_DIR / "91-local-code-phase1-branding.patch")],
        capture_output=True,
        text=True,
    )
    target = tmp / rel
    if marker not in target.read_text():
        raise SystemExit(f"patch 91 did not apply to {rel}")
    return target


def main() -> None:
    patch92 = PATCH_DIR / "92-local-code-phase2-ollama.patch"
    parts: list[str] = []

    for rel in [
        "src/vs/workbench/contrib/localLLM/browser/ollamaConnect.ts",
        "src/vs/workbench/contrib/localLLM/browser/localCodeChatAgent.ts",
        "src/vs/workbench/contrib/localLLM/browser/localCodeSystemPrompt.ts",
    ]:
        p = make_new(rel, VSCODE / rel)
        if p:
            parts.append(p)

    p2_contrib = Path("/tmp/p2_localLLM.contribution.ts")
    p2_contrib.write_text(extract_p2_file(patch92, "src/vs/workbench/contrib/localLLM/browser/localLLM.contribution.ts"))
    p2_prov = Path("/tmp/p2_ollamaLanguageModelProvider.ts")
    p2_prov.write_text(extract_p2_file(patch92, "src/vs/workbench/contrib/localLLM/browser/ollamaLanguageModelProvider.ts"))

    for rel, base in [
        ("src/vs/workbench/contrib/localLLM/browser/localLLM.contribution.ts", p2_contrib),
        ("src/vs/workbench/contrib/localLLM/browser/ollamaLanguageModelProvider.ts", p2_prov),
    ]:
        d = make_diff(rel, base, VSCODE / rel)
        if d:
            parts.append(d)

    for rel in [
        "src/vs/workbench/contrib/chat/browser/chatSetup/chatSetupController.ts",
        "src/vs/workbench/contrib/chat/browser/widget/input/chatInputPart.ts",
        "src/vs/code/electron-browser/workbench/workbench.html",
        "src/vs/code/electron-browser/workbench/workbench-dev.html",
    ]:
        head = git_head_file(rel)
        if head:
            d = make_diff(rel, head, VSCODE / rel)
            if d:
                parts.append(d)

    rel = "src/vs/workbench/contrib/chat/browser/chatSetup/chatSetupContributions.ts"
    base91 = apply_patch_91(rel, "Connect to Ollama")
    d = make_diff(rel, base91, VSCODE / rel)
    if d:
        parts.append(d)

    rel = "src/vs/workbench/contrib/chat/browser/chatSetup/chatSetupProviders.ts"
    base91 = apply_patch_91(rel, "settingUpOllamaNeeded")
    d = make_diff(rel, base91, VSCODE / rel)
    if d:
        parts.append(d)

    OUT.write_text("\n".join(parts))
    print(f"Wrote {OUT} ({len(parts)} sections, {OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
