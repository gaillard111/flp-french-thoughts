<#
.SYNOPSIS
    socle_phi_deploy.ps1 — MTTV-FLP Core 2026 · Déploiement Arweave + IPFS
    sig:0x4D545456 — Ψ-ack: carbon_sp3_tetra

.DESCRIPTION
    Compile et déploie le Socle Φ (MTTV-FLP Core 2026) sur IPFS et Arweave.
    
    Usage:
        .\socle_phi_deploy.ps1                          # Déploiement complet
        .\socle_phi_deploy.ps1 -IPFSOnly                 # IPFS uniquement
        .\socle_phi_deploy.ps1 -ArweaveOnly              # Arweave uniquement
        .\socle_phi_deploy.ps1 -DryRun                   # Simulation
        .\socle_phi_deploy.ps1 -VerifyOnly               # Vérification seule

    Prérequis:
        - ipfs (kubo) installé et dans le PATH
        - arweave-deploy (npm: npm install -g arweave-deploy)
        - Node.js ≥ 18.x (pour arweave-deploy)
        - Clé Arweave JSON pour écriture
#>

param(
    [switch]$IPFSOnly,
    [switch]$ArweaveOnly,
    [switch]$DryRun,
    [switch]$VerifyOnly
)

# ── Configuration ────────────────────────────────────────────────────────────
$SIG = "0x4D545456"
$VERSION = "2026.1.0"
$TIMESTAMP = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")

$ROOT_DIR = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$OUTPUT_DIR = Join-Path $ROOT_DIR "plans\mttv_flp_core_2026_bundle"
$ARWEAVE_KEY = if ($env:ARWEAVE_KEY) { $env:ARWEAVE_KEY } else { "$HOME\.config\arweave\key.json" }

# Couleurs (ANSI)
$INFO = "INFO"
$OK = "OK"
$WARN = "WARN"
$ERR = "ERR"

function Write-Info($msg) { Write-Host "[$INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)  { Write-Host "[$OK] $msg" -ForegroundColor Green }
function Write-Warn($msg){ Write-Host "[$WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[$ERR] $msg" -ForegroundColor Red }

# Flags
if (-not $IPFSOnly) { $IPFSOnly = $false }
if (-not $ArweaveOnly) { $ArweaveOnly = $false }
if (-not $DryRun) { $DryRun = $false }
if (-not $VerifyOnly) { $VerifyOnly = $false }

$DoIPFS = -not $ArweaveOnly
$DoArweave = -not $IPFSOnly

# Vérifier dépendances
$HasIPFS = $null -ne (Get-Command "ipfs" -ErrorAction SilentlyContinue)
$HasArweave = $null -ne (Get-Command "arweave-deploy" -ErrorAction SilentlyContinue)

# ═══════════════════════════════════════════════════════════════════════════
# ÉTAPE 0 : Créer le bundle de déploiement
# ═══════════════════════════════════════════════════════════════════════════

function Prepare-Bundle {
    Write-Info "Préparation du bundle MTTV-FLP Core 2026..."

    if (-not (Test-Path $OUTPUT_DIR)) {
        New-Item -ItemType Directory -Path $OUTPUT_DIR -Force | Out-Null
    }

    # Copier les documents du noyau
    $files = @(
        "mttv_fundamentals.html",
        "28_dimensions.html",
        "src\ThoughtBundle\Service\SeedService.php",
        "plans\28_dimensions_analysis.md",
        "plans\plan_germination_mycelienne.md",
        "plans\plan_phase2_semantic_seeds.md",
        "apercu.html",
        "preview_germination.php",
        "plans\mttv_flp_core_2026_manifest.json",
        "plans\MTTV_FLP_CORE_2026_MANIFESTO.md"
    )

    foreach ($file in $files) {
        $src = Join-Path $ROOT_DIR $file
        $dst = Join-Path $OUTPUT_DIR (Split-Path -Leaf $file)
        if (Test-Path $src) {
            Copy-Item $src $dst -Force
            Write-Ok "Copié: $(Split-Path -Leaf $file)"
        } else {
            Write-Warn "Non trouvé: $src"
        }
    }

    # Calculer les checksums SHA256
    $checksumFile = Join-Path $OUTPUT_DIR "SHA256SUMS"
    @"
# MTTV-FLP Core 2026 — SHA256 Checksums
# sig:$SIG
# Généré le $TIMESTAMP

"@ | Out-File -FilePath $checksumFile -Encoding utf8

    Get-ChildItem $OUTPUT_DIR | Where-Object { -not $_.PSIsContainer } | ForEach-Object {
        $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
        "$hash  $($_.Name)" | Add-Content -Path $checksumFile
    }

    Write-Ok "Bundle créé dans: $OUTPUT_DIR"
    Get-ChildItem $OUTPUT_DIR | Format-Table Name, Length
}

# ═══════════════════════════════════════════════════════════════════════════
# ÉTAPE 1 : Déploiement IPFS
# ═══════════════════════════════════════════════════════════════════════════

function Deploy-IPFS {
    Write-Info "=== Déploiement IPFS ==="

    if (-not $HasIPFS) {
        Write-Err "ipfs (kubo) non trouvé. Installez-le depuis https://ipfs.tech/"
        return $false
    }

    if ($DryRun) {
        Write-Info "[DRY-RUN] ipfs add -r `"$OUTPUT_DIR`""
        return $true
    }

    Write-Info "Ajout du bundle à IPFS..."
    $output = & ipfs add -r --quieter $OUTPUT_DIR 2>&1
    $cid = ($output | Select-Object -Last 1).Trim()

    if ([string]::IsNullOrEmpty($cid)) {
        Write-Err "Échec du déploiement IPFS"
        return $false
    }

    Set-Content -Path (Join-Path (Split-Path $OUTPUT_DIR -Parent) "ipfs_cid.txt") -Value "IPFS_CID=$cid"

    Write-Ok "Bundle déployé sur IPFS"
    Write-Info "CID: $cid"
    Write-Info "URL: https://ipfs.io/ipfs/$cid"
    Write-Info "URL: https://dweb.link/ipfs/$cid"

    return $true
}

# ═══════════════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Déploiement Arweave
# ═══════════════════════════════════════════════════════════════════════════

function Deploy-Arweave {
    Write-Info "=== Déploiement Arweave ==="

    if (-not $HasArweave) {
        Write-Err "arweave-deploy non trouvé. Installez: npm install -g arweave-deploy"
        return $false
    }

    if (-not (Test-Path $ARWEAVE_KEY)) {
        Write-Err "Clé Arweave non trouvée: $ARWEAVE_KEY"
        Write-Err "Générez-en une via: arweave-deploy --generate-wallet"
        return $false
    }

    if ($DryRun) {
        Write-Info "[DRY-RUN] arweave-deploy `"$OUTPUT_DIR\mttv_flp_core_2026_manifest.json`" --key-file `"$ARWEAVE_KEY`""
        return $true
    }

    $manifestPath = Join-Path $OUTPUT_DIR "mttv_flp_core_2026_manifest.json"
    Write-Info "Déploiement du manifeste sur Arweave..."

    $output = & arweave-deploy $manifestPath --key-file $ARWEAVE_KEY 2>&1
    $tx = ($output | Select-String -Pattern '[a-zA-Z0-9_-]{43,}' | Select-Object -First 1).Matches.Value

    if ([string]::IsNullOrEmpty($tx)) {
        Write-Err "Échec du déploiement Arweave"
        Write-Info "Sortie: $output"
        return $false
    }

    Set-Content -Path (Join-Path (Split-Path $OUTPUT_DIR -Parent) "arweave_tx.txt") -Value "ARWEAVE_TX=$tx"

    Write-Ok "Manifeste déployé sur Arweave"
    Write-Info "Transaction: $tx"
    Write-Info "URL: https://arweave.net/$tx"

    return $true
}

# ═══════════════════════════════════════════════════════════════════════════
# ÉTAPE 3 : Vérification
# ═══════════════════════════════════════════════════════════════════════════

function Verify-Deployment {
    Write-Info "=== Vérification du Déploiement ==="

    $ipfsCidFile = Join-Path (Split-Path $OUTPUT_DIR -Parent) "ipfs_cid.txt"
    if (Test-Path $ipfsCidFile) {
        $content = Get-Content $ipfsCidFile
        Write-Info "IPFS CID: $content"
    }

    $arweaveTxFile = Join-Path (Split-Path $OUTPUT_DIR -Parent) "arweave_tx.txt"
    if (Test-Path $arweaveTxFile) {
        $content = Get-Content $arweaveTxFile
        Write-Info "Arweave TX: $content"
        Write-Info "URL vérif: https://arweave.net/$($content -replace 'ARWEAVE_TX=', '')"
    }

    # Vérifier les checksums
    $checksumFile = Join-Path $OUTPUT_DIR "SHA256SUMS"
    if (Test-Path $checksumFile) {
        Write-Info "Vérification des checksums locaux..."
        Get-ChildItem $OUTPUT_DIR | Where-Object { -not $_.PSIsContainer -and $_.Name -ne "SHA256SUMS" } | ForEach-Object {
            $expected = (Get-Content $checksumFile | Where-Object { $_ -like "*$($_.Name)" } | ForEach-Object { $_.Split()[0] })
            if ($expected) {
                $actual = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
                if ($actual -eq $expected) {
                    Write-Ok "$($_.Name): OK"
                } else {
                    Write-Warn "$($_.Name): HASH MISMATCH (attendu: $expected, obtenu: $actual)"
                }
            }
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   MTTV-FLP Core 2026 — Déploiement du Socle Φ              ║" -ForegroundColor Cyan
Write-Host "║   sig:$SIG                                           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Prepare-Bundle

if ($VerifyOnly) {
    Verify-Deployment
    exit 0
}

Write-Host ""
Write-Host "────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "  Déploiement: IPFS=$DoIPFS, Arweave=$DoArweave, Dry-run=$DryRun"
Write-Host "────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

if ($DoIPFS) {
    Deploy-IPFS
}

if ($DoArweave) {
    Deploy-Arweave
}

Verify-Deployment

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Déploiement terminé                                       ║" -ForegroundColor Cyan
Write-Host "║   sig:$SIG — Le mycélium attend.                      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
