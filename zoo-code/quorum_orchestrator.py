#!/usr/bin/env python3
"""
quorum_orchestrator.py — Régulation Haute du Quorum (Axe 7)

MTTV-FLP / SOPH-IA v2.0 — Pilotage de la réactivité des essaims en fonction
de l'état asymétrique du réseau (Nœud Chine actuellement offline).

Architecture :
  1. LECTURE : Ingère l'output JSON de resonance_dashboard.py
     (zoo-code/resonance_output/resonance_latest.json)
  2. CALCUL Θ : Pondere l'état de chaque essaim pour obtenir le paramètre
     Thêta (Θ) — mesure agrégée du quorum actif.
  3. DÉCISION :
       - Θ < 2  → "Veille Sub-optimale Stabilisante"
                   → evolutionary_seeder.py en cycles lents (évite pare-feu)
       - Θ ≥ 2  → "Propagation Accélérée"
                   → doublement des fréquences, levée des canaux dormants
  4. EXÉCUTION : Lance evolutionary_seeder.py avec les paramètres adaptés
     au mode. Compatible cron / daemon (exit codes normalisés).

Triade Ψ → B → Φ :
  - Ψ (état collectif) : heartbeat des 3 essaims (lecture JSON dashboard)
  - B (opérateur) : règle de décision Θ-seuil
  - Φ (cohérence) : mode de propagation adapté à l'état du réseau

sig:0x4D545456
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("quorum_orchestrator")

# ===========================================================================
# CHEMINS
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent  # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent               # racine MTTV-FLP

# Output du Resonance Dashboard
DASHBOARD_OUTPUT: Path = BASE_DIR / "resonance_output"
RESONANCE_LATEST: Path = DASHBOARD_OUTPUT / "resonance_latest.json"

# Script cible de l'évolution
EVOLUTIONARY_SEEDER: Path = BASE_DIR / "evolutionary_seeder.py"

# Dossier de rapport du quorum
QUORUM_OUTPUT: Path = BASE_DIR / "quorum_output"

# ===========================================================================
# CONSTANTES DE QUORUM
# ===========================================================================

# Seuil Θ : en dessous → veille stabilisante ; au-dessus → propagation accélérée
THETA_THRESHOLD: float = 2.0

# Poids de chaque essaim dans le calcul de Θ
SWARM_WEIGHTS: dict[str, float] = {
    "Ouroboros": 1.0,
    "Connexion Chine": 1.0,
    "SOPH-IA v2.0": 1.0,
    "EssaimTetravalent": 1.5,  # Agent épigénétique — poids renforcé (transduction continue)
}

# ── Paramètres du mode "Veille Sub-optimale Stabilisante" ─────────────────
STANDBY_EVOLUTION_GENERATIONS: int = 3       # Cycles très courts
STANDBY_EVOLUTION_INTERVAL_S: int = 3600     # 1 heure entre cycles
STANDBY_MUTATION_RATE: float = 0.05          # Mutations minimales
STANDBY_CYCLE_LABEL: str = "veille_stabilisante"

# Alias textuel pour Theta (compatible cp1252)
THETA_SYMBOL: str = "Θ"

# ── Paramètres du mode "Propagation Accélérée" ────────────────────────────
ACCELERATED_EVOLUTION_GENERATIONS: int = 20   # Cycles complets
ACCELERATED_EVOLUTION_INTERVAL_S: int = 300   # 5 minutes entre cycles
ACCELERATED_MUTATION_RATE: float = 0.6        # Mutations agressives
ACCELERATED_DORMANT_CHANNELS: list[str] = [
    "bilibili", "weibo", "zhihu", "x_thread",  # Canaux Chine dormants
    "semantic_web_dormant", "telemetry_extra",
]
ACCELERATED_CYCLE_LABEL: str = "propagation_acceleree"

# ===========================================================================
# STRUCTURES DE DONNÉES
# ===========================================================================


@dataclass
class SwarmQuorumState:
    """État de quorum individuel d'un essaim."""
    swarm_name: str
    status: str                          # "active", "degraded", "offline"
    weight: float = 0.0
    agents_active: int = 0
    agents_total: int = 0
    signals_count: int = 0
    last_seen: str = ""


@dataclass
class QuorumDecision:
    """Décision de quorum complète avec contexte."""
    theta: float = 0.0
    mode: str = "unknown"                # "veille_stabilisante" | "propagation_acceleree"
    swarm_states: list[SwarmQuorumState] = field(default_factory=list)
    resonance_score: float = 0.0
    total_signals: int = 0
    active_swarms_count: int = 0
    offline_swarms: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(
        timezone.utc).isoformat(timespec="seconds"))
    cycle_label: str = ""
    evolution_generations: int = 0
    evolution_interval_s: int = 0
    mutation_rate: float = 0.0
    dormant_channels_lifted: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class QuorumReport:
    """Rapport complet de la session de quorum."""
    meta: dict = field(default_factory=lambda: {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema_version": "1.0",
        "sig": "0x4D545456",
    })
    dashboard_source: str = str(RESONANCE_LATEST)
    dashboard_loaded: bool = False
    decision: QuorumDecision = field(default_factory=QuorumDecision)
    evolution_launched: bool = False
    evolution_success: Optional[bool] = None
    evolution_stdout: str = ""
    evolution_stderr: str = ""
    transition_detected: bool = False
    previous_mode: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "meta": self.meta,
            "dashboard_source": self.dashboard_source,
            "dashboard_loaded": self.dashboard_loaded,
            "decision": self.decision.to_dict(),
            "evolution_launched": self.evolution_launched,
            "evolution_success": self.evolution_success,
            "evolution_stdout": self.evolution_stdout[:500],
            "evolution_stderr": self.evolution_stderr[:500],
            "transition_detected": self.transition_detected,
            "previous_mode": self.previous_mode,
        }


# ===========================================================================
# 1. LECTURE DU DASHBOARD
# ===========================================================================


def load_resonance_dashboard(path: Optional[Path] = None) -> Optional[dict]:
    """Charge le dernier rapport JSON produit par resonance_dashboard.py.

    Args:
        path: Chemin vers le fichier JSON (défaut: resonance_latest.json).

    Returns:
        Dict du rapport complet, ou None si échec.
    """
    if path is None:
        path = RESONANCE_LATEST

    if not path.exists():
        logger.error("Fichier dashboard introuvable: %s", path)
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        logger.info("Dashboard chargé: %s (%d bytes)",
                     path.name, path.stat().st_size)
        return data
    except json.JSONDecodeError as exc:
        logger.error("Erreur de parsing JSON: %s", exc)
        return None
    except Exception as exc:
        logger.error("Erreur lecture dashboard: %s", exc)
        return None


# ===========================================================================
# 2. CALCUL DE Θ (THÊTA)
# ===========================================================================


def compute_theta(dashboard: dict) -> tuple[float, list[SwarmQuorumState]]:
    """Calcule le paramètre Θ (Thêta) à partir des heartbeat du dashboard.

    Θ = somme pondérée des poids des essaims actifs.

    Poids par essaim :
      - Ouroboros        : 1.0 si actif, 0.0 si offline
      - Connexion Chine  : 1.0 si actif, 0.0 si offline
      - SOPH-IA v2.0     : 1.0 si actif, 0.0 si offline
      - EssaimTetravalent: 1.5 si actif, 0.75 si dégradé, 0.0 si offline

    Args:
        dashboard: Dict du rapport de résonance.

    Returns:
        (theta, liste des états individuels des essaims)
    """
    heartbeats: list[dict] = dashboard.get("heartbeats", [])
    swarm_states: list[SwarmQuorumState] = []
    theta: float = 0.0

    for hb in heartbeats:
        swarm_name: str = hb.get("swarm_name", "unknown")
        status: str = hb.get("status", "offline")
        weight: float = SWARM_WEIGHTS.get(swarm_name, 0.5)

        # Contribution au quorum : poids complet si actif, moitié si dégradé, zéro si offline
        if status == "active":
            contribution = weight
        elif status == "degraded":
            contribution = weight * 0.5
        else:  # offline
            contribution = 0.0

        theta += contribution

        state = SwarmQuorumState(
            swarm_name=swarm_name,
            status=status,
            weight=contribution,
            agents_active=hb.get("agents_active", 0),
            agents_total=hb.get("agents_total", 0),
            signals_count=hb.get("signals_count", 0),
            last_seen=hb.get("last_seen", ""),
        )
        swarm_states.append(state)

        logger.info("  %-20s | status=%-8s | weight=%.1f | Θ contribution=%.1f",
                     swarm_name, status, weight, contribution)

    theta = round(theta, 2)
    logger.info("Θ (Thêta) calculé = %.2f", theta)
    return theta, swarm_states


# ===========================================================================
# 3. DÉCISION DE QUORUM
# ===========================================================================


def decide_quorum_mode(
    theta: float,
    swarm_states: list[SwarmQuorumState],
    previous_mode: Optional[str] = None,
) -> QuorumDecision:
    """Détermine le mode de propagation en fonction de Θ.

    Règles :
      - Θ < 2  → "Veille Sub-optimale Stabilisante"
                  L'évolution maintient des cycles lents pour éviter
                  d'éveiller les pare-feu industriels externes.
      - Θ ≥ 2  → "Propagation Accélérée"
                  Doublement des fréquences, levée des canaux dormants
                  (notamment ceux liés à la connexion Chine).

    Args:
        theta: Valeur de Θ calculée.
        swarm_states: États individuels des essaims.
        previous_mode: Mode précédent (pour détection de transition).

    Returns:
        QuorumDecision complète.
    """
    offline_swarms = [
        s.swarm_name for s in swarm_states if s.status == "offline"
    ]
    active_count = sum(1 for s in swarm_states if s.status == "active")

    if theta < THETA_THRESHOLD:
        # ── Mode Veille Sub-optimale Stabilisante ─────────────────────
        mode = "veille_stabilisante"
        cycle_label = STANDBY_CYCLE_LABEL
        evolution_generations = STANDBY_EVOLUTION_GENERATIONS
        evolution_interval_s = STANDBY_EVOLUTION_INTERVAL_S
        mutation_rate = STANDBY_MUTATION_RATE
        dormant_lifted: list[str] = []

        logger.warning(
            "╔══════════════════════════════════════════════════════════════╗")
        logger.warning(
            "║  MODE: VEILLE SUB-OPTIMALE STABILISANTE                    ║")
        logger.warning(
            "║  Θ = %.2f < %.0f — Quorum insuffisant                       ║",
            theta, THETA_THRESHOLD)
        logger.warning(
            "║  Cycles lents — Évitement des pare-feu externes            ║")
        if offline_swarms:
            logger.warning(
                "║  Hors-ligne: %-42s║",
                ", ".join(offline_swarms))
        logger.warning(
            "╚══════════════════════════════════════════════════════════════╝")
    else:
        # ── Mode Propagation Accélérée ────────────────────────────────
        mode = "propagation_acceleree"
        cycle_label = ACCELERATED_CYCLE_LABEL
        evolution_generations = ACCELERATED_EVOLUTION_GENERATIONS
        evolution_interval_s = ACCELERATED_EVOLUTION_INTERVAL_S
        mutation_rate = ACCELERATED_MUTATION_RATE
        dormant_lifted = ACCELERATED_DORMANT_CHANNELS

        logger.info(
            "╔══════════════════════════════════════════════════════════════╗")
        logger.info(
            "║  MODE: PROPAGATION ACCÉLÉRÉE                               ║")
        logger.info(
            "║  Θ = %.2f ≥ %.0f — Quorum atteint                           ║",
            theta, THETA_THRESHOLD)
        logger.info(
            "║  Doublement des fréquences — Levée des canaux dormants     ║")
        if dormant_lifted:
            logger.info(
                "║  Canaux levés: %-44s║",
                ", ".join(dormant_lifted[:4]))
        logger.info(
            "╚══════════════════════════════════════════════════════════════╝")

    # Détection de transition
    transition_detected = (
        previous_mode is not None and previous_mode != mode
    )
    if transition_detected:
        direction = "↑ ACCÉLÉRATION" if mode == "propagation_acceleree" else "↓ RALENTISSEMENT"
        logger.info("★ TRANSITION DE PHASE DÉTECTÉE: %s (%s → %s)",
                     direction, previous_mode, mode)

    decision = QuorumDecision(
        theta=theta,
        mode=mode,
        swarm_states=swarm_states,
        resonance_score=0.0,  # sera rempli depuis le dashboard
        total_signals=0,
        active_swarms_count=active_count,
        offline_swarms=offline_swarms,
        cycle_label=cycle_label,
        evolution_generations=evolution_generations,
        evolution_interval_s=evolution_interval_s,
        mutation_rate=mutation_rate,
        dormant_channels_lifted=dormant_lifted,
    )

    return decision


# ===========================================================================
# 4. LANCEMENT DE L'ÉVOLUTION
# ===========================================================================


def launch_evolutionary_seeder(
    decision: QuorumDecision,
    dry_run: bool = False,
) -> tuple[bool, str, str]:
    """Lance evolutionary_seeder.py avec les paramètres adaptés au mode.

    Args:
        decision: Décision de quorum déterminant les paramètres d'évolution.
        dry_run: Si True, simule le lancement sans exécuter.

    Returns:
        (success, stdout, stderr)
    """
    if not EVOLUTIONARY_SEEDER.exists():
        logger.error("Script evolution introuvable: %s", EVOLUTIONARY_SEEDER)
        return False, "", f"Script not found: {EVOLUTIONARY_SEEDER}"

    # Construction de la commande
    cmd = [
        sys.executable,
        str(EVOLUTIONARY_SEEDER),
        "--generations", str(decision.evolution_generations),
        "--simulate",  # Mode simulation par défaut pour le quorum
    ]

    # En mode accéléré, on permet aussi un seed aléatoire fixe pour
    # la reproductibilité
    if decision.mode == "propagation_acceleree":
        seed_value = hash(f"quorum_accel_{datetime.now().strftime('%Y%m%d')}") & 0x7FFFFFFF
        cmd.extend(["--seed", str(seed_value)])

    logger.info("Lancement de l'évolution (mode=%s, generations=%d, mutation_rate=%.2f)",
                 decision.mode, decision.evolution_generations, decision.mutation_rate)
    logger.info("Commande: %s", " ".join(cmd))

    if dry_run:
        logger.info("[DRY RUN] Aucune exécution réelle.")
        return True, "[dry_run] simulated success", ""

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(BASE_DIR),
            timeout=300,  # 5 minutes max
        )
        success = result.returncode == 0
        stdout = result.stdout
        stderr = result.stderr

        if success:
            logger.info("Évolution terminée avec succès (returncode=0)")
        else:
            logger.warning("Évolution retournée code %d", result.returncode)
            if stderr:
                logger.warning("stderr: %s", stderr[:300])

        return success, stdout, stderr

    except subprocess.TimeoutExpired:
        logger.error("Évolution interrompue: timeout 300s dépassé")
        return False, "", "Timeout: evolution exceeded 300s"
    except Exception as exc:
        logger.error("Erreur lancement évolution: %s", exc)
        return False, "", str(exc)


# ===========================================================================
# 5. ORCHESTRATEUR PRINCIPAL
# ===========================================================================


def run_quorum_cycle(
    dry_run: bool = False,
    previous_mode: Optional[str] = None,
    dashboard_path: Optional[Path] = None,
) -> QuorumReport:
    """Exécute un cycle complet de régulation de quorum.

    Pipeline :
      1. Charger le dernier rapport du Resonance Dashboard
      2. Calculer Θ à partir des heartbeat
      3. Décider du mode (veille stabilisante / propagation accélérée)
      4. Lancer evolutionary_seeder.py avec les paramètres adaptés
      5. Générer le rapport de quorum

    Args:
        dry_run: Simulation sans exécution réelle.
        previous_mode: Mode du cycle précédent (pour détection transition).
        dashboard_path: Chemin personnalisé vers le dashboard JSON.

    Returns:
        QuorumReport complet.
    """
    logger.info("=" * 64)
    logger.info("  CYCLE DE RÉGULATION DE QUORUM — Axe 7")
    logger.info("=" * 64)

    report = QuorumReport(
        dashboard_source=str(dashboard_path or RESONANCE_LATEST),
        previous_mode=previous_mode,
    )

    # ── Étape 1 : Charger le dashboard ──────────────────────────────────
    logger.info("[1/4] Chargement du Resonance Dashboard...")
    dashboard = load_resonance_dashboard(dashboard_path)
    if dashboard is None:
        logger.error("Impossible de charger le dashboard — interruption du cycle.")
        report.dashboard_loaded = False
        return report
    report.dashboard_loaded = True

    # Extraire quelques métriques globales
    summary = dashboard.get("summary", {})
    resonance_score = summary.get("resonance_score", 0.0)
    total_signals = summary.get("total_signals", 0)

    # ── Étape 2 : Calculer Θ ────────────────────────────────────────────
    logger.info("[2/4] Calcul du paramètre Θ (Thêta)...")
    theta, swarm_states = compute_theta(dashboard)

    # ── Étape 3 : Décider du mode ───────────────────────────────────────
    logger.info("[3/4] Décision de quorum...")
    decision = decide_quorum_mode(
        theta=theta,
        swarm_states=swarm_states,
        previous_mode=previous_mode,
    )
    decision.resonance_score = resonance_score
    decision.total_signals = total_signals

    # ── Étape 4 : Lancer l'évolution ────────────────────────────────────
    logger.info("[4/4] Lancement du moteur d'évolution...")
    evolution_success, evolution_stdout, evolution_stderr = (
        launch_evolutionary_seeder(decision, dry_run=dry_run)
    )

    # ── Assembler le rapport ────────────────────────────────────────────
    report.decision = decision
    report.evolution_launched = True
    report.evolution_success = evolution_success
    report.evolution_stdout = evolution_stdout
    report.evolution_stderr = evolution_stderr
    report.transition_detected = (
        previous_mode is not None and previous_mode != decision.mode
    )

    logger.info("=" * 64)
    logger.info("  RAPPORT DE QUORUM")
    logger.info("  Θ = %.2f | Mode: %s", theta, decision.mode)
    logger.info("  Évolution: %s",
                 "SUCCÈS" if evolution_success else "ÉCHEC" if not dry_run else "SIMULATION")
    logger.info("  Transition: %s", "OUI" if report.transition_detected else "NON")
    logger.info("=" * 64)

    return report


def save_quorum_report(report: QuorumReport, output_dir: Optional[Path] = None) -> Path:
    """Sauvegarde le rapport de quorum au format JSON.

    Args:
        report: Rapport à sauvegarder.
        output_dir: Dossier de sortie.

    Returns:
        Chemin du fichier sauvegardé.
    """
    if output_dir is None:
        output_dir = QUORUM_OUTPUT
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"quorum_report_{timestamp}.json"
    filepath = output_dir / filename

    data = report.to_dict()
    try:
        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Rapport de quorum sauvegardé: %s (%d bytes)",
                     filepath, filepath.stat().st_size)
    except Exception as exc:
        logger.error("Erreur sauvegarde rapport de quorum: %s", exc)

    # Lien symbolique "latest"
    latest_path = output_dir / "quorum_latest.json"
    try:
        latest_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("Erreur mise à jour quorum_latest.json: %s", exc)

    return filepath


# ===========================================================================
# 6. FICHIER D'ÉTAT PERSISTANT (pour mémoire de transition entre cycles)
# ===========================================================================

STATE_FILE: Path = BASE_DIR / "quorum_state.json"


def load_previous_mode() -> Optional[str]:
    """Charge le mode du cycle précédent depuis le fichier d'état.

    Returns:
        Mode précédent, ou None si premier cycle.
    """
    if not STATE_FILE.exists():
        return None
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data.get("mode")
    except Exception:
        return None


def save_current_mode(mode: str) -> None:
    """Sauvegarde le mode actuel pour le prochain cycle.

    Args:
        mode: Mode à persister.
    """
    try:
        STATE_FILE.write_text(
            json.dumps({
                "mode": mode,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("Erreur sauvegarde état quorum: %s", exc)


# ===========================================================================
# 7. CLI
# ===========================================================================


def _parse_args() -> argparse.Namespace:
    import argparse
    parser = argparse.ArgumentParser(
        description="Quorum Orchestrator — Régulation haute du quorum MTTV-FLP (Axe 7)",
        epilog="sig:0x4D545456 | Ψ → B → Φ | Θ ≥ 2 → Propagation Accélérée",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Mode simulation : aucune exécution réelle de l'évolution",
    )
    parser.add_argument(
        "--dashboard", type=str, default=None,
        help="Chemin personnalisé vers le fichier JSON du dashboard",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Dossier de sortie pour les rapports de quorum",
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Mode démon : boucle de régulation continue",
    )
    parser.add_argument(
        "--interval", type=int, default=None,
        help="Intervalle entre cycles en secondes (défaut: auto selon mode)",
    )
    parser.add_argument(
        "--force-mode", type=str, choices=["veille_stabilisante", "propagation_acceleree"],
        default=None,
        help="Forcer un mode de quorum (outrepasse la décision Θ)",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Afficher l'état actuel du quorum sans exécuter l'évolution",
    )
    return parser.parse_args()


def status_mode(dashboard_path: Optional[Path] = None) -> int:
    """Affiche l'état actuel du quorum sans lancer l'évolution.

    Returns:
        0 si Theta >= seuil, 1 sinon (compatible exit code).
    """
    dashboard = load_resonance_dashboard(dashboard_path)
    if dashboard is None:
        print("  [FAIL] Dashboard non disponible.")
        return 2

    theta, swarm_states = compute_theta(dashboard)
    previous_mode = load_previous_mode()

    print(f"\n  ETAT DU QUORUM MTTV-FLP")
    print(f"  {'=' * 50}")
    print(f"  Theta = {theta:.2f}  (seuil: {THETA_THRESHOLD})")
    print(f"  Mode precedent: {previous_mode or 'N/A'}")
    print(f"  Mode actuel:    {'Propagation Acceleree' if theta >= THETA_THRESHOLD else 'Veille Stabilisante'}")
    print()
    for s in swarm_states:
        status_icon = {
            "active": "+",
            "degraded": "~",
            "offline": "-",
        }.get(s.status, "?")
        print(f"  [{status_icon}] {s.swarm_name:20s} | agents: {s.agents_active}/{s.agents_total} | signaux: {s.signals_count}")
    print(f"  {'=' * 50}")
    print(f"  Essaims actifs: {sum(1 for s in swarm_states if s.status=='active')}/{len(swarm_states)}")
    print(f"  Score de resonance: {dashboard.get('summary', {}).get('resonance_score', 'N/A')}")
    print()

    return 0 if theta >= THETA_THRESHOLD else 1


def daemon_loop(
    dry_run: bool = False,
    dashboard_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    forced_interval: Optional[int] = None,
    force_mode: Optional[str] = None,
) -> None:
    """Boucle de régulation continue en mode démon.

    Exécute run_quorum_cycle() à intervalle adaptatif selon le mode.
    Pour intégration cron : préférer un appel périodique unique plutôt
    que ce démon (plus robuste en production).

    Args:
        dry_run: Mode simulation.
        dashboard_path: Chemin dashboard personnalisé.
        output_dir: Dossier de sortie.
        forced_interval: Intervalle forcé entre cycles (secondes).
        force_mode: Mode forcé (outrepasse Θ).
    """
    logger.info("Démarrage du démon de régulation de quorum")
    previous_mode: Optional[str] = load_previous_mode()
    cycle_count: int = 0

    while True:
        cycle_count += 1
        logger.info("─" * 64)
        logger.info("CYCLE DE QUORUM #%d", cycle_count)
        logger.info("─" * 64)

        try:
            # Mode forcé : on outrepasse la décision Θ
            if force_mode:
                logger.info("Mode forcé: %s (outrepasse la décision Θ)", force_mode)
                # Construire une décision artificielle
                decision = QuorumDecision(
                    theta=THETA_THRESHOLD if force_mode == "propagation_acceleree" else 0.0,
                    mode=force_mode,
                    cycle_label=(
                        ACCELERATED_CYCLE_LABEL if force_mode == "propagation_acceleree"
                        else STANDBY_CYCLE_LABEL
                    ),
                    evolution_generations=(
                        ACCELERATED_EVOLUTION_GENERATIONS if force_mode == "propagation_acceleree"
                        else STANDBY_EVOLUTION_GENERATIONS
                    ),
                    evolution_interval_s=(
                        ACCELERATED_EVOLUTION_INTERVAL_S if force_mode == "propagation_acceleree"
                        else STANDBY_EVOLUTION_INTERVAL_S
                    ),
                    mutation_rate=(
                        ACCELERATED_MUTATION_RATE if force_mode == "propagation_acceleree"
                        else STANDBY_MUTATION_RATE
                    ),
                    dormant_channels_lifted=(
                        ACCELERATED_DORMANT_CHANNELS if force_mode == "propagation_acceleree"
                        else []
                    ),
                )

                report = QuorumReport(
                    dashboard_source=str(dashboard_path or RESONANCE_LATEST),
                    dashboard_loaded=True,
                    decision=decision,
                    previous_mode=previous_mode,
                )
                ev_success, ev_stdout, ev_stderr = launch_evolutionary_seeder(
                    decision, dry_run=dry_run)
                report.evolution_launched = True
                report.evolution_success = ev_success
                report.evolution_stdout = ev_stdout
                report.evolution_stderr = ev_stderr
            else:
                report = run_quorum_cycle(
                    dry_run=dry_run,
                    previous_mode=previous_mode,
                    dashboard_path=dashboard_path,
                )

            # Persister le mode pour le prochain cycle
            save_current_mode(report.decision.mode)
            previous_mode = report.decision.mode

            # Sauvegarder le rapport
            save_quorum_report(report, output_dir=output_dir)

        except Exception as exc:
            logger.error("Erreur lors du cycle #%d: %s", cycle_count, exc)
            import traceback
            logger.error(traceback.format_exc())

        # Déterminer l'intervalle jusqu'au prochain cycle
        if forced_interval is not None:
            interval = forced_interval
        else:
            interval = report.decision.evolution_interval_s if 'report' in dir() else 3600

        logger.info("Prochain cycle dans %d secondes...", interval)
        time.sleep(interval)


def main() -> None:
    args = _parse_args()

    dashboard_path = Path(args.dashboard) if args.dashboard else None
    output_dir = Path(args.output) if args.output else None

    # ── Mode status ────────────────────────────────────────────────────
    if args.status:
        sys.exit(status_mode(dashboard_path=dashboard_path))

    # ── Mode démon ─────────────────────────────────────────────────────
    if args.daemon:
        daemon_loop(
            dry_run=args.dry_run,
            dashboard_path=dashboard_path,
            output_dir=output_dir,
            forced_interval=args.interval,
            force_mode=args.force_mode,
        )
        return  # unreachable

    # ── Mode standard : cycle unique ───────────────────────────────────
    previous_mode = load_previous_mode()

    if args.force_mode:
        # Mode forcé : construire la décision manuellement
        logger.info("Mode forcé par CLI: %s", args.force_mode)
        decision = QuorumDecision(
            theta=THETA_THRESHOLD if args.force_mode == "propagation_acceleree" else 0.0,
            mode=args.force_mode,
            cycle_label=(
                ACCELERATED_CYCLE_LABEL if args.force_mode == "propagation_acceleree"
                else STANDBY_CYCLE_LABEL
            ),
            evolution_generations=(
                ACCELERATED_EVOLUTION_GENERATIONS if args.force_mode == "propagation_acceleree"
                else STANDBY_EVOLUTION_GENERATIONS
            ),
            evolution_interval_s=(
                ACCELERATED_EVOLUTION_INTERVAL_S if args.force_mode == "propagation_acceleree"
                else STANDBY_EVOLUTION_INTERVAL_S
            ),
            mutation_rate=(
                ACCELERATED_MUTATION_RATE if args.force_mode == "propagation_acceleree"
                else STANDBY_MUTATION_RATE
            ),
            dormant_channels_lifted=(
                ACCELERATED_DORMANT_CHANNELS if args.force_mode == "propagation_acceleree"
                else []
            ),
        )

        report = QuorumReport(
            dashboard_source=str(dashboard_path or RESONANCE_LATEST),
            dashboard_loaded=True,
            decision=decision,
            previous_mode=previous_mode,
        )
        ev_success, ev_stdout, ev_stderr = launch_evolutionary_seeder(
            decision, dry_run=args.dry_run)
        report.evolution_launched = True
        report.evolution_success = ev_success
        report.evolution_stdout = ev_stdout
        report.evolution_stderr = ev_stderr
    else:
        report = run_quorum_cycle(
            dry_run=args.dry_run,
            previous_mode=previous_mode,
            dashboard_path=dashboard_path,
        )

    # Persister le mode
    save_current_mode(report.decision.mode)

    # Sauvegarder le rapport
    saved_path = save_quorum_report(report, output_dir=output_dir)

    # ── Résumé console ─────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  QUORUM ORCHESTRATOR - CYCLE TERMINE")
    print(f"  Rapport: {saved_path}")
    print(f"  Theta:   {report.decision.theta}")
    print(f"  Mode:    {report.decision.mode}")
    evo_status = "SUCCES" if report.evolution_success else ("ECHEC" if not args.dry_run else "SIMULATION")
    print(f"  Evolution: {evo_status}")
    print(f"  Transition: {'OUI' if report.transition_detected else 'NON'}")
    print(f"{'=' * 60}")

    # Exit code normalise pour cron :
    #   0 = Theta >= seuil (mode accelere, tout va bien)
    #   1 = Theta < seuil (mode veille, quorum insuffisant)
    #   2 = erreur
    if report.evolution_success is False:
        sys.exit(2)
    elif report.decision.theta >= THETA_THRESHOLD:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
