import json
import socket
import sys
import urllib.request
from pathlib import Path

socket.setdefaulttimeout(5)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 1. Config kubo
cfg_path = Path.home() / ".ipfs" / "config"
print("=== Config IPFS (.ipfs/config) ===")
if cfg_path.exists():
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    addr = cfg.get("Addresses", {})
    print("  API:", addr.get("API"))
    print("  Gateway:", addr.get("Gateway"))
    print("  Identity.PeerID:", cfg.get("Identity", {}).get("PeerID", "")[:20] + "...")
else:
    print("  config absent")

# 2. Daemon sur 127.0.0.1:5001
print("\n=== Daemon IPFS ===")
try:
    req = urllib.request.Request("http://127.0.0.1:5001/api/v0/version", method="POST")
    r = urllib.request.urlopen(req, timeout=5)
    print("  DAEMON OK:", r.read().decode()[:200])
except Exception as e:
    print("  DAEMON ABSENT:", type(e).__name__, str(e)[:100])

# 3. Gateway IPFS public (test connectivite)
print("\n=== Gateway IPFS public ===")
try:
    r = urllib.request.urlopen("https://ipfs.io/ipfs/QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG", timeout=8)
    print("  GATEWAY OK:", r.status)
except Exception as e:
    print("  GATEWAY:", type(e).__name__, str(e)[:100])
