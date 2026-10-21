#Requires -RunAsAdministrator
$ErrorActionPreference = 'Continue'
$ips = @(
    '42.186.235.118',
    '42.186.82.32',
    '103.72.16.24',
    '103.72.17.10',
    '52.76.137.125',
    '52.221.3.167',
    '49.44.79.236'
)
$ifName = 'Loopback Pseudo-Interface 1'
$existingIps = @(Get-NetIPAddress -ErrorAction SilentlyContinue | Select-Object -ExpandProperty IPAddress)
foreach ($ip in $ips) {
    if ($existingIps -contains $ip) {
        Write-Host "loopback already has $ip"
        continue
    }
    try {
        netsh interface ipv4 add address $ifName $ip 255.255.255.255 | Out-Null
        Write-Host "added loopback $ip"
    } catch {
        Write-Warning "failed to add $ip : $_"
    }
}
Write-Host 'done (remove with remove_loopback_ips.ps1)'
