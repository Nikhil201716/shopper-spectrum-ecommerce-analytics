$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $projectRoot

if (Test-Path -LiteralPath ".\.venv\Scripts\python.exe") {
    & ".\.venv\Scripts\python.exe" -m streamlit run app.py
}
else {
    python -m streamlit run app.py
}

