# Lire le token depuis une variable d'environnement pour sécurité
$token = $env:GH_DEPLOY_TOKEN
if (-not $token) { throw "GH_DEPLOY_TOKEN environment variable not set" }
$repo = "gaillard111/mttv-flp-core"
$source = "c:\Users\Master\flp-french-thoughts\deploy"
$branch = "main"

$files = @(
    "DEPLOY_HIDORA.md",
    "mttv/.env.example",
    "mttv/docker-compose.yml",
    "mttv/Dockerfile",
    "mttv/entrypoint.sh",
    "mttv/healthcheck.py",
    "mttv/mttv.service",
    "mttv/requirements.txt"
)

foreach ($f in $files) {
    $fullPath = Join-Path $source $f
    $apiPath = "deploy/$f" -replace '\\', '/'
    $content = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($fullPath))
    
    $body = @{
        message = "feat(deploy): ajout configuration deploiement Hidora VPS"
        content = $content
        branch = $branch
    } | ConvertTo-Json -Compress
    
    $uri = "https://api.github.com/repos/$repo/contents/$apiPath"
    
    try {
        $result = Invoke-RestMethod -Uri $uri -Method Put -Headers @{
            "Authorization" = "token $token"
            "Accept" = "application/vnd.github.v3+json"
            "Content-Type" = "application/json"
        } -Body $body
        
        $sha = $result.commit.sha.Substring(0, 8)
        Write-Host "[OK] $apiPath -> $sha"
    }
    catch {
        $errMsg = $_.Exception.Message
        if ($errMsg -match '"message":"(.*?)"') {
            Write-Host "[ERR] $apiPath -> $($matches[1])"
        } else {
            Write-Host "[ERR] $apiPath -> $errMsg"
        }
    }
}
