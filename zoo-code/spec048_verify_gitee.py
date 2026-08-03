#!/usr/bin/env python3
"""Vérifie que les 4 fichiers SPEC-048 existent sur Gitee (branche evolution/tetravalent-core).

Le paramètre branch doit être passé en query string pour les requêtes GET Gitee.
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_spec048_diffusion import get_gitee_token  # noqa: E402

FILES = ["README.md", "PREPRINT_SPEC_048.md", "wiki/PREPRINT_SPEC_048.md", "zoo-code/PREPRINT_SPEC_048.md"]
BRANCH = "evolution/tetravalent-core"
GITEE_API = "https://gitee.com/api/v5"


def get_contents(rel_path: str):
    token = get_gitee_token()
    if not token:
        return None
    url = (
        f"{GITEE_API}/repos/girard/mttv-flp-core/contents/{urllib.parse.quote(rel_path)}"
        f"?access_token={urllib.parse.quote(token)}&branch={urllib.parse.quote(BRANCH)}"
    )
    req = urllib.request.Request(url, method="GET")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"    ! HTTP {e.code} : {e.read().decode('utf-8', 'replace')[:120]}")
        return None
    except Exception as e:
        print(f"    ! {ascii(e)}")
        return None


print(f"Vérification Gitee girard/mttv-flp-core @ {BRANCH}")
for f in FILES:
    r = get_contents(f)
    if r and "sha" in r:
        print(f"  [OK] {f}  size={r.get('size')}  sha={r['sha'][:12]}...")
    else:
        print(f"  [FAIL] {f}")

print("sig:0x4D5454562D464C50")
