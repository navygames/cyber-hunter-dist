#Requires -RunAsAdministrator
$ips = @(
    '42.186.235.118',
    '42.186.82.32',
    '103.72.16.24',
    '103.72.17.10',
    '52.76.137.125',
    '52.221.3.167'
)
$ifName = 'Loopback Pseudo-Interface 1'
foreach ($ip in $ips) {
    netsh interface ipv4 delete address $ifName $ip 2>$null | Out-Null
    Write-Host "removed $ip"
}
