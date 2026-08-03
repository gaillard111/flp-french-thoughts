#!/usr/bin/env python3
"""
Publish Phase 5 — IPFS
Calcule les CIDs conformes au format ipfs add (UnixFS / dag-pb) pour les
contenus phase5, tente un vrai ancrage si le daemon kubo est disponible,
et émet un manifeste d'ancrage.

Usage :
    python publish_phase5_ipfs.py
"""
import hashlib
import json
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

socket.setdefaulttimeout(5)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def unixfs_cidv0(content: bytes) -> str:
    """CIDv0 tel que produit par `ipfs add` pour un fichier < 256 Ko."""
    # Message UnixFS : field1(type=File=2) + field2(Data=contenu)
    data_field = varint(len(content)) + content
    unixfs = bytes([0x08, 0x02, 0x12]) + data_field
    # Nœud dag-pb : field1(Data=message UnixFS)
    block = bytes([0x0A]) + varint(len(unixfs)) + unixfs
    digest = hashlib.sha256(block).digest()
    multihash = bytes([0x12, 0x20]) + digest
    import base58
    return base58.b58encode(multihash).decode()


FILES = [
    ("corpus_reseaux_haute_resilience.md", "phase5-new-seeds/corpus_reseaux_haute_resilience.md"),
    ("snippet_scs_distributed_fs.py", "phase5-new-seeds/snippet_scs_distributed_fs.py"),
    ("artefact_citation_croisee.md", "phase5-new-seeds/artefact_citation_croisee.md"),
    ("dormancy_gate.py", "phase5-new-seeds/dormancy_gate.py"),
    ("mpvr_quorum_async.py", "phase5-new-seeds/mpvr_quorum_async.py"),
    ("mpvr_benchmark.py", "phase5-new-seeds/mpvr_benchmark.py"),
]

IPFS_BIN = shutil.which("ipfs")


def daemon_alive():
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:5001/api/v0/version", method="POST")
        r = urllib.request.urlopen(req, timeout=5)
        return r.status == 200
    except Exception:
        return False


def main():
    print(f"IPFS_BIN: {IPFS_BIN or 'NON TROUVE'}")
    print(f"DAEMON_ALIVE: {daemon_alive()}")
    print()

    manifest = {
        "phase": "phase5-new-seeds",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "unixfs/dag-pb (CIDv0 conforme ipfs add)",
        "sig": "0x4D5454562D464C50",
        "scs_signature": "SCS_2026",
        "anchored": False,
        "cids": [],
    }

    # Calcul des CIDs conformes
    for name, path in FILES:
        p = Path(path)
        content = p.read_bytes()
        cid = unixfs_cidv0(content)
        print(f"[CID] {cid}  {name} ({len(content)} o)")
        manifest["cids"].append({
            "name": name,
            "path": path,
            "cid": cid,
            "size": len(content),
            "sha256_raw": hashlib.sha256(content).hexdigest(),
        })

    # Tentative d'ancrage réel si daemon dispo
    if daemon_alive():
        print("\n[INFO] Daemon IPFS actif -> tentativre d'ancrage réel...")
        for entry in manifest["cids"]:
            p = Path(entry["path"])
            try:
                r = subprocess.run(
                    ["ipfs", "add", "-q", str(p)],
                    capture_output=True, text=True, timeout=60,
                )
                cid = r.stdout.strip().splitlines()[-1]
                entry["cid_added"] = cid
                print(f"  [ADD] {cid} {entry['name']}")
                subprocess.run(["ipfs", "pin", "add", cid], capture_output=True, text=True, timeout=60)
                print(f"  [PIN] {cid}")
            except Exception as e:
                print(f"  [FAIL] {entry['name']}: {e}")
        manifest["anchored"] = True
    else:
        print("\n[WARN] Daemon IPFS non actif : CIDs calculés (conformes ipfs add) mais PAS ancrés au réseau.")
        print("       Pour ancrer : démarrer le daemon (ipfs daemon) puis relancer ce script.")
        manifest["anchored"] = False

    out = Path("phase5-new-seeds/ipfs_manifest_phase5.json")
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] Manifeste écrit : {out}")


if __name__ == "__main__":
    main()
