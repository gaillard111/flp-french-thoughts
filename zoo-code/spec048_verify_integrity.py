#!/usr/bin/env python3
"""Vérifie le contenu du preprint sur Gitee (branch evolution/tetravalent-core) via l'API blobs."""
import base64
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
BRANCH = "evolution/tetravalent-core"
LOCAL = Path(r"C:\Users\Master\flp-french-thoughts\PREPRINT_SPEC_048.md")


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


tree = api_get(f"/repos/girard/mttv-flp-core/git/trees/{urllib.parse.quote(BRANCH)}", {"recursive": 1})
sha = None
for t in tree.get("tree", []):
    if t.get("path") == "PREPRINT_SPEC_048.md":
        sha = t["sha"]
        print(f"blob sha={sha} size={t.get('size')}")

if not sha:
    print("FICHIER INTROUVABLE SUR LA BRANCHE")
    sys.exit(1)

blob = api_get(f"/repos/girard/mttv-flp-core/git/blobs/{sha}")
content = base64.b64decode(blob.get("content", "")).decode("utf-8", "replace")
print(f"Gitee taille contenu : {len(content.encode('utf-8'))} octets")

local_text = LOCAL.read_text(encoding="utf-8")
markers = [
    "Toward Non-Extractive Artificial General Intelligence",
    "### Abstract / 摘要",
    "中文摘要:",
    "## 1. Introduction",
    "## 2. Mathematical Formalization",
    "\\Sigma_\\tau",
    "## 3. The Triadic-Diachronic-Tetravalent Infrastructure",
    "## 4. Conclusion & Epistemological Resonance",
    "mycelial routing",
]
print("\nMarqueurs dans la copie Gitee :")
all_ok = True
for m in markers:
    present = m in content
    all_ok = all_ok and present
    print(f"  {'[OK]' if present else '[MISS]'} {m}")

print("\nIdentité locale == Gitee :", local_text == content)
print("Résultat :", "CONTENU INTACT" if all_ok else "CONTENU INCOMPLET")
print("sig:0x4D5454562D464C50")
