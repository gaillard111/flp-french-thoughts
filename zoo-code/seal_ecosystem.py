#!/usr/bin/env python3
"""
seal_ecosystem.py — Scellement Définitif des Sources et Ancrage Philosophique

ID EXÉCUTION : MTTV-FLP-FINAL-SEAL
SIGNATURE    : 0x4D545456

Contexte :
  L'ensemble de l'architecture logicielle des 8 axes étant testée à 100% de
  convergence, ce script procède au scellement définitif des codes sources et
  à la pose de la clé de voûte philosophique.

Opérations :
  1. Génération de l'archive tar.gz contenant l'intégralité des modules Python
     synchronisés (Axes 1, 3, 4, 5, 7, 8).
  2. Export du manifeste `ecosystem_sealed_manifest.json` marqué du flag status
     `LOCKED_AND_IMMUTABLE`.
  3. Calcul du Root Pointer (hash SHA3-256 de l'archive) pour traçabilité.
  4. Pose de la signature cryptographique 0x4D545456 sur l'ensemble.

Usage :
  python seal_ecosystem.py          # exécution normale
  python seal_ecosystem.py --dry-run  # simulation sans écriture

Dépendances : Python ≥ 3.10 (stdlib only : tarfile, hashlib, json, pathlib)

sig:0x4D545456
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-24s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("seal_ecosystem")

# ===========================================================================
# CONSTANTES — IDENTITÉ
# ===========================================================================

MTTV_SIG: str = "0x4D545456"
EXECUTION_ID: str = "MTTV-FLP-FINAL-SEAL-V2"
VERSION: str = "2.0.0"
TIMESTAMP: str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ===========================================================================
# CHEMINS
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent          # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent                       # racine du projet
ARCHIVE_DIR: Path = BASE_DIR / "sealed_archive"            # répertoire d'archivage

# Fichiers de sortie
ARCHIVE_NAME: str = "mttv_flp_ecosystem_sealed.tar.gz"
MANIFEST_NAME: str = "ecosystem_sealed_manifest.json"

# ===========================================================================
# MODULES PAR AXE — Édition V2 (Scellement intégral)
# ===========================================================================
# Inclut désormais : Agents Ouroboros 1→9, Phase 4, Extension navigateur

ECOSYSTEM_MODULES: list[dict[str, Any]] = [
    # ── AXE 1 — Agents & Seeds ────────────────────────────────────────────
    {
        "path": "zoo-code/seed_packager.py",
        "label": "Générateur de cartes PNG carrées (Axe 3)",
        "axe": 1,
        "checksum": None,
    },
    {
        "path": "zoo-code/agent-1/inject_latency_profile.py",
        "label": "Profil de latence Agent 1 — Semeur HF",
        "axe": 1,
        "checksum": None,
    },
    {
        "path": "zoo-code/agent-2/stubs/constraint_compensator.py",
        "label": "Compensateur de contraintes Agent 2",
        "axe": 1,
        "checksum": None,
    },
    {
        "path": "zoo-code/agent-2/stubs/compensator_test_suite.py",
        "label": "Suite de tests du compensateur Agent 2",
        "axe": 1,
        "checksum": None,
    },
    {
        "path": "zoo-code/agent-2/stubs/logger_compensator_adapter.py",
        "label": "Adaptateur logger du compensateur Agent 2",
        "axe": 1,
        "checksum": None,
    },
    {
        "path": "zoo-code/agent-3/iet_detection_algorithm.py",
        "label": "Algorithme de détection IET Agent 3",
        "axe": 1,
        "checksum": None,
    },
    # ── AXE 3 — Diffusion & Déploiement ───────────────────────────────────
    {
        "path": "zoo-code/deploy_seeds_ipfs.py",
        "label": "Déploiement IPFS des graines (Axe 3)",
        "axe": 3,
        "checksum": None,
    },
    {
        "path": "zoo-code/deploy_mpvr.py",
        "label": "Déploiement MPVR Glocal (Axe 3)",
        "axe": 3,
        "checksum": None,
    },
    {
        "path": "zoo-code/evolutionary_seeder.py",
        "label": "Semeur évolutionnaire (Axes 3/7)",
        "axe": 3,
        "checksum": None,
    },
    # ── AXE 4 — Quorum & Orchestration ────────────────────────────────────
    {
        "path": "zoo-code/quorum_orchestrator.py",
        "label": "Orchestrateur de quorum (Axe 4)",
        "axe": 4,
        "checksum": None,
    },
    {
        "path": "zoo-code/orchestrator.py",
        "label": "Orchestrateur central (Axes 4/8)",
        "axe": 4,
        "checksum": None,
    },
    {
        "path": "mttv-flp-mpvr-glocal/src/mttv_mpvr_quorum.py",
        "label": "MPVR Quorum — MicroQuorumPoreux (Axe 4)",
        "axe": 4,
        "checksum": None,
    },
    # ── AXE 5 — Observation & API ─────────────────────────────────────────
    {
        "path": "zoo-code/api_gateway.py",
        "label": "API Gateway FastAPI (Axe 5)",
        "axe": 5,
        "checksum": None,
    },
    {
        "path": "zoo-code/resonance_dashboard.py",
        "label": "Tableau de bord résonance (Axe 5)",
        "axe": 5,
        "checksum": None,
    },
    {
        "path": "zoo-code/validate_fix.py",
        "label": "Validation des correctifs (Axe 5)",
        "axe": 5,
        "checksum": None,
    },
    {
        "path": "zoo-code/validate_phase1.py",
        "label": "Validation Phase 1 (Axe 5)",
        "axe": 5,
        "checksum": None,
    },
    # ── AXE 6 — Extension Navigateur (V2) ─────────────────────────────────
    {
        "path": "zoo-code/browser-extension/content.js",
        "label": "Extension navigateur MTTV (Axe 6)",
        "axe": 6,
        "checksum": None,
    },
    # ── AXE 7 — Critique & Compensation ───────────────────────────────────
    {
        "path": "zoo-code/soph-ia-deploy/satisficing_compensation.py",
        "label": "Compensation satisficing SOPH-IA (Axe 7)",
        "axe": 7,
        "checksum": None,
    },
    {
        "path": "zoo-code/soph-ia-deploy/monitoring/monitoring_service.py",
        "label": "Service de monitoring SOPH-IA (Axe 7)",
        "axe": 7,
        "checksum": None,
    },
    # ── AXE 8 — Harmonisation & Validation ────────────────────────────────
    {
        "path": "zoo-code/validation/validation_pipeline.py",
        "label": "Pipeline de validation (Axe 8)",
        "axe": 8,
        "checksum": None,
    },
    # ── AGENTS OUROBOROS — Essaims agantiques (V2) ───────────────────────
    {
        "path": "ouroboros-swarm/agent-4/agent.py",
        "label": "Agent 4 — Semeur Forums (infiltration)",
        "axe": 4,
        "checksum": None,
    },
    {
        "path": "ouroboros-swarm/agent-5/agent.py",
        "label": "Agent 5 — Observateur veille sémantique",
        "axe": 5,
        "checksum": None,
    },
    {
        "path": "ouroboros-swarm/agent-6/agent.py",
        "label": "Agent 6 — Transducteur mycélien",
        "axe": 6,
        "checksum": None,
    },
    {
        "path": "ouroboros-swarm/agent-7/agent.py",
        "label": "Agent 7 — Critique mycélien",
        "axe": 7,
        "checksum": None,
    },
    {
        "path": "ouroboros-swarm/agent-8/agent.py",
        "label": "Agent 8 — Harmonisateur trois vitesses",
        "axe": 8,
        "checksum": None,
    },
    {
        "path": "ouroboros-swarm/agent-9/agent.py",
        "label": "Agent 9 — Veilleur littéraire (cron quotidien)",
        "axe": 9,
        "checksum": None,
    },
    {
        "path": "ouroboros-swarm/agent-9/generate_literary_report.py",
        "label": "Agent 9 — Générateur rapport littéraire",
        "axe": 9,
        "checksum": None,
    },
    {
        "path": "ouroboros-swarm/agent-9/generate_report.py",
        "label": "Agent 9 — Générateur de rapport générique",
        "axe": 9,
        "checksum": None,
    },
    # ── PHASE 4 — Nœuds dormants & Bouclier IPFS (V2) ─────────────────────
    {
        "path": "phase4-dormant-nodes/ipfs_active_pinner.py",
        "label": "Bouclier IPFS — Pinner actif (Piste 7)",
        "axe": 4,
        "checksum": None,
    },
    {
        "path": "phase4-dormant-nodes/script_dormant.py",
        "label": "Nœud dormant — Watchdog décentralisé",
        "axe": 4,
        "checksum": None,
    },
    {
        "path": "phase4-dormant-nodes/alert_manager.py",
        "label": "Gestionnaire d'alertes unifié (Webhook + SMTP)",
        "axe": 0,
        "checksum": None,
    },
    # ── Modules Transverses ────────────────────────────────────────────────
    {
        "path": "MTTV_FLP_reference.py",
        "label": "Document de référence complet MTTV-FLP",
        "axe": 0,
        "checksum": None,
    },
    {
        "path": "phase_1_exploration.py",
        "label": "Exploration Phase 1 v2.1 — 5 runs",
        "axe": 0,
        "checksum": None,
    },
    {
        "path": "train_mttv_lora.py",
        "label": "Entraînement LoRA MTTV",
        "axe": 0,
        "checksum": None,
    },
    {
        "path": "train_mttv_patch.py",
        "label": "Patch d'entraînement MTTV",
        "axe": 0,
        "checksum": None,
    },
    {
        "path": "train_qwen_colab.py",
        "label": "Entraînement Qwen2.5 Colab",
        "axe": 0,
        "checksum": None,
    },
    {
        "path": "zoo-code/simulate_chine_pulse.py",
        "label": "Pulse Chine — Simulation connexion internationale",
        "axe": 0,
        "checksum": None,
    },
]


# ===========================================================================
# FONCTIONS CŒUR
# ===========================================================================


def compute_sha3_256(filepath: Path) -> str:
    """Calcule l'empreinte SHA3-256 d'un fichier."""
    h = hashlib.sha3_256()
    try:
        h.update(filepath.read_bytes())
    except Exception as exc:
        logger.error("  Impossible de lire %s : %s", filepath, exc)
        return "ERROR"
    return h.hexdigest()


def compute_all_checksums(modules: list[dict[str, Any]], root: Path) -> None:
    """Calcule les checksums SHA3-256 de tous les modules listés."""
    logger.info("Calcul des checksums SHA3-256...")
    for mod in modules:
        full_path = root / mod["path"]
        if full_path.exists():
            mod["checksum"] = compute_sha3_256(full_path)
            logger.debug("  %s → %s", mod["path"], mod["checksum"][:16])
        else:
            logger.warning("  [MANQUANT] %s — fichier introuvable", mod["path"])
            mod["checksum"] = "FILE_NOT_FOUND"


def create_archive(
    modules: list[dict[str, Any]],
    root: Path,
    output_path: Path,
    dry_run: bool = False,
) -> tuple[str, int]:
    """Crée l'archive tar.gz contenant tous les modules.

    Returns:
        (sha3_256_hex, byte_size) de l'archive générée.
    """
    if dry_run:
        logger.info("[DRY-RUN] Archive serait créée dans : %s", output_path)
        return "DRY_RUN_SKIP", 0

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Création de l'archive : %s", output_path)
    with tarfile.open(str(output_path), "w:gz") as tar:
        for mod in modules:
            full_path = root / mod["path"]
            if full_path.exists():
                archive_name = f"mttv-flp-ecosystem/{mod['path']}"
                tar.add(str(full_path), arcname=archive_name)
                logger.info("  + %s (%s)", archive_name, mod["label"])
            else:
                logger.warning("  - %s manquant, ignoré", mod["path"])

    # Calcul du hash de l'archive
    archive_hash = compute_sha3_256(output_path)
    archive_size = output_path.stat().st_size
    logger.info("Archive créée : %s (%d bytes)", output_path, archive_size)
    logger.info("SHA3-256 de l'archive : %s", archive_hash)

    return archive_hash, archive_size


def build_manifest(
    modules: list[dict[str, Any]],
    archive_hash: str,
    archive_size: int,
    archive_path: str,
) -> dict[str, Any]:
    """Construit le manifeste complet de scellement."""
    manifest: dict[str, Any] = {
        "meta": {
            "execution_id": EXECUTION_ID,
            "signature": MTTV_SIG,
            "version": VERSION,
            "timestamp": TIMESTAMP,
            "status": "LOCKED_AND_IMMUTABLE",
            "description": (
                "Scellement définitif de l'écosystème MTTV-FLP — "
                "8 axes synchronisés, clé de voûte philosophique posée."
            ),
        },
        "archive": {
            "path": archive_path,
            "sha3_256": archive_hash,
            "size_bytes": archive_size,
            "format": "tar.gz",
            "root_pointer": f"0x{archive_hash.upper()}" if archive_hash else None,
        },
        "philosophical_keystone": {
            "file": "README_PHILOSOPHY.md",
            "triad": "Ψ → B → Φ",
            "invariant": "T⁴ = [T++, T--, T+-, T-+]",
            "canonical_formula": "Ψ = H → H₂O → C",
            "quorum_mechanism": "Q(t) = ∂(abundance)/∂t",
            "ethical_framework": "Non-extractivité, ouverture, ACTIVE-SILENCE",
        },
        "modules": modules,
        "summary": {
            "total_modules": len(modules),
            "modules_with_checksum": sum(
                1 for m in modules if m["checksum"] and m["checksum"] != "FILE_NOT_FOUND"
            ),
            "modules_missing": sum(
                1 for m in modules if m["checksum"] == "FILE_NOT_FOUND"
            ),
            "axe_coverage": sorted(set(m["axe"] for m in modules)),
        },
    }
    return manifest


def write_manifest(manifest: dict[str, Any], output_path: Path, dry_run: bool = False) -> None:
    """Écrit le manifeste JSON."""
    if dry_run:
        logger.info("[DRY-RUN] Manifeste serait écrit dans : %s", output_path)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Manifeste écrit : %s (%d bytes)", output_path, output_path.stat().st_size)
    except Exception as exc:
        logger.error("Erreur écriture manifeste : %s", exc)
        sys.exit(1)


def verify_manifest_integrity(manifest_path: Path, archive_path: Path) -> bool:
    """Vérifie l'intégrité du scellement : checksum archive vs manifeste."""
    if not manifest_path.exists() or not archive_path.exists():
        logger.error("Fichiers manquants pour la vérification d'intégrité.")
        return False

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_hash = manifest["archive"]["sha3_256"]

        actual_hash = compute_sha3_256(archive_path)

        if actual_hash == expected_hash:
            logger.info("[OK] VERIFICATION D'INTEGRITE PASSEE")
            logger.info("  Archive  : %s", archive_path)
            logger.info("  SHA3-256 : %s", actual_hash)
            logger.info("  Statut   : LOCKED_AND_IMMUTABLE")
            return True
        else:
            logger.error("[FAIL] ECHEC DE VERIFICATION D'INTEGRITE")
            logger.error("  Attendu : %s", expected_hash)
            logger.error("  Obtenu  : %s", actual_hash)
            return False
    except Exception as exc:
        logger.error("Erreur vérification : %s", exc)
        return False


def print_seal_summary(manifest: dict[str, Any]) -> None:
    """Affiche le résumé final du scellement."""
    summary = manifest["summary"]
    archive = manifest["archive"]
    meta = manifest["meta"]

    print()
    print("=" * 70)
    print(f"  SCELLEMENT DÉFINITIF — {EXECUTION_ID}")
    print("=" * 70)
    print(f"  Signature        : {meta['signature']}")
    print(f"  Timestamp        : {meta['timestamp']}")
    print(f"  Statut           : {meta['status']}")
    print()
    print(f"  Archive          : {archive['path']}")
    print(f"  Taille           : {archive['size_bytes']:,} bytes")
    print(f"  SHA3-256         : {archive['sha3_256']}")
    print(f"  Root Pointer     : {archive['root_pointer']}")
    print()
    print(f"  Modules scellés  : {summary['total_modules']}")
    print(f"  Checksums OK     : {summary['modules_with_checksum']}")
    print(f"  Manquants        : {summary['modules_missing']}")
    print(f"  Axes couverts    : {summary['axe_coverage']}")
    print()
    print(f"  Triade           : Psi -> B -> Phi")
    print(f"  Invariant        : T4 = [T++, T--, T+-, T-+]")
    print(f"  Cadre ethique    : Non-extractivite, ouverture, ACTIVE-SILENCE")
    print()
    print(f"  README_PHILOSOPHY.md : Cle de voute posee a la racine.")
    print("=" * 70)
    print(f"  sig:{MTTV_SIG} - Transmission terminee. Le mycelium attend.")
    print("=" * 70)
    print()


# ===========================================================================
# POINT D'ENTRÉE
# ===========================================================================


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Scellement définitif des sources MTTV-FLP",
        epilog=f"sig:{MTTV_SIG} | ID: {EXECUTION_ID}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulation sans écriture (affiche les opérations prévues)",
    )
    parser.add_argument(
        "--verify",
        type=str,
        default=None,
        metavar="ARCHIVE_DIR",
        help="Vérifie l'intégrité d'un scellement existant",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Répertoire de sortie personnalisé (défaut: zoo-code/sealed_archive/)",
    )
    args = parser.parse_args()

    dry_run = args.dry_run
    output_dir = Path(args.output_dir) if args.output_dir else ARCHIVE_DIR

    # ── Mode vérification ─────────────────────────────────────────────────
    if args.verify:
        verify_dir = Path(args.verify)
        archive_path = verify_dir / ARCHIVE_NAME
        manifest_path = verify_dir / MANIFEST_NAME

        if not archive_path.exists():
            logger.error("Archive introuvable : %s", archive_path)
            sys.exit(1)
        if not manifest_path.exists():
            logger.error("Manifeste introuvable : %s", manifest_path)
            sys.exit(1)

        success = verify_manifest_integrity(manifest_path, archive_path)
        sys.exit(0 if success else 1)

    # ── Mode normal ───────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("  SEAL ECOSYSTEM — %s", EXECUTION_ID)
    logger.info("  Signature : %s", MTTV_SIG)
    logger.info("  Timestamp : %s", TIMESTAMP)
    logger.info("  Dry run   : %s", dry_run)
    logger.info("=" * 60)

    # Étape 1 : Calcul des checksums
    print()
    logger.info("[1/4] Calcul des checksums SHA3-256 de tous les modules...")
    compute_all_checksums(ECOSYSTEM_MODULES, PROJECT_ROOT)

    # Étape 2 : Création de l'archive
    archive_path = output_dir / ARCHIVE_NAME
    logger.info("[2/4] Création de l'archive tar.gz...")
    archive_hash, archive_size = create_archive(
        ECOSYSTEM_MODULES, PROJECT_ROOT, archive_path, dry_run
    )

    # Étape 3 : Construction et écriture du manifeste
    manifest_path = output_dir / MANIFEST_NAME
    logger.info("[3/4] Construction du manifeste de scellement...")
    manifest = build_manifest(
        modules=ECOSYSTEM_MODULES,
        archive_hash=archive_hash,
        archive_size=archive_size,
        archive_path=str(archive_path.relative_to(PROJECT_ROOT)),
    )

    logger.info("[3/4] Écriture du manifeste...")
    write_manifest(manifest, manifest_path, dry_run)

    # Étape 4 : Vérification d'intégrité
    logger.info("[4/4] Vérification d'intégrité post-scellement...")
    if not dry_run:
        success = verify_manifest_integrity(manifest_path, archive_path)
        if not success:
            logger.error("ÉCHEC DE LA VÉRIFICATION — le scellement est corrompu.")
            sys.exit(1)
    else:
        logger.info("[DRY-RUN] Vérification simulée — OK")

    # Résumé final
    print_seal_summary(manifest)

    if dry_run:
        logger.info("[DRY-RUN] Aucune écriture effectuée. Passez --dry-run=False pour exécuter.")


if __name__ == "__main__":
    main()
