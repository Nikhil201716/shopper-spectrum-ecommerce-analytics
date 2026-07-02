param(
    [int]$DebounceSeconds = 20
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$syncScript = Join-Path $PSScriptRoot "sync_to_github.ps1"

Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath ".git")) {
    throw "This folder is not a Git repository. Publish it once before starting auto-sync."
}

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $projectRoot
$watcher.IncludeSubdirectories = $true
$watcher.NotifyFilter = [System.IO.NotifyFilters]'FileName, DirectoryName, LastWrite, Size'
$watcher.EnableRaisingEvents = $true

$dirty = [bool](git status --porcelain)
$lastChange = Get-Date
$sourceIdentifiers = @(
    "ShopperSpectrum.Changed",
    "ShopperSpectrum.Created",
    "ShopperSpectrum.Deleted",
    "ShopperSpectrum.Renamed"
)
$subscriptions = @(
    Register-ObjectEvent $watcher Changed -SourceIdentifier $sourceIdentifiers[0]
    Register-ObjectEvent $watcher Created -SourceIdentifier $sourceIdentifiers[1]
    Register-ObjectEvent $watcher Deleted -SourceIdentifier $sourceIdentifiers[2]
    Register-ObjectEvent $watcher Renamed -SourceIdentifier $sourceIdentifiers[3]
)

Write-Host "Watching $projectRoot"
Write-Host "Saved changes will be committed and pushed after $DebounceSeconds quiet seconds. Press Ctrl+C to stop."

try {
    while ($true) {
        Start-Sleep -Seconds 2
        foreach ($pendingEvent in @(Get-Event -ErrorAction SilentlyContinue)) {
            if ($pendingEvent.SourceIdentifier -notin $sourceIdentifiers) {
                continue
            }
            $path = $pendingEvent.SourceEventArgs.FullPath
            Remove-Event -EventIdentifier $pendingEvent.EventIdentifier -ErrorAction SilentlyContinue
            if ($path -match '\\.git\\|\\__pycache__\\|\\.pytest_cache\\|\\.venv\\|~$|\.tmp$|\.log$') {
                continue
            }
            $dirty = $true
            $lastChange = Get-Date
        }
        if ($dirty -and ((Get-Date) - $lastChange).TotalSeconds -ge $DebounceSeconds) {
            $dirty = $false
            try {
                & $syncScript
            }
            catch {
                Write-Warning $_
                $dirty = $true
                $lastChange = Get-Date
            }
        }
    }
}
finally {
    foreach ($subscription in $subscriptions) {
        Unregister-Event -SubscriptionId $subscription.Id -ErrorAction SilentlyContinue
    }
    $watcher.Dispose()
}
