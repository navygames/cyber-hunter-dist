#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$CaPath = Join-Path $Root "certs\ca.cert.pem"
if (-not (Test-Path -LiteralPath $CaPath)) {
    throw "CA not found at $CaPath - run generate_certs.py first"
}

function Import-ToStore($StoreName) {
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", $StoreName)
    $store.Open("ReadWrite")
    try {
        $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($CaPath)
        $existing = $store.Certificates | Where-Object { $_.Thumbprint -eq $cert.Thumbprint }
        if ($existing) {
            Write-Host "CA already trusted in $StoreName Root"
            return
        }
        $store.Add($cert)
        Write-Host "imported CA into $StoreName Root (thumbprint $($cert.Thumbprint))"
    } finally {
        $store.Close()
    }
}

Import-ToStore "CurrentUser"
Import-ToStore "LocalMachine"
Write-Host "done - Python urllib3 should accept the mock patch server cert chain"
