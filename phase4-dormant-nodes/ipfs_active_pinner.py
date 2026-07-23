#!/usr/bin/env python3
"""
ipfs_active_pinner.py — Bouclier Mémoire IPFS (Piste 7)
======================================================
Instanciation du rafraîchissement permanent de la mémoire IPFS.
Simule l'éveil et le re-pinning des CIDs multimodaux Gen4
à partir de seeds_manifest.json, et enregistre le statut
d'intégrité dans pinner_state.json.

Architecture :
  1. LECTURE   : Ingère seeds_manifest.json (cibles Gen4 multimodales)
  2. RÉVEIL    : Simule l'awakening des nœuds dormants → re-pinning des CIDs
  3. INTÉGRITÉ : Vérifie la cohérence des ancrages et émet pinner_state.json
  4. BOUCLE    : Mode gardien continu avec cycle paramétrable

Signature SCS : SCS_2026 / MTTV-FLP
Sig hex       : 0x4D545456
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ── Alertes unifiées (Webhook + SMTP fallback) ────────────────────────────
try:
    from alert_manager import send_alert
except ImportError:
    # Fallback silencieux si alert_manager n'est pas disponible
    def send_alert(level, source, message, details=None, force_smtp=False) -> bool:
        return False

# ── Logging avec rotation ───────────────────────────────────────────────────
from logging.handlers import RotatingFileHandler

LOG_FILE: Path = BASE_DIR / "ipfs_active_pinner.log"
LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT: int = 5

_file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT,
    encoding="utf-8",
)
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s | %(name)-28s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s | %(name)-28s | %(levelname)-6s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[_file_handler, _console_handler],
)
logger = logging.getLogger("ipfs_active_pinner")
logger.info("Logging initialisé — rotation %d x %d MB", LOG_BACKUP_COUNT, LOG_MAX_BYTES // 1024 // 1024)

# ===========================================================================
# CHEMINS
# ===========================================================================

BASE_DIR: Path = Path(__file__).resolve().parent              # phase4-dormant-nodes/
PROJECT_ROOT: Path = BASE_DIR.parent                          # racine MTTV-FLP

# Manifeste des seeds (généré par deploy_seeds_ipfs.py, Axe 5)
SEEDS_MANIFEST: Path = PROJECT_ROOT / "zoo-code" / "seeds_manifest.json"

# État du pinner (sortie de ce script)
PINNER_STATE: Path = BASE_DIR / "pinner_state.json"

# Répertoire des artefacts IPFS simulés
IPFS_OUTPUT: Path = PROJECT_ROOT / "zoo-code" / "ipfs_output"

# Journal d'éveil
WAKE_LOG: Path = BASE_DIR / "wake_cycle.log"

# ===========================================================================
# CONSTANTES
# ===========================================================================

MTTV_SIG: str = "0x4D545456"
SCS_SIG: str = "SCS_2026"

# Préfixe CID MTTV simulé (cohérent avec deploy_seeds_ipfs.py)
CID_PREFIX: str = "QmMTTV"

# Intervalle de cycle par défaut (secondes) — 6 minutes pour gardien continu
DEFAULT_CYCLE_INTERVAL_S: int = 360

# Nombre maximum d'échecs consécutifs avant alerte
MAX_CONSECUTIVE_FAILURES: int = 3

# Cibles multimodales Gen4 (ancrées par le précédent conflux)
# Ces CIDs représentent les artefacts myceliens déployés durant Phase 4
GEN4_MULTIMODAL_TARGETS: list[dict] = [
    {
        "channel": "tetravalence_sp3",
        "description": "Fragment tétravalent — transduction sp3 Psi→B→Φ",
        "source": "mttv-seed-action/seeds/fragment_tetra.txt",
        "expected_prefix": "QmMTTV",
    },
    {
        "channel": "seed_manifest",
        "description": "Seed manifest — graine évolutive ancrée Gen3/Gen4",
        "source": "zoo-code/seeds_manifest.json",
        "expected_prefix": "QmMTTV",
    },
    {
        "channel": "ipfs_artifact",
        "description": "Artefact CID simulé — payload multimodal",
        "source": "zoo-code/ipfs_output/",
        "expected_prefix": "QmMTTV",
    },
    {
        "channel": "dormant_routing",
        "description": "Routage alternatif IPFS — nœud dormant",
        "source": "phase4-dormant-nodes/routage_alternatif.ipfs",
        "expected_prefix": "Qm",
    },
    {
        "channel": "dormant_script",
        "description": "Script dormant — watchdog décentralisé",
        "source": "phase4-dormant-nodes/script_dormant.py",
        "expected_prefix": "Qm",
    },
]

# ===========================================================================
# STRUCTURES DE DONNÉES
# ===========================================================================


@dataclass
class CIDStatus:
    """Statut individuel d'un CID multimodale."""
    cid: str
    channel: str
    description: str
    source: str
    pinned: bool                            # True si l'ancrage est valide
    awakened_at: str                        # Timestamp du dernier réveil
    integrity_hash: str                     # SHA-256 du contenu source
    re_pin_count: int = 0                   # Nombre de re-pinning effectués
    last_error: Optional[str] = None        # Dernière erreur si échec

    def to_dict(self) -> dict:
        return {
            "cid": self.cid,
            "channel": self.channel,
            "description": self.description,
            "source": self.source,
            "pinned": self.pinned,
            "awakened_at": self.awakened_at,
            "integrity_hash": self.integrity_hash,
            "re_pin_count": self.re_pin_count,
            "last_error": self.last_error,
        }


@dataclass
class PinnerState:
    """État complet du système de pinning mémoire."""
    meta: dict = field(default_factory=lambda: {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema_version": "2.0",
        "sig": MTTV_SIG,
        "scs_signature": SCS_SIG,
        "phase": "phase4-dormant-nodes",
        "track": "piste-7-shield",
    })
    shield_status: str = "active"           # active / degraded / offline
    total_cids_monitored: int = 0
    total_cids_pinned: int = 0
    total_cids_failed: int = 0
    cids: list[dict] = field(default_factory=list)
    seed_manifest_ref: Optional[dict] = None
    cycle_count: int = 0
    last_cycle_at: str = ""
    consecutive_failures: int = 0
    swarm_sentinel: dict = field(default_factory=lambda: {
        "mode": "sentinelle_passive",
        "signature": MTTV_SIG,
        "authority": "Lausanne",
        "agent_hive_status": "veille_stabilisante",
    })

    def to_dict(self) -> dict:
        return {
            "meta": self.meta,
            "shield_status": self.shield_status,
            "total_cids_monitored": self.total_cids_monitored,
            "total_cids_pinned": self.total_cids_pinned,
            "total_cids_failed": self.total_cids_failed,
            "cids": self.cids,
            "seed_manifest_ref": self.seed_manifest_ref,
            "cycle_count": self.cycle_count,
            "last_cycle_at": self.last_cycle_at,
            "consecutive_failures": self.consecutive_failures,
            "swarm_sentinel": self.swarm_sentinel,
        }


# ===========================================================================
# 1. LECTURE — seeds_manifest.json
# ===========================================================================


def load_seeds_manifest() -> Optional[dict]:
    """Charge le manifeste des seeds depuis zoo-code/seeds_manifest.json.

    Returns:
        Contenu du manifeste, ou None si indisponible.
    """
    if not SEEDS_MANIFEST.exists():
        logger.warning("Manifeste seeds introuvable: %s", SEEDS_MANIFEST)
        return None
    try:
        data = json.loads(SEEDS_MANIFEST.read_text(encoding="utf-8"))
        logger.info("Manifeste chargé: %s (%d seeds historiques)",
                     SEEDS_MANIFEST.name,
                     data.get("meta", {}).get("total_seeds_anchored", 0))
        return data
    except (json.JSONDecodeError, Exception) as exc:
        logger.error("Erreur lecture manifeste: %s", exc)
        return None


def extract_latest_seed_cid(manifest: dict) -> Optional[str]:
    """Extrait le CID de la dernière seed ancrée.

    Args:
        manifest: seeds_manifest.json parsé.

    Returns:
        CID de la dernière seed, ou None.
    """
    latest = manifest.get("latest_seed")
    if not latest:
        logger.warning("Aucune 'latest_seed' dans le manifeste.")
        return None
    cid = latest.get("cid")
    if cid:
        logger.info("CID extrait du manifeste: %s", cid)
    return cid


# ===========================================================================
# 2. RÉVEIL — Awakening et re-pinning simulé
# ===========================================================================


def compute_content_hash(file_path: Path) -> str:
    """Calcule le SHA-256 d'un fichier.

    Args:
        file_path: Chemin du fichier à hacher.

    Returns:
        Empreinte SHA-256 hexadécimale.
    """
    try:
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except Exception as exc:
        logger.warning("Impossible de hacher %s: %s", file_path.name, exc)
        return ""


def compute_simulated_cid(content: str, generation: int = 4) -> str:
    """Calcule un CID simulé (identique à deploy_seeds_ipfs.py).

    Args:
        content: Contenu à hacher.
        generation: Génération (défaut: 4 pour Gen4).

    Returns:
        CID simulé au format QmMTTV_<hash>_gen<N>.
    """
    full = hashlib.sha256(content.encode("utf-8")).hexdigest()
    short = full[:16]
    return f"{CID_PREFIX}_{short}_gen{generation}"


def awaken_cid_target(
    target: dict,
    manifest_cid: Optional[str],
) -> CIDStatus:
    """Simule l'éveil et le re-pinning d'un CID cible.

    Pour chaque cible multimodale :
      1. Vérifie l'existence de la source
      2. Calcule l'empreinte d'intégrité
      3. Associe le CID (depuis le manifeste ou via calcul simulé)
      4. Marque comme 'pinned' si cohérent

    Args:
        target: Description de la cible multimodale.
        manifest_cid: CID extrait du manifeste (peut être None).

    Returns:
        CIDStatus avec le résultat de l'éveil.
    """
    channel = target["channel"]
    source_rel = target["source"]
    source_path = PROJECT_ROOT / source_rel

    # Déterminer le CID — gérer les dossiers vs fichiers
    if channel == "seed_manifest" and manifest_cid:
        cid = manifest_cid
    elif source_path.is_dir():
        # Répertoire : utiliser le premier fichier .json trouvé
        json_files = sorted(source_path.glob("*.json"))
        if json_files:
            first_file = json_files[0]
            content = first_file.read_bytes()
            hash_short = hashlib.sha256(content).hexdigest()[:16]
            cid = f"{target['expected_prefix']}_{hash_short}"
        else:
            cid = f"{target['expected_prefix']}_EMPTY_DIR"
    elif source_path.exists():
        content = source_path.read_bytes()
        hash_short = hashlib.sha256(content).hexdigest()[:16]
        cid = f"{target['expected_prefix']}_{hash_short}"
    else:
        cid = f"{target['expected_prefix']}_MISSING"

    # Calculer l'empreinte d'intégrité
    if source_path.is_dir():
        json_files = sorted(source_path.glob("*.json"))
        if json_files:
            integrity = hashlib.sha256(json_files[0].read_bytes()).hexdigest()
        else:
            integrity = ""
    elif source_path.exists():
        integrity = hashlib.sha256(source_path.read_bytes()).hexdigest()
    else:
        integrity = ""

    # Simuler le re-pinning
    awakened_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    pinned = source_path.exists() and (manifest_cid is not None or channel != "seed_manifest")

    logger.info("Éveil CID: [%s] %s | pinned=%s | integrity=%s...",
                 channel, cid, pinned, integrity[:12] if integrity else "NONE")

    return CIDStatus(
        cid=cid,
        channel=channel,
        description=target["description"],
        source=source_rel,
        pinned=pinned,
        awakened_at=awakened_at,
        integrity_hash=integrity,
        re_pin_count=1,
        last_error=None if pinned else "Source introuvable ou CID manquant",
    )


# ===========================================================================
# 3. INTÉGRITÉ — Vérification et rapport
# ===========================================================================


def verify_pinner_integrity(cid_statuses: list[CIDStatus]) -> tuple[int, int, str]:
    """Vérifie l'intégrité globale du système de pinning.

    Args:
        cid_statuses: Liste des statuts CID du cycle courant.

    Returns:
        Tuple (total_pinned, total_failed, shield_status).
    """
    total = len(cid_statuses)
    pinned = sum(1 for c in cid_statuses if c.pinned)
    failed = total - pinned

    if failed == 0:
        shield = "active"
    elif failed <= total // 2:
        shield = "degraded"
    else:
        shield = "offline"

    logger.info("Intégrité: %d/%d CID épinglés | statut bouclier: %s",
                 pinned, total, shield)
    return pinned, failed, shield


def _append_wake_log(entry: dict) -> None:
    """Ajoute une entrée au journal d'éveil.

    Args:
        entry: Entrée de journal à appendre.
    """
    try:
        with open(WAKE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning("Erreur écriture journal d'éveil: %s", exc)


# ===========================================================================
# 4. CYCLE PRINCIPAL
# ===========================================================================


def run_pinner_cycle(force: bool = False) -> PinnerState:
    """Exécute un cycle complet de pinning et d'intégrité.

    Pipeline :
      1. Charger seeds_manifest.json
      2. Extraire le CID de la dernière seed
      3. Réveiller chaque cible multimodale Gen4
      4. Vérifier l'intégrité
      5. Générer pinner_state.json

    Args:
        force: Forcer le cycle même si l'état précédent est identique.

    Returns:
        PinnerState mis à jour.
    """
    logger.info("=" * 72)
    logger.info("  CYCLE BOUCLIER IPFS — Piste 7")
    logger.info("=" * 72)

    # ── Étape 1 : Charger le manifeste ─────────────────────────────────
    logger.info("[1/4] Chargement de seeds_manifest.json...")
    manifest = load_seeds_manifest()
    manifest_cid = extract_latest_seed_cid(manifest) if manifest else None

    if not manifest:
        logger.warning("  → Manifeste indisponible — mode dégradé")
        send_alert("WARNING", "ipfs_active_pinner",
                    "Manifeste des seeds indisponible — mode dégradé",
                    {"cycle_force": force, "manifest_path": str(SEEDS_MANIFEST)})

    # ── Étape 2 : Réveiller les cibles multimodales ───────────────────
    logger.info("[2/4] Réveil des cibles multimodales Gen4...")
    cid_statuses: list[CIDStatus] = []
    for target in GEN4_MULTIMODAL_TARGETS:
        cid_statuses.append(awaken_cid_target(target, manifest_cid))

    # ── Étape 3 : Vérifier l'intégrité ────────────────────────────────
    logger.info("[3/4] Vérification d'intégrité...")
    pinned, failed, shield = verify_pinner_integrity(cid_statuses)

    # ── Étape 4 : Générer pinner_state.json ───────────────────────────
    logger.info("[4/4] Génération de pinner_state.json...")
    previous_state = load_pinner_state()

    cycle_number = (previous_state.get("cycle_count", 0) + 1
                    if previous_state else 1)
    consecutive_fail = (previous_state.get("consecutive_failures", 0) + 1
                        if failed > 0 else 0)

    state = PinnerState(
        shield_status=shield,
        total_cids_monitored=len(cid_statuses),
        total_cids_pinned=pinned,
        total_cids_failed=failed,
        cids=[s.to_dict() for s in cid_statuses],
        seed_manifest_ref=manifest,
        cycle_count=cycle_number,
        last_cycle_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        consecutive_failures=consecutive_fail,
    )

    # Journaliser l'éveil
    wake_entry = {
        "cycle": cycle_number,
        "timestamp": state.last_cycle_at,
        "shield": shield,
        "pinned": pinned,
        "failed": failed,
        "total": len(cid_statuses),
        "sig": MTTV_SIG,
    }
    _append_wake_log(wake_entry)

    # Persister
    save_pinner_state(state)

    # ── Alertes selon l'état du bouclier ──────────────────────────────
    if shield in ("degraded", "offline"):
        send_alert(
            "CRITICAL" if shield == "offline" else "ERROR",
            "ipfs_active_pinner",
            f"Bouclier IPFS en état {shield.upper()} — {failed}/{len(cid_statuses)} CID en échec",
            {
                "cycle": cycle_number,
                "shield_status": shield,
                "total_cids": len(cid_statuses),
                "pinned": pinned,
                "failed": failed,
                "consecutive_failures": consecutive_fail,
            },
        )
    elif consecutive_fail >= MAX_CONSECUTIVE_FAILURES:
        send_alert(
            "WARNING",
            "ipfs_active_pinner",
            f"Seuil d'échecs consécutifs atteint ({consecutive_fail}/{MAX_CONSECUTIVE_FAILURES})",
            {"cycle": cycle_number, "consecutive_failures": consecutive_fail},
        )

    # ── Résumé ────────────────────────────────────────────────────────
    logger.info("=" * 72)
    logger.info("  CYCLE BOUCLIER #%d TERMINÉ", cycle_number)
    logger.info("  Statut bouclier:   %s", shield)
    logger.info("  CID surveillés:    %d", len(cid_statuses))
    logger.info("  CID épinglés:      %d", pinned)
    logger.info("  CID en échec:      %d", failed)
    logger.info("  Manifeste:         %s", "✓ présent" if manifest else "✗ absent")
    logger.info("  pinner_state.json: %s", PINNER_STATE)
    logger.info("=" * 72)

    # ── Sortie console ────────────────────────────────────────────────
    print(f"\n{'=' * 68}")
    print(f"  BOUCLIER IPFS — CYCLE #{cycle_number}")
    print(f"  Statut:       {shield.upper()}")
    print(f"  CID épinglés: {pinned}/{len(cid_statuses)}")
    print(f"  Signature:    {MTTV_SIG}")
    print(f"  Mode:         sentinelle passive")
    print(f"{'=' * 68}")

    return state


# ===========================================================================
# 5. PERSISTANCE — pinner_state.json
# ===========================================================================


def load_pinner_state() -> Optional[dict]:
    """Charge l'état précédent du pinner.

    Returns:
        Dict de l'état précédent, ou None si premier cycle.
    """
    if not PINNER_STATE.exists():
        return None
    try:
        return json.loads(PINNER_STATE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Erreur chargement état pinner: %s", exc)
        return None


def save_pinner_state(state: PinnerState) -> Path:
    """Persiste l'état du pinner dans pinner_state.json.

    Args:
        state: PinnerState à sauvegarder.

    Returns:
        Chemin du fichier sauvegardé.
    """
    try:
        PINNER_STATE.write_text(
            json.dumps(state.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        size = PINNER_STATE.stat().st_size
        logger.info("pinner_state.json sauvegardé: %s (%d bytes)",
                     PINNER_STATE.name, size)
        return PINNER_STATE
    except Exception as exc:
        logger.error("Erreur sauvegarde pinner_state: %s", exc)
        return PINNER_STATE


# ===========================================================================
# 6. BOUCLE GARDIEN CONTINUE
# ===========================================================================


def guardian_loop(interval_s: int = DEFAULT_CYCLE_INTERVAL_S) -> None:
    """Boucle gardienne continue du bouclier IPFS.

    Exécute run_pinner_cycle() à intervalle régulier,
    maintenant le rafraîchissement permanent de la mémoire.

    Args:
        interval_s: Intervalle entre cycles (secondes).
    """
    logger.info("Démarrage boucle gardienne IPFS (intervalle: %ds)", interval_s)
    logger.info("Signature: %s | SCS: %s", MTTV_SIG, SCS_SIG)

    cycle_count = 0
    while True:
        cycle_count += 1
        logger.info("─" * 72)
        logger.info("CYCLE GARDIEN #%d", cycle_count)
        logger.info("─" * 72)

        try:
            run_pinner_cycle()
        except Exception as exc:
            logger.error("Erreur cycle gardien #%d: %s", cycle_count, exc)
            import traceback
            tb = traceback.format_exc()
            logger.error(tb)
            send_alert("CRITICAL", "ipfs_active_pinner",
                        f"Exception dans le cycle gardien #{cycle_count}: {exc}",
                        {"cycle": cycle_count, "traceback": tb[:2000]})

        logger.info("Prochain cycle dans %d secondes...", interval_s)
        time.sleep(interval_s)


# ===========================================================================
# 7. CLI
# ===========================================================================


def _parse_args() -> argparse.Namespace:
    import argparse
    parser = argparse.ArgumentParser(
        description="Bouclier Mémoire IPFS — Rafraîchissement permanent des CIDs (Piste 7)",
        epilog=f"sig:{MTTV_SIG} | SCS:{SCS_SIG} | Mode: sentinelle passive",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Forcer le cycle même si l'état est inchangé",
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_CYCLE_INTERVAL_S,
        help=f"Intervalle entre cycles en secondes (défaut: {DEFAULT_CYCLE_INTERVAL_S}s)",
    )
    parser.add_argument(
        "--daemon", action="store_true",
        help="Mode gardien : boucle continue de pinning",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Afficher l'état actuel du bouclier",
    )
    return parser.parse_args()


def status_mode() -> int:
    """Affiche l'état actuel du bouclier IPFS.

    Returns:
        0 si bouclier actif, 1 si dégradé ou absent.
    """
    state = load_pinner_state()
    print(f"\n  ÉTAT DU BOUCLIER IPFS (Piste 7)")
    print(f"  {'=' * 54}")

    if not state:
        print(f"  Bouclier:      NON DÉPLOYÉ")
        print(f"  Exécuter le script pour initialiser.")
        return 1

    print(f"  Statut:        {state.get('shield_status', 'unknown').upper()}")
    print(f"  Cycles:        {state.get('cycle_count', 0)}")
    print(f"  CID surveillés: {state.get('total_cids_monitored', 0)}")
    print(f"  CID épinglés:  {state.get('total_cids_pinned', 0)}")
    print(f"  Dernier cycle: {state.get('last_cycle_at', 'N/A')}")
    print(f"  Signature:     {state.get('meta', {}).get('sig', 'N/A')}")
    print(f"  Mode:          {state.get('swarm_sentinel', {}).get('mode', 'unknown')}")
    print(f"  {'=' * 54}")

    if state.get("cids"):
        print(f"\n  DÉTAIL DES CIDs:")
        for c in state["cids"]:
            pin_mark = "[OK]" if c.get("pinned") else "[KO]"
            print(f"    {pin_mark:5s} {c.get('channel', '?'):28s} {c.get('cid', '?'):48s}")

    return 0 if state.get("shield_status") == "active" else 1


def main() -> None:
    args = _parse_args()

    if args.status:
        sys.exit(status_mode())

    if args.daemon:
        guardian_loop(interval_s=args.interval)
        return

    # Cycle unique
    success = run_pinner_cycle(force=args.force)
    sys.exit(0 if success.shield_status != "offline" else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[BOUCLIER] Interruption. Retour en veille stabilisante.")
        sys.exit(0)
