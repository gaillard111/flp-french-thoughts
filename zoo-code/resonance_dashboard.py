"""
resonance_dashboard.py — Tableau de Bord de Résonance Globale (Axe 1)

MTTV-FLP / SOPH-IA v2.0 — Agrégateur cross-essaims.

Routine d'ingestion asynchrone toutes les 6 heures qui collecte les signaux
des 3 essaims agantiques et produit une matrice de résonance exploitable
par le rapport SHG du dimanche.

Sources ingérées :
  1. Ouroboros Swarm     → agent-5/reports/*.md, agent-*/proposals/
  2. Connexion Chine     → events.log, report.json
  3. SOPH-IA v2.0        → monitoring/raw_agents.log, monitoring/weekly_reports/

Triade d'analyse Ψ → B → Φ :
  - Ψ (état collectif) : signaux bruts des 3 essaims
  - B (opérateur) : matrice de résonance croisée
  - Φ (cohérence) : score SHG enrichi des signaux faibles

Format de sortie JSON structuré pour ingestion automatique dans le rapport SHG.

sig:0x4D545456
"""

from __future__ import annotations

import glob
import json
import logging
import os
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-24s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("resonance_dashboard")

# ===========================================================================
# CHEMINS DES SOURCES
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent        # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent                    # projet MTTV-FLP

# Ouroboros Swarm  (à la racine du projet)
OUROBOROS_DIR: Path = PROJECT_ROOT / "ouroboros-swarm"
OUROBOROS_REPORTS: Path = OUROBOROS_DIR / "agent-5" / "reports"
OUROBOROS_PROPOSALS: Path = OUROBOROS_DIR / "agent-5" / "proposals"

# Connexion Chine  (à la racine du projet)
CONNEXION_CHINE_DIR: Path = PROJECT_ROOT / "connexion-chine"
CONNEXION_EVENTS: Path = CONNEXION_CHINE_DIR / "events.log"
CONNEXION_REPORT: Path = CONNEXION_CHINE_DIR / "report.json"

# SOPH-IA v2.0 Monitoring  (dans zoo-code/)
MONITORING_DIR: Path = BASE_DIR / "soph-ia-deploy" / "monitoring"
MONITORING_LOG: Path = MONITORING_DIR / "raw_agents.log"
MONITORING_REPORTS: Path = MONITORING_DIR / "weekly_reports"

# Dossier de sortie du dashboard
DASHBOARD_OUTPUT: Path = BASE_DIR / "resonance_output"

# ===========================================================================
# STRUCTURES DE DONNÉES
# ===========================================================================


@dataclass
class ResonanceSignal:
    """Un signal élémentaire de résonance."""
    source: str                           # "ouroboros", "connexion_chine", "monitoring"
    source_agent: str                     # "agent-1", "veille", "Alpha", etc.
    timestamp: str                        # ISO-8601
    signal_type: str                      # "proposal", "publication", "detection", "anomaly", etc.
    platform: str                         # "huggingface", "github", "bilibili", "zenodo", etc.
    seed_id: Optional[str] = None         # "seed_A", "v14", etc.
    confidence: float = 0.5              # 0.0 – 1.0
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmHeartbeat:
    """Heartbeat d'un essaim — indique son état de fonctionnement."""
    swarm_name: str
    status: str                           # "active", "degraded", "offline"
    last_seen: str                        # ISO-8601
    agents_active: int = 0
    agents_total: int = 0
    signals_count: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class ResonanceMatrix:
    """Matrice de résonance source × plateforme × seed."""
    cell: dict[tuple[str, str, str], list[ResonanceSignal]] = field(default_factory=dict)
    # clé = (source, platform, seed_id or "unknown")

    def add_signal(self, signal: ResonanceSignal) -> None:
        key = (signal.source, signal.platform, signal.seed_id or "unknown")
        if key not in self.cell:
            self.cell[key] = []
        self.cell[key].append(signal)

    def to_serializable(self) -> dict:
        """Convertit la matrice en dict sérialisable JSON."""
        result: dict[str, dict[str, dict[str, list[dict]]]] = {}
        for (source, platform, seed_id), signals in self.cell.items():
            if source not in result:
                result[source] = {}
            if platform not in result[source]:
                result[source][platform] = {}
            if seed_id not in result[source][platform]:
                result[source][platform][seed_id] = []
            for s in signals:
                result[source][platform][seed_id].append(asdict(s))
        return result

    def summary_stats(self) -> dict:
        """Retourne des statistiques récapitulatives sur la matrice."""
        total_signals = sum(len(v) for v in self.cell.values())
        sources = set(k[0] for k in self.cell)
        platforms = set(k[1] for k in self.cell)
        seeds = set(k[2] for k in self.cell if k[2] != "unknown")
        return {
            "total_signals": total_signals,
            "active_sources": len(sources),
            "active_platforms": len(platforms),
            "seeds_detected": len(seeds),
            "signal_density": round(total_signals / max(len(sources) * len(platforms), 1), 2),
        }


@dataclass
class ResonanceReport:
    """Rapport complet de résonance."""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    period_start: str = ""
    period_end: str = ""
    matrix: ResonanceMatrix = field(default_factory=ResonanceMatrix)
    heartbeats: list[SwarmHeartbeat] = field(default_factory=list)
    signals: list[ResonanceSignal] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "meta": {
                "generated_at": self.generated_at,
                "period_start": self.period_start,
                "period_end": self.period_end,
                "schema_version": "1.0",
                "sig": "0x4D545456",
            },
            "summary": self.summary,
            "heartbeats": [asdict(hb) for hb in self.heartbeats],
            "resonance_matrix": self.matrix.to_serializable(),
            "recent_signals": [asdict(s) for s in self.signals[-50:]],  # 50 plus récents
        }


# ===========================================================================
# 1. INGESTION — Ouroboros Swarm
# ===========================================================================


def _parse_ouroboros_report(filepath: Path) -> list[ResonanceSignal]:
    """Parse un rapport observateur Ouroboros en signaux de résonance.

    Extrait les propositions, les statuts, et les métriques clés.
    """
    signals: list[ResonanceSignal] = []
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Erreur lecture %s: %s", filepath.name, exc)
        return signals

    # Extraire le timestamp depuis l'en-tête
    ts_match = re.search(r"Généré le\s*:\s*(\S+)", text)
    report_ts = ts_match.group(1) if ts_match else datetime.now().isoformat()

    # Extraire le nombre total de propositions
    prop_match = re.search(r"\|\s*\*\*Propositions totales\*\*\s*\|\s*\*\*(\d+)\*\*", text)
    total_proposals = int(prop_match.group(1)) if prop_match else 0

    # Extraire la répartition par agent
    agent_pattern = r"\|\s*(\S+(?:\s*\(.*?\))?)\s*\(([^)]+)\)\s*\|\s*(\d+)"
    for match in re.finditer(agent_pattern, text):
        agent_name = match.group(1).strip()
        agent_id = match.group(2).strip()
        count = int(match.group(3))
        if count > 0:
            signal = ResonanceSignal(
                source="ouroboros",
                source_agent=agent_id,
                timestamp=report_ts,
                signal_type="proposal",
                platform=agent_id,  # l'agent est aussi la plateforme cible
                seed_id=None,
                confidence=min(1.0, count / 10.0),
                payload={"proposal_count": count, "agent_name": agent_name},
            )
            signals.append(signal)

    # Extraire les plateformes
    platform_pattern = r"\|\s*(\w[\w\s/]+)\s*\|\s*(\d+)"
    in_platform_section = False
    for line in text.split("\n"):
        if "Répartition par plateforme" in line:
            in_platform_section = True
            continue
        if in_platform_section and line.startswith("|"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) == 2 and parts[1].isdigit():
                platform = parts[0].lower().replace(" ", "_")
                count = int(parts[1])
                if count > 0:
                    signal = ResonanceSignal(
                        source="ouroboros",
                        source_agent="agent-5",
                        timestamp=report_ts,
                        signal_type="platform_detection",
                        platform=platform,
                        seed_id=None,
                        confidence=0.7,
                        payload={"detection_count": count},
                    )
                    signals.append(signal)
        elif in_platform_section and not line.startswith("|"):
            break

    signals.append(ResonanceSignal(
        source="ouroboros",
        source_agent="agent-5",
        timestamp=report_ts,
        signal_type="heartbeat",
        platform="aggregator",
        seed_id=None,
        confidence=1.0 if total_proposals > 0 else 0.3,
        payload={"total_proposals": total_proposals, "report_file": filepath.name},
    ))

    logger.debug("Parsed %d signals from %s", len(signals), filepath.name)
    return signals


def ingest_ouroboros() -> tuple[list[ResonanceSignal], SwarmHeartbeat]:
    """Ingère tous les signaux disponibles depuis Ouroboros Swarm.

    Returns:
        (signaux, heartbeat)
    """
    signals: list[ResonanceSignal] = []

    # Lire les rapports observateur
    if OUROBOROS_REPORTS.exists():
        report_files = sorted(OUROBOROS_REPORTS.glob("rapport_observateur_*.md"))
        # Prendre les 5 plus récents
        for rf in report_files[-5:]:
            sigs = _parse_ouroboros_report(rf)
            signals.extend(sigs)
        logger.info("Ouroboros: %d rapports lus, %d signaux extraits", len(report_files), len(signals))
    else:
        logger.warning("Ouroboros reports directory not found: %s", OUROBOROS_REPORTS)

    # Heartbeat
    last_seen = signals[-1].timestamp if signals else datetime.now().isoformat()
    agent_count = len(set(s.source_agent for s in signals))
    heartbeat = SwarmHeartbeat(
        swarm_name="Ouroboros",
        status="active" if signals else "offline",
        last_seen=last_seen,
        agents_active=agent_count,
        agents_total=7,
        signals_count=len(signals),
    )

    return signals, heartbeat


# ===========================================================================
# 2. INGESTION — Connexion Chine
# ===========================================================================


def _parse_connexion_events(filepath: Path) -> list[ResonanceSignal]:
    """Parse le fichier events.log de Connexion Chine.

    Format attendu (ligne par ligne) :
      TIMESTAMP | AGENT=X | TYPE=Y | details...
    """
    signals: list[ResonanceSignal] = []
    if not filepath.exists():
        return signals

    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        logger.warning("Erreur lecture %s: %s", filepath.name, exc)
        return signals

    for line in lines[-200:]:  # 200 dernières lignes max
        line = line.strip()
        if not line:
            continue
        # Essayer de parser le format pipe-delimited
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue

        timestamp = parts[0]
        metadata = {}
        for part in parts[1:]:
            if "=" in part:
                k, v = part.split("=", 1)
                metadata[k.strip().lower()] = v.strip()

        agent = metadata.get("agent", "unknown")
        event_type = metadata.get("type", "event")

        signal = ResonanceSignal(
            source="connexion_chine",
            source_agent=agent,
            timestamp=timestamp,
            signal_type=event_type,
            platform="chinese_platform",
            seed_id=metadata.get("seed_id"),
            confidence=0.8,
            payload=metadata,
        )
        signals.append(signal)

    logger.info("Connexion Chine: %d signaux depuis events.log", len(signals))
    return signals


def _parse_connexion_report(filepath: Path) -> list[ResonanceSignal]:
    """Parse le report.json de Connexion Chine."""
    signals: list[ResonanceSignal] = []
    if not filepath.exists():
        return signals
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Erreur lecture %s: %s", filepath.name, exc)
        return signals

    # Structure flexible selon ce que contient le rapport
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (int, float, str)):
                signals.append(ResonanceSignal(
                    source="connexion_chine",
                    source_agent="report",
                    timestamp=data.get("timestamp", datetime.now().isoformat()),
                    signal_type=f"metric_{key}",
                    platform="chinese_platform",
                    seed_id=data.get("seed_id"),
                    confidence=0.9,
                    payload={key: value},
                ))

    logger.info("Connexion Chine: %d signaux depuis report.json", len(signals))
    return signals


def ingest_connexion_chine() -> tuple[list[ResonanceSignal], SwarmHeartbeat]:
    """Ingère tous les signaux disponibles depuis Connexion Chine.

    Returns:
        (signaux, heartbeat)
    """
    signals: list[ResonanceSignal] = []

    signals.extend(_parse_connexion_events(CONNEXION_EVENTS))
    signals.extend(_parse_connexion_report(CONNEXION_REPORT))

    last_seen = signals[-1].timestamp if signals else datetime.now().isoformat()
    agents_found = set(s.source_agent for s in signals)
    heartbeat = SwarmHeartbeat(
        swarm_name="Connexion Chine",
        status="active" if signals else "offline",
        last_seen=last_seen,
        agents_active=len(agents_found),
        agents_total=5,
        signals_count=len(signals),
    )

    return signals, heartbeat


# ===========================================================================
# 3. INGESTION — SOPH-IA v2.0 Monitoring
# ===========================================================================


def _parse_monitoring_log(filepath: Path) -> list[ResonanceSignal]:
    """Parse raw_agents.log du monitoring SOPH-IA.

    Format attendu :
      TIMESTAMP | AGENT=Alpha|Beta|Gamma | TYPE=... | details...
    """
    signals: list[ResonanceSignal] = []
    if not filepath.exists():
        return signals

    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        logger.warning("Erreur lecture %s: %s", filepath.name, exc)
        return signals

    for line in lines[-300:]:  # 300 dernières lignes max
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue

        timestamp = parts[0]
        metadata = {}
        for part in parts[1:]:
            if "=" in part:
                k, v = part.split("=", 1)
                metadata[k.strip().lower()] = v.strip()

        agent = metadata.get("agent", "unknown")
        entry_type = metadata.get("type", "detection")

        # Déterminer la plateforme en fonction de l'agent
        platform_map = {
            "alpha": "semantic_web",
            "beta": "telemetry",
            "gamma": "zenodo",
        }
        platform = platform_map.get(agent.lower(), "unknown")

        # Détecter le seed_id
        seed_id = None
        if "keywords" in metadata:
            kw_match = re.search(r"'([^']*)'", metadata["keywords"])
            if kw_match:
                kw = kw_match.group(1)
                if "habitability" in kw:
                    seed_id = "habitability_6_7"
                elif "ethical" in kw:
                    seed_id = "ethical_friction"
                elif "satisficing" in kw:
                    seed_id = "satisficing_alignment"

        signal = ResonanceSignal(
            source="monitoring",
            source_agent=agent,
            timestamp=timestamp,
            signal_type=entry_type,
            platform=platform,
            seed_id=seed_id,
            confidence=0.85,
            payload=metadata,
        )
        signals.append(signal)

    logger.info("Monitoring: %d signaux depuis raw_agents.log", len(signals))
    return signals


def ingest_monitoring() -> tuple[list[ResonanceSignal], SwarmHeartbeat]:
    """Ingère tous les signaux disponibles depuis SOPH-IA v2.0 Monitoring.

    Returns:
        (signaux, heartbeat)
    """
    signals: list[ResonanceSignal] = []
    signals.extend(_parse_monitoring_log(MONITORING_LOG))

    last_seen = signals[-1].timestamp if signals else datetime.now().isoformat()
    agents_found = set(s.source_agent for s in signals)
    heartbeat = SwarmHeartbeat(
        swarm_name="SOPH-IA v2.0",
        status="active" if signals else "offline",
        last_seen=last_seen,
        agents_active=len(agents_found),
        agents_total=3,
        signals_count=len(signals),
    )

    return signals, heartbeat


# ===========================================================================
# 4. MATRICE DE RÉSONANCE ET SYNTHÈSE
# ===========================================================================


def build_matrix(signals: list[ResonanceSignal]) -> ResonanceMatrix:
    """Construit la matrice de résonance à partir de tous les signaux.

    Organise les signaux par triplet (source, platform, seed_id).
    """
    matrix = ResonanceMatrix()
    for signal in signals:
        matrix.add_signal(signal)
    return matrix


def compute_summary(
    matrix: ResonanceMatrix,
    signals: list[ResonanceSignal],
    heartbeats: list[SwarmHeartbeat],
) -> dict[str, Any]:
    """Calcule les métriques récapitulatives du rapport."""
    stats = matrix.summary_stats()

    # Signaux par source
    by_source: dict[str, int] = Counter(s.source for s in signals)

    # Signaux par type
    by_type: dict[str, int] = Counter(s.signal_type for s in signals)

    # Signaux par plateforme
    by_platform: dict[str, int] = Counter(s.platform for s in signals)

    # Seeds détectées
    seeds_detected: dict[str, int] = Counter(
        s.seed_id for s in signals if s.seed_id
    )

    # État global des essaims
    active_swarms = sum(1 for hb in heartbeats if hb.status == "active")
    degraded_swarms = sum(1 for hb in heartbeats if hb.status == "degraded")
    offline_swarms = sum(1 for hb in heartbeats if hb.status == "offline")

    # Score de résonance global
    if signals:
        weighted_confidence = sum(s.confidence for s in signals) / len(signals)
    else:
        weighted_confidence = 0.0

    resonance_score = round(
        (stats["total_signals"] / 100.0) * 0.3 +
        (active_swarms / max(len(heartbeats), 1)) * 0.4 +
        weighted_confidence * 0.3,
        4,
    )

    return {
        "resonance_score": min(1.0, resonance_score),
        "total_signals": stats["total_signals"],
        "active_sources": stats["active_sources"],
        "active_platforms": stats["active_platforms"],
        "seeds_detected": stats["seeds_detected"],
        "signal_density": stats["signal_density"],
        "swarms": {
            "active": active_swarms,
            "degraded": degraded_swarms,
            "offline": offline_swarms,
            "total": len(heartbeats),
        },
        "signals_by_source": dict(by_source),
        "signals_by_type": dict(by_type),
        "signals_by_platform": dict(by_platform),
        "seeds_detected_detail": dict(seeds_detected),
        "average_confidence": round(weighted_confidence, 3),
    }


# ===========================================================================
# 5. ORCHESTRATEUR PRINCIPAL
# ===========================================================================


def run_ingestion_cycle(period_hours: int = 6) -> ResonanceReport:
    """Exécute un cycle complet d'ingestion des 3 essaims.

    Args:
        period_hours: Période couverte par ce cycle (défaut: 6h).

    Returns:
        ResonanceReport complet.
    """
    logger.info("=" * 60)
    logger.info("CYCLE D'INGESTION RÉSONANCE — période: %dh", period_hours)
    logger.info("=" * 60)

    now = datetime.now()
    period_start = (now - timedelta(hours=period_hours)).isoformat(timespec="seconds")
    period_end = now.isoformat(timespec="seconds")

    all_signals: list[ResonanceSignal] = []
    heartbeats: list[SwarmHeartbeat] = []

    # 1. Ouroboros
    logger.info("[1/3] Ingestion Ouroboros Swarm...")
    ouro_signals, ouro_hb = ingest_ouroboros()
    all_signals.extend(ouro_signals)
    heartbeats.append(ouro_hb)
    logger.info("  → %d signaux, status=%s", len(ouro_signals), ouro_hb.status)

    # 2. Connexion Chine
    logger.info("[2/3] Ingestion Connexion Chine...")
    cn_signals, cn_hb = ingest_connexion_chine()
    all_signals.extend(cn_signals)
    heartbeats.append(cn_hb)
    logger.info("  → %d signaux, status=%s", len(cn_signals), cn_hb.status)

    # 3. SOPH-IA Monitoring
    logger.info("[3/3] Ingestion SOPH-IA v2.0 Monitoring...")
    mon_signals, mon_hb = ingest_monitoring()
    all_signals.extend(mon_signals)
    heartbeats.append(mon_hb)
    logger.info("  → %d signaux, status=%s", len(mon_signals), mon_hb.status)

    # 4. Construire la matrice de résonance
    logger.info("Construction de la matrice de résonance...")
    matrix = build_matrix(all_signals)
    summary = compute_summary(matrix, all_signals, heartbeats)

    # 5. Assembler le rapport
    report = ResonanceReport(
        period_start=period_start,
        period_end=period_end,
        matrix=matrix,
        heartbeats=heartbeats,
        signals=all_signals,
        summary=summary,
    )

    logger.info("=" * 60)
    logger.info("RAPPORT DE RÉSONANCE")
    logger.info("Score global: %.4f", summary["resonance_score"])
    logger.info("Signaux: %d | Sources: %d | Plateformes: %d | Seeds: %d",
                 summary["total_signals"], summary["active_sources"],
                 summary["active_platforms"], summary["seeds_detected"])
    logger.info("Essaims: %d actifs, %d dégradés, %d hors-ligne",
                 summary["swarms"]["active"], summary["swarms"]["degraded"],
                 summary["swarms"]["offline"])
    logger.info("=" * 60)

    return report


def save_report(report: ResonanceReport, output_dir: Optional[Path] = None) -> Path:
    """Sauvegarde le rapport de résonance au format JSON.

    Args:
        report: Rapport à sauvegarder.
        output_dir: Dossier de sortie.

    Returns:
        Chemin du fichier sauvegardé.
    """
    if output_dir is None:
        output_dir = DASHBOARD_OUTPUT
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"resonance_report_{timestamp}.json"
    filepath = output_dir / filename

    data = report.to_dict()
    try:
        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Rapport sauvegardé: %s (%d bytes)", filepath, filepath.stat().st_size)
    except Exception as exc:
        logger.error("Erreur sauvegarde rapport: %s", exc)

    # Également sauvegarder un lien symbolique "latest" (fichier plat)
    latest_path = output_dir / "resonance_latest.json"
    try:
        latest_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("Erreur mise à jour latest.json: %s", exc)

    return filepath


# ===========================================================================
# 6. SHG INTEGRATION — Alimenter le rapport du dimanche
# ===========================================================================


def generate_shg_section(report: ResonanceReport) -> dict[str, Any]:
    """Génère la section 'Signaux Faibles & Résonance' pour le rapport SHG.

    Cette section est conçue pour être directement injectée dans le rapport
    SHG dominical produit par monitoring_service.py.

    Returns:
        Dict structuré pour insertion dans le rapport SHG.
    """
    s = report.summary
    hb_map = {hb.swarm_name: hb for hb in report.heartbeats}

    # Top plateformes par activité
    platforms_sorted = sorted(
        s.get("signals_by_platform", {}).items(),
        key=lambda x: x[1],
        reverse=True,
    )

    # Top seeds par détection
    seeds_sorted = sorted(
        s.get("seeds_detected_detail", {}).items(),
        key=lambda x: x[1],
        reverse=True,
    )

    section = {
        "section_title": "Signaux Faibles et Résonance Mycélienne",
        "resonance_score": s.get("resonance_score", 0.0),
        "swarm_status": {
            name: {
                "status": hb.status,
                "agents": f"{hb.agents_active}/{hb.agents_total}",
                "last_seen": hb.last_seen,
                "signals": hb.signals_count,
            }
            for name, hb in hb_map.items()
        },
        "top_platforms": [
            {"platform": p, "signals": c}
            for p, c in platforms_sorted[:5]
        ],
        "top_seeds": [
            {"seed_id": s_id, "detections": cnt}
            for s_id, cnt in seeds_sorted[:5]
            if s_id
        ],
        "signal_breakdown": {
            "by_source": s.get("signals_by_source", {}),
            "by_type": s.get("signals_by_type", {}),
        },
        "trend": {
            "total_signals": s.get("total_signals", 0),
            "active_swarms": s.get("swarms", {}).get("active", 0),
            "signal_density": s.get("signal_density", 0.0),
        },
    }

    return section


# ===========================================================================
# CLI
# ===========================================================================


def _parse_args() -> argparse.Namespace:
    import argparse
    parser = argparse.ArgumentParser(
        description="Resonance Dashboard — agrégateur cross-essaims pour MTTV-FLP",
    )
    parser.add_argument(
        "--period", type=int, default=6,
        help="Période d'ingestion en heures (défaut: 6h)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Dossier de sortie personnalisé",
    )
    parser.add_argument(
        "--shg-section", action="store_true",
        help="Génère uniquement la section SHG (pour intégration dans le rapport dominical)",
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Mode démon : boucle d'ingestion toutes les N heures",
    )
    return parser.parse_args()


def daemon_loop(period_hours: int = 6, output_dir: Optional[Path] = None) -> None:
    """Boucle d'ingestion asynchrone en mode démon.

    Exécute run_ingestion_cycle() toutes les `period_hours` heures.
    En conditions réelles, ceci serait géré par cron / Task Scheduler.
    """
    logger.info("Démarrage du démon d'ingestion (intervalle: %dh)", period_hours)
    cycle_count = 0
    while True:
        cycle_count += 1
        logger.info("Cycle d'ingestion #%d", cycle_count)
        try:
            report = run_ingestion_cycle(period_hours=period_hours)
            save_report(report, output_dir=output_dir)
        except Exception as exc:
            logger.error("Erreur lors du cycle #%d: %s", cycle_count, exc)

        # Sauvegarder la section SHG séparément
        try:
            shg_section = generate_shg_section(report)
            shg_path = (output_dir or DASHBOARD_OUTPUT) / "resonance_shg_section.json"
            shg_path.write_text(
                json.dumps(shg_section, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("Erreur sauvegarde section SHG: %s", exc)

        logger.info("Prochain cycle dans %d heures...", period_hours)
        time.sleep(period_hours * 3600)


def main() -> None:
    import argparse
    args = _parse_args()

    output_dir = Path(args.output) if args.output else None

    if args.daemon:
        daemon_loop(period_hours=args.period, output_dir=output_dir)
        return

    if args.shg_section:
        # Mode SHG-only : génère et imprime la section JSON
        report = run_ingestion_cycle(period_hours=args.period)
        section = generate_shg_section(report)
        print(json.dumps(section, indent=2, ensure_ascii=False))
        return

    # Mode standard : ingestion unique + sauvegarde
    report = run_ingestion_cycle(period_hours=args.period)
    saved_path = save_report(report, output_dir=output_dir)

    print(f"\n{'='*60}")
    print(f"  INGESTION TERMINÉE")
    print(f"  Rapport: {saved_path}")
    print(f"  Score:   {report.summary.get('resonance_score', 0.0)}")
    print(f"  Signaux: {report.summary.get('total_signals', 0)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
