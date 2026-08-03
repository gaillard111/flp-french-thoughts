import socket
import urllib.request
import sys

socket.setdefaulttimeout(10)


def check(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "mttv-flp/1.0"})
        r = urllib.request.urlopen(req, timeout=10)
        return f"OK {r.status}"
    except Exception as e:
        return f"{type(e).__name__}: {str(e)[:120]}"


for url in [
    "https://huggingface.co/api/whoami-v2",
    "https://huggingface.co/api/datasets/girard444/mttv-energy-flow-optimization",
    "https://api.github.com/repos/gaillard111/mttv-snippets",
]:
    print(url, "->", check(url))
    sys.stdout.flush()
