# Force-run all collectors immediately
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
& "$root\.venv\Scripts\python.exe" collector\main.py --once
