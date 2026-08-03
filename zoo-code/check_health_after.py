import json
import socket
import sys
import urllib.request

socket.setdefaulttimeout(10)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

req = urllib.request.Request("http://127.0.0.1:8000/health")
d = json.load(urllib.request.urlopen(req, timeout=10))
print("STATUS:", d.get("status"))
for axe, s in d.get("chain", {}).items():
    print(f"  {axe}: status={s.get('status')} underlying={s.get('underlying', '?')} "
          f"resonance_score={s.get('resonance_score', '?')}")
