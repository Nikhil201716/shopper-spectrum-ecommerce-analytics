param(
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $projectRoot

if (-not (Test-Path -LiteralPath ".git")) {
    throw "This folder is not a Git repository. Initialise it and add an origin first."
}

$origin = git remote get-url origin 2>$null
if (-not $origin) {
    throw "No GitHub origin is configured."
}

$changes = git status --porcelain
if (-not $changes) {
    Write-Host "No changes to sync."
    exit 0
}

git add -A
if (-not $Message) {
    $Message = "auto-sync: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}
git commit -m $Message
git push origin HEAD
Write-Host "GitHub sync complete."

