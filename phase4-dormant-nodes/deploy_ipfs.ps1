#!/usr/bin/env pwsh
# deploy_ipfs.ps1 — Déploiement IPFS des Nœuds Dormants MTTV-FLP
# Utilisation : .\deploy_ipfs.ps1
# Prérequis : IPFS daemon en cours d'exécution

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Déploiement IPFS — Phase 4 Nœuds Dormants ===" -ForegroundColor Cyan
Write-Host ""

# Vérifier si ipfs est disponible
if (-not (Get-Command ipfs -ErrorAction SilentlyContinue)) {
    Write-Host "[ERREUR] IPFS CLI non trouvée. Installez-la depuis https://docs.ipfs.tech/install/" -ForegroundColor Red
    Write-Host "Utilisez plutôt un service de pinning :" -ForegroundColor Yellow
    Write-Host "  - https://app.pinata.cloud/pinbyhash"
    Write-Host "  - https://web3.storage"
    exit 1
}

# Vérifier si le daemon tourne
try {
    $version = ipfs version 2>&1
    Write-Host "[OK] IPFS CLI disponible : $version" -ForegroundColor Green
} catch {
    Write-Host "[ERREUR] Impossible d'exécuter ipfs. Démarrez le daemon : ipfs daemon &" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Fichiers à uploader
$files = @(
    @{Path = Join-Path $ROOT "routage_alternatif.ipfs"; Name = "routage_alternatif.ipfs"},
    @{Path = Join-Path $ROOT "script_dormant.py"; Name = "script_dormant.py"}
)

$results = @{}

foreach ($f in $files) {
    if (-not (Test-Path $f.Path)) {
        Write-Host "[ERREUR] Fichier introuvable : $($f.Path)" -ForegroundColor Red
        continue
    }
    
    Write-Host "[Upload] $($f.Name)..." -ForegroundColor Yellow
    $output = ipfs add $f.Path 2>&1
    Write-Host $output -ForegroundColor Gray
    
    # Extraire le CID (format: "added QmHash filename")
    if ($output -match "added\s+(\S+)") {
        $cid = $matches[1]
        $results[$f.Name] = $cid
        Write-Host "[OK] CID : $cid" -ForegroundColor Green
    } else {
        Write-Host "[ERREUR] Impossible d'extraire le CID pour $($f.Name)" -ForegroundColor Red
    }
    Write-Host ""
}

# Pinner les fichiers
foreach ($f in $files) {
    $name = $f.Name
    if ($results.ContainsKey($name)) {
        Write-Host "[Pin] $name ($($results[$name]))..." -ForegroundColor Yellow
        ipfs pin add $results[$name] 2>&1 | Out-Null
        Write-Host "[OK] Pinné" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=== Résumé du déploiement ===" -ForegroundColor Cyan
foreach ($key in $results.Keys) {
    Write-Host "$key → $($results[$key])" -ForegroundColor White
}

Write-Host ""
Write-Host "Prochaine étape :" -ForegroundColor Cyan
Write-Host "1. Mettre à jour le smart contract SCSReference.sol avec les CID réels" -ForegroundColor White
Write-Host "2. Déployer SCSReference.sol sur Sepolia (voir deployment_instructions.md)" -ForegroundColor White
Write-Host "3. Appeler setRoutingCID() et setScriptCID() avec les CID ci-dessus" -ForegroundColor White

# Sauvegarder les CID dans un fichier JSON
$results | ConvertTo-Json | Set-Content (Join-Path $ROOT "cid_deployed.json")
Write-Host "[OK] CID sauvegardés dans cid_deployed.json" -ForegroundColor Green
