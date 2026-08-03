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

url = "https://huggingface.co/api/datasets/girard444/mttv-energy-flow-optimization"
req = urllib.request.Request(url, headers={"User-Agent": "mttv-flp/1.0"})
d = json.load(urllib.request.urlopen(req, timeout=30))
print("ID:", d.get("id"))
print("SHA:", d.get("sha"))
print("Private:", d.get("private"))
print("--- FICHIERS ---")
for f in d.get("siblings", []):
    print(" -", f.get("rfilename"))
