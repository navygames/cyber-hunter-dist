#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"
$HostName = "g94na.update.easebar.com"
$HostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
$lines = Get-Content -LiteralPath $HostsPath | Where-Object { $_ -notmatch [regex]::Escape($HostName) }
Set-Content -LiteralPath $HostsPath -Value $lines -Encoding ascii
Write-Host "removed hosts entries for $HostName"
