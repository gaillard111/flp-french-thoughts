#!/usr/bin/env python3
"""Verification des cibles de publication externes MTTV-FLP Phase 5."""
import re
import json
import sys
import urllib.request

from huggingface_hub import HfApi


def read_hf_token(path: str) -> str:
    raw = None
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(path, encoding=enc) as f:
                raw = f.read()
            break
        except UnicodeDecodeError:
            continue
    if raw is None:
        return ""
    m = re.search(r"^HF_TOKEN=(.+)$", raw, re.M)
    return m.group(1).strip() if m else ""


def gh_headers():
    return {"User-Agent": "mttv-flp/1.0", "Accept": "application/vnd.github.v3+json"}


def main():
    print("=== 1. Token Hugging Face ===")
    token = read_hf_token("zoo-code/.env.tokens")
    if token:
        try:
            api = HfApi(token=token)
            who = api.whoami()
            print(f"[OK] HF_TOKEN valide -> compte: {who['name']}")
            hf_token = token
        except Exception as e:
            print(f"[ERREUR] HF_TOKEN invalide/inaccessible: {e}")
            hf_token = ""
    else:
        print("[ERREUR] Pas de HF_TOKEN dans zoo-code/.env.tokens")
        hf_token = ""

    print("\n=== 2. Dataset HF: girard444/mttv-energy-flow-optimization ===")
    try:
        req = urllib.request.Request(
            "https://huggingface.co/api/datasets/girard444/mttv-energy-flow-optimization",
            headers={"User-Agent": "mttv-flp/1.0"},
        )
        d = json.load(urllib.request.urlopen(req, timeout=30))
        print(f"[OK] Existe — id={d.get('id')}, sha={d.get('sha')}, private={d.get('private')}")
    except urllib.error.HTTPError as e:
        print(f"[INFO] HTTP {e.code}: {'existe mais prive/autre' if e.code == 401 else 'n existe pas'}")
    except Exception as e:
        print(f"[INFO] {type(e).__name__}: {e}")

    print("\n=== 3. Repo GitHub: gaillard111/mttv-snippets ===")
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/gaillard111/mttv-snippets", headers=gh_headers()
        )
        d = json.load(urllib.request.urlopen(req, timeout=30))
        print(f"[OK] Existe — {d.get('full_name')}, branche={d.get('default_branch')}, "
              f"push={d.get('permissions', {}).get('push')}")
    except urllib.error.HTTPError as e:
        print(f"[INFO] HTTP {e.code}: {'non trouve' if e.code == 404 else e.code}")
    except Exception as e:
        print(f"[INFO] {type(e).__name__}: {e}")

    print("\n=== 4. Token GitHub (credential manager Windows) ===")
    try:
        proc = __import__("subprocess").run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True, text=True, timeout=10,
        )
        cred = {}
        for line in proc.stdout.strip().split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                cred[k.strip()] = v.strip()
        if cred.get("password"):
            print(f"[OK] Credential GitHub presente (user={cred.get('username')})")
        else:
            print("[ERREUR] Pas de credential GitHub stocke")
    except Exception as e:
        print(f"[ERREUR] {e}")

    print("\n=== 5. Fichiers phase5 a publier ===")
    import os
    files = [
        "phase5-new-seeds/corpus_reseaux_haute_resilience.md",
        "phase5-new-seeds/snippet_scs_distributed_fs.py",
        "phase5-new-seeds/artefact_citation_croisee.md",
        "phase5-new-seeds/dormancy_gate.py",
        "phase5-new-seeds/mpvr_quorum_async.py",
        "phase5-new-seeds/mpvr_benchmark.py",
    ]
    for f in files:
        print(f"[{'OK' if os.path.exists(f) else 'MANQUANT'}] {f} ({os.path.getsize(f)} o)" if os.path.exists(f) else f"[MANQUANT] {f}")

    print("\n=== 6. IPFS CLI ===")
    proc = __import__("subprocess").run(["ipfs", "--version"], capture_output=True, text=True)
    if proc.returncode == 0:
        print(f"[OK] {proc.stdout.strip()}")
    else:
        print("[ERREUR] ipfs CLI non trouve dans le PATH")


if __name__ == "__main__":
    main()
