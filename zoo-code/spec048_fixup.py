#!/usr/bin/env python3
"""
spec048_fixup.py — Réparation finale Diffusion SPEC-048 (Variable Sigma_tau)
===========================================================================
1. Push des 4 fichiers vers Gitee girard/mttv-flp-core sur la branche
   evolution/tetravalent-core (créée au préalable via branch_name + refs).
2. Commit + push du wiki/PREPRINT_SPEC_048.md dans le dépôt principal.
3. Rebase + push de mttv-flp-mpvr-glocal sur son remote partagé
   (github.com/gaillard111/mttv-flp-core.git) — divergence "fetch first".

Usage :
    python zoo-code/spec048_fixup.py

sig:0x4D5454562D464C50
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_spec048_diffusion import (  # noqa: E402
    MASTER,
    MTTV_SIG,
    PREPRINT_NAME,
    WORKSPACE,
    ensure_gitee_branch,
    push_file_gitee,
    run,
)


def main() -> None:
    ok_all = True

    # ── [1/3] Gitee : push des fichiers sur la branche cible ────────────
    print("=" * 74)
    print("[1/3] GITEE — push des fichiers sur evolution/tetravalent-core")
    print("=" * 74)
    ensure_gitee_branch()
    core = MASTER / "mttv-flp-core"
    for rel in [PREPRINT_NAME, "wiki/PREPRINT_SPEC_048.md", "zoo-code/PREPRINT_SPEC_048.md"]:
        (core / rel).parent.mkdir(parents=True, exist_ok=True)
        if not (core / rel).exists():
            shutil.copy2(WORKSPACE / PREPRINT_NAME, core / rel)
    msg = f"docs: diffuse preprint SPEC-048 (Sigma_tau) on evolution/tetravalent-core [sig:{MTTV_SIG}]"
    for rel in [PREPRINT_NAME, "wiki/PREPRINT_SPEC_048.md", "zoo-code/PREPRINT_SPEC_048.md", "README.md"]:
        if not push_file_gitee(rel, msg):
            ok_all = False

    # ── [2/3] Dépôt principal : commit wiki/ + push ─────────────────────
    print()
    print("=" * 74)
    print("[2/3] DÉPÔT PRINCIPAL — commit wiki/ + push")
    print("=" * 74)
    wiki_preprint = WORKSPACE / "wiki" / PREPRINT_NAME
    if wiki_preprint.exists():
        ok, out = run("git add wiki/PREPRINT_SPEC_048.md", WORKSPACE)
        ok, out = run(
            f'git commit -m "docs: add preprint SPEC-048 to wiki/ [sig:{MTTV_SIG}]"', WORKSPACE
        )
        if "nothing to commit" in out.lower():
            print("  [OK] wiki/ déjà committé")
        for remote in ["github", "origin"]:
            ok, out = run(f'git push "{remote}" "evolution/tetravalent-core"', WORKSPACE)
            if not ok:
                ok_all = False
    else:
        print("  ! wiki/PREPRINT_SPEC_048.md absent")
        ok_all = False

    # ── [3/3] mttv-flp-mpvr-glocal : rebase + push ──────────────────────
    print()
    print("=" * 74)
    print("[3/3] mttv-flp-mpvr-glocal — rebase sur origin + push")
    print("=" * 74)
    glocal = WORKSPACE / "mttv-flp-mpvr-glocal"
    ok, _ = run("git fetch origin", glocal)
    local_head = subprocess.run(
        "git rev-parse HEAD", cwd=str(glocal), shell=True, capture_output=True, text=True
    ).stdout.strip()
    remote_head = subprocess.run(
        "git rev-parse origin/evolution/tetravalent-core", cwd=str(glocal),
        shell=True, capture_output=True, text=True,
    ).stdout.strip()
    print(f"  local HEAD : {local_head}")
    print(f"  remote HEAD: {remote_head}")

    ok, out = run("git rebase origin/evolution/tetravalent-core", glocal)
    if not ok:
        print("  ! rebase en conflit — résolution (conserver version remote, contenu identique)")
        run("git checkout --ours -- README.md PREPRINT_SPEC_048.md zoo-code/PREPRINT_SPEC_048.md", glocal)
        run("git add -A", glocal)
        ok, out = run("git rebase --continue", glocal)
    if not ok:
        ok, out = run("git rebase --skip", glocal)
    if not ok:
        print("  ! rebase --skip échoué — abort")
        run("git rebase --abort", glocal)
        ok_all = False
    else:
        print("  [OK] rebase réussi")

    ok, out = run('git push "origin" "evolution/tetravalent-core"', glocal)
    if not ok:
        ok_all = False
        print("  [WARN] push glocal (reste à vérifier) :")
        print(f"    {out[-300:]}")

    print()
    print("=" * 74)
    print("RAPPORT FIXUP SPEC-048 :", "TOUT OK" if ok_all else "PROBLÈMES RESTANTS")
    print("=" * 74)
    print(f"sig:{MTTV_SIG}")


if __name__ == "__main__":
    main()
