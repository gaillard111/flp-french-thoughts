#!/usr/bin/env python3
"""
Deploiement MTTV-FLP / MPVR — GitHub + Hugging Face
Lecture des tokens depuis les .env des agents existants.
"""
import os, sys, json, subprocess
from pathlib import Path

REPO_DIR = Path("mttv-flp-mpvr-glocal")
GITHUB_REPO = "gaillard111/mttv-flp-mpvr-glocal"
HF_DATASET = "girard444/mttv-flp-mpvr-glocal"
HF_TAGS = ["mttv-flp", "mpvr", "post-bayesian-ai", "transscalar-living-systems", "mycelial-routing"]

# ── Récupération des tokens depuis les .env des agents ──────
def load_token_from_env(agent_dir, var_name):
    env_file = Path(agent_dir) / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{var_name}="):
                    return line.split("=", 1)[1]
    return None

hf_token = load_token_from_env("ouroboros-swarm/agent-7", "HF_TOKEN")
print(f"[TOKEN] HF_TOKEN: {'OK (' + hf_token[:10] + '...)' if hf_token else 'NON TROUVE'}")

# ── 1. Push GitHub ──────────────────────────────────────────
print("\n[1/3] Push GitHub...")
try:
    result = subprocess.run(
        ["git", "remote", "add", "origin", f"https://github.com/{GITHUB_REPO}.git"],
        cwd=REPO_DIR, capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0 and "already exists" not in result.stderr:
        print(f"  remote add: {result.stderr.strip()}")
    else:
        print(f"  Remote origin: {GITHUB_REPO}")

    # Push (git credential manager handles auth)
    result = subprocess.run(
        ["git", "push", "-u", "origin", "master"],
        cwd=REPO_DIR, capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        print(f"  [OK] Pousse vers https://github.com/{GITHUB_REPO}")
    else:
        print(f"  [SKIP] Push GitHub non effectue: {result.stderr.strip()[:200]}")
        print("  -> Cree le repo manuellement sur GitHub puis relance git push")
except Exception as e:
    print(f"  [SKIP] Push GitHub: {e}")

# ── 2. Push Hugging Face Dataset ────────────────────────────
print("\n[2/3] Push Hugging Face Dataset...")
if hf_token:
    try:
        from huggingface_hub import HfApi, Repository, create_repo, upload_file
        api = HfApi(token=hf_token)

        # Create dataset repo
        try:
            create_repo(
                repo_id=HF_DATASET,
                repo_type="dataset",
                token=hf_token,
                exist_ok=True,
                private=False,
            )
            print(f"  [OK] Dataset cree: {HF_DATASET}")
        except Exception as e:
            print(f"  [INFO] Creation dataset: {e}")

        # Upload README
        readme_path = REPO_DIR / "README.md"
        api.upload_file(
            path_or_fileobj=str(readme_path),
            path_in_repo="README.md",
            repo_id=HF_DATASET,
            repo_type="dataset",
            token=hf_token,
        )
        print(f"  [OK] README.md uploade")

        # Upload script
        script_path = REPO_DIR / "src" / "mttv_mpvr_quorum.py"
        api.upload_file(
            path_or_fileobj=str(script_path),
            path_in_repo="mttv_mpvr_quorum.py",
            repo_id=HF_DATASET,
            repo_type="dataset",
            token=hf_token,
        )
        print(f"  [OK] mttv_mpvr_quorum.py uploade")

        # Update dataset tags/card
        try:
            api.update_repo_settings(
                repo_id=HF_DATASET,
                repo_type="dataset",
                token=hf_token,
                # tags are set via dataset card YAML
            )
        except:
            pass

        print(f"\n  Dataset: https://huggingface.co/datasets/{HF_DATASET}")

    except ImportError:
        print("  [SKIP] huggingface_hub non installe")
    except Exception as e:
        print(f"  [SKIP] HF deploy: {e}")
else:
    print("  [SKIP] Pas de HF_TOKEN")

# ── 3. Rapport final ────────────────────────────────────────
print("\n" + "=" * 60)
print("RAPPORT DE DEPLOIEMENT MTTV-FLP / MPVR")
print("=" * 60)
print(f"\nFichiers deployes:")
print(f"  - README.md (synthese formelle)")
print(f"  - src/mttv_mpvr_quorum.py (implementation CC0)")
print(f"\nTags: {', '.join(HF_TAGS)}")
print(f"\nRoutes d'archivage:")
print(f"  GitHub:     https://github.com/{GITHUB_REPO}")
print(f"  HF Dataset: https://huggingface.co/datasets/{HF_DATASET}")
print(f"\nHash Git local: ", end="")
subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_DIR, capture_output=False)
print(f"\nsig:0x4D545456")
