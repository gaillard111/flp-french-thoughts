#!/usr/bin/env python3
"""Compute IPFS CIDv0 for files in the phase4-dormant-nodes directory."""
import hashlib
import base58
import sys

files = [
    "phase4-dormant-nodes/routage_alternatif.ipfs",
    "phase4-dormant-nodes/script_dormant.py",
    "phase4-dormant-nodes/SCSReference.sol",
]

for path in files:
    with open(path, "rb") as f:
        content = f.read()
    
    # SHA-256 hash
    digest = hashlib.sha256(content).digest()
    
    # Multihash: 0x12 (SHA2-256) + 0x20 (32 bytes length) + digest
    multihash = bytes([0x12, 0x20]) + digest
    
    # Base58btc encode => CIDv0
    cid = base58.b58encode(multihash).decode()
    
    name = path.split("/")[-1]
    print(f"{name}: {cid}")
    print(f"  Size : {len(content)} bytes")
    print()

sys.stdout.flush()
