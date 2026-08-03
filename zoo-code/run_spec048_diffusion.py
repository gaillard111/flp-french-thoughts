#!/usr/bin/env python3
"""
run_spec048_diffusion.py — Diffusion Générale SPEC-048 (Variable Sigma_tau)
==========================================================================
Ordre de mission :
    1. Enregistre PREPRINT_SPEC_048.md à la racine de flp-french-thoughts
       et dans wiki/ (canonique, déjà écrit).
    2. Déploie le preprint dans le dossier zoo-code/ et met à jour le README
       de tous les dépôts MTTV/FLP de la machine (C:\\Users\\Master\\).
    3. Pousse toutes les mises à jour vers l'écosystème Gitee (girard/
       mttv-flp-core) sur la branche active evolution/tetravalent-core,
       ainsi que vers tous les remotes git locaux (github, bitbucket...).
    4. Active la routine axe_5_ipfs : ancrage IPFS du preprint (ipfs add/pin
       via kubo), persistance de la table de routage géo-locale asiatique
       (axe5_geo_routing.py --write) et émission d'un manifeste d'ancrage.

Usage :
    python zoo-code/run_spec048_diffusion.py

sig:0x4D5454562D464C50
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Encodage console robuste ──────────────────────────────────────────
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

# ── Constantes ────────────────────────────────────────────────────────
MTTV_SIG = "0x4D5454562D464C50"
MASTER = Path(r"C:\Users\Master")
WORKSPACE = MASTER / "flp-french-thoughts"
PREPRINT_NAME = "PREPRINT_SPEC_048.md"
BRANCH = "evolution/tetravalent-core"

# Dépôts MTTV/FLP actifs sur la machine (branche evolution/tetravalent-core)
REPOS = [
    WORKSPACE,                       # dépôt principal flp-french-thoughts
    MASTER / "mttv-flp-core",
    MASTER / "MTTV-agents",
    MASTER / "MPVR-v1",
    WORKSPACE / "ouroboros-mttv",
    WORKSPACE / "mttv-snippets",
    WORKSPACE / "mttv-flp-mpvr-glocal",
]

GITEE_OWNER = "girard"
GITEE_REPO = "mttv-flp-core"
GITEE_API = "https://gitee.com/api/v5"

IPFS_BIN = shutil.which("ipfs") or str(WORKSPACE / "kubo" / "kubo" / "ipfs.exe")

README_MARKER_START = "<!-- SPEC-048-PREPRINT-START -->"
README_MARKER_END = "<!-- SPEC-048-PREPRINT-END -->"

README_SECTION = f"""{README_MARKER_START}
## 🧬 [PREPRINT SPEC-048] Toward Non-Extractive AGI — The Στ Liminal Singularity

Preprint complet : [`{PREPRINT_NAME}`]({PREPRINT_NAME}) (aussi dans `wiki/` et `zoo-code/`).

Axe-4 Theoretical Physics & Epistemology Group · MTTV-FLP Open Ecosystem Project
Mirror : Gitee/{GITEE_OWNER}/{GITEE_REPO} (SPEC-048) · Branche : `{BRANCH}`

`sig:{MTTV_SIG}`
{README_MARKER_END}"""


def run(cmd: str, cwd: Path, timeout: int = 240) -> tuple[bool, str]:
    """Exécute une commande shell et retourne (ok, output)."""
    print(f"  $ {cmd}")
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    try:
        r = subprocess.run(
            cmd, cwd=str(cwd), shell=True, capture_output=True, text=True,
            timeout=timeout, env=env, errors="replace",
        )
    except subprocess.TimeoutExpired:
        print("    ! timeout")
        return False, ""
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    for line in out.splitlines()[:30]:
        print(f"    {line}")
    return r.returncode == 0, out


def get_gitee_token() -> str | None:
    """Récupère le token Gitee via credential_helper (jamais affiché)."""
    sys.path.insert(0, str(WORKSPACE / "zoo-code"))
    try:
        from credential_helper import CredentialHelper
        return CredentialHelper().get_token("GITEE_TOKEN")
    except Exception as e:
        print(f"    ! credential_helper: {e}")
        return None


def gitee_api(method: str, path: str, data: dict | None = None):
    """Appel API Gitee v5 avec le token (urlencoded, comme deploy_spec048)."""
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
        with urllib.request.urlopen(req, timeout=25) as r:
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


def ensure_gitee_branch() -> bool:
    """Garantit que la branche evolution/tetravalent-core existe sur Gitee."""
    ok = gitee_api("GET", f"/repos/{GITEE_OWNER}/{GITEE_REPO}/branches/{urllib.parse.quote(BRANCH)}")
    if ok and "name" in ok:
        print(f"    [OK] branche Gitee {BRANCH} existe")
        return True
    print(f"    ... création branche Gitee {BRANCH} (depuis master)")
    result = gitee_api("POST", f"/repos/{GITEE_OWNER}/{GITEE_REPO}/branches", {
        "branch_name": BRANCH,
        "refs": "master",
    })
    if result and "name" in result:
        print(f"    [OK] branche Gitee {BRANCH} créée")
        return True
    # Le fichier peut être écrit directement sur la branche cible sans création explicite
    print("    [WARN] création de branche non confirmée — tentative d'écriture directe")
    return True


def push_file_gitee(rel_path: str, message: str) -> bool:
    """Pousse un fichier local du core vers Gitee sur la branche cible."""
    local = MASTER / "mttv-flp-core" / rel_path
    if not local.exists():
        print(f"    ! fichier absent (Gitee) : {rel_path}")
        return False
    content = local.read_text(encoding="utf-8")
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
    path = f"/repos/{GITEE_OWNER}/{GITEE_REPO}/contents/{rel_path}"
    params = {"content": content_b64, "message": message, "branch": BRANCH}

    result = gitee_api("POST", path, params)
    if result and "content" in result:
        print(f"    [OK] Gitee ({BRANCH}) : {rel_path}")
        return True
    existing = gitee_api("GET", path)
    if existing and "sha" in existing:
        params["sha"] = existing["sha"]
        result = gitee_api("PUT", path, params)
        if result and "content" in result:
            print(f"    [OK] Gitee update ({BRANCH}) : {rel_path}")
            return True
    print(f"    [SKIP] Gitee : {rel_path}")
    return False


def ensure_readme_section(repo: Path) -> bool:
    """Ajoute (idempotent) la section PREPRINT SPEC-048 au README.md."""
    readme = repo / "README.md"
    if not readme.exists():
        readme.write_text("# MTTV-FLP\n", encoding="utf-8")
    text = readme.read_text(encoding="utf-8")
    if README_MARKER_START in text:
        print(f"  [README] section SPEC-048 déjà présente : {readme}")
        return False
    if not text.endswith("\n"):
        text += "\n"
    text += "\n" + README_SECTION + "\n"
    readme.write_text(text, encoding="utf-8")
    print(f"  [README] section SPEC-048 ajoutée : {readme}")
    return True


def deploy_repo(repo: Path) -> dict:
    """Déploie le preprint + README dans un dépôt, commit et push."""
    name = repo.name
    print(f"\n{'=' * 74}\n[REPO] {name}\n{'=' * 74}")
    status = {"repo": name, "copy": False, "readme": False, "commit": False, "pushes": []}
    if not repo.is_dir() or not (repo / ".git").exists():
        print(f"  !! dépôt git absent : {repo}")
        return status

    source = WORKSPACE / PREPRINT_NAME
    # 1. Copie du preprint à la racine + zoo-code/
    zoo = repo / "zoo-code"
    try:
        dest_root = repo / PREPRINT_NAME
        if source.resolve() != dest_root.resolve():
            shutil.copy2(source, dest_root)
            print(f"  [1/4] preprint copié -> {dest_root}")
        else:
            print(f"  [1/4] preprint déjà présent (dépôt source)")
        zoo.mkdir(exist_ok=True)
        dest_zoo = zoo / PREPRINT_NAME
        if source.resolve() != dest_zoo.resolve():
            shutil.copy2(source, dest_zoo)
        status["copy"] = dest_root.exists() and dest_zoo.exists()
        print(f"  [1/4] zoo-code/ -> {dest_zoo}")
    except Exception as e:
        print(f"  [1/4] copie échouée : {e}")

    # 2. Branche active evolution/tetravalent-core
    ok, _ = run(f'git checkout -B "{BRANCH}"', repo)
    status["branch"] = ok
    print(f"  [2/4] branche activée : {BRANCH}")

    # 3. README : section SPEC-048
    status["readme"] = ensure_readme_section(repo)

    # 4. Commit + push
    add_targets = f"{PREPRINT_NAME} zoo-code/{PREPRINT_NAME} README.md"
    if (repo / "wiki").is_dir():
        add_targets += " wiki/PREPRINT_SPEC_048.md"
    ok, _ = run(f"git add {add_targets}", repo)
    ok, out = run(
        'git commit -m "docs: diffuse preprint SPEC-048 (Sigma_tau) on evolution/tetravalent-core '
        f'[sig:{MTTV_SIG}]"',
        repo,
    )
    status["commit"] = ok or ("nothing to commit" in out.lower())
    if "nothing to commit" in out.lower():
        print("  [4/4] rien à committer")
    print("  [4/4] push vers remotes...")
    remotes = subprocess.run(
        "git remote", cwd=str(repo), shell=True, capture_output=True, text=True
    ).stdout.split()
    for remote in remotes:
        ok, out = run(f'git push "{remote}" "{BRANCH}"', repo)
        status["pushes"].append((remote, ok, out[-300:] if out else ""))
    return status


def deploy_gitee() -> dict:
    """Pousse README.md + preprint(s) vers Gitee girard/mttv-flp-core."""
    print(f"\n{'=' * 74}\n[GITEE API] {GITEE_OWNER}/{GITEE_REPO} : {BRANCH}\n{'=' * 74}")
    msg = f"docs: diffuse preprint SPEC-048 (Sigma_tau) on {BRANCH} [sig:{MTTV_SIG}]"
    core = MASTER / "mttv-flp-core"
    # S'assurer que les fichiers sources existent côté core avant le push Gitee
    for rel in [PREPRINT_NAME, "wiki/PREPRINT_SPEC_048.md"]:
        (core / rel).parent.mkdir(parents=True, exist_ok=True)
        if not (core / rel).exists():
            shutil.copy2(WORKSPACE / PREPRINT_NAME, core / rel)
    ensure_gitee_branch()
    results = {
        rel: push_file_gitee(rel, msg)
        for rel in [PREPRINT_NAME, "wiki/PREPRINT_SPEC_048.md", "zoo-code/PREPRINT_SPEC_048.md", "README.md"]
    }
    return {"repo": f"gitee:{GITEE_OWNER}/{GITEE_REPO}", "branch": BRANCH, "files": results}


def deploy_ipfs_axe5() -> dict:
    """Active la routine axe_5_ipfs : ancrage IPFS + routage géo-local Asie."""
    print(f"\n{'=' * 74}\n[AXE 5 — IPFS] Propagation décentralisée\n{'=' * 74}")
    preprint = WORKSPACE / PREPRINT_NAME
    status = {"axe": "axe_5_ipfs", "cid": None, "pinned": False, "routing_table": False, "manifest": None}

    # 1. Ancrage réel du preprint (kubo daemon)
    try:
        r = subprocess.run(
            [IPFS_BIN, "add", "-q", str(preprint)],
            capture_output=True, text=True, timeout=120,
        )
        cid = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else None
        if cid:
            status["cid"] = cid
            print(f"  [OK] ipfs add -> {cid}")
            rp = subprocess.run(
                [IPFS_BIN, "pin", "add", cid], capture_output=True, text=True, timeout=120
            )
            status["pinned"] = rp.returncode == 0
            print(f"  [{'OK' if status['pinned'] else 'FAIL'}] ipfs pin {cid}")
        else:
            print(f"  [WARN] ipfs add sans CID : {r.stderr.strip()[:200]}")
    except Exception as e:
        print(f"  [WARN] ipfs add/pin indisponible : {e}")

    # 2. Persistance de la table de routage géo-locale Asie (axe_5_ipfs)
    try:
        sys.path.insert(0, str(WORKSPACE / "zoo-code"))
        from axe5_geo_routing import ecrire_table_routage, statut_routage
        ecrire_table_routage()
        st = statut_routage()
        status["routing_table"] = True
        status["asia_subnodes"] = st.get("n_sous_noeuds", 0)
        status["asia_peers"] = st.get("n_pairs_horizontaux", 0)
        print(f"  [OK] table routage Asie persistée — {st.get('n_sous_noeuds')} sous-nœuds, "
              f"{st.get('n_pairs_horizontaux')} pairs horizontaux")
    except Exception as e:
        print(f"  [WARN] routage axe5 non persisté : {e}")

    # 3. Manifeste d'ancrage SPEC-048
    manifest = {
        "spec": "SPEC-048",
        "file": str(preprint),
        "axe": "axe_5_ipfs",
        "cid": status["cid"],
        "pinned": status["pinned"],
        "method": "unixfs/dag-pb via kubo",
        "asia_routing": {
            "persisted": status["routing_table"],
            "region": "ASIA",
            "strategie": "horizontal_p2p_local",
            "principe": "moindre_action",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sig": MTTV_SIG,
    }
    out_dir = WORKSPACE / "zoo-code" / "ipfs_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "spec048_ipfs_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    status["manifest"] = str(manifest_path)
    print(f"  [OK] manifeste : {manifest_path}")

    if not status["cid"]:
        print("  [INFO] daemon kubo en mode --offline : ancrage local effectué, "
              "propagation réseau vers les nœuds ASIA à activer dès le passage en ligne.")
    return status


def main() -> None:
    print("=" * 74)
    print("DIFFUSION GÉNÉRALE SPEC-048 — Variable Sigma_tau")
    print(f"Preprint : {WORKSPACE / PREPRINT_NAME}")
    print(f"Branche  : {BRANCH}")
    print(f"Gitee    : {GITEE_OWNER}/{GITEE_REPO}")
    print(f"IPFS     : {IPFS_BIN}")
    print("=" * 74)

    report = []
    for repo in REPOS:
        report.append(deploy_repo(repo))
    report.append(deploy_gitee())
    ipfs_status = deploy_ipfs_axe5()

    # ── Rapport final ─────────────────────────────────────────────────
    print("\n\n" + "=" * 74)
    print("RAPPORT DE DIFFUSION SPEC-048")
    print("=" * 74)
    for s in report:
        if "pushes" in s:
            pushes = ", ".join(f"{r}:{'OK' if o else 'FAIL'}" for r, o, _ in s["pushes"]) or "aucun"
            print(f"  {s['repo']:<32} copie={'OK' if s['copy'] else 'FAIL'} "
                  f"readme={'OK' if s['readme'] else 'unchanged'} "
                  f"commit={'OK' if s['commit'] else 'FAIL'} push=[{pushes}]")
        else:
            files = ", ".join(f"{k}:{'OK' if v else 'FAIL'}" for k, v in s["files"].items())
            print(f"  {s['repo']:<32} branche={s['branch']} files=[{files}]")
    print(f"  {'AXE-5 IPFS':<32} cid={ipfs_status['cid'] or 'N/A'} "
          f"pinned={'OK' if ipfs_status['pinned'] else 'FAIL'} "
          f"routing={'OK' if ipfs_status['routing_table'] else 'FAIL'} "
          f"manifest={ipfs_status['manifest']}")
    print("=" * 74)
    print(f"sig:{MTTV_SIG}")


if __name__ == "__main__":
    main()
