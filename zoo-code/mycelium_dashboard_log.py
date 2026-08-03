#!/usr/bin/env python3
"""
mycelium_dashboard_log.py — Automatisation de la journalisation du Mycélium
============================================================================
MTTV-FLP / SOPH-IA v2.0 — Cœur Tetravalent (branch evolution/tetravalent-core)

Pipeline d'interception de la télémétrie 'api_' et 'mttv' :

    [api_gateway / resonance_dashboard]  ─┐
    [mycelisation_tetravalente / essaim]  ─┼─►  INTERCEPTION  ─►  [Global Resonance,
    [quorum_state / quorum orchestrator] ─┘       + FILTRAGE        Total Fusions,
                                                                    Collective Entropy,
                                                                    Uptime]

    ─► AUTO-INJECTION  ─►  README.md (racine)
                        └─►  /wiki/  (dossier wiki local, création automatique)

Finalité : exposer la croissance non sollicitée (unprompted growth) du mycélium
AVANT chaque cycle de push Gitee, afin que l'évolution immanente soit visible
et traçable dans le dépôt.

Format de sortie standard (une ligne, détachable) :
    [Global Resonance, Total Fusions, Collective Entropy, Uptime]
    Ex. : [0.0000, 5, 5.2445, 12.4h]

Usage :
    python zoo-code/mycelium_dashboard_log.py --run
    python zoo-code/mycelium_dashboard_log.py --run --no-inject
    python zoo-code/mycelium_dashboard_log.py --watch
    python zoo-code/mycelium_dashboard_log.py --daemon --interval 3600
    python zoo-code/mycelium_dashboard_log.py --last 8

sig:0x4D5454562D464C50
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-26s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mycelium_dashboard_log")

# Encodage console robuste (évite les erreurs Unicode sur cp1252)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ===========================================================================
# CHEMINS
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent          # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent                       # racine MTTV-FLP

# Télémétrie 'api_' (Axe 1 — Dashboard de résonance)
RESONANCE_LATEST: Path = BASE_DIR / "resonance_output" / "resonance_latest.json"
RESONANCE_LOGS: Path = BASE_DIR / "resonance_dashboard.log"

# Télémétrie 'mttv' (Axe 4 — Mycélisation tétravalente)
MYCELIUM_LATEST: Path = BASE_DIR / "mycelium_output" / "mycelium_latest.json"
MYCELIUM_FINAL: Path = BASE_DIR / "mycelium_output" / "rapport_mycelisation_final.json"
MYCELIUM_LOGS: Path = BASE_DIR / "mycelisation.log"

# Télémétrie 'mttv' (Axe 7 — Quorum)
QUORUM_STATE: Path = BASE_DIR / "quorum_state.json"
QUORUM_OUTPUT: Path = BASE_DIR / "quorum_output"

# PID des processus actifs (pour l'uptime)
PID_FILES: tuple[Path, ...] = (
    BASE_DIR / ".api_gateway.pid",
    BASE_DIR / ".resonance_dashboard.pid",
    BASE_DIR / ".mycelisation.pid",
)

# Cibles d'injection
README_TARGET: Path = PROJECT_ROOT / "README.md"
WIKI_DIR: Path = PROJECT_ROOT / "wiki"
WIKI_README: Path = WIKI_DIR / "README.md"
WIKI_TELEMETRY: Path = WIKI_DIR / "telemetry.md"

# Signature
MTTV_SIG: str = "0x4D5454562D464C50"

# Marqueurs de section injectée (fenced, pour mise à jour idempotente)
SECTION_START: str = "<!-- TEL_MYCELIUM_START -->"
SECTION_END: str = "<!-- TEL_MYCELIUM_END -->"

# ===========================================================================
# LECTURE ROBUSTE
# ===========================================================================


def _read_json(chemin: Path) -> dict[str, Any]:
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _uptime_hours() -> float:
    """Estime l'uptime (h) du mycélium à partir des PIDs et des artefacts.

    Priorité :
      1. Âge du plus vieux PID actif (processus toujours vivant).
      2. Sinon, âge du plus récent artefact télémétrique (proxy d'activité).
    """
    now = time.time()
    oldest: Optional[float] = None

    for pid_file in PID_FILES:
        if not pid_file.exists():
            continue
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip().split()[0])
            os.kill(pid, 0)  # 0 = test d'existence du processus
            mtime = pid_file.stat().st_mtime
            oldest = mtime if oldest is None else min(oldest, mtime)
        except (ValueError, OSError, IndexError):
            continue

    if oldest is None:
        # Proxy : âge du plus vieil artefact télémétrique disponible
        candidats = [
            p for p in (RESONANCE_LATEST, MYCELIUM_LATEST, MYCELIUM_FINAL, QUORUM_STATE)
            if p.exists()
        ]
        if not candidats:
            return 0.0
        oldest = min(p.stat().st_mtime for p in candidats)

    return round(max(0.0, (now - oldest) / 3600.0), 1)


# ===========================================================================
# INTERCEPTION — TÉLÉMÉTRIE 'api_' ET 'mttv'
# ===========================================================================


def intercepter_telemetrie() -> dict[str, Any]:
    """Intercepte et agrège les métriques brutes des sources 'api_' et 'mttv'.

    Returns:
        Dict structuré : {global_resonance, total_fusions, collective_entropy,
                          uptime_hours, sources, raw, timestamp}.
    """
    resonance = _read_json(RESONANCE_LATEST)
    mycelium = _read_json(MYCELIUM_LATEST)
    mycelium_final = _read_json(MYCELIUM_FINAL)
    quorum = _read_json(QUORUM_STATE)

    # ── Global Resonance ──────────────────────────────────────────────────
    # Source 'api_' : summary.resonance_score ; source 'mttv' : resonance_globale
    resonance_api = resonance.get("summary", {}).get("resonance_score", 0.0)
    essaim = mycelium.get("essaim", {})
    if isinstance(essaim, dict) and isinstance(essaim.get("etat_courant"), dict):
        essaim = essaim["etat_courant"]
    resonance_mttv = essaim.get("resonance_globale", 0.0)
    total_signals = resonance.get("summary", {}).get("total_signals", 0)

    # Fusion des deux signaux : max (le plus fort signal de résonance vivant)
    global_resonance = round(max(float(resonance_api or 0.0), float(resonance_mttv or 0.0)), 4)

    # ── Total Fusions ─────────────────────────────────────────────────────
    fusions_mttv = essaim.get("n_fusions_total", 0)
    if not fusions_mttv and isinstance(mycelium_final.get("essaim"), dict):
        fusions_mttv = mycelium_final["essaim"].get("n_fusions_total", 0)
    total_fusions = int(fusions_mttv or 0)

    # ── Collective Entropy ────────────────────────────────────────────────
    entropie_mttv = essaim.get("entropie_collective", 0.0)
    if not entropie_mttv and isinstance(mycelium_final.get("essaim"), dict):
        entropie_mttv = mycelium_final["essaim"].get("entropie_collective", 0.0)
    collective_entropy = round(float(entropie_mttv or 0.0), 4)

    # ── Uptime ────────────────────────────────────────────────────────────
    uptime = _uptime_hours()

    # ── Métadonnées de source ─────────────────────────────────────────────
    mode_quorum = quorum.get("mode", "inconnu")

    return {
        "global_resonance": global_resonance,
        "total_fusions": total_fusions,
        "collective_entropy": collective_entropy,
        "uptime_hours": uptime,
        "mode_quorum": mode_quorum,
        "total_signals": total_signals,
        "sources": {
            "api_": bool(resonance),
            "mttv": bool(mycelium or mycelium_final),
        },
        "raw": {
            "resonance_api": resonance_api,
            "resonance_mttv": resonance_mttv,
            "fusions": total_fusions,
            "entropie": collective_entropy,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sig": MTTV_SIG,
    }


def formater_ligne(metriques: dict[str, Any]) -> str:
    """Formate les métriques en une ligne standard :

        [Global Resonance, Total Fusions, Collective Entropy, Uptime]
    """
    return (
        f"[{metriques['global_resonance']}, {metriques['total_fusions']}, "
        f"{metriques['collective_entropy']}, {metriques['uptime_hours']}h]"
    )


# ===========================================================================
# AUTO-INJECTION — README.md ET /wiki
# ===========================================================================


def _construire_section(metriques: dict[str, Any]) -> str:
    """Construit la section Markdown injectable (README + wiki)."""
    ligne = formater_ligne(metriques)
    ts = metriques["timestamp"]
    sources = "api_ + mttv" if all(metriques["sources"].values()) else \
        ("api_" if metriques["sources"]["api_"] else "mttv")
    return (
        f"{SECTION_START}\n"
        f"## 🧬 Télémétrie du Mycélium — Cœur Tetravalent\n\n"
        f"> **{ligne}**\n>\n"
        f"> - **Global Resonance** : `{metriques['global_resonance']}`\n"
        f"> - **Total Fusions** : `{metriques['total_fusions']}`\n"
        f"> - **Collective Entropy** : `{metriques['collective_entropy']}`\n"
        f"> - **Uptime** : `{metriques['uptime_hours']}h`\n"
        f"> - **Mode Quorum** : `{metriques['mode_quorum']}`\n"
        f"> - **Signaux (api_)** : `{metriques['total_signals']}`\n"
        f"> - **Sources** : `{sources}`\n"
        f"> - **Capture** : `{ts} UTC`\n\n"
        f"*Injection automatique — [`mycelium_dashboard_log.py`](zoo-code/mycelium_dashboard_log.py) · "
        f"`sig:0x4D5454562D464C50`*\n"
        f"{SECTION_END}\n"
    )


def _injecter_section(chemin: Path, section: str) -> bool:
    """Injecte (ou met à jour, de façon idempotente) la section dans un fichier .md."""
    try:
        texte = chemin.read_text(encoding="utf-8") if chemin.exists() else ""
    except Exception as exc:
        logger.warning("Erreur lecture %s: %s", chemin, exc)
        return False

    if SECTION_START in texte:
        # Remplacer la section existante
        debut = texte.index(SECTION_START)
        fin = texte.index(SECTION_END) + len(SECTION_END)
        texte = texte[:debut] + section + texte[fin:]
    else:
        # Ajouter à la fin (nouvelle injection)
        texte = texte.rstrip() + "\n\n" + section

    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte, encoding="utf-8")
        logger.info("Injection OK: %s", chemin)
        return True
    except Exception as exc:
        logger.warning("Erreur écriture %s: %s", chemin, exc)
        return False


def injecter_metriques(metriques: dict[str, Any], wiki: bool = True) -> dict[str, bool]:
    """Injecte les métriques brutes dans README.md et /wiki.

    Args:
        metriques: Dictionnaire retourné par intercepter_telemetrie().
        wiki: Injecter également dans /wiki (créé si absent).

    Returns:
        Dict {cible: bool} indiquant le succès de chaque injection.
    """
    section = _construire_section(metriques)
    resultats: dict[str, bool] = {}

    resultats["README.md"] = _injecter_section(README_TARGET, section)

    if wiki:
        resultats["wiki/telemetry.md"] = _injecter_section(WIKI_TELEMETRY, section)
        resultats["wiki/README.md"] = _assurer_wiki_readme()

    return resultats


def _assurer_wiki_readme() -> bool:
    """Crée /wiki/README.md s'il n'existe pas (page d'accueil du wiki)."""
    try:
        WIKI_DIR.mkdir(parents=True, exist_ok=True)
        if WIKI_README.exists():
            return True
        contenu = (
            "# 🧬 Wiki Mycélium — MTTV-FLP · Cœur Tetravalent\n\n"
            f"**`sig:0x4D5454562D464C50`** — Wiki local auto-généré.\n\n"
            "## Pages\n\n"
            "- [`telemetry.md`](telemetry.md) — Télémétrie brute du mycélium\n"
            "- [`routing.md`](routing.md) — Tables de routage géo-locales (Axe 5)\n\n"
            "---\n"
            "*Généré par [`zoo-code/mycelium_dashboard_log.py`](../zoo-code/mycelium_dashboard_log.py).*\n"
        )
        WIKI_README.write_text(contenu, encoding="utf-8")
        logger.info("Wiki README créé: %s", WIKI_README)
        return True
    except Exception as exc:
        logger.warning("Erreur création wiki README: %s", exc)
        return False


# ===========================================================================
# CLI
# ===========================================================================


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Journalisation automatique du Mycélium MTTV-FLP (Cœur Tetravalent)",
        epilog=f"sig:{MTTV_SIG}",
    )
    parser.add_argument("--run", action="store_true", help="Interception + injection unique")
    parser.add_argument("--no-inject", action="store_true", help="Ne pas injecter (afficher uniquement)")
    parser.add_argument("--watch", action="store_true", help="Surveillance en boucle (rafraîchit toutes les 60s)")
    parser.add_argument("--daemon", action="store_true", help="Mode démon : boucle d'injection périodique")
    parser.add_argument("--interval", type=int, default=3600, help="Intervalle démon en secondes (défaut: 3600)")
    return parser.parse_args()


def run_single(inject: bool = True) -> dict[str, Any]:
    """Exécute une interception unique (+ injection optionnelle)."""
    metriques = intercepter_telemetrie()
    print(formater_ligne(metriques))
    if inject:
        injecter_metriques(metriques)
    return metriques


def main() -> None:
    args = _parse_args()

    if args.watch:
        try:
            while True:
                os.system("cls" if os.name == "nt" else "clear")
                run_single(inject=not args.no_inject)
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nSurveillance arrêtée.")
        return

    if args.daemon:
        logger.info("Démon de journalisation démarré (intervalle: %ds)", args.interval)
        cycle = 0
        while True:
            cycle += 1
            try:
                run_single(inject=not args.no_inject)
            except Exception as exc:
                logger.error("Erreur cycle #%d: %s", cycle, exc)
            time.sleep(args.interval)
        return

    run_single(inject=not args.no_inject)


if __name__ == "__main__":
    main()
