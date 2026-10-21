#Requires -RunAsAdministrator
param(
    [string]$ServerIp = "127.0.0.1"
)
$ErrorActionPreference = "Stop"
$Marker = "# CyberHunter Revival Server"
$HostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"

if ($ServerIp -eq "YOUR_VPS_IP_HERE" -or $ServerIp -eq "") {
    Write-Warning "ServerIp is not configured. Edit revival_config.env and set REVIVAL_SERVER_IP."
    Write-Warning "Falling back to 127.0.0.1 (offline mode only)."
    $ServerIp = "127.0.0.1"
}

Write-Host "Redirecting NetEase hostnames -> $ServerIp" -ForegroundColor Cyan

$Hosts = @(
    "g94na.update.easebar.com",
    "drpf-g94na.proxima.nie.netease.com",
    "applog.matrix.easebar.com",
    "data-detect.nie.netease.com",
    "mgbsdkjp.matrix.easebar.com",
    "sdk-os.mpsdk.easebar.com",
    "mbdl.update.netease.com",
    "dns.update.netease.com",
    "dns.update.easebar.com",
    "whoami.nie.netease.com",
    "enabledns.com"
)

function Read-HostsLines {
    for ($i = 0; $i -lt 20; $i++) {
        try { return @([System.IO.File]::ReadAllLines($HostsPath)) }
        catch {
            if ($i -eq 19) { throw }
            Start-Sleep -Milliseconds 250
        }
    }
}

function Write-HostsLines([string[]]$lines) {
    for ($i = 0; $i -lt 20; $i++) {
        try {
            [System.IO.File]::WriteAllLines(
                $HostsPath,
                $lines,
                [System.Text.UTF8Encoding]::new($false)
            )
            return
        } catch {
            if ($i -eq 19) { throw }
            Start-Sleep -Milliseconds 250
        }
    }
}

$hostPattern = '(?i)(^|\s)(' + (($Hosts | ForEach-Object { [regex]::Escape($_) }) -join '|') + ')(\s|$)'
$existingLines = Read-HostsLines
$redirectLines = @($Hosts | ForEach-Object { "$ServerIp`t$_`t$Marker" })
$alreadyMatched = $true
foreach ($line in $redirectLines) {
    if ($existingLines -notcontains $line) {
        $alreadyMatched = $false
        break
    }
}
if ($alreadyMatched) {
    Write-Host "Hosts already redirected -> $ServerIp" -ForegroundColor Green
    return
}
$filteredLines = @($existingLines | Where-Object { $_ -notmatch $hostPattern })
Write-HostsLines @($filteredLines + $redirectLines)

foreach ($h in $Hosts) {
    Write-Host "added: $ServerIp $h"
}

ipconfig /flushdns | Out-Null
Write-Host "Hosts updated -> $ServerIp  (run remove_hosts.ps1 to undo)" -ForegroundColor Green
