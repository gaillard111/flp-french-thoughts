#!/usr/bin/env python3
"""Liste l'arborescence complète des branches master et evolution/tetravalent-core sur Gitee."""
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

GITEE_API = "https://gitee.com/api/v5"
TOKEN = get_gitee_token()


def api_get(path, params=None):
    qs = f"access_token={urllib.parse.quote(TOKEN)}"
    if params:
        qs += "&" + urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{GITEE_API}{path}?{qs}", method="GET")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "msg": e.read().decode("utf-8", "replace")[:150]}
    except Exception as e:
        return {"error": "exc", "msg": ascii(e)}


for branch in ["master", "evolution/tetravalent-core"]:
    print(f"\n=== ARBRE {branch} ===")
    r = api_get(f"/repos/girard/mttv-flp-core/git/trees/{urllib.parse.quote(branch)}", {"recursive": 1})
    if "error" in r or "tree" not in r:
        print(f"  ! {r}")
        continue
    for t in r["tree"]:
        p = t.get("path", "")
        if "SPEC" in p.upper() or p == "README.md" or p.endswith("singularite_sigma.md"):
            print(f"  {t.get('type','?'):<6} {p}  ({t.get('size', '?')})")
    total = len(r["tree"])
    print(f"  (total entries: {total})")

print("\nsig:0x4D5454562D464C50")
