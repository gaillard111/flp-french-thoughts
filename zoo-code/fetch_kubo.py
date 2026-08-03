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

# Récupérer la dernière version stable de kubo (IPFS) depuis GitHub
url = "https://api.github.com/repos/ipfs/kubo/releases/latest"
req = urllib.request.Request(url, headers={"User-Agent": "mttv-flp/1.0"})
try:
    data = json.load(urllib.request.urlopen(req, timeout=30))
    print("TAG:", data.get("tag_name"))
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if "windows-amd64" in name and name.endswith(".zip"):
            print("ASSET:", name)
            print("URL:", asset.get("browser_download_url"))
            print("SIZE:", asset.get("size"))
            break
except Exception as e:
    print("ERR", type(e).__name__, str(e)[:200])
