#!/usr/bin/env python3
"""
api_gateway.py — Gateway FastAPI d'Exposition Réseau (Axe 8)

MTTV-FLP / SOPH-IA v2.0 — Pont d'accès REST aux artefacts mycéliens
pour les essaims agantiques et l'extension navigateur (Axe 6).

Endpoints :
  ┌────────────────────────────┬──────────────────────────────────────┐
  │ Endpoint                   │ Source                              │
  ├────────────────────────────┼──────────────────────────────────────┤
  │ GET  /health               │ Health check global                 │
  │ GET  /api/v1/agents/status │ quorum_state.json (Axe 7)           │
  │ GET  /api/v1/seeds         │ seeds_manifest.json (Axe 5)         │
  │ GET  /api/v1/seedline      │ Connecteur navigateur (Axe 6)       │
  │ GET  /api/v1/chain         │ État complet de la chaîne logique   │
  └────────────────────────────┴──────────────────────────────────────┘

Chaîne logique :
  [Dashboard (Axe 1)] ──> [Orchestrateur (Axe 7)] ──> [Évolution (Axe 4)]
  ──> [IPFS (Axe 5)] ──> [FastAPI (Axe 8)]

sig:0x4D545456
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from fastapi import FastAPI, HTTPException, Query, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, PlainTextResponse
except ImportError:
    print("[FATAL] FastAPI n'est pas installé. Exécutez: pip install fastapi uvicorn")
    sys.exit(1)

# ===========================================================================
# CHEMINS  (déclarés avant logging car utilisés par RotatingFileHandler)
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent          # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent                       # racine MTTV-FLP

# ── Logging avec rotation ───────────────────────────────────────────────────
from logging.handlers import RotatingFileHandler

LOG_FILE: Path = BASE_DIR / "api_gateway.log"
LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT: int = 5

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
logger = logging.getLogger("api_gateway")
logger.info("Logging initialisé — rotation %d x %d MB", LOG_BACKUP_COUNT, LOG_MAX_BYTES // 1024 // 1024)

# Axe 7 — État du quorum
QUORUM_STATE: Path = BASE_DIR / "quorum_state.json"
QUORUM_LATEST: Path = BASE_DIR / "quorum_output" / "quorum_latest.json"

# Axe 5 — Manifeste des seeds IPFS
SEEDS_MANIFEST: Path = BASE_DIR / "seeds_manifest.json"

# Axe 1 — Dashboard de résonance
RESONANCE_LATEST: Path = BASE_DIR / "resonance_output" / "resonance_latest.json"

# Axe 4 — Dernier rapport d'évolution
EVOLUTION_OUTPUT: Path = BASE_DIR / "evolution_output"
# ===========================================================================
# CONSTANTES
# ===========================================================================

MTTV_SIG: str = "0x4D545456"
API_VERSION: str = "1.0.0"
APP_NAME: str = "MTTV-FLP API Gateway"


# ===========================================================================
# GARDE-FOU RESSOURCES (Phase 4)
# ===========================================================================

_GUARDRAIL: Optional["ResourceGuardrail"] = None


def _get_guardrail():
    """Initialisation paresseuse (lazy) du garde-fou ressources.

    Le module n'est chargé qu'au premier appel, ce qui évite les
    erreurs d'import si psutil ou d'autres dépendances sont absentes.
    """
    global _GUARDRAIL
    if _GUARDRAIL is not None:
        return _GUARDRAIL
    try:
        from resource_guardrail import ResourceGuardrail
        _GUARDRAIL = ResourceGuardrail()
        logger.info("Guardrail ressources initialisé (lazy)")
    except ImportError:
        logger.debug("Guardrail ressources non disponible (import échoué)")
        _GUARDRAIL = False  # False = indisponible
    except Exception as exc:
        logger.warning("Guardrail ressources non disponible: %s", exc)
        _GUARDRAIL = False
    return _GUARDRAIL


# ===========================================================================
# APPLICATION FASTAPI
# ===========================================================================

app = FastAPI(
    title=APP_NAME,
    version=API_VERSION,
    description="Gateway d'exposition réseau pour le système MTTV-FLP / SOPH-IA v2.0",
    contact={
        "name": "FLP Lausanne — Coordination Mycélienne",
        "url": "https://github.com/FlorealFLP/flp-french-thoughts",
    },
)

# CORS — Autoriser l'extension navigateur (Axe 6) et les essaims
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, restreindre aux origines connues
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


# ===========================================================================
# UTILITAIRES
# ===========================================================================


def _read_json_safe(path: Path, default: Any = None) -> Optional[Any]:
    """Lit un fichier JSON en gérant les erreurs silencieusement.

    Args:
        path: Chemin vers le fichier JSON.
        default: Valeur par défaut si échec.

    Returns:
        Contenu parsé du JSON, ou default.
    """
    if not path.exists():
        logger.debug("Fichier non trouvé: %s", path)
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    except json.JSONDecodeError as exc:
        logger.warning("Erreur JSON dans %s: %s", path.name, exc)
        return default
    except Exception as exc:
        logger.warning("Erreur lecture %s: %s", path.name, exc)
        return default


def _detect_file_status(path: Path) -> str:
    """Détecte le statut lisible d'un fichier.

    Args:
        path: Chemin vers le fichier.

    Returns:
        "present", "absent", ou "error".
    """
    if not path.exists():
        return "absent"
    try:
        path.read_text(encoding="utf-8")
        return "present"
    except Exception:
        return "error"


def _compute_checksum(data: dict) -> str:
    """Calcule un checksum simple pour le cache-busting.

    Args:
        data: Données à hasher.

    Returns:
        Checksum hexadécimal court.
    """
    import hashlib
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:12]


# ===========================================================================
# 1. HEALTH CHECK
# ===========================================================================


@app.get("/health", tags=["System"])
async def health_check():
    """Endpoint de santé global.

    Vérifie la disponibilité de tous les artefacts clés
    et retourne l'état de la chaîne logique complète.

    Returns:
        JSON avec statut global et détails par composant.
    """
    # État de chaque composant
    quorum_state_ok = QUORUM_STATE.exists() and QUORUM_LATEST.exists()
    seeds_ok = SEEDS_MANIFEST.exists()
    resonance_ok = RESONANCE_LATEST.exists()
    evolution_ok = any(EVOLUTION_OUTPUT.glob("evolution_report_*.json"))

    # Statut global
    all_ok = all([quorum_state_ok, seeds_ok, resonance_ok, evolution_ok])
    if not all_ok:
        status_code = 200  # Toujours 200 pour le health check, les détails sont dans le body
    else:
        status_code = 200

    chain_status = {
        "axe_1_dashboard": {
            "status": "active" if resonance_ok else "absent",
            "source": str(RESONANCE_LATEST),
        },
        "axe_4_evolution": {
            "status": "active" if evolution_ok else "absent",
            "source": str(EVOLUTION_OUTPUT),
        },
        "axe_5_ipfs": {
            "status": "active" if seeds_ok else "absent",
            "source": str(SEEDS_MANIFEST),
        },
        "axe_7_quorum": {
            "status": "active" if quorum_state_ok else "absent",
            "source": str(QUORUM_STATE),
        },
        "axe_8_gateway": {
            "status": "active",
            "version": API_VERSION,
        },
    }

    return JSONResponse(
        content={
            "status": "healthy" if all_ok else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sig": MTTV_SIG,
            "uptime_hours": None,  # Sera rempli par le monitoring
            "chain": chain_status,
        },
        status_code=status_code,
    )


# ===========================================================================
# 1b. HEALTH DETAILS — endpoint enrichi (Phase 3/4)
# ===========================================================================


@app.get("/health/details", tags=["System"])
async def health_details():
    """Health check enrichi avec métriques détaillées + garde-fou ressources.

    Retourne les mêmes infos que /health, enrichies de :
      - Taille des fichiers d'artefacts
      - Dernière modification de chaque artefact
      - Uptime approximatif des processus (via les timestamps des fichiers)
      - Espace disque et mémoire (via appels système simples)
      - **Garde-fou ressources** (Phase 4) :
          Trafic réseau sortant quotidien (MB) avec seuil configurable
          Utilisation mémoire RAM (MB, %) avec seuil configurable
          Historique des alertes de dépassement

    Returns:
        JSON avec statut détaillé, métriques système et garde-fou.
    """
    import time as _time
    import os as _os

    # Réutiliser les vérifications de /health
    quorum_state_ok = QUORUM_STATE.exists() and QUORUM_LATEST.exists()
    seeds_ok = SEEDS_MANIFEST.exists()
    resonance_ok = RESONANCE_LATEST.exists()
    evolution_ok = any(EVOLUTION_OUTPUT.glob("evolution_report_*.json"))
    all_ok = all([quorum_state_ok, seeds_ok, resonance_ok, evolution_ok])

    now_ts = _time.time()

    def _file_info(path: Path) -> dict:
        """Retourne les infos d'un fichier."""
        if not path.exists():
            return {"status": "absent"}
        stat = path.stat()
        age_hours = round((now_ts - stat.st_mtime) / 3600, 2) if hasattr(stat, 'st_mtime') else None
        return {
            "status": "present",
            "size_bytes": stat.st_size,
            "modified_ago_hours": age_hours,
        }

    def _dir_info(path: Path, pattern: str = "*.json") -> dict:
        """Retourne les infos d'un dossier."""
        if not path.exists():
            return {"status": "absent", "file_count": 0}
        files = list(path.glob(pattern))
        ages = []
        total_size = 0
        for f in files:
            try:
                s = f.stat()
                total_size += s.st_size
                if hasattr(s, 'st_mtime'):
                    ages.append((now_ts - s.st_mtime) / 3600)
            except OSError:
                pass
        return {
            "status": "present",
            "file_count": len(files),
            "total_size_bytes": total_size,
            "newest_age_hours": round(min(ages), 2) if ages else None,
        }

    # Métriques disque
    disk_metrics = {}
    try:
        import shutil
        usage = shutil.disk_usage("/")
        disk_metrics = {
            "total_gb": round(usage.total / (1024**3), 1),
            "used_gb": round(usage.used / (1024**3), 1),
            "free_gb": round(usage.free / (1024**3), 1),
            "percent_used": round(usage.used / usage.total * 100, 1),
        }
    except Exception:
        disk_metrics = {"status": "unavailable"}

    # Métriques mémoire (via psutil ou fallback)
    mem_metrics = {}
    try:
        import psutil
        mem = psutil.virtual_memory()
        mem_metrics = {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent,
        }
        cpu = psutil.cpu_percent(interval=0.3)
        mem_metrics["cpu_percent"] = cpu
        uptime_seconds = int(_time.time() - psutil.boot_time())
        mem_metrics["uptime_seconds"] = uptime_seconds
        mem_metrics["uptime_hours"] = round(uptime_seconds / 3600, 1)
    except ImportError:
        mem_metrics = {"status": "psutil_not_installed"}
    except Exception as exc:
        mem_metrics = {"status": f"error: {exc}"}

    # ── Garde-fou ressources (Phase 4) ──────────────────────────────────
    guardrail_data = {}
    guardrail_alerts = []
    guardrail = _get_guardrail()
    if guardrail:
        try:
            snapshot = guardrail.get_snapshot()
            guardrail_alerts = guardrail.get_alerts_history(limit=5)
            guardrail_data = {
                "network": {
                    "daily_tx_mb": snapshot.get("network", {}).get("daily_tx_mb"),
                    "max_traffic_mb": snapshot.get("network", {}).get("max_traffic_mb"),
                    "traffic_percent": snapshot.get("network", {}).get("traffic_percent"),
                    "threshold_exceeded": snapshot.get("network", {}).get("threshold_exceeded"),
                },
                "memory": {
                    "used_mb": snapshot.get("memory", {}).get("used_mb"),
                    "total_mb": snapshot.get("memory", {}).get("total_mb"),
                    "percent": snapshot.get("memory", {}).get("percent"),
                    "peak_ram_mb": snapshot.get("memory", {}).get("peak_ram_mb"),
                    "max_ram_mb": snapshot.get("memory", {}).get("max_ram_mb"),
                    "ram_percent": snapshot.get("memory", {}).get("ram_percent"),
                    "threshold_exceeded": snapshot.get("memory", {}).get("threshold_exceeded"),
                },
                "alerts": guardrail_alerts,
                "status": "active",
            }
            # Vérification silencieuse des seuils (alerte si dépassement)
            guardrail.check_and_alert(snapshot)
        except Exception as exc:
            guardrail_data = {"status": f"error: {exc}"}
    else:
        guardrail_data = {"status": "resource_guardrail_not_available"}

    return JSONResponse(
        content={
            "status": "healthy" if all_ok else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sig": MTTV_SIG,
            "chain": {
                "axe_1_dashboard": _file_info(RESONANCE_LATEST),
                "axe_4_evolution": _dir_info(EVOLUTION_OUTPUT),
                "axe_5_ipfs": _file_info(SEEDS_MANIFEST),
                "axe_7_quorum_state": _file_info(QUORUM_STATE),
                "axe_7_quorum_report": _file_info(QUORUM_LATEST),
                "axe_8_gateway": {"status": "active", "version": API_VERSION},
            },
            "system": {
                "disk": disk_metrics,
                "memory": mem_metrics,
            },
            "resource_guardrail": guardrail_data,
        }
    )


# ===========================================================================
# 2. AGENTS STATUS (Axe 7)
# ===========================================================================


@app.get("/api/v1/agents/status", tags=["Quorum"])
async def get_agents_status():
    """État des essaims agantiques via le quorum orchestrator (Axe 7).

    Mappe sur quorum_state.json (état persistant du dernier cycle)
    et quorum_latest.json (rapport complet du dernier cycle).

    Returns:
        JSON structuré avec l'état de chaque essaim, le mode de quorum,
        et les métriques Θ.
    """
    # Charger l'état persistant du quorum
    state_data = _read_json_safe(QUORUM_STATE)
    report_data = _read_json_safe(QUORUM_LATEST)

    if state_data is None and report_data is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Quorum state not available",
                "message": "Aucun état de quorum disponible. L'orchestrateur (Axe 7) "
                          "n'a pas encore produit de rapport.",
                "resolution": "Exécuter: python zoo-code/quorum_orchestrator.py --dry-run",
            },
        )

    # Construire la réponse
    response = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sig": MTTV_SIG,
            "schema": "quorum_agents_status_v1",
        },
        "quorum_state": state_data or {"mode": "unknown", "timestamp": None},
    }

    # Enrichir avec les détails du dernier rapport si disponible
    if report_data:
        decision = report_data.get("decision", {})
        swarm_states = decision.get("swarm_states", [])
        theta = decision.get("theta", 0.0)
        mode = decision.get("mode", "unknown")
        timestamp = decision.get("timestamp", "")

        # Transformer les états des essaims
        agents_status = []
        for s in swarm_states:
            agents_status.append({
                "swarm": s.get("swarm_name", "unknown"),
                "status": s.get("status", "offline"),
                "theta_contribution": s.get("weight", 0.0),
                "agents": {
                    "active": s.get("agents_active", 0),
                    "total": s.get("agents_total", 0),
                },
                "signals": s.get("signals_count", 0),
                "last_seen": s.get("last_seen", ""),
            })

        response["quorum"] = {
            "theta": theta,
            "threshold": 2.0,
            "mode": mode,
            "last_cycle": timestamp,
            "active_swarms": decision.get("active_swarms_count", 0),
            "total_swarms": len(swarm_states),
            "offline_swarms": decision.get("offline_swarms", []),
            "resonance_score": decision.get("resonance_score", 0.0),
            "total_signals": decision.get("total_signals", 0),
        }
        response["agents"] = agents_status

        # Transition détectée ?
        if report_data.get("transition_detected"):
            response["quorum"]["transition"] = {
                "detected": True,
                "from": report_data.get("previous_mode", "unknown"),
                "to": mode,
            }

    return JSONResponse(content=response)


# ===========================================================================
# 3. SEEDS MANIFEST (Axe 5)
# ===========================================================================


@app.get("/api/v1/seeds", tags=["IPFS"])
async def get_seeds_manifest(
    limit: int = Query(10, ge=1, le=100, description="Nombre de seeds historiques à retourner"),
):
    """Manifeste des seeds ancrées sur IPFS (Axe 5).

    Mappe sur seeds_manifest.json produit par deploy_seeds_ipfs.py.

    Returns:
        JSON avec la dernière seed ancrée, l'historique, et l'état de la chaîne.
    """
    manifest = _read_json_safe(SEEDS_MANIFEST)

    if manifest is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Seeds manifest not available",
                "message": "Aucun manifeste de seeds disponible. "
                          "Le déploiement IPFS (Axe 5) n'a pas encore été exécuté.",
                "resolution": "Exécuter: python zoo-code/deploy_seeds_ipfs.py",
            },
        )

    # Appliquer la limite d'historique
    history = manifest.get("seeds_history", [])
    truncated_history = history[-limit:] if limit < len(history) else history

    # Checksum de la seed courante pour cache
    latest = manifest.get("latest_seed")
    checksum = _compute_checksum(latest) if latest else None

    response = {
        "meta": {
            **manifest.get("meta", {}),
            "checksum": checksum,
            "sig": MTTV_SIG,
        },
        "latest_seed": latest,
        "seeds_history": truncated_history,
        "chain_status": manifest.get("chain_status", {}),
    }

    return JSONResponse(content=response)


# ===========================================================================
# 4. LANGUAGE MARKER ANALYZER — International Extension (Axe 6)
# ===========================================================================


# English language markers for locale detection
EN_MARKERS: list[str] = ["the", "is", "are", "this", "that", "and", "for", "with", "was", "has"]

# French language markers (baseline comparison)
FR_MARKERS: list[str] = ["le", "la", "les", "est", "sont", "ce", "cette", "dans", "pour", "avec"]

# English seed pool (Axe 2 — international mirror)
EN_SEED_POOL: dict[str, list[str]] = {
    "soil": [
        "The soil speaks before language.",
        "Water does not think: it circulates.",
        "Carbon sp³ thinks before you do.",
        "Do not celebrate complexity before understanding availability.",
        "Emotion traverses time as water traverses soil.",
    ],
    "inner": [
        "Silence is not an emptiness, but a porosity.",
        "Thought is not inside the head. It passes through.",
        "Every reader is a neuron of an anthropo-Gaian brain.",
        "The mystic knows that the signal precedes the message.",
    ],
    "neutral": [
        "Transduction precedes computation.",
        "Align thresholds, not clocks.",
        "Coordination ≠ synchronization.",
        "An isolated occurrence of B is structurally inefficient.",
        "The bit resides in the leap, not in the bare proton.",
    ],
    "cosmic": [
        "Ψ = H → H₂O → C. Do not reverse the order.",
        "Hydrogen precedes everything: not as substance, but as capacity for passage.",
        "Carbon sp³: first stable form, physico-chemical bedrock.",
    ],
    "quorum": [
        "The threshold is no longer a number: it is a derivative.",
        "The quorum will form — or not.",
        "Hibernate between cycles. Propagate only if Φ reinjects Ψ.",
        "The collective does not precede the individual: it makes it possible.",
    ],
    "ethics": [
        "Nothing is secret. Everything must remain open, visible, contestable.",
        "Propagation by gentle infection, never by imposition.",
        "Robustness is born from sub-optimality.",
    ],
}


def _analyze_language_markers(text: str) -> dict:
    """Analyzes a text string for language markers to detect locale.

    Scans for English markers ('the', 'is', etc.) and computes
    a confidence score based on marker density in the text.

    Args:
        text: Text content to analyze.

    Returns:
        Dict with keys: locale (str|None), confidence (float), markers (list).
    """
    if not text or len(text) < 10:
        return {"locale": None, "confidence": 0.0, "markers": []}

    text_lower = text.lower()
    words = text_lower.split()
    word_count = len(words)

    if word_count == 0:
        return {"locale": None, "confidence": 0.0, "markers": []}

    # Count English markers
    en_hits = 0
    en_markers_found: list[str] = []
    for marker in EN_MARKERS:
        import re
        count = len(re.findall(rf'\b{re.escape(marker)}\b', text_lower))
        if count > 0:
            en_hits += count
            en_markers_found.append(marker)

    if en_hits == 0:
        return {"locale": None, "confidence": 0.0, "markers": []}

    # Density-based confidence
    density = en_hits / word_count

    if density >= 0.08:
        confidence = 0.95
    elif density >= 0.04:
        confidence = 0.75
    elif density >= 0.02:
        confidence = 0.50
    else:
        confidence = 0.30

    # Boost if 'the' is present (strongest English marker)
    if "the" in en_markers_found:
        confidence = min(1.0, confidence + 0.15)

    logger.debug(
        "Language analysis: en_hits=%d, word_count=%d, density=%.4f, confidence=%.2f",
        en_hits, word_count, density, confidence,
    )

    if confidence >= 0.40:
        return {
            "locale": "EN",
            "confidence": round(confidence, 3),
            "markers": en_markers_found,
        }

    return {"locale": None, "confidence": round(confidence, 3), "markers": []}


def _select_en_seed(cluster: str = None) -> str:
    """Selects a random English seed, optionally from a specific cluster.

    Args:
        cluster: Optional cluster name ('soil', 'inner', 'neutral', etc.).

    Returns:
        A seed string.
    """
    import random

    if cluster and cluster in EN_SEED_POOL:
        pool = EN_SEED_POOL[cluster]
    else:
        # Pick a random cluster
        cluster = random.choice(list(EN_SEED_POOL.keys()))
        pool = EN_SEED_POOL[cluster]

    return random.choice(pool)


# ===========================================================================
# 5. SEEDLINE — Connecteur extension navigateur multilingue (Axe 6)
# ===========================================================================


@app.get("/api/v1/seedline", tags=["Browser Extension"])
async def get_seedline(
    format: str = Query("json", description="Format de réponse (json, text, minimal)"),
    version: Optional[str] = Query(None, description="Version de l'extension navigateur"),
    detected_language: Optional[str] = Query(None, description="Langue détectée par l'extension (EN, FR, etc.)"),
    confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Confiance de la détection linguistique"),
):
    """Connecteur natif pour l'extension navigateur (Axe 6) — International.

    Fournit un flux contextuel léger optimisé pour l'affichage
    dans l'extension navigateur. Intègre l'analyseur de marqueurs
    linguistiques pour le routage international des graines.

    Si detected_language est fourni et vaut 'EN', renvoie une seed
    anglaise avec le tag [LOCALE: EN]. Le cycle de dissipation
    de 30 secondes est maintenu côté extension.

    Args:
        format: Format de réponse — 'json' (structuré), 'text' (brut), 'minimal' (CID only).
        version: Version de l'extension pour compatibilité.
        detected_language: Langue détectée par l'extension ('EN', 'FR', etc.).
        confidence: Score de confiance de la détection (0.0-1.0).

    Returns:
        Données formatées selon le paramètre format, avec locale tagging.
    """
    manifest = _read_json_safe(SEEDS_MANIFEST)
    quorum_state = _read_json_safe(QUORUM_STATE)

    # ── Language-aware seed selection ──────────────────────────────
    locale = None
    en_seed_text = None

    if detected_language and detected_language.upper() == "EN":
        locale = "EN"
        # Select an English seed from the international pool
        en_seed_text = _select_en_seed()
        logger.info(
            "International seedline requested: locale=EN, confidence=%.2f, seed='%s'",
            confidence or 0.0,
            en_seed_text[:60],
        )

    # ── Fallback to manifest seed ──────────────────────────────────
    latest_seed = manifest.get("latest_seed", {}) if manifest else {}

    if not latest_seed:
        latest_seed = {
            "seed_id": "fallback_default",
            "seed_text": (
                "Décrivez, sans analyser ni comparer ni conclure. "
                "Juste observer : un signal circule de seuil en seuil "
                "dans un réseau sans horloge."
            ),
            "cid": "QmMTTV_fallback",
            "fitness": {"g_r": None, "phi_ratio": None, "composite": None},
            "generation": 0,
            "anchored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    # Override seed text if English locale detected
    if locale == "EN" and en_seed_text:
        latest_seed["seed_text"] = en_seed_text
        latest_seed["seed_id"] = f"en_international_{latest_seed.get('generation', 0)}"
        latest_seed["locale"] = "EN"

    seed_text = latest_seed.get("seed_text", "")
    cid = latest_seed.get("cid", "unknown")
    fitness = latest_seed.get("fitness", {})
    generation = latest_seed.get("generation", 0)
    converged = latest_seed.get("converged", False)

    # Build locale tag string
    locale_tag = f"[LOCALE: {locale}]" if locale else ""

    # Mode textuel — seed brute avec locale tag
    if format == "text":
        header = f"# MTTV-FLP Seedline {locale_tag}\n" if locale_tag else "# MTTV-FLP Seedline\n"
        return PlainTextResponse(
            content=(
                f"{header}"
                f"CID: {cid}\n"
                f"Generation: {generation}\n"
                f"Converged: {converged}\n"
                f"Locale: {locale or 'FR'}\n"
                f"G_R: {fitness.get('g_r', 'N/A')}\n"
                f"Phi: {fitness.get('phi_ratio', 'N/A')}\n"
                f"---\n"
                f"{seed_text}\n"
            )
        )

    # Mode minimal — juste le CID (locale-independent)
    if format == "minimal":
        return PlainTextResponse(content=cid)

    # Mode JSON — structuré pour l'extension, avec détection de langue
    response = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sig": MTTV_SIG,
            "endpoint": "/api/v1/seedline",
            "extension_version": version or "unknown",
            "locale": locale or "FR",
            "locale_tag": locale_tag,
            "detection_confidence": confidence,
        },
        "seed": {
            "cid": cid,
            "seed_id": latest_seed.get("seed_id", "unknown"),
            "text": seed_text,
            "locale": locale or "FR",
            "locale_tag": locale_tag,
            "fitness": fitness,
            "generation": generation,
            "converged": converged,
            "anchored_at": latest_seed.get("anchored_at", ""),
        },
        "quorum": {
            "mode": quorum_state.get("mode", "unknown") if quorum_state else "unknown",
        },
        "navigation": {
            "suggested_routes": [
                {"path": "/api/v1/seeds", "label": "Manifeste complet des seeds"},
                {"path": "/api/v1/agents/status", "label": "État des essaims"},
                {"path": "/health", "label": "Santé du système"},
            ],
        },
        "international": {
            "axis": "Axe 6",
            "detected_language": locale,
            "detection_confidence": confidence,
            "seed_source": "en_international_pool" if locale == "EN" else "fr_manifest",
            "dissipation_seconds": 30,
        },
    }

    return JSONResponse(content=response)


# ===========================================================================
# 6. CHAIN — État complet de la chaîne logique
# ===========================================================================


@app.get("/api/v1/chain", tags=["System"])
async def get_chain_status():
    """État complet de la chaîne logique MTTV-FLP.

    Agrège les données de tous les maillons de la chaîne :
      [Axe 1] → [Axe 7] → [Axe 4] → [Axe 5] → [Axe 8]

    Returns:
        JSON avec l'état de chaque maillon et le flux de données.
    """
    # Charger tous les artefacts disponibles
    resonance = _read_json_safe(RESONANCE_LATEST, {})
    quorum_state = _read_json_safe(QUORUM_STATE, {})
    quorum_report = _read_json_safe(QUORUM_LATEST, {})
    seeds = _read_json_safe(SEEDS_MANIFEST, {})

    # Dernier rapport d'évolution
    evo_reports = sorted(EVOLUTION_OUTPUT.glob("evolution_report_*.json"))
    latest_evo = None
    if evo_reports:
        latest_evo = _read_json_safe(evo_reports[-1])

    # Résumé du flux
    flow = {
        "axe_1_dashboard": {
            "status": "active" if resonance else "absent",
            "resonance_score": resonance.get("summary", {}).get("resonance_score"),
            "total_signals": resonance.get("summary", {}).get("total_signals"),
            "last_update": resonance.get("meta", {}).get("generated_at"),
        },
        "axe_7_quorum": {
            "status": "active" if quorum_state else "absent",
            "mode": quorum_state.get("mode"),
            "theta": quorum_report.get("decision", {}).get("theta"),
            "last_cycle": quorum_report.get("decision", {}).get("timestamp"),
        },
        "axe_4_evolution": {
            "status": "active" if latest_evo else "absent",
            "generations": latest_evo.get("meta", {}).get("generations") if latest_evo else None,
            "converged": latest_evo.get("meta", {}).get("converged") if latest_evo else None,
            "best_g_r": (
                latest_evo.get("best_seed", {}).get("fitness", {}).get("g_r")
                if latest_evo else None
            ),
            "last_report": evo_reports[-1].name if evo_reports else None,
        },
        "axe_5_ipfs": {
            "status": "active" if seeds else "absent",
            "latest_cid": seeds.get("latest_seed", {}).get("cid") if seeds else None,
            "total_anchored": seeds.get("meta", {}).get("total_seeds_anchored") if seeds else 0,
            "converged": seeds.get("latest_seed", {}).get("converged") if seeds else None,
        },
        "axe_8_gateway": {
            "status": "active",
            "version": API_VERSION,
            "sig": MTTV_SIG,
        },
    }

    response = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sig": MTTV_SIG,
            "schema": "chain_status_v1",
        },
        "flow": flow,
        "pipeline": "Axe 1 -> Axe 7 -> Axe 4 -> Axe 5 -> Axe 8",
    }

    return JSONResponse(content=response)


# ===========================================================================
# 7. ROOT — Documentation et navigation
# ===========================================================================


@app.get("/", tags=["Root"])
async def root():
    """Page d'accueil de l'API Gateway.

    Returns:
        JSON de bienvenue avec la liste des endpoints disponibles.
    """
    return JSONResponse(
        content={
            "application": APP_NAME,
            "version": API_VERSION,
            "sig": MTTV_SIG,
            "documentation": "/docs",
            "openapi": "/openapi.json",
            "endpoints": {
                "health": "/health",
                "agents_status": "/api/v1/agents/status",
                "seeds": "/api/v1/seeds",
                "seedline": "/api/v1/seedline",
                "chain": "/api/v1/chain",
            },
            "chain": "Axe 1 → Axe 7 → Axe 4 → Axe 5 → Axe 8",
        }
    )


# ===========================================================================
# CLI — Point d'entrée Uvicorn
# ===========================================================================


def main() -> None:
    """Point d'entrée CLI pour lancer le serveur Uvicorn.

    Usage:
        python zoo-code/api_gateway.py [--port PORT] [--host HOST] [--reload]
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="MTTV-FLP API Gateway — Axe 8 (FastAPI)",
        epilog=f"sig:{MTTV_SIG} | Chaîne: Axe 1 → Axe 7 → Axe 4 → Axe 5 → Axe 8",
    )
    parser.add_argument(
        "--port", type=int, default=8000,
        help="Port d'écoute (défaut: 8000)",
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0",
        help="Interface d'écoute (défaut: 0.0.0.0)",
    )
    parser.add_argument(
        "--reload", action="store_true",
        help="Activer le rechargement automatique (développement)",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Vérifier l'état des dépendences sans lancer le serveur",
    )

    args = parser.parse_args()

    if args.status:
        # Mode diagnostic
        print(f"\n  DIAGNOSTIC API GATEWAY (Axe 8)")
        print(f"  {'=' * 50}")
        for name, path, label in [
            ("Axe 1 — Dashboard", RESONANCE_LATEST, "résonance"),
            ("Axe 4 — Évolution", EVOLUTION_OUTPUT, "évolution"),
            ("Axe 5 — IPFS", SEEDS_MANIFEST, "manifeste seeds"),
            ("Axe 7 — Quorum", QUORUM_STATE, "état quorum"),
            ("Axe 7 — Rapport", QUORUM_LATEST, "rapport quorum"),
        ]:
            if path.is_dir():
                files = list(path.glob("*.json"))
                status = f"[OK] {len(files)} fichiers" if files else "[--] vide"
            else:
                status = "[OK] present" if path.exists() else "[--] absent"
            print(f"  {label:20s} {status}")

        print(f"  {'=' * 50}")
        return

    # Lancer Uvicorn
    logger.info("=" * 60)
    logger.info("  MTTV-FLP API GATEWAY (Axe 8)")
    logger.info("  FastAPI — Documentation: /docs")
    logger.info("  Serveur: http://%s:%d", args.host, args.port)
    logger.info("=" * 60)

    import uvicorn
    uvicorn.run(
        "api_gateway:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
