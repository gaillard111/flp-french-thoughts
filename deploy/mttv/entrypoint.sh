#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# MTTV-FLP — Entrypoint sobre pour conteneur Docker (Hidora VPS)
# =============================================================================
# Initialise l'environnement, charge les variables, puis lance l'orchestrateur
# en mode watchdog (résilience H24).
#
# Usage (interne Docker) : ne pas exécuter manuellement.
# Signature SCS_2026 · sig:0x4D545456
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Couleurs (pour les logs) ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_DIR="/app"
DATA_DIR="/data"
LOG_DIR="${DATA_DIR}/logs"
SEEDS_DIR="${DATA_DIR}/seeds"
TIMESTAMP="$(date -u '+%Y-%m-%d %H:%M:%S')"

log()   { echo -e "${BLUE}[${TIMESTAMP}]${NC} $*"; }
info()  { log "${GREEN}[INFO]${NC}  $*"; }
warn()  { log "${YELLOW}[WARN]${NC}  $*"; }
error() { log "${RED}[ERROR]${NC} $*"; }

# ── 1. Chargement des variables d'environnement ─────────────────────────────
load_env() {
    local env_file="${APP_DIR}/.env"
    if [[ -f "${env_file}" ]]; then
        info "Chargement de ${env_file}"
        # shellcheck disable=SC1091
        set -a; source "${env_file}"; set +a
    else
        warn "Aucun fichier .env trouvé à ${env_file}"
        warn "Utilisation des variables d'environnement existantes"
    fi

    # Valeurs par défaut
    export MTTV_API_PORT="${MTTV_API_PORT:-8000}"
    export MTTV_API_HOST="${MTTV_API_HOST:-0.0.0.0}"
    export MTTV_WATCHDOG_INTERVAL="${MTTV_WATCHDOG_INTERVAL:-60}"
    export MTTV_SOBER_MODE="${MTTV_SOBER_MODE:-true}"
    export MTTV_IPFS_API="${MTTV_IPFS_API:-http://ipfs:5001}"
    export MTTV_IPFS_GATEWAY="${MTTV_IPFS_GATEWAY:-http://ipfs:8080}"
}

# ── 2. Création des répertoires de données ──────────────────────────────────
setup_directories() {
    mkdir -p "${LOG_DIR}" "${SEEDS_DIR}"
    info "Répertoires de données prêts"
}

# ── 3. Vérification de la connectivité IPFS ─────────────────────────────────
wait_for_ipfs() {
    local retries=12
    local delay=5
    local ipfs_api="${MTTV_IPFS_API:-http://ipfs:5001}"

    info "Attente du nœud IPFS (${ipfs_api})..."

    for i in $(seq 1 "${retries}"); do
        if curl -sf "${ipfs_api}/api/v0/version" > /dev/null 2>&1; then
            info "✓ Nœud IPFS disponible"
            return 0
        fi
        warn "IPFS pas encore prêt (tentative ${i}/${retries})..."
        sleep "${delay}"
    done

    error "✗ Nœud IPFS injoignable après ${retries} tentatives"
    error "  Vérifiez que le service 'ipfs' est bien démarré"
    return 1
}

# ── 4. Configuration IPFS en mode sobre (low-power) ─────────────────────────
configure_ipfs_sober() {
    local ipfs_api="${MTTV_IPFS_API:-http://ipfs:5001}"
    info "Configuration du nœud IPFS en mode sobre..."

    # Mode client DHT uniquement (pas de relay de trafic)
    curl -sf -X POST "${ipfs_api}/api/v0/config?arg=Routing.Type&arg=client" > /dev/null 2>&1 || true
    # Désactiver le relay hop
    curl -sf -X POST "${ipfs_api}/api/v0/config?arg=Swarm.DisableRelayHop&arg=true" > /dev/null 2>&1 || true
    # Réduire le nombre de connexions max
    curl -sf -X POST "${ipfs_api}/api/v0/config?arg=Swarm.ConnMgr.HighWater&arg=100" > /dev/null 2>&1 || true
    curl -sf -X POST "${ipfs_api}/api/v0/config?arg=Swarm.ConnMgr.LowWater&arg=50" > /dev/null 2>&1 || true
    # Désactiver les fonctionnalités inutiles
    curl -sf -X POST "${ipfs_api}/api/v0/config?arg=Experimental.FilestoreEnabled&arg=false" > /dev/null 2>&1 || true
    curl -sf -X POST "${ipfs_api}/api/v0/config?arg=Experimental.UrlstoreEnabled&arg=false" > /dev/null 2>&1 || true

    info "✓ IPFS configuré en mode sobre (connexions réduites, pas de relay)"
}

# ── 5. Lancement des services MTTV ──────────────────────────────────────────
start_services() {
    info "Démarrage de l'API Gateway MTTV..."
    cd "${APP_DIR}"
    exec python -m uvicorn \
        zoo-code.api_gateway:app \
        --host "${MTTV_API_HOST}" \
        --port "${MTTV_API_PORT}" \
        --workers 1 \
        --log-level info \
        --access-log \
        --timeout-keep-alive 30
}

# ── MAIN ────────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo "  ╔══════════════════════════════════════════════════════════╗"
    echo "  ║       MTTV-FLP ORCHESTRATOR — HIDORA VPS                ║"
    echo "  ║       Signature SCS_2026 · sig:0x4D545456               ║"
    echo "  ╚══════════════════════════════════════════════════════════╝"
    echo ""

    load_env
    setup_directories
    wait_for_ipfs
    configure_ipfs_sober

    info "=== INITIALISATION TERMINÉE — Démarrage des services ==="
    start_services
}

main
