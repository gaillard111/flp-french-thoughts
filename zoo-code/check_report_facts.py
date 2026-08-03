import socket
import sys
import urllib.request

socket.setdefaulttimeout(5)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

targets = [
    ("API Gateway :8000", "http://127.0.0.1:8000/"),
    ("axe_5_ipfs :5001 (kubo)", "http://127.0.0.1:5001/api/v0/version"),
]
for name, url in targets:
    try:
        req = urllib.request.Request(url, method="POST" if "api/v0" in url else "GET")
        r = urllib.request.urlopen(req, timeout=5)
        print(f"[OK]   {name} -> HTTP {r.status}")
    except Exception as e:
        print(f"[NON]  {name} -> {type(e).__name__}: {str(e)[:80]}")
