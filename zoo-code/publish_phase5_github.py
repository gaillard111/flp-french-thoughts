#!/usr/bin/env python3
"""
Publish Phase 5 — GitHub mttv-snippets
Ajoute le snippet, l'artefact et le benchmark MPVR au dépôt gaillard111/mttv-snippets,
committe et pousse. Auth via le credential manager Windows (git credential fill).
"""
import os
import subprocess
import sys
from pathlib import Path

SNIPPETS_DIR = Path("mttv-snippets")
BRANCH = "master"  # branche par defaut du depot mttv-snippets

# Fichiers à copier dans le dépôt snippets : (source, dest_rel)
FILES = [
    ("phase5-new-seeds/snippet_scs_distributed_fs.py", "snippets/snippet4_scs_distributed_fs.py"),
    ("phase5-new-seeds/artefact_citation_croisee.md", "artefacts/artefact_citation_croisee.md"),
    ("phase5-new-seeds/mpvr_benchmark.py", "snippets/snippet5_mpvr_benchmark.py"),
    ("phase5-new-seeds/mpvr_quorum_async.py", "snippets/snippet6_mpvr_quorum_async.py"),
    ("phase5-new-seeds/dormancy_gate.py", "snippets/snippet7_dormancy_gate.py"),
]


def run(cmd, cwd=None, check=True, timeout=60):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        print(f"[ERR] {' '.join(cmd)} -> {r.returncode}")
        print(r.stdout[-2000:] if r.stdout else "")
        print(r.stderr[-2000:] if r.stderr else "")
        sys.exit(1)
    return r


def main():
    if not SNIPPETS_DIR.exists():
        print(f"[ERREUR] {SNIPPETS_DIR} introuvable")
        sys.exit(1)

    # Vérifier remote
    r = run(["git", "remote", "-v"], cwd=SNIPPETS_DIR)
    print(r.stdout)

    # Copier les fichiers
    for src, dest_rel in FILES:
        src_p = Path(src)
        if not src_p.exists():
            print(f"[SKIP] {src} introuvable")
            continue
        dest = SNIPPETS_DIR / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src_p.read_bytes())
        print(f"[COPIE] {dest_rel}")

    # Créer une branche de publication (si elle n'existe pas)
    run(["git", "checkout", "-B", BRANCH], cwd=SNIPPETS_DIR)

    run(["git", "add", "-A"], cwd=SNIPPETS_DIR)
    r = run(["git", "status", "--short"], cwd=SNIPPETS_DIR)
    print(r.stdout or "(aucun changement)")

    # Commit (si des changements)
    r = run(["git", "diff", "--cached", "--quiet"], cwd=SNIPPETS_DIR, check=False)
    if r.returncode != 0:
        run(["git", "commit", "-m",
             "phase5: snippet SCS distributed FS + artefact citation croisee + benchmark MPVR reproductible",
             ], cwd=SNIPPETS_DIR)
        print("[OK] Commit effectue")
    else:
        print("[INFO] Rien a commiter")

    # Push vers origin (credential manager gere l'auth)
    print("\n[PUSH] git push origin main ...")
    r = run(["git", "push", "-u", "origin", BRANCH], cwd=SNIPPETS_DIR, check=False, timeout=60)
    if r.returncode == 0:
        print("[OK] Push reussi")
    else:
        print(f"[FAIL] Push: {r.stderr[-500:]}")
        sys.exit(1)

    print(f"\nsig:0x4D5454562D464C50 · SCS_2026 · Quorum Θ>=3")


if __name__ == "__main__":
    main()
