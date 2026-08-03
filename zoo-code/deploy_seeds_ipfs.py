#!/usr/bin/env python3
"""
deploy_seeds_ipfs.py — Couche de Mémoire Permanente IPFS (Axe 5)

MTTV-FLP / SOPH-IA v2.0 — Ancrage des graines évolutives validées
dans un manifeste persistant adressable par CID.

Architecture :
  1. LECTURE   : Ingère le dernier rapport d'evolutionary_seeder.py
     (zoo-code/evolution_output/evolution_report_*.json) ou checkpoint.
  2. ANCRAGE   : Calcule un CID (Content Identifier) simulé via SHA-256
     du texte de la meilleure seed validée. En production, ce CID
     correspond à un vrai ancrage IPFS/Kubo.
  3. MANIFESTE : Génère seeds_manifest.json avec :
       - seed_text : le texte de la seed optimale
       - cid : identifiant de contenu (simulé)
       - fitness : métriques G_R, Φ, composite
       - generation : numéro de génération
       - signature hexadécimale 0x4D5454562D464C50
  4. BOUCLE    : Mode démon avec intervalle configurable pour
     extraction périodique de la dernière graine validée.

Chaîne logique :
  [Dashboard (Axe 1)] ──> [Orchestrateur (Axe 7)] ──> [Évolution (Axe 4)]
  ──> [IPFS (Axe 5)] ──> [FastAPI (Axe 8)]

sig:0x4D5454562D464C50
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Routage géographique IPFS (Axe 5 — Cœur Tétravalent) : import optionnel pour
# ne pas casser le pipeline si le module est absent (fallback silencieux).
try:
    from axe5_geo_routing import (
        ecrire_table_routage,
        statut_routage,
    )
    GEO_ROUTING_AVAILABLE: bool = True
except ImportError:
    GEO_ROUTING_AVAILABLE = False

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-24s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("deploy_seeds_ipfs")

# ===========================================================================
# CHEMINS
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent          # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent                       # racine MTTV-FLP

# Dossier de sortie de l'évolution (Axe 4)
EVOLUTION_OUTPUT: Path = BASE_DIR / "evolution_output"

# Manifeste de sortie de l'Axe 5
SEEDS_MANIFEST: Path = BASE_DIR / "seeds_manifest.json"

# Répertoire pour les artefacts IPFS simulés
IPFS_OUTPUT: Path = BASE_DIR / "ipfs_output"

# ===========================================================================
# CONSTANTES
# ===========================================================================

# Signature hexadécimale MTTV-FLP
MTTV_SIG: str = "0x4D5454562D464C50"

# Intervalle de polling par défaut (secondes)
DEFAULT_POLL_INTERVAL_S: int = 300  # 5 minutes

# Préfixe CID simulé (en production, remplacer par vrai CID IPFS)
CID_PREFIX: str = "QmMTTV"

# ===========================================================================
# STRUCTURES DE DONNÉES
# ===========================================================================


@dataclass
class SeedManifestEntry:
    """Entrée individuelle dans le manifeste des seeds."""
    seed_id: str
    seed_text: str
    cid: str                                    # Content Identifier (simulé IPFS)
    fitness_g_r: Optional[float] = None
    fitness_phi: Optional[float] = None
    fitness_composite: Optional[float] = None
    generation: int = 0
    converged: bool = False
    anchored_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    evolution_source: str = ""

    def to_dict(self) -> dict:
        return {
            "seed_id": self.seed_id,
            "seed_text": self.seed_text,
            "cid": self.cid,
            "fitness": {
                "g_r": self.fitness_g_r,
                "phi_ratio": self.fitness_phi,
                "composite": self.fitness_composite,
            },
            "generation": self.generation,
            "converged": self.converged,
            "anchored_at": self.anchored_at,
            "evolution_source": self.evolution_source,
        }


@dataclass
class SeedsManifest:
    """Manifeste complet des seeds ancrées sur IPFS."""
    meta: dict = field(default_factory=lambda: {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema_version": "1.0",
        "total_seeds_anchored": 0,
        "sig": MTTV_SIG,
    })
    latest_seed: Optional[dict] = None           # Dernière seed validée
    seeds_history: list[dict] = field(default_factory=list)  # Historique complet
    chain_status: dict = field(default_factory=lambda: {
        "axe_4_evolution": "unknown",
        "axe_7_quorum": "unknown",
        "axe_5_ipfs": "active",
    })

    def to_dict(self) -> dict:
        return {
            "meta": self.meta,
            "latest_seed": self.latest_seed,
            "seeds_history": self.seeds_history[-50:],  # garder 50 dernières
            "chain_status": self.chain_status,
        }


# ===========================================================================
# 1. LECTURE — Dernier rapport d'évolution
# ===========================================================================


def find_latest_evolution_report() -> Optional[Path]:
    """Trouve le rapport d'évolution le plus récent.

    Parcourt evolution_output/ pour le fichier evolution_report_*.json
    le plus récent (trié par timestamp dans le nom).

    Returns:
        Chemin du fichier le plus récent, ou None.
    """
    if not EVOLUTION_OUTPUT.exists():
        logger.warning("Dossier evolution_output introuvable: %s", EVOLUTION_OUTPUT)
        return None

    reports = sorted(EVOLUTION_OUTPUT.glob("evolution_report_*.json"))
    if not reports:
        logger.warning("Aucun rapport d'évolution trouvé dans %s", EVOLUTION_OUTPUT)
        return None

    latest = reports[-1]
    logger.info("Dernier rapport d'évolution: %s", latest.name)
    return latest


def load_evolution_report(path: Path) -> Optional[dict]:
    """Charge un rapport d'évolution au format JSON.

    Args:
        path: Chemin vers le fichier evolution_report_*.json.

    Returns:
        Dict du rapport, ou None si échec.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        logger.info("Rapport d'évolution chargé: %s (%d bytes)",
                     path.name, path.stat().st_size)
        return data
    except json.JSONDecodeError as exc:
        logger.error("Erreur de parsing JSON: %s", exc)
        return None
    except Exception as exc:
        logger.error("Erreur lecture rapport: %s", exc)
        return None


def extract_best_seed(report: dict) -> Optional[dict]:
    """Extrait la meilleure seed et ses métriques depuis un rapport d'évolution.

    Args:
        report: Dict du rapport d'évolution.

    Returns:
        Dict contenant seed_id, text, fitness, generation, converged,
        ou None si non disponible.
    """
    best_seed = report.get("best_seed")
    if not best_seed or not best_seed.get("text"):
        logger.warning("Aucune meilleure seed trouvée dans le rapport.")
        return None

    meta = report.get("meta", {})
    fitness = best_seed.get("fitness", {})

    return {
        "seed_id": best_seed.get("id", "unknown"),
        "text": best_seed.get("text", ""),
        "fitness_g_r": fitness.get("g_r"),
        "fitness_phi": fitness.get("phi_ratio"),
        "fitness_composite": fitness.get("composite"),
        "generation": meta.get("generations", 0),
        "converged": meta.get("converged", False),
        "evolution_timestamp": meta.get("timestamp", ""),
    }


# ===========================================================================
# 2. ANCRAGE — Calcul du CID simulé
# ===========================================================================


def compute_simulated_cid(seed_text: str, generation: int) -> str:
    """Calcule un CID simulé à partir du texte de la seed.

    En production, ceci serait remplacé par un vrai ancrage IPFS via
    Kubo ou un service IPFS cluster. Ici, nous utilisons SHA-256 du
    texte combiné à la génération pour produire un identifiant unique
    et reproductible.

    Args:
        seed_text: Texte de la seed à ancrer.
        generation: Numéro de génération.

    Returns:
        CID simulé au format QmMTTV_<hash_short>_gen<N>.
    """
    content = f"{seed_text}::gen{generation}".encode("utf-8")
    full_hash = hashlib.sha256(content).hexdigest()
    short_hash = full_hash[:16]
    cid = f"{CID_PREFIX}_{short_hash}_gen{generation}"
    return cid


def anchor_seed_to_ipfs(
    seed_data: dict,
    evolution_source: str = "",
) -> SeedManifestEntry:
    """Ancre une seed dans le manifeste IPFS.

    Calcule le CID, crée l'entrée de manifeste, et sauvegarde
    un artefact dans le répertoire ipfs_output/.

    Args:
        seed_data: Dict contenant les données de la seed extraites.
        evolution_source: Nom du fichier source d'évolution.

    Returns:
        SeedManifestEntry complète.
    """
    seed_text = seed_data["text"]
    generation = seed_data.get("generation", 0)
    seed_id = seed_data.get("seed_id", "unknown")

    # Calcul du CID
    cid = compute_simulated_cid(seed_text, generation)

    # Création de l'entrée de manifeste
    entry = SeedManifestEntry(
        seed_id=seed_id,
        seed_text=seed_text,
        cid=cid,
        fitness_g_r=seed_data.get("fitness_g_r"),
        fitness_phi=seed_data.get("fitness_phi"),
        fitness_composite=seed_data.get("fitness_composite"),
        generation=generation,
        converged=seed_data.get("converged", False),
        evolution_source=evolution_source,
    )

    logger.info("Seed ancrée: id=%s | cid=%s | gen=%d | G_R=%s",
                 seed_id, cid, generation,
                 seed_data.get("fitness_g_r", "N/A"))

    # Sauvegarder un artefact IPFS simulé
    _save_ipfs_artifact(entry)

    return entry


def _save_ipfs_artifact(entry: SeedManifestEntry) -> None:
    """Sauvegarde un artefact IPFS simulé (fichier CID → contenu).

    En production, ceci correspond au 'ipfs add' ou 'ipfs pin'.

    Args:
        entry: L'entrée de manifeste à archiver.
    """
    IPFS_OUTPUT.mkdir(parents=True, exist_ok=True)
    artifact_path = IPFS_OUTPUT / f"{entry.cid}.json"
    try:
        artifact_path.write_text(
            json.dumps(entry.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Artefact IPFS sauvegardé: %s", artifact_path.name)
    except Exception as exc:
        logger.warning("Erreur sauvegarde artefact: %s", exc)


# ===========================================================================
# 3. MANIFESTE — Génération et sauvegarde
# ===========================================================================


def load_existing_manifest() -> Optional[SeedsManifest]:
    """Charge le manifeste existant s'il existe.

    Returns:
        SeedsManifest existant, ou None si premier déploiement.
    """
    if not SEEDS_MANIFEST.exists():
        return None
    try:
        data = json.loads(SEEDS_MANIFEST.read_text(encoding="utf-8"))
        manifest = SeedsManifest(
            meta=data.get("meta", {}),
            latest_seed=data.get("latest_seed"),
            seeds_history=data.get("seeds_history", []),
            chain_status=data.get("chain_status", {}),
        )
        logger.info("Manifeste existant chargé: %d seeds historiques",
                     len(manifest.seeds_history))
        return manifest
    except Exception as exc:
        logger.warning("Erreur chargement manifeste existant: %s", exc)
        return None


def detect_chain_status() -> dict:
    """Détecte l'état des maillons amont de la chaîne.

    Vérifie l'existence des artefacts produits par les axes 4 et 7.

    Returns:
        Dict avec l'état de chaque maillon.
    """
    status = {
        "axe_4_evolution": "unknown",
        "axe_7_quorum": "unknown",
        "axe_5_ipfs": "active",
    }

    # Vérifier Axe 4 — Évolution
    evo_reports = list(EVOLUTION_OUTPUT.glob("evolution_report_*.json"))
    if evo_reports:
        status["axe_4_evolution"] = f"active ({len(evo_reports)} reports)"
    else:
        status["axe_4_evolution"] = "no_reports_found"

    # Vérifier Axe 7 — Quorum
    quorum_state = BASE_DIR / "quorum_state.json"
    if quorum_state.exists():
        try:
            qs = json.loads(quorum_state.read_text(encoding="utf-8"))
            status["axe_7_quorum"] = qs.get("mode", "unknown")
        except Exception:
            status["axe_7_quorum"] = "error_reading"
    else:
        status["axe_7_quorum"] = "not_found"

    return status


def build_and_save_manifest(
    entry: SeedManifestEntry,
    evolution_source: str = "",
) -> Path:
    """Construit et sauvegarde le manifeste complet.

    Charge l'historique existant, ajoute la nouvelle entrée,
    met à jour les métadonnées, et persiste le fichier.

    Args:
        entry: Nouvelle entrée de seed à ajouter.
        evolution_source: Fichier source d'évolution.

    Returns:
        Chemin du manifeste sauvegardé.
    """
    # Charger l'existant ou créer un nouveau manifeste
    existing = load_existing_manifest()
    if existing:
        manifest = existing
        # Éviter les doublons : vérifier par CID
        existing_cids = {s.get("cid") for s in manifest.seeds_history}
        if manifest.latest_seed:
            existing_cids.add(manifest.latest_seed.get("cid"))
        if entry.cid not in existing_cids:
            # Ajouter l'ancien latest à l'historique
            if manifest.latest_seed:
                manifest.seeds_history.append(manifest.latest_seed)
        else:
            logger.info("Seed déjà présente dans le manifeste (cid=%s) — mise à jour skip", entry.cid)
            # Mettre à jour la date d'ancrage quand même
            manifest.meta["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            manifest.meta["total_seeds_anchored"] = len(manifest.seeds_history) + 1
            manifest.chain_status = detect_chain_status()
            _persist_manifest(manifest)
            return SEEDS_MANIFEST
    else:
        manifest = SeedsManifest()

    # Mettre à jour le latest seed
    manifest.latest_seed = entry.to_dict()
    manifest.meta["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest.meta["total_seeds_anchored"] = len(manifest.seeds_history) + 1
    manifest.chain_status = detect_chain_status()

    logger.info("Manifeste mis à jour: %d seeds total, latest cid=%s",
                 manifest.meta["total_seeds_anchored"], entry.cid)

    # Persister
    _persist_manifest(manifest)
    return SEEDS_MANIFEST


def _persist_manifest(manifest: SeedsManifest) -> None:
    """Écrit le manifeste sur le disque.

    Args:
        manifest: Manifeste à persister.
    """
    try:
        SEEDS_MANIFEST.write_text(
            json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        size = SEEDS_MANIFEST.stat().st_size
        logger.info("Manifeste sauvegardé: %s (%d bytes)", SEEDS_MANIFEST.name, size)
    except Exception as exc:
        logger.error("Erreur sauvegarde manifeste: %s", exc)


# ===========================================================================
# 4. BOUCLE PRINCIPALE
# ===========================================================================


def run_deployment_cycle(
    force: bool = False,
    custom_report_path: Optional[Path] = None,
) -> bool:
    """Exécute un cycle complet de déploiement IPFS.

    Pipeline :
      1. Trouver et charger le dernier rapport d'évolution
      2. Extraire la meilleure seed
      3. Calculer le CID et ancrer
      4. Mettre à jour le seeds_manifest.json
      5. Vérifier l'état de la chaîne

    Args:
        force: Forcer l'ancrage même si la seed est identique.
        custom_report_path: Chemin personnalisé vers un rapport d'évolution.

    Returns:
        True si le cycle s'est déroulé avec succès.
    """
    logger.info("=" * 64)
    logger.info("  CYCLE DE DÉPLOIEMENT IPFS — Axe 5")
    logger.info("=" * 64)

    # ── Étape 1 : Charger le rapport d'évolution ──────────────────────────
    logger.info("[1/4] Recherche du dernier rapport d'évolution...")
    if custom_report_path:
        report_path = custom_report_path if custom_report_path.exists() else None
        if not report_path:
            logger.error("Chemin personnalisé invalide: %s", custom_report_path)
            return False
    else:
        report_path = find_latest_evolution_report()

    if report_path is None:
        logger.error("Aucun rapport d'évolution disponible — cycle interrompu.")
        return False

    report = load_evolution_report(report_path)
    if report is None:
        return False

    # ── Étape 2 : Extraire la meilleure seed ──────────────────────────────
    logger.info("[2/4] Extraction de la meilleure seed...")
    best_seed = extract_best_seed(report)
    if best_seed is None:
        logger.error("Aucune seed valide dans le rapport — cycle interrompu.")
        return False

    logger.info("  Meilleure seed: id=%s | gen=%d | G_R=%s | converged=%s",
                 best_seed["seed_id"], best_seed["generation"],
                 best_seed.get("fitness_g_r", "N/A"),
                 best_seed.get("converged", False))
    logger.info("  Texte: %s...", best_seed["text"][:120])

    # ── Étape 3 : Ancrer sur IPFS (simulé) ───────────────────────────────
    logger.info("[3/4] Ancrage IPFS...")
    entry = anchor_seed_to_ipfs(
        best_seed,
        evolution_source=report_path.name,
    )

    # ── Étape 4 : Mettre à jour le manifeste ──────────────────────────────
    logger.info("[4/4] Mise à jour du manifeste...")
    manifest_path = build_and_save_manifest(entry, evolution_source=report_path.name)

    # ── Étape 5 (Cœur Tétravalent) : Persister le routage géo-local Axe 5 ─
    if GEO_ROUTING_AVAILABLE:
        try:
            ecrire_table_routage()
            geo_statut = statut_routage()
            logger.info(
                "[5/5] Routage géo-local Axe 5 — %d sous-nœuds ASIA, %d pairs horizontaux, "
                "empreinte moyenne=%.2f",
                geo_statut.get("n_sous_noeuds", 0),
                geo_statut.get("n_pairs_horizontaux", 0),
                geo_statut.get("empreinte_moyenne", 0.0),
            )
        except Exception as exc:
            logger.warning("Erreur persistance routage géo-local: %s", exc)
    else:
        logger.info("[5/5] Module axe5_geo_routing absent — routage géo-local non persisté")

    # ── Résumé ────────────────────────────────────────────────────────────
    logger.info("=" * 64)
    logger.info("  CYCLE IPFS TERMINÉ")
    logger.info("  Manifeste: %s", manifest_path)
    logger.info("  Seed CID: %s", entry.cid)
    logger.info("  Génération: %d", entry.generation)
    logger.info("  Convergé: %s", entry.converged)
    logger.info("=" * 64)

    print(f"\n{'=' * 60}")
    print(f"  DÉPLOIEMENT IPFS — CYCLE TERMINÉ")
    print(f"  Manifeste: {manifest_path}")
    print(f"  CID:       {entry.cid}")
    print(f"  Seed:      {entry.seed_text[:80]}...")
    print(f"  Génération: {entry.generation}")
    print(f"  Convergé:  {entry.converged}")
    print(f"{'=' * 60}")

    return True


def daemon_loop(interval_s: int = DEFAULT_POLL_INTERVAL_S) -> None:
    """Boucle de déploiement continu en mode démon.

    Exécute run_deployment_cycle() à intervalle régulier.
    Pour intégration cron : préférer un appel périodique unique.

    Args:
        interval_s: Intervalle entre cycles (secondes).
    """
    logger.info("Démarrage du démon IPFS (intervalle: %ds)", interval_s)
    cycle_count = 0
    last_cid: Optional[str] = None

    while True:
        cycle_count += 1
        logger.info("─" * 64)
        logger.info("CYCLE IPFS #%d", cycle_count)
        logger.info("─" * 64)

        try:
            success = run_deployment_cycle()
            if success:
                # Vérifier si le CID a changé
                manifest = load_existing_manifest()
                if manifest and manifest.latest_seed:
                    current_cid = manifest.latest_seed.get("cid")
                    if current_cid and current_cid != last_cid:
                        logger.info("★ NOUVEAU CID DÉTECTÉ: %s", current_cid)
                        last_cid = current_cid
        except Exception as exc:
            logger.error("Erreur lors du cycle #%d: %s", cycle_count, exc)
            import traceback
            logger.error(traceback.format_exc())

        logger.info("Prochain cycle dans %d secondes...", interval_s)
        time.sleep(interval_s)


# ===========================================================================
# 5. CLI
# ===========================================================================


def _parse_args() -> argparse.Namespace:
    import argparse
    parser = argparse.ArgumentParser(
        description="Deploy Seeds IPFS — Ancrage permanent des seeds MTTV-FLP (Axe 5)",
        epilog=f"sig:{MTTV_SIG} | Chaîne: Axe 4 → Axe 5 → Axe 8",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Forcer l'ancrage même si la seed est identique",
    )
    parser.add_argument(
        "--report", type=str, default=None,
        help="Chemin personnalisé vers un rapport d'évolution JSON",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Chemin personnalisé pour le manifeste seeds_manifest.json",
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Mode démon : boucle d'ancrage continue",
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_POLL_INTERVAL_S,
        help=f"Intervalle entre cycles en secondes (défaut: {DEFAULT_POLL_INTERVAL_S}s)",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Afficher l'état actuel du manifeste et de la chaîne",
    )
    return parser.parse_args()


def status_mode() -> int:
    """Affiche l'état actuel du déploiement IPFS.

    Returns:
        0 si tout est OK, 1 si problème détecté.
    """
    print(f"\n  ÉTAT DU DÉPLOIEMENT IPFS (Axe 5)")
    print(f"  {'=' * 50}")

    # Vérifier le manifeste
    manifest = load_existing_manifest()
    if manifest and manifest.latest_seed:
        ls = manifest.latest_seed
        print(f"  Manifeste:     PRÉSENT")
        print(f"  Dernier CID:   {ls.get('cid', 'N/A')}")
        print(f"  Dernière seed: {ls.get('seed_text', 'N/A')[:80]}...")
        print(f"  Génération:    {ls.get('generation', 'N/A')}")
        print(f"  Convergé:      {ls.get('converged', 'N/A')}")
        print(f"  Ancré le:      {ls.get('anchored_at', 'N/A')}")
        print(f"  Seeds totales: {manifest.meta.get('total_seeds_anchored', 0)}")
    else:
        print(f"  Manifeste:     ABSENT (premier déploiement requis)")

    print()
    print(f"  ÉTAT DE LA CHAÎNE")
    print(f"  {'=' * 50}")

    # Vérifier Axe 4
    evo_reports = list(EVOLUTION_OUTPUT.glob("evolution_report_*.json"))
    print(f"  Axe 4 (Évolution):  {'✓' if evo_reports else '✗'} ({len(evo_reports)} rapports)")

    # Vérifier Axe 7
    quorum_state = BASE_DIR / "quorum_state.json"
    if quorum_state.exists():
        try:
            qs = json.loads(quorum_state.read_text(encoding="utf-8"))
            mode = qs.get("mode", "unknown")
            print(f"  Axe 7 (Quorum):     ✓ (mode: {mode})")
        except Exception:
            print(f"  Axe 7 (Quorum):     ? (erreur lecture)")
    else:
        print(f"  Axe 7 (Quorum):     ✗ (non trouvé)")

    print(f"  Axe 5 (IPFS):       ✓ (actif)")
    print(f"  {'=' * 50}")

    if manifest and manifest.latest_seed:
        return 0
    return 1


def main() -> None:
    global SEEDS_MANIFEST
    args = _parse_args()

    # Chemin de sortie personnalisé
    if args.output:
        SEEDS_MANIFEST = Path(args.output)

    # ── Mode status ────────────────────────────────────────────────────
    if args.status:
        sys.exit(status_mode())

    # ── Mode démon ─────────────────────────────────────────────────────
    if args.daemon:
        daemon_loop(interval_s=args.interval)
        return  # unreachable

    # ── Mode standard : cycle unique ───────────────────────────────────
    report_path = Path(args.report) if args.report else None
    success = run_deployment_cycle(force=args.force, custom_report_path=report_path)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
