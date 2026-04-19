$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$global:OutputEncoding = $utf8NoBom

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

chcp 65001 > $null

Write-Host "UTF-8 session configured for PowerShell pipelines and Python."
Write-Host "Console input:  $([Console]::InputEncoding.WebName)"
Write-Host "Console output: $([Console]::OutputEncoding.WebName)"
Write-Host "OutputEncoding: $($global:OutputEncoding.WebName)"
Write-Host "PYTHONUTF8:     $env:PYTHONUTF8"
