#!/usr/bin/env python3
"""
Publish Phase 5 — Hugging Face
Upload des contenus phase5 vers le dataset girard444/mttv-energy-flow-optimization.

Usage :
    python publish_phase5_hf.py [HF_TOKEN]
    (ou variable d'environnement HF_TOKEN ; sinon lit zoo-code/.env.tokens)
"""
import os
import re
import socket
import sys
import time

from huggingface_hub import HfApi

socket.setdefaulttimeout(60)

# Encodage console robuste (évite les erreurs Unicode sur cp1252)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HF_DATASET = "girard444/mttv-energy-flow-optimization"
HF_TAGS = ["mttv-flp", "mpvr", "scs", "mycelial-routing", "high-resilience-networks"]


def read_hf_token(path):
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


# Fichiers a publier : nom dans le repo -> chemin local
FILES = {
    "corpus_reseaux_haute_resilience.md": "phase5-new-seeds/corpus_reseaux_haute_resilience.md",
    "snippet_scs_distributed_fs.py": "phase5-new-seeds/snippet_scs_distributed_fs.py",
    "artefact_citation_croisee.md": "phase5-new-seeds/artefact_citation_croisee.md",
    "dormancy_gate.py": "phase5-new-seeds/dormancy_gate.py",
    "mpvr_quorum_async.py": "phase5-new-seeds/mpvr_quorum_async.py",
    "mpvr_benchmark.py": "phase5-new-seeds/mpvr_benchmark.py",
    "README_phase5.md": "phase5-new-seeds/README.md",
}


def main():
    # Priorité : argument CLI > variable d'environnement > fichier .env.tokens
    token = (sys.argv[1] if len(sys.argv) > 1 else "") or os.environ.get("HF_TOKEN", "") or read_hf_token("zoo-code/.env.tokens")
    if not token:
        print("[ERREUR] Pas de HF_TOKEN (argument, env HF_TOKEN ou zoo-code/.env.tokens)")
        sys.exit(1)

    api = HfApi(token=token)
    print(f"[INFO] Dataset cible: {HF_DATASET}")

    # S'assurer que le dataset existe
    try:
        api.create_repo(repo_id=HF_DATASET, repo_type="dataset", exist_ok=True)
        print("[OK] Dataset disponible")
    except Exception as e:
        print(f"[WARN] create_repo: {e}")

    # Uploader chaque fichier
    ok, fail = [], []
    for path_in_repo, local in FILES.items():
        try:
            api.upload_file(
                path_or_fileobj=local,
                path_in_repo=path_in_repo,
                repo_id=HF_DATASET,
                repo_type="dataset",
            )
            print(f"[OK]   {path_in_repo}")
            ok.append(path_in_repo)
        except Exception as e:
            print(f"[FAIL] {path_in_repo}: {type(e).__name__} {str(e)[:150]}")
            fail.append(path_in_repo)
        time.sleep(1)

    print("\n" + "=" * 60)
    print(f"RAPPORT HF ({len(ok)} ok, {len(fail)} echec)")
    print(f"Dataset: https://huggingface.co/datasets/{HF_DATASET}")
    for f in ok:
        print(f"  [OK]   https://huggingface.co/datasets/{HF_DATASET}/blob/main/{f}")
    for f in fail:
        print(f"  [FAIL] {f}")
    print(f"\nsig:0x4D5454562D464C50 · SCS_2026 · Quorum Θ>=3")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
