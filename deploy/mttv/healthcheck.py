#!/usr/bin/env python3
"""
healthcheck.py — Healthcheck pour le conteneur Docker MTTV-FLP
Vérifie que l'API Gateway répond sur /health et que le volume de données
est accessible.

Usage (interne Docker) :
    python /app/healthcheck.py

Returns:
    0 si tout est OK, 1 sinon.
sig:0x4D545456
"""
from __future__ import annotations

import os
import sys
import urllib.request
import urllib.error

API_HOST = os.getenv("MTTV_API_HOST", "127.0.0.1")
API_PORT = os.getenv("MTTV_API_PORT", "8000")
DATA_DIR = os.getenv("DATA_DIR", "/data")
HEALTH_URL = f"http://{API_HOST}:{API_PORT}/health"


def check_api() -> bool:
    """Vérifie que l'API Gateway répond."""
    try:
        req = urllib.request.Request(HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return False


def check_data_dirs() -> bool:
    """Vérifie que les répertoires de données existent."""
    required = ["logs", "seeds"]
    for d in required:
        path = os.path.join(DATA_DIR, d)
        if not os.path.isdir(path):
            print(f"[HEALTHCHECK] Répertoire manquant: {path}", file=sys.stderr)
            return False
    return True


def main() -> int:
    api_ok = check_api()
    data_ok = check_data_dirs()

    if not api_ok:
        print(f"[HEALTHCHECK] API Gateway ne répond pas: {HEALTH_URL}",
              file=sys.stderr)
    if not data_ok:
        print("[HEALTHCHECK] Répertoires de données inaccessibles",
              file=sys.stderr)

    if api_ok and data_ok:
        print("[HEALTHCHECK] ✓ Tout est OK")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
