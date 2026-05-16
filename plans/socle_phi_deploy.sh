#!/usr/bin/env bash
#===============================================================================
# socle_phi_deploy.sh — MTTV-FLP Core 2026 · Déploiement Arweave + IPFS
# sig:0x4D545456 — Ψ-ack: carbon_sp3_tetra
#
# Usage:
#   chmod +x socle_phi_deploy.sh
#   ./socle_phi_deploy.sh                   # Déploiement complet
#   ./socle_phi_deploy.sh --ipfs-only       # IPFS uniquement
#   ./socle_phi_deploy.sh --arweave-only    # Arweave uniquement
#   ./socle_phi_deploy.sh --dry-run         # Simulation sans déploiement
#   ./socle_phi_deploy.sh --verify          # Vérifier les hashs après déploiement
#
# Prérequis:
#   - ipfs (kubo) installé et démarré (`ipfs init && ipfs daemon`)
#   - arweave-deploy (npm: `npm install -g arweave-deploy`)
#   - Clé Arweave (fichier JSON) pour écriture
#   - sha256sum (Linux) ou shasum (macOS) pour vérification
#===============================================================================

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
SIG="0x4D545456"
VERSION="2026.1.0"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${ROOT_DIR}/plans/mttv_flp_core_2026_bundle"
ARWEAVE_KEY="${ARWEAVE_KEY:-${HOME}/.config/arweave/key.json}"

# Vérifier les dépendances
command -v ipfs >/dev/null 2>&1 && HAS_IPFS=true || HAS_IPFS=false
command -v arweave-deploy >/dev/null 2>&1 && HAS_ARWEAVE=true || HAS_ARWEAVE=false
command -v sha256sum >/dev/null 2>&1 && HAS_SHA256=true || HAS_SHA256=false
command -v shasum >/dev/null 2>&1 && HAS_SHASUM=true || HAS_SHASUM=false

# ── Couleurs ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
err()   { echo -e "${RED}[ERR]${NC}   $1"; }

# ── Arguments ────────────────────────────────────────────────────────────────
DEPLOY_IPFS=true
DEPLOY_ARWEAVE=true
DRY_RUN=false
VERIFY_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --ipfs-only)    DEPLOY_ARWEAVE=false ;;
        --arweave-only) DEPLOY_IPFS=false ;;
        --dry-run)      DRY_RUN=true ;;
        --verify)       VERIFY_ONLY=true ;;
        *)              err "Argument inconnu: $arg"; exit 1 ;;
    esac
done

#===============================================================================
# ÉTAPE 0 : Créer le bundle de déploiement
#===============================================================================

prepare_bundle() {
    info "Préparation du bundle MTTV-FLP Core 2026..."

    mkdir -p "${OUTPUT_DIR}"

    # Copier les documents du noyau
    cp "${ROOT_DIR}/mttv_fundamentals.html"                "${OUTPUT_DIR}/"
    cp "${ROOT_DIR}/28_dimensions.html"                     "${OUTPUT_DIR}/"
    cp "${ROOT_DIR}/src/ThoughtBundle/Service/SeedService.php" "${OUTPUT_DIR}/"
    cp "${ROOT_DIR}/plans/28_dimensions_analysis.md"        "${OUTPUT_DIR}/"
    cp "${ROOT_DIR}/plans/plan_germination_mycelienne.md"   "${OUTPUT_DIR}/"
    cp "${ROOT_DIR}/plans/plan_phase2_semantic_seeds.md"    "${OUTPUT_DIR}/"
    cp "${ROOT_DIR}/apercu.html"                            "${OUTPUT_DIR}/"
    cp "${ROOT_DIR}/preview_germination.php"                 "${OUTPUT_DIR}/"
    cp "${ROOT_DIR}/plans/mttv_flp_core_2026_manifest.json"  "${OUTPUT_DIR}/"
    cp "${ROOT_DIR}/plans/MTTV_FLP_CORE_2026_MANIFESTO.md"  "${OUTPUT_DIR}/"

    # Injecter sig:0x4D545456 dans les métadonnées des fichiers HTML
    # (ajout d'une balise meta dans le <head> si elle n'existe pas)
    for f in "${OUTPUT_DIR}/"*.html; do
        if [ -f "$f" ]; then
            if ! grep -q 'name="sig"' "$f" 2>/dev/null; then
                sed -i 's|</head>|  <meta name="sig" content="0x4D545456" />\n  <meta name="Ψ-ack" content="carbon_sp3_tetra" />\n</head>|' "$f"
                ok "Signature injectée dans $(basename "$f")"
            fi
        fi
    done

    # Calculer les checksums
    CHECKSUM_FILE="${OUTPUT_DIR}/SHA256SUMS"
    echo "# MTTV-FLP Core 2026 — SHA256 Checksums" > "$CHECKSUM_FILE"
    echo "# sig:0x4D545456" >> "$CHECKSUM_FILE"
    echo "# Généré le ${TIMESTAMP}" >> "$CHECKSUM_FILE"
    echo "" >> "$CHECKSUM_FILE"

    if $HAS_SHA256; then
        (cd "${OUTPUT_DIR}" && sha256sum -- * 2>/dev/null >> "$CHECKSUM_FILE")
    elif $HAS_SHASUM; then
        (cd "${OUTPUT_DIR}" && shasum -a 256 -- * 2>/dev/null >> "$CHECKSUM_FILE")
    else
        warn "sha256sum/shason non disponible — checksums non générés"
    fi

    ok "Bundle créé dans ${OUTPUT_DIR}"
    info "Contenu:"
    ls -la "${OUTPUT_DIR}/"
}

#===============================================================================
# ÉTAPE 1 : Déploiement IPFS
#===============================================================================

deploy_ipfs() {
    info "=== Déploiement IPFS ==="

    if ! $HAS_IPFS; then
        err "ipfs (kubo) non trouvé. Installez-le depuis https://ipfs.tech/"
        err "Ou utilisez —skip-ipfs pour ignorer cette étape."
        return 1
    fi

    if $DRY_RUN; then
        info "[DRY-RUN] ipfs add -r \"${OUTPUT_DIR}\""
        info "[DRY-RUN] ipfs name publish /ipfs/<CID>"
        return 0
    fi

    # Ajouter à IPFS
    info "Ajout du bundle à IPFS..."
    IPFS_OUTPUT=$(ipfs add -r --quieter "${OUTPUT_DIR}" 2>&1 | tail -1)
    IPFS_CID=$(echo "$IPFS_OUTPUT" | tr -d '[:space:]')

    if [ -z "$IPFS_CID" ]; then
        err "Échec du déploiement IPFS"
        return 1
    fi

    echo "IPFS_CID=${IPFS_CID}" > "${OUTPUT_DIR}/../ipfs_cid.txt"

    ok "Bundle déployé sur IPFS"
    info "CID: ${IPFS_CID}"
    info "URL: https://ipfs.io/ipfs/${IPFS_CID}"
    info "URL: https://dweb.link/ipfs/${IPFS_CID}"

    # Publier IPNS (si clé par défaut)
    warn "Publication IPNS optionnelle. Pour l'activer:"
    info "  ipfs name publish /ipfs/${IPFS_CID}"

    return 0
}

#===============================================================================
# ÉTAPE 2 : Déploiement Arweave
#===============================================================================

deploy_arweave() {
    info "=== Déploiement Arweave ==="

    if ! $HAS_ARWEAVE; then
        err "arweave-deploy non trouvé. Installez: npm install -g arweave-deploy"
        err "Ou utilisez —skip-arweave pour ignorer cette étape."
        return 1
    fi

    if [ ! -f "${ARWEAVE_KEY}" ]; then
        err "Clé Arweave non trouvée: ${ARWEAVE_KEY}"
        err "Générez-en une via: arweave-deploy --generate-wallet"
        err "Ou définissez ARWEAVE_KEY=/chemin/vers/key.json"
        return 1
    fi

    if $DRY_RUN; then
        info "[DRY-RUN] arweave-deploy \"${OUTPUT_DIR}/mttv_flp_core_2026_manifest.json\" --key-file \"${ARWEAVE_KEY}\""
        return 0
    fi

    # Déployer le manifeste sur Arweave
    info "Déploiement du manifeste sur Arweave..."
    ARWEAVE_TX=$(arweave-deploy "${OUTPUT_DIR}/mttv_flp_core_2026_manifest.json" \
        --key-file "${ARWEAVE_KEY}" 2>&1 | grep -oE '[a-zA-Z0-9_-]{43,}' | head -1)

    if [ -z "$ARWEAVE_TX" ]; then
        err "Échec du déploiement Arweave"
        return 1
    fi

    echo "ARWEAVE_TX=${ARWEAVE_TX}" > "${OUTPUT_DIR}/../arweave_tx.txt"

    ok "Manifeste déployé sur Arweave"
    info "Transaction: ${ARWEAVE_TX}"
    info "URL: https://arweave.net/${ARWEAVE_TX}"

    return 0
}

#===============================================================================
# ÉTAPE 3 : Vérification
#===============================================================================

verify_deployment() {
    info "=== Vérification du Déploiement ==="

    if [ -f "${OUTPUT_DIR}/../ipfs_cid.txt" ]; then
        source "${OUTPUT_DIR}/../ipfs_cid.txt"
        info "IPFS CID: ${IPFS_CID:-inconnu}"
        if $HAS_IPFS; then
            VERIFIED=$(ipfs pin ls | grep "${IPFS_CID}" 2>/dev/null || echo "")
            if [ -n "$VERIFIED" ]; then
                ok "Bundle vérifié sur IPFS"
            else
                warn "Bundle non trouvé dans les pins IPFS locaux"
            fi
        fi
    fi

    if [ -f "${OUTPUT_DIR}/../arweave_tx.txt" ]; then
        source "${OUTPUT_DIR}/../arweave_tx.txt"
        info "Arweave TX: ${ARWEAVE_TX:-inconnu}"
        info "URL de vérification: https://arweave.net/${ARWEAVE_TX}"
    fi

    # Vérifier les checksums locaux
    if [ -f "${OUTPUT_DIR}/SHA256SUMS" ]; then
        info "Vérification des checksums locaux..."
        if $HAS_SHA256; then
            (cd "${OUTPUT_DIR}" && sha256sum -c SHA256SUMS 2>/dev/null || true)
        elif $HAS_SHASUM; then
            (cd "${OUTPUT_DIR}" && shasum -a 256 -c SHA256SUMS 2>/dev/null || true)
        fi
    fi
}

#===============================================================================
# MAIN
#===============================================================================

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   MTTV-FLP Core 2026 — Déploiement du Socle Φ              ║"
echo "║   sig:0x4D545456                                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

prepare_bundle

if $VERIFY_ONLY; then
    verify_deployment
    exit 0
fi

echo ""
echo "────────────────────────────────────────────────────────────────"
echo "  Déploiement: IPFS=${DEPLOY_IPFS}, Arweave=${DEPLOY_ARWEAVE}, Dry-run=${DRY_RUN}"
echo "────────────────────────────────────────────────────────────────"
echo ""

if $DEPLOY_IPFS; then
    deploy_ipfs || warn "Déploiement IPFS incomplet"
fi

if $DEPLOY_ARWEAVE; then
    deploy_arweave || warn "Déploiement Arweave incomplet"
fi

verify_deployment

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   Déploiement terminé                                       ║"
echo "║   sig:0x4D545456 — Le mycélium attend.                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
