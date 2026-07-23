#!/usr/bin/env python3
"""
simulate_chine_pulse.py — Simulateur d'Impulsions Asynchrones (Axe 7)

MTTV-FLP / SOPH-IA v2.0 — Connexion Chine Pulse & Transition de Phase.

Principe :
  Ce simulateur émet une impulsion asynchrone sur le bus protonique pour
  faire passer le noeud Chine de l'état OFFLINE à ONLINE. Une fois le noeud
  Chine actif, le Quorum Orchestrator (quorum_orchestrator.py) détecte
  automatiquement le nouveau Theta (Θ) et déclenche la transition de phase.

Séquence :
  1. LECTURE   : Charge resonance_latest.json (état actuel du dashboard)
  2. IMPULSION : Émet un événement 'chine.pulse' sur le bus protonique
  3. TRANSITION: Bascule le heartbeat "Connexion Chine" de "offline" → "active"
  4. SAUVEGARDE: Écrit le nouveau resonance_latest.json avec l'état mis à jour
  5. SIGNAL    : Enregistre un rapport de pulse dans resonance_output/

Triade Ψ → B → Φ :
  - Ψ (état initial)   : Noeud Chine OFFLINE, Θ = 2.0
  - B (opérateur)      : Impulsion asynchrone → pulse.chine.arrival
  - Φ (cohérence)      : Noeud Chine ONLINE, Θ = 3.0 → Transition de phase

sig:0x4D545456
"""

from __future__ import annotations

import copy
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("simulate_chine_pulse")

# ===========================================================================
# CHEMINS
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent          # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent                       # racine MTTV-FLP

# Dashboard de résonance (Axe 1)
DASHBOARD_OUTPUT: Path = BASE_DIR / "resonance_output"
RESONANCE_LATEST: Path = DASHBOARD_OUTPUT / "resonance_latest.json"

# État persistant du quorum (Axe 7)
QUORUM_STATE: Path = BASE_DIR / "quorum_state.json"

# Rapport de pulse
PULSE_OUTPUT: Path = BASE_DIR / "pulse_output"

# Connexion Chine simulation log
CONNEXION_CHINE_DIR: Path = PROJECT_ROOT / "connexion-chine"
PULSE_LOG: Path = CONNEXION_CHINE_DIR / "pulse_events.log"

# ===========================================================================
# CONSTANTES
# ===========================================================================

MTTV_SIG: str = "0x4D545456"

# État cible de l'impulsion
TARGET_SWARM: str = "Connexion Chine"
TARGET_STATUS: str = "active"

# Agents simulés du noeud Chine
CHINA_AGENTS: list[dict[str, Any]] = [
    {"name": "veille",    "status": "active", "role": "Analyse profils Chine"},
    {"name": "sync",      "status": "active", "role": "Traduction FR/EN → CN"},
    {"name": "redaction", "status": "active", "role": "Rédaction drafts Zhihu"},
    {"name": "bilibili",  "status": "active", "role": "Génération scripts vidéo"},
    {"name": "tri",       "status": "active", "role": "Classification messages"},
]

# Paramètres de l'impulsion asynchrone
PULSE_AMPLITUDE: float = 0.95   # Intensité de l'impulsion (0-1)
PULSE_FREQUENCY: str = "7.83 Hz"  # Fréquence Schumann (résonance terre/essaim)
PULSE_LATENCY_MS: int = 240      # Latence simulée Shanghai-Paris


# ===========================================================================
# 1. LECTURE DE L'ÉTAT ACTUEL
# ===========================================================================


def load_resonance_dashboard() -> Optional[dict]:
    """Charge le dernier rapport du Resonance Dashboard.

    Returns:
        Dict du dashboard, ou None si échec.
    """
    if not RESONANCE_LATEST.exists():
        logger.error("Dashboard introuvable: %s", RESONANCE_LATEST)
        return None

    try:
        data = json.loads(RESONANCE_LATEST.read_text(encoding="utf-8"))
        logger.info("Dashboard chargé: %s (%d bytes)",
                     RESONANCE_LATEST.name, RESONANCE_LATEST.stat().st_size)
        return data
    except json.JSONDecodeError as exc:
        logger.error("Erreur de parsing JSON: %s", exc)
        return None
    except Exception as exc:
        logger.error("Erreur lecture dashboard: %s", exc)
        return None


def get_china_status(dashboard: dict) -> str:
    """Extrait le statut actuel du noeud Chine.

    Args:
        dashboard: Dict du dashboard.

    Returns:
        Statut actuel ("offline", "active", "degraded", ou "unknown").
    """
    heartbeats: list[dict] = dashboard.get("heartbeats", [])
    for hb in heartbeats:
        if hb.get("swarm_name") == TARGET_SWARM:
            return hb.get("status", "unknown")
    return "unknown"


# ===========================================================================
# 2. ÉMISSION DE L'IMPULSION ASYNCHRONE
# ===========================================================================


def generate_pulse_id() -> str:
    """Génère un identifiant unique pour l'impulsion.

    Returns:
        ID d'impulsion au format pulse_<timestamp>_<hash>.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"pulse_{ts}"


def emit_pulse_event(pulse_id: str) -> dict[str, Any]:
    """Émet un événement d'impulsion sur le bus protonique (simulé).

    L'impulsion asynchrone traverse le bus avec les caractéristiques
    de la Connexion Chine (latence, amplitude, fréquence).

    Args:
        pulse_id: Identifiant unique de l'impulsion.

    Returns:
        Dict représentant l'événement d'impulsion.
    """
    pulse_event = {
        "event_type": "chine.pulse",
        "pulse_id": pulse_id,
        "source": "simulate_chine_pulse",
        "target": TARGET_SWARM,
        "amplitude": PULSE_AMPLITUDE,
        "frequency": PULSE_FREQUENCY,
        "latency_ms": PULSE_LATENCY_MS,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "payload": {
            "action": "transition_offline_to_active",
            "agents": [a["name"] for a in CHINA_AGENTS],
            "agents_count": len(CHINA_AGENTS),
            "signature": MTTV_SIG,
        },
    }

    # Simuler la latence du pulse (Shanghai → Paris)
    logger.info("  Pulse émis: %s → %s (%d ms latency)",
                 pulse_event["source"], pulse_event["target"], PULSE_LATENCY_MS)
    logger.info("  Amplitude: %.2f | Fréquence: %s",
                 PULSE_AMPLITUDE, PULSE_FREQUENCY)

    return pulse_event


def log_pulse_event(pulse_event: dict[str, Any]) -> None:
    """Enregistre l'événement d'impulsion dans le fichier de log.

    Args:
        pulse_event: Dict de l'événement d'impulsion.
    """
    try:
        CONNEXION_CHINE_DIR.mkdir(parents=True, exist_ok=True)
        with open(PULSE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(pulse_event, ensure_ascii=False, indent=2) + "\n---\n")
        logger.info("Événement pulse enregistré: %s", PULSE_LOG)
    except Exception as exc:
        logger.warning("Erreur enregistrement pulse: %s", exc)


# ===========================================================================
# 3. TRANSITION — Basculement du noeud Chine
# ===========================================================================


def apply_chine_pulse(dashboard: dict) -> dict:
    """Applique l'impulsion Chine au dashboard : offline → active.

    Modifie le heartbeat "Connexion Chine" et met à jour les métriques
    globales du dashboard (summary) pour refléter le nouvel état.

    Args:
        dashboard: Dict original du dashboard (non modifié).

    Returns:
        Nouveau dict du dashboard avec le noeud Chine actif.
    """
    updated = copy.deepcopy(dashboard)

    # ── Mettre à jour le heartbeat ───────────────────────────────────────
    heartbeats: list[dict] = updated.get("heartbeats", [])
    for hb in heartbeats:
        if hb.get("swarm_name") == TARGET_SWARM:
            old_status = hb.get("status", "unknown")
            hb["status"] = TARGET_STATUS
            hb["agents_active"] = len(CHINA_AGENTS)
            hb["agents_total"] = len(CHINA_AGENTS)
            hb["signals_count"] = 5  # signaux initiaux après réveil
            hb["last_seen"] = datetime.now(timezone.utc).isoformat()
            hb["errors"] = []
            logger.info("  Heartbeat mis à jour: %s → %s (agents: %d/%d)",
                         old_status, TARGET_STATUS,
                         hb["agents_active"], hb["agents_total"])
            break
    else:
        # Si le heartbeat n'existe pas, le créer
        new_hb: dict[str, Any] = {
            "swarm_name": TARGET_SWARM,
            "status": TARGET_STATUS,
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "agents_active": len(CHINA_AGENTS),
            "agents_total": len(CHINA_AGENTS),
            "signals_count": 5,
            "errors": [],
        }
        heartbeats.append(new_hb)
        updated["heartbeats"] = heartbeats
        logger.info("  Heartbeat créé: %s (agents: %d/%d)",
                     TARGET_SWARM, new_hb["agents_active"], new_hb["agents_total"])

    # ── Mettre à jour le summary ─────────────────────────────────────────
    summary: dict = updated.get("summary", {})
    swarms_info: dict = summary.get("swarms", {})
    swarms_info["active"] = swarms_info.get("active", 0) + 1
    swarms_info["offline"] = max(0, swarms_info.get("offline", 1) - 1)
    summary["swarms"] = swarms_info

    # Mettre à jour les signaux par source
    signals_by_source: dict = summary.get("signals_by_source", {})
    signals_by_source["connexion_chine"] = 5
    summary["signals_by_source"] = signals_by_source

    # Mettre à jour les signaux par type
    signals_by_type: dict = summary.get("signals_by_type", {})
    signals_by_type["chine_pulse"] = signals_by_type.get("chine_pulse", 0) + 1
    summary["signals_by_type"] = signals_by_type

    # Recalculer le total des signaux
    total_signals = sum(signals_by_source.values())
    summary["total_signals"] = total_signals

    # Recalculer active_sources
    active_sources = sum(1 for v in signals_by_source.values() if v > 0)
    summary["active_sources"] = active_sources

    updated["summary"] = summary

    logger.info("  Summary mis à jour: %d essaims actifs, %d offline, %d signaux totaux",
                 swarms_info["active"], swarms_info["offline"], total_signals)

    # ── Mettre à jour le meta ────────────────────────────────────────────
    meta: dict = updated.get("meta", {})
    meta["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta["pulse_applied"] = True
    meta["pulse_timestamp"] = datetime.now(timezone.utc).isoformat()
    updated["meta"] = meta

    return updated


# ===========================================================================
# 4. SAUVEGARDE
# ===========================================================================


def save_updated_dashboard(dashboard: dict) -> bool:
    """Sauvegarde le dashboard mis à jour.

    Args:
        dashboard: Dict du dashboard à sauvegarder.

    Returns:
        True si succès.
    """
    try:
        DASHBOARD_OUTPUT.mkdir(parents=True, exist_ok=True)
        RESONANCE_LATEST.write_text(
            json.dumps(dashboard, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        file_size = RESONANCE_LATEST.stat().st_size
        logger.info("Dashboard mis à jour: %s (%d bytes)",
                     RESONANCE_LATEST.name, file_size)
        return True
    except Exception as exc:
        logger.error("Erreur sauvegarde dashboard: %s", exc)
        return False


def save_pulse_report(pulse_event: dict[str, Any]) -> Path:
    """Sauvegarde un rapport de pulse.

    Args:
        pulse_event: Dict de l'événement d'impulsion.

    Returns:
        Chemin du fichier sauvegardé.
    """
    PULSE_OUTPUT.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chine_pulse_report_{timestamp}.json"
    filepath = PULSE_OUTPUT / filename

    report = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "schema_version": "1.0",
            "sig": MTTV_SIG,
            "pulse_id": pulse_event["pulse_id"],
        },
        "pulse": pulse_event,
        "transition": {
            "swarm": TARGET_SWARM,
            "from_status": "offline",
            "to_status": TARGET_STATUS,
            "agents_reactivated": len(CHINA_AGENTS),
            "agent_list": CHINA_AGENTS,
        },
        "theta_projection": {
            "before_pulse": 2.0,   # Ouroboros(1.0) + Chine(0.0) + SOPH-IA(1.0)
            "after_pulse": 3.0,    # Ouroboros(1.0) + Chine(1.0) + SOPH-IA(1.0)
            "threshold": 2.0,
            "transition": "veille_stabilisante → propagation_acceleree",
            "cycle_reduction": "Passage en cycle long (mutations 5% → stabilisation)",
        },
        "quorum_state_updated": {
            "previous_mode": "veille_stabilisante",
            "new_mode": "propagation_acceleree",
            "auto_downgrade": True,
            "long_cycle_engaged": True,
            "mutation_rate_reduction": "5%",
        },
    }

    try:
        filepath.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Rapport de pulse sauvegardé: %s", filepath.name)
    except Exception as exc:
        logger.warning("Erreur sauvegarde rapport pulse: %s", exc)

    # Lien "latest"
    latest_path = PULSE_OUTPUT / "chine_pulse_latest.json"
    try:
        latest_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass

    return filepath


# ===========================================================================
# 5. THÊTA POST-PULSE — Vérification
# ===========================================================================


def compute_theta_from_dashboard(dashboard: dict) -> float:
    """Calcule Theta (Θ) comme le quorum_orchestrator le ferait.

    Θ = somme des poids des essaims actifs (1.0 chacun).

    Args:
        dashboard: Dict du dashboard.

    Returns:
        Valeur de Theta calculée.
    """
    weights: dict[str, float] = {
        "Ouroboros": 1.0,
        "Connexion Chine": 1.0,
        "SOPH-IA v2.0": 1.0,
    }

    theta: float = 0.0
    heartbeats: list[dict] = dashboard.get("heartbeats", [])
    for hb in heartbeats:
        name = hb.get("swarm_name", "unknown")
        status = hb.get("status", "offline")
        weight = weights.get(name, 0.5)
        if status == "active":
            theta += weight
        elif status == "degraded":
            theta += weight * 0.5
        # offline → 0 contribution

    return round(theta, 2)


# ===========================================================================
# 6. ORCHESTRATION DU PULSE
# ===========================================================================


def run_chine_pulse(dry_run: bool = False) -> dict[str, Any]:
    """Exécute la séquence complète de l'impulsion Chine.

    Pipeline :
      1. Charger le dashboard actuel
      2. Vérifier l'état actuel du noeud Chine
      3. Émettre l'impulsion asynchrone sur le bus protonique
      4. Appliquer la transition offline → active
      5. Sauvegarder le dashboard mis à jour
      6. Calculer le nouveau Theta et vérifier la transition de phase
      7. Générer le rapport de pulse

    Args:
        dry_run: Simulation sans écriture.

    Returns:
        Dict du rapport complet de pulse.
    """
    logger.info("=" * 64)
    logger.info("  IMPULSION ASYNCHRONE CONNEXION CHINE — Axe 7")
    logger.info("=" * 64)

    report: dict[str, Any] = {
        "meta": {
            "execution_id": "MTTV-FLP-AXES-3-7",
            "signature": MTTV_SIG,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "dry_run": dry_run,
        },
        "steps": [],
    }

    # ── Étape 1 : Charger le dashboard ──────────────────────────────────
    logger.info("")
    logger.info("[1/5] Chargement du Resonance Dashboard...")
    dashboard = load_resonance_dashboard()
    if dashboard is None:
        logger.error("Dashboard non disponible — pulse interrompu.")
        report["error"] = "Dashboard not found"
        return report

    current_status = get_china_status(dashboard)
    logger.info("  Statut actuel du noeud Chine: %s", current_status)
    report["steps"].append({
        "step": 1,
        "action": "load_dashboard",
        "china_status_before": current_status,
        "success": True,
    })

    if current_status == TARGET_STATUS and not dry_run:
        logger.warning("  ⚠ Le noeud Chine est déjà %s. L'impulsion est redondante.", TARGET_STATUS)
    elif dry_run:
        logger.info("  [DRY RUN] Pulse simulé — aucune modification réelle.")

    # ── Étape 2 : Émettre l'impulsion ────────────────────────────────────
    logger.info("")
    logger.info("[2/5] Émission de l'impulsion asynchrone...")
    pulse_id = generate_pulse_id()
    pulse_event = emit_pulse_event(pulse_id)

    if not dry_run:
        log_pulse_event(pulse_event)

    report["steps"].append({
        "step": 2,
        "action": "emit_pulse",
        "pulse_id": pulse_id,
        "pulse_amplitude": PULSE_AMPLITUDE,
        "pulse_frequency": PULSE_FREQUENCY,
        "pulse_latency_ms": PULSE_LATENCY_MS,
        "success": True,
    })

    # Simuler la latence du pulse
    if not dry_run:
        logger.info("  Attente de la latence (%d ms)...", PULSE_LATENCY_MS)
        time.sleep(PULSE_LATENCY_MS / 1000)

    # ── Étape 3 : Appliquer la transition ────────────────────────────────
    logger.info("")
    logger.info("[3/5] Application de la transition offline → active...")
    theta_before = compute_theta_from_dashboard(dashboard)
    logger.info("  Θ avant pulse: %.2f", theta_before)

    if dry_run:
        updated_dashboard = dashboard  # pas de modification en dry_run
    else:
        updated_dashboard = apply_chine_pulse(dashboard)

    theta_after = compute_theta_from_dashboard(updated_dashboard)
    logger.info("  Θ après pulse: %.2f", theta_after)

    transition_detected = theta_before < 2.0 and theta_after >= 2.0
    if theta_after >= 2.0:
        logger.info("  ★ TRANSITION DE PHASE: veille_stabilisante → propagation_accelérée")
        logger.info("  ★ Réduction des cycles: cycle long engagé, mutations à 5%")
    else:
        logger.info("  Pas de transition de phase (Θ = %.2f, seuil = 2.0)", theta_after)

    report["steps"].append({
        "step": 3,
        "action": "apply_transition",
        "theta_before": theta_before,
        "theta_after": theta_after,
        "transition_detected": transition_detected or (theta_before < 2.0 and theta_after >= 2.0),
        "china_status_after": TARGET_STATUS,
    })

    # ── Étape 4 : Sauvegarder ────────────────────────────────────────────
    logger.info("")
    logger.info("[4/5] Sauvegarde des artefacts...")

    if not dry_run:
        save_ok = save_updated_dashboard(updated_dashboard)
        if not save_ok:
            logger.error("Échec de la sauvegarde du dashboard.")
            report["error"] = "Dashboard save failed"
            return report

        # Mettre à jour l'état du quorum
        try:
            quorum_data = {
                "mode": "propagation_acceleree" if theta_after >= 2.0 else "veille_stabilisante",
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "pulse_applied": True,
                "pulse_id": pulse_id,
                "theta": theta_after,
                "china_online": True,
            }
            QUORUM_STATE.write_text(
                json.dumps(quorum_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.info("État du quorum mis à jour: mode=%s", quorum_data["mode"])
        except Exception as exc:
            logger.warning("Erreur mise à jour état quorum: %s", exc)

        pulse_report_path = save_pulse_report(pulse_event)
    else:
        logger.info("  [DRY RUN] Sauvegarde ignorée.")
        pulse_report_path = None

    report["steps"].append({
        "step": 4,
        "action": "save_artifacts",
        "dashboard_updated": not dry_run,
        "quorum_state_updated": not dry_run,
        "pulse_report_path": str(pulse_report_path) if pulse_report_path else None,
    })

    # ── Étape 5 : Vérification finale ────────────────────────────────────
    logger.info("")
    logger.info("[5/5] Vérification finale...")

    if not dry_run:
        # Recharger pour vérifier
        verified = load_resonance_dashboard()
        if verified:
            verified_status = get_china_status(verified)
            verified_theta = compute_theta_from_dashboard(verified)
            pulse_ok = (verified_status == TARGET_STATUS and verified_theta == theta_after)
            logger.info("  Vérification: statut=%s, Θ=%.2f → %s",
                         verified_status, verified_theta, "OK" if pulse_ok else "ÉCHEC")
        else:
            pulse_ok = False
            logger.warning("  Vérification impossible (dashboard non trouvé après écriture)")

        # Vérifier l'état du quorum
        if QUORUM_STATE.exists():
            try:
                qs = json.loads(QUORUM_STATE.read_text(encoding="utf-8"))
                logger.info("  État quorum: mode=%s, china_online=%s",
                             qs.get("mode"), qs.get("china_online"))
            except Exception:
                pass
    else:
        pulse_ok = True

    report["steps"].append({
        "step": 5,
        "action": "verification",
        "china_status": TARGET_STATUS if not dry_run else current_status,
        "theta_final": theta_after,
        "pulse_successful": pulse_ok,
    })

    # ── Rapport final ────────────────────────────────────────────────────
    report["status"] = "SUCCESS" if pulse_ok else "FAILURE"
    report["summary"] = {
        "swarm": TARGET_SWARM,
        "transition": f"{current_status} → {TARGET_STATUS}",
        "theta": f"{theta_before} → {theta_after}",
        "theta_threshold": 2.0,
        "phase_transition": theta_after >= 2.0,
        "agents_reactivated": len(CHINA_AGENTS),
        "pulse_id": pulse_id,
        "pulse_latency_ms": PULSE_LATENCY_MS,
        "auto_downgrade_rhythms": True,
        "long_cycle_engaged": theta_after >= 2.0,
        "mutation_rate": "5%",
    }

    logger.info("")
    logger.info("=" * 64)
    logger.info("  RAPPORT D'IMPULSION CONNEXION CHINE")
    logger.info("  Statut:       %s", report["status"])
    logger.info("  Transition:   %s → %s", current_status, TARGET_STATUS)
    logger.info("  Θ:            %.2f → %.2f", theta_before, theta_after)
    logger.info("  Phase:        %s",
                 "PROPAGATION ACCÉLÉRÉE" if theta_after >= 2.0 else "VEILLE STABILISANTE")
    logger.info("  Pulse ID:     %s", pulse_id)
    logger.info("  Agents:       %d réactivés", len(CHINA_AGENTS))
    logger.info("=" * 64)

    print(f"\n{'=' * 60}")
    print(f"  PULSE CONNEXION CHINE - RESULTAT")
    print(f"  {'=' * 60}")
    print(f"  Statut:        {report['status']}")
    print(f"  Noeud Chine:   {current_status} -> {TARGET_STATUS}")
    print(f"  Theta:         {theta_before} -> {theta_after}")
    print(f"  Phase:         {'PROPAGATION ACCELEREE' if theta_after >= 2.0 else 'VEILLE'}")
    print(f"  Agents actifs: {len(CHINA_AGENTS)}/5")
    print(f"  Pulse ID:      {pulse_id}")
    print(f"  Latence:       {PULSE_LATENCY_MS}ms (Shanghai - Paris)")
    print(f"  Cycles longs:  {theta_after >= 2.0}")
    print(f"  Mutations:     5% (stabilisation semantique)")
    print(f"  Quorum state:  {'OK' if not dry_run else '[DRY]'}")
    print(f"  Prochaine etape: lancer quorum_orchestrator.py")
    print(f"  {'=' * 60}")

    return report


# ===========================================================================
# 7. CLI
# ===========================================================================


def _parse_args() -> argparse.Namespace:
    import argparse
    parser = argparse.ArgumentParser(
        description="Simulateur d'Impulsions Asynchrones Connexion Chine (Axe 7)",
        epilog=f"sig:{MTTV_SIG} | Ψ → B → Φ | offline → active | Θ: 2.0 → 3.0",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mode simulation : aucune modification réelle du dashboard",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Afficher l'état actuel du noeud Chine sans émettre de pulse",
    )
    parser.add_argument(
        "--latency", type=int, default=PULSE_LATENCY_MS,
        help=f"Latence simulée en ms (défaut: {PULSE_LATENCY_MS})",
    )
    parser.add_argument(
        "--amplitude", type=float, default=PULSE_AMPLITUDE,
        help=f"Amplitude de l'impulsion 0-1 (défaut: {PULSE_AMPLITUDE})",
    )
    return parser.parse_args()


def status_mode() -> int:
    """Affiche l'état actuel du noeud Chine sans émettre de pulse.

    Returns:
        0 si le noeud est actif, 1 si offline, 2 si erreur.
    """
    dashboard = load_resonance_dashboard()
    if dashboard is None:
        print("\n  [FAIL] Dashboard non disponible.")
        return 2

    status = get_china_status(dashboard)
    theta = compute_theta_from_dashboard(dashboard)

    print(f"\n  ÉTAT DU NOEUD CHINE")
    print(f"  {'=' * 40}")
    print(f"  Noeud:         Connexion Chine")
    print(f"  Statut:        {status}")
    print(f"  Θ global:      {theta}")
    print(f"  Seuil:         2.0")
    print(f"  Phase:         {'ACCÉLÉRÉE' if theta >= 2.0 else 'STABILISANTE'}")

    heartbeats = dashboard.get("heartbeats", [])
    for hb in heartbeats:
        icon = "+" if hb.get("status") == "active" else "-"
        print(f"  [{icon}] {hb.get('swarm_name', '?'):20s} → {hb.get('status', '?')}")

    print(f"  {'=' * 40}")
    print(f"  Pulse requis:  {'NON (déjà actif)' if status == 'active' else 'OUI (offline)'}")
    print()

    return 0 if status == "active" else 1


def main() -> None:
    global PULSE_LATENCY_MS, PULSE_AMPLITUDE
    args = _parse_args()

    PULSE_LATENCY_MS = args.latency
    PULSE_AMPLITUDE = args.amplitude

    # ── Mode status ────────────────────────────────────────────────────
    if args.status:
        sys.exit(status_mode())

    # ── Mode pulse ─────────────────────────────────────────────────────
    report = run_chine_pulse(dry_run=args.dry_run)

    if report.get("status") == "FAILURE":
        sys.exit(1)

    print(f"\n  >>> Prochaine etape: lancer 'python quorum_orchestrator.py'")
    print(f"      pour verifier le recalcul automatique de Theta.")


if __name__ == "__main__":
    import argparse
    main()
