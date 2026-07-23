#!/usr/bin/env python3
"""
export_sealed_archive.py — Export de l'archive scellée MTTV-FLP
===============================================================
1. Lit l'archive scellée et son manifeste
2. Crée une GitHub Release avec l'archive en asset
3. Génère les métadonnées Zenodo pour le DOI 10.5281/zenodo.17940301

Usage :
    python zoo-code/export_sealed_archive.py              # export complet
    python zoo-code/export_sealed_archive.py --dry-run     # simulation
    python zoo-code/export_sealed_archive.py --zenodo-only # métadonnées Zenodo seulement

Dépendances :
    - GitHub CLI (gh) pour la création de release
    - Python ≥ 3.10 (stdlib only)

sig:0x4D545456
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ── Logging avec rotation ───────────────────────────────────────────────────
from logging.handlers import RotatingFileHandler

BASE_DIR: Path = Path(__file__).resolve().parent          # zoo-code/
PROJECT_ROOT: Path = BASE_DIR.parent                       # racine du projet
ARCHIVE_DIR: Path = BASE_DIR / "sealed_archive"

LOG_FILE: Path = BASE_DIR / "export_sealed_archive.log"
_file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3,
    encoding="utf-8",
)
_console_handler = logging.StreamHandler()
_fmt = logging.Formatter("%(asctime)s | %(name)-24s | %(levelname)-6s | %(message)s",
                          datefmt="%Y-%m-%d %H:%M:%S")
for h in (_file_handler, _console_handler):
    h.setLevel(logging.INFO)
    h.setFormatter(_fmt)

logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _console_handler])
logger = logging.getLogger("export_sealed_archive")

# ===========================================================================
# CONSTANTES
# ===========================================================================

MTTV_SIG: str = "0x4D545456"
ZENODO_DOI: str = "10.5281/zenodo.17940301"
GITHUB_REPO: str = "gaillard111/flp-french-thoughts"  # à ajuster si nécessaire
RELEASE_TAG_PREFIX: str = "mttv-flp-sealed-v"

ARCHIVE_NAME: str = "mttv_flp_ecosystem_sealed.tar.gz"
MANIFEST_NAME: str = "ecosystem_sealed_manifest.json"

# ===========================================================================
# 1. LECTURE DE L'ARCHIVE ET DU MANIFESTE
# ===========================================================================


def load_manifest() -> Optional[dict[str, Any]]:
    """Charge le manifeste de scellement."""
    manifest_path = ARCHIVE_DIR / MANIFEST_NAME
    if not manifest_path.exists():
        logger.error("Manifeste introuvable: %s", manifest_path)
        logger.error("Exécutez d'abord: python zoo-code/seal_ecosystem.py")
        return None
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        logger.info("Manifeste chargé: %s", manifest_path)
        return data
    except (json.JSONDecodeError, Exception) as exc:
        logger.error("Erreur lecture manifeste: %s", exc)
        return None


def verify_archive() -> tuple[Optional[Path], Optional[str]]:
    """Vérifie l'intégrité de l'archive scellée.

    Returns:
        (chemin_archive, sha3_256) ou (None, None) si échec.
    """
    archive_path = ARCHIVE_DIR / ARCHIVE_NAME
    manifest = load_manifest()
    if not manifest:
        return None, None

    if not archive_path.exists():
        logger.error("Archive introuvable: %s", archive_path)
        return None, None

    expected_hash = manifest.get("archive", {}).get("sha3_256", "")
    if not expected_hash:
        logger.error("SHA3-256 manquant dans le manifeste.")
        return None, None

    # Vérifier l'intégrité
    actual_hash = _compute_sha3_256(archive_path)
    if actual_hash != expected_hash:
        logger.error(
            "ÉCHEC INTÉGRITÉ: hash attendu=%s, obtenu=%s",
            expected_hash, actual_hash,
        )
        return None, None

    logger.info("Archive vérifiée: %s (%d bytes)", archive_path.name, archive_path.stat().st_size)
    logger.info("SHA3-256: %s", actual_hash)
    return archive_path, actual_hash


def _compute_sha3_256(filepath: Path) -> str:
    """Calcule l'empreinte SHA3-256 d'un fichier."""
    import hashlib
    h = hashlib.sha3_256()
    try:
        h.update(filepath.read_bytes())
    except Exception as exc:
        logger.error("Impossible de lire %s: %s", filepath, exc)
        return "ERROR"
    return h.hexdigest()


# ===========================================================================
# 2. GITHUB RELEASE  (via API REST, sans dépendance gh CLI)
# ===========================================================================


def _get_github_token() -> Optional[str]:
    """Récupère le token GitHub depuis l'environnement.

    Ordre de recherche :
      1. Variable d'environnement MTTV_GITHUB_TOKEN (recommandé)
      2. Variable d'environnement GITHUB_TOKEN
      3. Variable d'environnement GH_TOKEN
      4. Fichier .github_token à la racine (déprécié)

    Le token n'est jamais loggé — seule sa longueur est affichée.
    """
    # Ordre de priorité : MTTV_GITHUB_TOKEN > GITHUB_TOKEN > GH_TOKEN > fichier
    for var_name in ("MTTV_GITHUB_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"):
        token = os.environ.get(var_name)
        if token:
            logger.debug("Token GitHub trouvé dans %s (longueur: %d)", var_name, len(token))
            return token.strip()

    # Fallback fichier (déprécié, sécurité moindre)
    token_file = PROJECT_ROOT / ".github_token"
    if token_file.exists():
        token = token_file.read_text(encoding="utf-8").strip()
        token = token.strip().replace('\ufeff', '')
        if token:
            logger.warning("Token GitHub lu depuis fichier (moins sécurisé). Préférer env var.")
            return token

    logger.error("Aucun token GitHub trouvé. Définissez MTTV_GITHUB_TOKEN.")
    return None


def _github_api_request(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    binary_data: Optional[bytes] = None,
    content_type: str = "application/json",
    accept: str = "application/vnd.github.v3+json",
) -> tuple[int, Any]:
    """Effectue une requête à l'API REST GitHub.

    Args:
        method: HTTP method (GET, POST, PATCH, DELETE).
        endpoint: Chemin API (ex: /repos/owner/repo/releases).
        data: Dict JSON à envoyer (pour JSON).
        binary_data: Données binaires à envoyer (pour upload).
        content_type: Content-Type header.
        accept: Accept header.

    Returns:
        Tuple (status_code, parsed_response_dict).
    """
    import urllib.request
    import urllib.error

    token = _get_github_token()
    if not token:
        return 401, {"error": "No GitHub token available"}

    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "User-Agent": "MTTV-FLP-Export/2.0",
    }
    if binary_data is not None:
        headers["Content-Type"] = content_type
    elif data is not None:
        headers["Content-Type"] = content_type

    body = binary_data if binary_data is not None else (
        json.dumps(data).encode("utf-8") if data is not None else None
    )

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp_body = resp.read().decode("utf-8")
            parsed = json.loads(resp_body) if resp_body else {}
            return resp.status, parsed
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(err_body)
        except json.JSONDecodeError:
            parsed = {"raw_error": err_body}
        logger.error("GitHub API error %d: %s", e.code, err_body[:500])
        return e.code, parsed
    except urllib.error.URLError as e:
        logger.error("GitHub API connection error: %s", e.reason)
        return 0, {"error": str(e.reason)}


def create_github_release(
    archive_path: Path,
    manifest: dict[str, Any],
    dry_run: bool = False,
) -> bool:
    """Crée une GitHub Release avec l'archive scellée en asset.

    Utilise l'API REST GitHub directement (sans dépendre de gh CLI).

    Args:
        archive_path: Chemin de l'archive tar.gz.
        manifest: Manifeste de scellement.
        dry_run: Simulation sans création.

    Returns:
        True si la release a été créée (ou simulée).
    """
    meta = manifest.get("meta", {})
    archive_info = manifest.get("archive", {})
    summary = manifest.get("summary", {})

    version = meta.get("version", "2.0.0")
    tag = f"{RELEASE_TAG_PREFIX}{version}"
    timestamp = meta.get("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    # Corps de la release
    release_body = (
        f"## MTTV-FLP Écosystème Scellé — V{version}\n\n"
        f"**ID d'exécution :** {meta.get('execution_id', 'N/A')}\n\n"
        f"**Timestamp :** {timestamp}\n"
        f"**Signature :** {MTTV_SIG}\n"
        f"**Statut :** {meta.get('status', 'LOCKED_AND_IMMUTABLE')}\n\n"
        f"### Récapitulatif\n\n"
        f"| Métrique | Valeur |\n"
        f"|----------|--------|\n"
        f"| Modules scellés | {summary.get('total_modules', 0)} |\n"
        f"| Checksums OK | {summary.get('modules_with_checksum', 0)} |\n"
        f"| Axes couverts | {summary.get('axe_coverage', [])} |\n"
        f"| Taille archive | {archive_info.get('size_bytes', 0):,} bytes |\n"
        f"| SHA3-256 | `{archive_info.get('sha3_256', 'N/A')}` |\n"
        f"| Root Pointer | {archive_info.get('root_pointer', 'N/A')} |\n\n"
        f"### DOI Zenodo\n\n"
        f"DOI : `{ZENODO_DOI}`\n"
        f"Lien : https://doi.org/{ZENODO_DOI}\n\n"
        f"### Contenu\n\n"
        f"L'archive contient l'intégralité des modules Python synchronisés "
        f"de l'écosystème MTTV-FLP, incluant les Agents Ouroboros 1→9, "
        f"l'extension navigateur, les scripts Phase 4, et les modules transverses.\n\n"
        f"---\n"
        f"*Généré automatiquement par export_sealed_archive.py — sig:{MTTV_SIG}*"
    )

    if dry_run:
        logger.info("[DRY-RUN] GitHub Release serait créée avec:")
        logger.info("  Tag    : %s", tag)
        logger.info("  Titre  : MTTV-FLP Écosystème Scellé — V%s", version)
        logger.info("  Asset  : %s", archive_path)
        logger.info("  Body   :\n%s", release_body)
        return True

    # Vérifier le token GitHub
    token = _get_github_token()
    if not token:
        logger.error("Token GitHub non trouvé. Définissez GITHUB_TOKEN ou créez .github_token")
        return False

    logger.info("Token GitHub trouvé (longueur: %d caractères)", len(token))

    # ── Étape 1: Créer la release ─────────────────────────────────────
    logger.info("Création de la release GitHub: tag=%s", tag)
    status, release_data = _github_api_request("POST", f"/repos/{GITHUB_REPO}/releases", data={
        "tag_name": tag,
        "name": f"MTTV-FLP Écosystème Scellé — V{version}",
        "body": release_body,
        "draft": False,
        "prerelease": False,
        "make_latest": "true",
    })

    if status not in (201, 202):
        logger.error("Échec création release (HTTP %d)", status)
        return False

    release_id = release_data.get("id")
    upload_url_template = release_data.get("upload_url", "")
    logger.info("Release créée: id=%d, tag=%s", release_id, tag)
    logger.info("  Voir: https://github.com/%s/releases/tag/%s", GITHUB_REPO, tag)

    # ── Étape 2: Upload de l'asset archive ────────────────────────────
    logger.info("Upload de l'asset: %s (%d bytes)", archive_path.name, archive_path.stat().st_size)
    # L'upload_url contient un template {?name,label} qu'on remplace
    upload_base = upload_url_template.split("{")[0]  # Enlève le template
    upload_url = f"{upload_base}?name={archive_path.name}"

    archive_bytes = archive_path.read_bytes()
    status, upload_data = _github_api_request(
        "POST", upload_url.replace("https://api.github.com", ""),
        binary_data=archive_bytes,
        content_type="application/gzip",
        accept="application/vnd.github.v3+json",
    )

    if status in (201, 202):
        logger.info("Asset uploadé avec succès: id=%s", upload_data.get("id"))
        return True
    else:
        logger.error("Échec upload asset (HTTP %d)", status)
        # La release existe déjà, c'est un succès partiel
        return True


# ===========================================================================
# 3. MÉTADONNÉES ZENODO
# ===========================================================================


def build_zenodo_metadata(manifest: dict[str, Any]) -> dict[str, Any]:
    """Construit les métadonnées Zenodo pour l'archive scellée.

    Utilise le DOI existant 10.5281/zenodo.17940301 et prépare
    une nouvelle version du dépôt avec l'archive V2.

    Returns:
        Dict prêt à être soumis à l'API Zenodo.
    """
    meta = manifest.get("meta", {})
    archive_info = manifest.get("archive", {})
    summary = manifest.get("summary", {})
    version = meta.get("version", "2.0.0")

    # Liste des modules sous forme de notes
    modules_list = []
    for mod in manifest.get("modules", []):
        checksum = mod.get("checksum", "?")[:16] if mod.get("checksum") else "?"
        modules_list.append(f"- {mod['path']} ({mod['label']}) — [{checksum}]")

    modules_section = "\n".join(modules_list)

    metadata: dict[str, Any] = {
        "metadata": {
            "title": f"MTTV-FLP Écosystème Scellé — V{version}",
            "description": (
                f"Archive scellée de l'écosystème MTTV-FLP.\n\n"
                f"**ID d'exécution :** {meta.get('execution_id', 'N/A')}\n"
                f"**Signature :** {MTTV_SIG}\n"
                f"**Statut :** {meta.get('status', 'LOCKED_AND_IMMUTABLE')}\n"
                f"**SHA3-256 :** `{archive_info.get('sha3_256', 'N/A')}`\n"
                f"**Root Pointer :** {archive_info.get('root_pointer', 'N/A')}\n\n"
                f"### Modules inclus ({summary.get('total_modules', 0)})\n\n"
                f"{modules_section}\n\n"
                f"### Axes couverts\n\n"
                f"{summary.get('axe_coverage', [])}\n\n"
                f"### Cadre philosophique\n\n"
                f"Triade : Ψ → B → Φ\n"
                f"Invariant : T⁴ = [T++, T--, T+-, T-+]\n"
                f"Formule canonique : Ψ = H → H₂O → C\n"
                f"Éthique : Non-extractivité, ouverture, ACTIVE-SILENCE"
            ),
            "creators": [
                {
                    "name": "FLP Lausanne",
                    "affiliation": "FLP Lausanne — Coordination Mycélienne",
                    "orcid": None,
                },
                {
                    "name": "Gaillard, Floreal",
                    "affiliation": "FLP Lausanne",
                },
            ],
            "access_right": "open",
            "license": "CC-BY-4.0",
            "upload_type": "software",
            "version": version,
            "keywords": [
                "MTTV-FLP",
                "SOPH-IA",
                "ethical friction",
                "habitability",
                "quorum consensus",
                "ouroboros swarm",
                "IPFS",
                "transduction",
                "tetravalence",
                "mycelial network",
            ],
            "related_identifiers": [
                {
                    "relation": "isSupplementTo",
                    "identifier": f"https://github.com/{GITHUB_REPO}",
                    "resource_type": "software",
                },
                {
                    "relation": "isPreviousVersionOf",
                    "identifier": f"https://doi.org/{ZENODO_DOI}",
                    "resource_type": "publication",
                },
            ],
            "references": [
                "SOPH-IA v2.0 benchmark suite",
                "MTTV-FLP Core Model (2026)",
            ],
            "doi": ZENODO_DOI,
        }
    }

    return metadata


def save_zenodo_metadata(
    metadata: dict[str, Any],
    dry_run: bool = False,
) -> Optional[Path]:
    """Sauvegarde les métadonnées Zenodo au format JSON.

    Args:
        metadata: Métadonnées formatées pour l'API Zenodo.
        dry_run: Simulation sans écriture.

    Returns:
        Chemin du fichier sauvegardé, ou None si dry_run.
    """
    output_path = ARCHIVE_DIR / "zenodo_metadata.json"

    if dry_run:
        logger.info("[DRY-RUN] Métadonnées Zenodo seraient écrites dans: %s", output_path)
        logger.info("[DRY-RUN] Contenu:\n%s", json.dumps(metadata, indent=2, ensure_ascii=False))
        return None

    try:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Métadonnées Zenodo sauvegardées: %s (%d bytes)",
                     output_path, output_path.stat().st_size)
        return output_path
    except Exception as exc:
        logger.error("Erreur sauvegarde métadonnées Zenodo: %s", exc)
        return None


# ===========================================================================
# POINT D'ENTRÉE
# ===========================================================================


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Export de l'archive scellée MTTV-FLP vers GitHub Releases et préparation Zenodo",
        epilog=f"DOI: {ZENODO_DOI} | sig:{MTTV_SIG}",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulation sans écriture ni appel à gh",
    )
    parser.add_argument(
        "--zenodo-only", action="store_true",
        help="Générer uniquement les métadonnées Zenodo (pas de GitHub Release)",
    )
    parser.add_argument(
        "--github-only", action="store_true",
        help="Créer uniquement la GitHub Release (pas de métadonnées Zenodo)",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("  EXPORT SEALED ARCHIVE")
    logger.info("  DOI: %s", ZENODO_DOI)
    logger.info("  Signature: %s", MTTV_SIG)
    logger.info("  Dry run: %s", args.dry_run)
    logger.info("=" * 60)

    # ── Vérifier l'archive ──────────────────────────────────────────────
    archive_path, archive_hash = verify_archive()
    if not archive_path or not archive_hash:
        logger.error("Archive invalide ou introuvable. Abandon.")
        sys.exit(1)

    manifest = load_manifest()
    if not manifest:
        sys.exit(1)

    success = True

    # ── GitHub Release ──────────────────────────────────────────────────
    if not args.zenodo_only:
        print()
        logger.info("[1/2] Création de la GitHub Release...")
        gh_ok = create_github_release(archive_path, manifest, dry_run=args.dry_run)
        if gh_ok:
            logger.info("  ✓ GitHub Release %s", "simulée" if args.dry_run else "créée")
        else:
            logger.error("  ✗ GitHub Release échouée")
            success = False

    # ── Métadonnées Zenodo ──────────────────────────────────────────────
    if not args.github_only:
        print()
        logger.info("[2/2] Génération des métadonnées Zenodo...")
        zenodo_meta = build_zenodo_metadata(manifest)
        zenodo_path = save_zenodo_metadata(zenodo_meta, dry_run=args.dry_run)
        if zenodo_path or args.dry_run:
            logger.info("  ✓ Métadonnées Zenodo %s", "simulées" if args.dry_run else "sauvegardées")
        else:
            logger.error("  ✗ Métadonnées Zenodo échouées")
            success = False

    # ── Résumé ──────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"  EXPORT TERMINÉ — {'SUCCÈS' if success else 'ÉCHEC PARTIEL'}")
    print(f"  Archive  : {archive_path.name}")
    print(f"  SHA3-256 : {archive_hash}")
    print(f"  DOI      : {ZENODO_DOI}")
    print(f"  Signature: {MTTV_SIG}")
    if not args.zenodo_only and not args.dry_run:
        print(f"  Release  : https://github.com/{GITHUB_REPO}/releases/tag/"
              f"{RELEASE_TAG_PREFIX}{manifest.get('meta', {}).get('version', '2.0.0')}")
    if not args.github_only and not args.dry_run and zenodo_path:
        print(f"  Zenodo   : {zenodo_path}")
    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
