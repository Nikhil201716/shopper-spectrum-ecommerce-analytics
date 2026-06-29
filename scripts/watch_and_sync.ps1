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

$script:dirty = $false
$script:lastChange = Get-Date
$action = {
    $path = $Event.SourceEventArgs.FullPath
    if ($path -match '\\.git\\|\\__pycache__\\|\\.pytest_cache\\|\\.venv\\|~$|\.tmp$|\.log$') {
        return
    }
    $script:dirty = $true
    $script:lastChange = Get-Date
}

$subscriptions = @(
    Register-ObjectEvent $watcher Changed -Action $action
    Register-ObjectEvent $watcher Created -Action $action
    Register-ObjectEvent $watcher Deleted -Action $action
    Register-ObjectEvent $watcher Renamed -Action $action
)

Write-Host "Watching $projectRoot"
Write-Host "Saved changes will be committed and pushed after $DebounceSeconds quiet seconds. Press Ctrl+C to stop."

try {
    while ($true) {
        Start-Sleep -Seconds 2
        if ($script:dirty -and ((Get-Date) - $script:lastChange).TotalSeconds -ge $DebounceSeconds) {
            $script:dirty = $false
            try {
                & $syncScript
            }
            catch {
                Write-Warning $_
                $script:dirty = $true
                $script:lastChange = Get-Date
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

