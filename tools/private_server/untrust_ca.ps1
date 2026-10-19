#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$CaPath = Join-Path $Root "certs\ca.cert.pem"
if (-not (Test-Path -LiteralPath $CaPath)) {
    Write-Host "no CA at $CaPath"
    exit 0
}
$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($CaPath)
foreach ($StoreName in @("CurrentUser", "LocalMachine")) {
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", $StoreName)
    $store.Open("ReadWrite")
    try {
        $removed = $store.Certificates.Find(
            [System.Security.Cryptography.X509Certificates.X509FindType]::FindByThumbprint,
            $cert.Thumbprint,
            $false
        )
        foreach ($c in $removed) {
            $store.Remove($c)
            Write-Host "removed CA from $StoreName Root"
        }
    } finally {
        $store.Close()
    }
}
