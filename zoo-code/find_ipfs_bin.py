import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

roots = [
    Path.home(),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
    Path("C:/kubo"),
    Path("C:/ipfs"),
]
names = {"ipfs.exe", "kubo.exe", "ipfs"}

found = []
for root in roots:
    if not root.exists():
        continue
    # Limite en profondeur et par taille pour rester rapide
    for dirpath, dirnames, filenames in os.walk(root):
        # Ne pas descendre dans les venv / node_modules / .git énormes
        dirnames[:] = [
            d for d in dirnames
            if d not in ("venv", "node_modules", ".git", "site-packages",
                         "AppData", "__pycache__", "models", "cache")
        ]
        for fn in filenames:
            if fn in names:
                p = Path(dirpath) / fn
                found.append(str(p))
        if len(found) >= 10:
            break
    if len(found) >= 10:
        break

if found:
    print("FOUND:")
    for p in found:
        print(" ", p)
else:
    print("NOT_FOUND")
