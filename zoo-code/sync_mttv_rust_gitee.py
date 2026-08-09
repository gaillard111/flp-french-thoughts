#!/usr/bin/env python3
"""
sync_mttv_rust_gitee.py — Synchronise le prototype Rust complet (mttv_rust/)
vers le miroir Gitee girard/mttv-flp-core (branche evolution/tetravalent-core).

Validation humaine reçue (09/08 ~21:44). Le prototype A→B→C (Étape C incluse)
est poussé sur Gitee, préfixé `mttv_rust/`, pour préserver la structure.

Mécanisme : API Gitee v5 /contents, base64, comme push_file_gitee de
run_spec048_diffusion.py. Idempotent : POST si absent, PUT avec sha si présent.

sig:0x4D5454562D464C50
"""
from __future__ import annotations

import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

MASTER = Path(r"C:\Users\Master")
WORKSPACE = MASTER / "flp-french-thoughts"
SRC = WORKSPACE / "mttv_rust"
GITEE_OWNER = "girard"
GITEE_REPO = "mttv-flp-core"
GITEE_API = "https://gitee.com/api/v5"
BRANCH = "evolution/tetravalent-core"
PREFIX = "mttv_rust"  # préfixe dans le dépôt Gitee

# Exclusions (build, git, caches)
EXCLUDED_DIRS = {"target", ".git", ".cargo", "criterion"}
EXCLUDED_EXT = {".exe", ".o", ".pdb"}


def get_gitee_token() -> str | None:
    sys.path.insert(0, str(WORKSPACE / "zoo-code"))
    try:
        from credential_helper import CredentialHelper
        return CredentialHelper().get_token("GITEE_TOKEN")
    except Exception as e:
        print(f"    ! credential_helper: {e}")
        return None


def gitee_api(method: str, path: str, data: dict | None = None):
    token = get_gitee_token()
    if not token:
        print("    ! GITEE_TOKEN introuvable")
        return None
    url = f"{GITEE_API}{path}"
    if data is None:
        data = {}
    data["access_token"] = token
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            err = raw.decode("utf-8")
        except Exception:
            err = str(raw)
        safe = err.encode("ascii", "replace").decode("ascii")[:200]
        print(f"    ! Gitee HTTP {e.code}: {safe}")
        return None
    except Exception as e:
        print(f"    ! Gitee: {ascii(e)}")
        return None


def ensure_branch() -> bool:
    ok = gitee_api(
        "GET",
        f"/repos/{GITEE_OWNER}/{GITEE_REPO}/branches/{urllib.parse.quote(BRANCH)}",
    )
    if ok and "name" in ok:
        print(f"    [OK] branche Gitee {BRANCH} existe")
        return True
    print(f"    ... création branche Gitee {BRANCH}")
    gitee_api(
        "POST",
        f"/repos/{GITEE_OWNER}/{GITEE_REPO}/branches",
        {"branch_name": BRANCH, "refs": "master"},
    )
    print("    [WARN] branche non confirmée — tentative d'écriture directe")
    return True


def push_file(rel_path: str) -> bool:
    """Pousse un fichier de SRC vers Gitee sous PREFIX/rel_path."""
    local = SRC / rel_path
    if not local.exists() or not local.is_file():
        return False
    try:
        content = local.read_text(encoding="utf-8")
    except Exception as e:
        print(f"    [SKIP] binaire/illisible {rel_path} : {e}")
        return False
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    gitee_rel = f"{PREFIX}/{rel_path.replace(chr(92), '/')}"
    path = f"/repos/{GITEE_OWNER}/{GITEE_REPO}/contents/{urllib.parse.quote(gitee_rel)}"
    params = {
        "content": content_b64,
        "message": f"mttv_rust: sync {rel_path} (prototype A->B->C, Etape C scellee)",
        "branch": BRANCH,
    }

    result = gitee_api("POST", path, params)
    if result and "content" in result:
        print(f"    [OK] Gitee ({BRANCH}) : {gitee_rel}")
        return True
    existing = gitee_api("GET", path)
    if existing and "sha" in existing:
        params["sha"] = existing["sha"]
        result = gitee_api("PUT", path, params)
        if result and "content" in result:
            print(f"    [OK] Gitee update ({BRANCH}) : {gitee_rel}")
            return True
    print(f"    [SKIP] Gitee : {gitee_rel}")
    return False


def collect_files(root: Path) -> list[str]:
    files: list[str] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        parts = rel.parts
        if any(seg in EXCLUDED_DIRS for seg in parts):
            continue
        if p.suffix in EXCLUDED_EXT:
            continue
        files.append(str(rel).replace(chr(92), "/"))
    return files


def main() -> int:
    if not SRC.is_dir():
        print(f"!! mttv_rust absent : {SRC}")
        return 1
    if not get_gitee_token():
        print("!! token Gitee introuvable — synchronisation impossible")
        return 1

    print(f"Synchronisation Gitee : {SRC} -> {GITEE_OWNER}/{GITEE_REPO}@{BRANCH}")
    if not ensure_branch():
        return 1

    files = collect_files(SRC)
    print(f"Fichiers à synchroniser : {len(files)}")
    ok = 0
    for f in files:
        if push_file(f):
            ok += 1
    print(f"\n=== RESULTAT : {ok}/{len(files)} fichiers synchronisés ===")
    print("sig:0x4D5454562D464C50")
    return 0 if ok == len(files) else 2


if __name__ == "__main__":
    raise SystemExit(main())
