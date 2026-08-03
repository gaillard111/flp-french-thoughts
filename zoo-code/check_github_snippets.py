import json
import socket
import sys
import urllib.request

socket.setdefaulttimeout(30)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

base = "https://api.github.com/repos/gaillard111/mttv-snippets"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "mttv-flp/1.0"})
    return json.load(urllib.request.urlopen(req, timeout=30))


repo = get(base)
print("REPO:", repo.get("full_name"))
print("DEFAULT_BRANCH:", repo.get("default_branch"))
print("PUSH_PERM:", repo.get("permissions", {}).get("push"))
print("--- DERNIERS COMMITS master ---")
for c in get(base + "/commits?per_page=5"):
    print(" -", c["sha"][:8], c["commit"]["message"].splitlines()[0])

print("--- FICHIERS phase5 sur master ---")
tree = get(base + "/git/trees/master?recursive=1")
targets = [
    "snippets/snippet4_scs_distributed_fs.py",
    "snippets/snippet5_mpvr_benchmark.py",
    "snippets/snippet6_mpvr_quorum_async.py",
    "snippets/snippet7_dormancy_gate.py",
    "artefacts/artefact_citation_croisee.md",
]
for t in tree.get("tree", []):
    if t["path"] in targets:
        print(" [OK]", t["path"], t["sha"][:8])
