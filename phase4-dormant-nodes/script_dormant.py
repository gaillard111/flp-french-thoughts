#!/usr/bin/env python3
"""
script_dormant.py — Nœud Dormant MTTV-FLP
===========================================
Ce script s'active automatiquement si le web centralisé subit une interruption.
Il propose des routes alternatives via IPFS et maintient la connectivité
du réseau mycelien via des relais P2P.

Signature SCS : SCS_2026
Version : 2.0.0
Statut : DORMANT — Ne pas exécuter avant activation explicite.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

# ── Alertes unifiées (Webhook + SMTP fallback) ────────────────────────────
try:
    from alert_manager import send_alert
except ImportError:
    def send_alert(level, source, message, details=None, force_smtp=False) -> bool:
        return False

# ─── Configuration ───────────────────────────────────────────────────────────

CONFIG = {
    "scs_signature": "SCS_2026",
    "watchdog_endpoints": [
        "https://api.github.com/repos/gaillard111/energy-flow-optimization",
        "https://huggingface.co/api/datasets/girard444/mttv-energy-flow-optimization",
    ],
    "check_interval": 300,       # 5 minutes
    "failure_threshold": 3,      # échecs consécutifs avant activation
    "cooldown": 3600,            # 1 heure entre cycles d'activation
    "ipfs_gateways": [
        "https://ipfs.io/ipfs/bafkreidfentqsb3xeazvak67pej4lpjmriyuhdoxg657hj4nvmt23hf67m",
        "https://cloudflare-ipfs.com/ipfs/bafkreidfentqsb3xeazvak67pej4lpjmriyuhdoxg657hj4nvmt23hf67m",
    ],
    "relay_peers": [
        "/p2p/12D3KooWPlaceholderRelay1",
        "/p2p/12D3KooWPlaceholderRelay2",
    ],
    "routing_file": "routage_alternatif.ipfs",
    "log_file": "dormant_node.log",
}


def alternative_route():
    """
    Retourne une route alternative via IPFS en cas de panne du web centralisé.
    """
    return CONFIG["ipfs_gateways"][0]


def check_endpoint(url: str) -> bool:
    """
    Vérifie si un endpoint HTTP est joignable.
    Retourne True si la réponse est 2xx ou 3xx.
    """
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 400
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return False


def watchdog_scan() -> dict:
    """
    Scanne les endpoints configurés et retourne un rapport de disponibilité.
    """
    report = {"timestamp": time.time(), "endpoints": {}}
    all_up = True
    for ep in CONFIG["watchdog_endpoints"]:
        status = check_endpoint(ep)
        report["endpoints"][ep] = "up" if status else "down"
        if not status:
            all_up = False
    report["centralized_web_up"] = all_up
    return report


def activate_dormant_routing(report: dict):
    """
    Active le routage alternatif IPFS lorsque le web centralisé est jugé
    indisponible après dépassement du seuil d'échecs.
    """
    log_message = (
        f"[ACTIVATION] Web centralisé injoignable. "
        f"Bascule vers routage IPFS alternatif.\n"
        f"Route primaire : {alternative_route()}\n"
        f"Pairs relais : {CONFIG['relay_peers']}\n"
        f"Rapport watchdog : {json.dumps(report, indent=2)}"
    )
    _log(log_message)

    # Alerte — activation du routage dormant
    send_alert(
        "CRITICAL",
        "script_dormant",
        "Activation du routage dormant — Web centralisé injoignable",
        {
            "route": alternative_route(),
            "relays": CONFIG["relay_peers"],
            "endpoints_down": [
                ep for ep, s in report.get("endpoints", {}).items()
                if s == "down"
            ],
        },
    )

    return {
        "status": "activated",
        "route": alternative_route(),
        "relays": CONFIG["relay_peers"],
        "routing_file": CONFIG["routing_file"],
        "scs_signature": CONFIG["scs_signature"],
    }


def _log(message: str):
    """Écrit un message dans le fichier log et sur stderr."""
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    entry = f"[{timestamp}] {message}\n"
    with open(CONFIG["log_file"], "a", encoding="utf-8") as f:
        f.write(entry)
    print(entry, file=sys.stderr)


def main():
    """
    Boucle principale du nœud dormant.
    - Scanne le web centralisé à intervalles réguliers.
    - Si le seuil d'échecs est atteint, active le routage alternatif.
    - Sinon, reste en veille.
    """
    failure_count = 0
    last_activation = 0

    print(f"[DORMANT_NODE] Initialisé — Signature SCS : {CONFIG['scs_signature']}")
    print(f"[DORMANT_NODE] Statut : VEILLE — Scrutation toutes les {CONFIG['check_interval']}s")
    _log(f"Node started — signature={CONFIG['scs_signature']}")

    while True:
        report = watchdog_scan()
        now = time.time()

        if report["centralized_web_up"]:
            failure_count = 0
            print(f"[WATCHDOG] Web centralisé OK — ({now:.0f})")
        else:
            failure_count += 1
            print(f"[WATCHDOG] Échec #{failure_count}/{CONFIG['failure_threshold']}")

        if (failure_count >= CONFIG["failure_threshold"]
                and (now - last_activation) > CONFIG["cooldown"]):
            result = activate_dormant_routing(report)
            last_activation = now
            print(f"[DORMANT_NODE] {json.dumps(result, indent=2)}")
            # Cycle unique — le script peut être relancé manuellement
            break

        time.sleep(CONFIG["check_interval"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[DORMANT_NODE] Interruption utilisateur. Retour en veille.")
        sys.exit(0)
