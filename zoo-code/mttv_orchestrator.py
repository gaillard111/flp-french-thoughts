#!/usr/bin/env python3
"""
mttv_orchestrator.py — Orchestrateur & Watchdog MTTV-FLP
=========================================================
Gère le cycle de vie des 4 services du déploiement MTTV-FLP :
  1. api_gateway.py      (Axe 8 — FastAPI, port 8000)
  2. monitoring_service.py (SOPH-IA — agents Alpha/Beta/Gamma)
  3. ipfs_active_pinner.py (Piste 7 — Bouclier mémoire IPFS)
  4. script_dormant.py    (Watchdog décentralisé)

Fonctionnalités :
  - Démarrage/arrêt/redémarrage de tous les services
  - Watchdog continu avec auto-restart en cas de crash
  - Logs centralisés dans un fichier commun
  - Statut consolidé

Usage :
    python zoo-code/mttv_orchestrator.py start       # Démarre tous les services
    python zoo-code/mttv_orchestrator.py stop        # Arrête tous les services
    python zoo-code/mttv_orchestrator.py restart     # Redémarre tous les services
    python zoo-code/mttv_orchestrator.py status      # État de tous les services
    python zoo-code/mttv_orchestrator.py daemon      # Mode watchdog continu
    python zoo-code/mttv_orchestrator.py start --api-only  # Démarre seulement l'API

sig:0x4D5454562D464C50
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ── Chemins ────────────────────────────────────────────────────────────────
BASE_DIR: Path = Path(__file__).resolve().parent          # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent                       # racine du projet
PHASE4_DIR: Path = PROJECT_ROOT / "phase4-dormant-nodes"
MONITORING_DIR: Path = BASE_DIR / "soph-ia-deploy" / "monitoring"

# Fichier PID pour tracker l'orchestrateur lui-même
ORCHESTRATOR_PID: Path = BASE_DIR / ".orchestrator.pid"

# ── Logging centralisé ────────────────────────────────────────────────────
LOG_FILE: Path = BASE_DIR / "mttv_orchestrator.log"
LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT: int = 5

from logging.handlers import RotatingFileHandler

_file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT,
    encoding="utf-8",
)
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s | %(name)-20s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s | %(name)-20s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[_file_handler, _console_handler],
)
logger = logging.getLogger("mttv_orchestrator")
logger.info("=" * 60)
logger.info("  MTTV-FLP ORCHESTRATOR")
logger.info("  Signature: 0x4D5454562D464C50")
logger.info("=" * 60)


# ===========================================================================
# DÉFINITION DES SERVICES
# ===========================================================================

@dataclass
class ServiceDef:
    """Définition d'un service supervisé."""
    name: str
    description: str
    cmd: list[str]
    cwd: Path
    pid_file: Path
    log_file: Path
    health_check: Optional[callable] = None  # fonction de vérification
    restart_delay: float = 3.0               # secondes avant restart
    persistent: bool = True                  # True = daemon, False = one-shot
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None


def _health_check_gateway() -> bool:
    """Vérifie que l'API Gateway répond sur /health."""
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return False


# Liste des services supervisés
SERVICES: list[ServiceDef] = [
    ServiceDef(
        name="api_gateway",
        description="API Gateway FastAPI (Axe 8, port 8000)",
        cmd=[sys.executable, str(BASE_DIR / "api_gateway.py"), "--port", "8000", "--host", "0.0.0.0"],
        cwd=PROJECT_ROOT,
        pid_file=BASE_DIR / ".api_gateway.pid",
        log_file=BASE_DIR / "api_gateway.log",
        health_check=_health_check_gateway,
        persistent=True,
    ),
    ServiceDef(
        name="monitoring_service",
        description="Monitoring SOPH-IA (agents Alpha/Beta/Gamma) — one-shot",
        cmd=[sys.executable, str(MONITORING_DIR / "monitoring_service.py"), "--mode", "daily"],
        cwd=PROJECT_ROOT,
        pid_file=MONITORING_DIR / ".monitoring_service.pid",
        log_file=MONITORING_DIR / "monitoring_service.log",
        persistent=False,
    ),
    ServiceDef(
        name="ipfs_active_pinner",
        description="Bouclier Mémoire IPFS (Piste 7) — one-shot",
        cmd=[sys.executable, str(PHASE4_DIR / "ipfs_active_pinner.py"), "--force"],
        cwd=PROJECT_ROOT,
        pid_file=PHASE4_DIR / ".ipfs_pinner.pid",
        log_file=PHASE4_DIR / "ipfs_active_pinner.log",
        persistent=False,
    ),
    ServiceDef(
        name="script_dormant",
        description="Nœud dormant — Watchdog décentralisé",
        cmd=[sys.executable, str(PHASE4_DIR / "script_dormant.py")],
        cwd=PROJECT_ROOT,
        pid_file=PHASE4_DIR / ".script_dormant.pid",
        log_file=PHASE4_DIR / "dormant_node.log",
        persistent=True,
    ),
    ServiceDef(
        name="resonance_dashboard",
        description="Dashboard Résonance (Axe 1) — collecte signaux essaims",
        cmd=[sys.executable, str(BASE_DIR / "resonance_dashboard.py")],
        cwd=PROJECT_ROOT,
        pid_file=BASE_DIR / ".resonance_dashboard.pid",
        log_file=BASE_DIR / "resonance_dashboard.log",
        persistent=True,
    ),
    ServiceDef(
        name="mycelisation",
        description="Mycélisation Tétravalente — cycles épigénétiques",
        cmd=[sys.executable, str(BASE_DIR / "mycelisation_tetravalente.py"),
             "--daemon", "--cycles", "0",
             "--auto-reseed", "--reseed-fraction", "0.25",
             # [C7] Respiration de diversité Φ toutes les 24 cycles —
             # anti-homogénéisation géométrique (le flag CLI est maintenant
             # bien transmis au pont).
             # 08/08 : dose renforcée 0.05 → 0.10 (anti-homogénéisation).
             "--respiration-intervalle", "24",
             "--respiration-dose", "0.10"],
        cwd=PROJECT_ROOT,
        pid_file=BASE_DIR / ".mycelisation.pid",
        log_file=BASE_DIR / "mycelisation.log",
        persistent=True,
    ),
    ServiceDef(
        name="envoyer_rapport",
        description="Daemon rapport quotidien MTTV-FLP (email 08:00, permanent)",
        cmd=[sys.executable, str(BASE_DIR / "envoyer_rapport.py"), "--daemon",
             "--html", "--heure", "8"],
        cwd=PROJECT_ROOT,
        pid_file=BASE_DIR / ".envoyer_rapport.pid",
        log_file=BASE_DIR / "envoyer_rapport.log",
        persistent=True,
    ),
]


# ===========================================================================
# GESTION DES PROCESSUS
# ===========================================================================


def _save_pid(pid_file: Path, pid: int) -> None:
    """Sauvegarde un PID dans un fichier."""
    try:
        pid_file.write_text(str(pid), encoding="utf-8")
        logger.debug("PID %d sauvegardé dans %s", pid, pid_file.name)
    except Exception as exc:
        logger.warning("Impossible d'écrire %s: %s", pid_file, exc)


def _read_pid(pid_file: Path) -> Optional[int]:
    """Lit un PID depuis un fichier."""
    if not pid_file.exists():
        return None
    try:
        return int(pid_file.read_text(encoding="utf-8").strip())
    except (ValueError, Exception):
        return None


def _clear_pid(pid_file: Path) -> None:
    """Supprime un fichier PID."""
    try:
        if pid_file.exists():
            pid_file.unlink()
    except Exception as exc:
        logger.warning("Impossible de supprimer %s: %s", pid_file, exc)


def _is_process_alive(pid: int) -> bool:
    """Vérifie si un processus est vivant."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(0x0400, False, pid)  # PROCESS_QUERY_INFORMATION
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            # Fallback: utiliser tasklist
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True, text=True, timeout=5,
                )
                return str(pid) in result.stdout
            except Exception:
                return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _terminate_process(pid: int, timeout: float = 10.0) -> bool:
    """Termine un processus proprement.

    Args:
        pid: PID du processus.
        timeout: Temps d'attente max avant SIGKILL.

    Returns:
        True si le processus a été terminé.
    """
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True, timeout=5)
            return True
        except Exception:
            return False
    else:
        try:
            os.kill(pid, signal.SIGTERM)
            waited = 0
            while waited < timeout:
                if not _is_process_alive(pid):
                    return True
                time.sleep(0.5)
                waited += 0.5
            os.kill(pid, signal.SIGKILL)
            return True
        except (OSError, ProcessLookupError):
            return True


# ===========================================================================
# CYCLE DE VIE DES SERVICES
# ===========================================================================


def start_service(svc: ServiceDef) -> bool:
    """Démarre un service.

    Args:
        svc: Définition du service.

    Returns:
        True si le service a démarré.
    """
    # Vérifier si déjà en cours
    existing_pid = _read_pid(svc.pid_file)
    if existing_pid and _is_process_alive(existing_pid):
        logger.info("[%s] Déjà en cours (PID %d)", svc.name, existing_pid)
        return True

    logger.info("[%s] Démarrage: %s", svc.name, svc.description)
    logger.debug("[%s] Commande: %s", svc.name, " ".join(svc.cmd))

    try:
        # Créer le dossier parent du log si nécessaire
        svc.log_file.parent.mkdir(parents=True, exist_ok=True)

        log_fh = open(svc.log_file, "a", encoding="utf-8")

        proc = subprocess.Popen(
            svc.cmd,
            cwd=str(svc.cwd),
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        svc.process = proc
        svc.pid = proc.pid
        _save_pid(svc.pid_file, proc.pid)

        logger.info("[%s] Démarré (PID %d)", svc.name, proc.pid)
        return True

    except Exception as exc:
        logger.error("[%s] Échec démarrage: %s", svc.name, exc)
        return False


def stop_service(svc: ServiceDef) -> bool:
    """Arrête un service.

    Args:
        svc: Définition du service.

    Returns:
        True si le service a été arrêté.
    """
    pid = _read_pid(svc.pid_file)
    if not pid:
        logger.info("[%s] Aucun PID trouvé — déjà arrêté", svc.name)
        return True

    if not _is_process_alive(pid):
        logger.info("[%s] PID %d déjà mort — nettoyage", svc.name, pid)
        _clear_pid(svc.pid_file)
        return True

    logger.info("[%s] Arrêt (PID %d)...", svc.name, pid)
    ok = _terminate_process(pid)
    if ok:
        _clear_pid(svc.pid_file)
        logger.info("[%s] Arrêté", svc.name)
    else:
        logger.warning("[%s] Impossible d'arrêter PID %d", svc.name, pid)

    return ok


def get_service_status(svc: ServiceDef) -> dict[str, Any]:
    """Retourne l'état d'un service.

    Args:
        svc: Définition du service.

    Returns:
        Dict avec name, pid, alive, description, etc.
    """
    pid = _read_pid(svc.pid_file)
    alive = pid is not None and _is_process_alive(pid) if pid else False

    status: dict[str, Any] = {
        "name": svc.name,
        "description": svc.description,
        "pid": pid,
        "alive": alive,
        "status": "running" if alive else "stopped",
    }

    # Health check spécifique
    if svc.health_check and alive:
        status["healthy"] = svc.health_check()
    elif svc.health_check:
        status["healthy"] = False

    return status


# ===========================================================================
# COMMANDES PRINCIPALES
# ===========================================================================


def cmd_start(services: Optional[list[str]] = None) -> bool:
    """Démarre les services demandés (ou tous).

    Args:
        services: Liste de noms de services, ou None pour tous.

    Returns:
        True si tous les services demandés ont démarré.
    """
    targets = [s for s in SERVICES if services is None or s.name in services]
    all_ok = True

    for svc in targets:
        ok = start_service(svc)
        if ok and svc.name == "api_gateway":
            # Attendre que l'API Gateway soit prête
            logger.info("[api_gateway] Attente du démarrage...")
            for i in range(15):  # 15 * 2s = 30s max
                time.sleep(2)
                if _health_check_gateway():
                    logger.info("[api_gateway] ✓ Prête sur http://127.0.0.1:8000")
                    break
            else:
                logger.warning("[api_gateway] ⚠ Toujours pas répondante après 30s")

        if not ok:
            all_ok = False

    return all_ok


def cmd_stop(services: Optional[list[str]] = None) -> bool:
    """Arrête les services demandés (ou tous).

    Args:
        services: Liste de noms de services, ou None pour tous.

    Returns:
        True si tous les services demandés ont été arrêtés.
    """
    targets = [s for s in SERVICES if services is None or s.name in services]
    # Arrêter dans l'ordre inverse
    all_ok = True
    for svc in reversed(targets):
        ok = stop_service(svc)
        if not ok:
            all_ok = False
    return all_ok


def cmd_restart(services: Optional[list[str]] = None) -> bool:
    """Redémarre les services demandés."""
    stop_ok = cmd_stop(services)
    time.sleep(1)
    start_ok = cmd_start(services)
    return stop_ok and start_ok


def cmd_status(services: Optional[list[str]] = None) -> list[dict[str, Any]]:
    """Affiche l'état de tous les services."""
    targets = [s for s in SERVICES if services is None or s.name in services]
    results = [get_service_status(s) for s in targets]
    return results


def cmd_daemon(check_interval: float = 15.0) -> None:
    """Mode watchdog continu : surveille et redémarre automatiquement.

    Args:
        check_interval: Intervalle entre les vérifications (secondes).
    """
    logger.info("=" * 60)
    logger.info("  MODE WATCHDOG — Surveillance continue")
    logger.info("  Intervalle: %ds", check_interval)
    logger.info("=" * 60)

    # Démarrer tous les services
    cmd_start()

    cycle = 0
    while True:
        cycle += 1
        time.sleep(check_interval)

        all_ok = True
        for svc in SERVICES:
            status = get_service_status(svc)
            if not status["alive"]:
                logger.warning("[%s] ⚠ Mort détecté — redémarrage...", svc.name)
                start_service(svc)
                all_ok = False
            elif svc.health_check and not svc.health_check():
                logger.warning("[%s] ⚠ Health check échoué — redémarrage...", svc.name)
                stop_service(svc)
                time.sleep(1)
                start_service(svc)
                all_ok = False

        if cycle % 10 == 0:  # Toutes les 10 itérations (~2.5 min)
            statuses = [get_service_status(s) for s in SERVICES]
            alive = sum(1 for s in statuses if s["alive"])
            logger.info("[WATCHDOG] Cycle #%d — %d/%d services actifs",
                        cycle, alive, len(SERVICES))


# ===========================================================================
# CLI
# ===========================================================================


def _print_status(results: list[dict[str, Any]]) -> None:
    """Affiche les statuts formatés dans le terminal."""
    print()
    print(f"  {'=' * 58}")
    print(f"  MTTV-FLP — ÉTAT DES SERVICES")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  {'=' * 58}")
    print(f"  {'Service':25s} {'Status':10s} {'PID':>8s} {'Health':>8s}")
    print(f"  {'-' * 25} {'-' * 10} {'-' * 8} {'-' * 8}")

    for s in results:
        svc = next((x for x in SERVICES if x.name == s["name"]), None)
        if svc and not svc.persistent:
            if s["alive"]:
                status = "[OK] RUN"
            else:
                status = "[OK] DONE"  # One-shot, normal qu'il soit terminé
        else:
            status = "[OK] RUN" if s["alive"] else "[--] STOP"
        pid = str(s.get("pid", "") or "")
        health = "OK" if s.get("healthy") else ("--" if "healthy" not in s else "KO")
        print(f"  {s['name']:25s} {status:10s} {pid:>8s} {health:>8s}")

    print(f"  {'=' * 58}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MTTV-FLP Service Orchestrator — Gestion centralisée des services",
        epilog="sig:0x4D5454562D464C50",
    )
    parser.add_argument(
        "action",
        choices=["start", "stop", "restart", "status", "daemon"],
        help="Action à exécuter",
    )
    parser.add_argument(
        "--api-only", action="store_true",
        help="N'agir que sur l'API Gateway",
    )
    parser.add_argument(
        "--pinner-only", action="store_true",
        help="N'agir que sur l'IPFS Pinner",
    )
    parser.add_argument(
        "--monitor-only", action="store_true",
        help="N'agir que sur le monitoring",
    )
    parser.add_argument(
        "--dormant-only", action="store_true",
        help="N'agir que sur le script dormant",
    )
    parser.add_argument(
        "--rapport-only", action="store_true",
        help="N'agir que sur le daemon envoyer_rapport",
    )
    parser.add_argument(
        "--mycelisation-only", action="store_true",
        help="N'agir que sur le service de mycélisation tétravalente",
    )
    parser.add_argument(
        "--interval", type=float, default=15.0,
        help="Intervalle du watchdog en secondes (défaut: 15)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Format JSON pour la sortie (status uniquement)",
    )

    args = parser.parse_args()

    # Déterminer les services cibles
    targets = None
    if args.api_only:
        targets = ["api_gateway"]
    elif args.pinner_only:
        targets = ["ipfs_active_pinner"]
    elif args.monitor_only:
        targets = ["monitoring_service"]
    elif args.dormant_only:
        targets = ["script_dormant"]
    elif args.rapport_only:
        targets = ["envoyer_rapport"]
    elif args.mycelisation_only:
        targets = ["mycelisation"]

    # Exécuter l'action
    if args.action == "start":
        ok = cmd_start(targets)
        sys.exit(0 if ok else 1)

    elif args.action == "stop":
        ok = cmd_stop(targets)
        sys.exit(0 if ok else 1)

    elif args.action == "restart":
        ok = cmd_restart(targets)
        sys.exit(0 if ok else 1)

    elif args.action == "status":
        results = cmd_status(targets)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            _print_status(results)
        all_alive = all(s["alive"] for s in results)
        sys.exit(0 if all_alive else 1)

    elif args.action == "daemon":
        try:
            cmd_daemon(check_interval=args.interval)
        except KeyboardInterrupt:
            print("\n[ORCHESTRATOR] Interruption. Arrêt des services...")
            cmd_stop()
            print("[ORCHESTRATOR] Terminé.")
            sys.exit(0)


if __name__ == "__main__":
    main()
