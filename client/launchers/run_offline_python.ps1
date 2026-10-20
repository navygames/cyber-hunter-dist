#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Canonical Cyber Hunter offline launcher: Python services + Frida.

.DESCRIPTION
  Starts the local Python patch, HTTP, and gateway stubs, launches client.exe,
  then attaches client/frida/lobby_full.js. Invoked by the Navy Games Launcher;
  it is not a separate entry point.
#>
param(
    # 0 = stay attached until client.exe exits. A fixed 3600 s detached
    # Frida after an hour, which removed the outbound redirect hooks
    # mid-session (next connect went to a dead NetEase IP).
    [int]$AttachWait = 0,
    # Attach before the patch screen constructs its state. A delayed attach can
    # observe g_finished after UI creation, destroy that UI, and strand startup
    # before client2game is imported.
    [int]$AttachDelay = 0,
    [int]$LobbyTimeout = 240,
    # A client that dies during start-up (before the lobby) is relaunched
    # automatically this many times in total, so a crash does not mean
    # pressing Play again.
    [int]$MaxAttempts = 3,
    [int]$ArmedTimeout = 300,
    [string]$Profile = 'full_metadata',
    # Empty = read REVIVAL_SERVER_IP from revival_config.env. 127.0.0.1 (or
    # unset) is LOCAL mode: this script starts patch/http/gateway here.
    # Any other IP is REMOTE mode: those already run there, so only the
    # client-side half (hosts, CA, loopback, Frida) happens on this PC.
    [string]$ServerIp = '',
    # frida  = attach client/frida/lobby_full.js (default, unchanged).
    # native = no Frida: the client itself imports game/script/reawakening/*.nxs
    #          (built by tools\neox_script\build_native.py, copied below) from
    #          our common/logo_mgr override. docs/NATIVE_SCRIPTS.md.
    [ValidateSet('frida', 'native')]
    [string]$Boot = 'frida'
)

$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$PrivateServer = if (Test-Path (Join-Path $Repo 'Runtime\tools')) { Join-Path $Repo 'Runtime\tools' } else { Join-Path $Repo 'tools\private_server' }
$ClientFrida = if (Test-Path (Join-Path $Repo 'Runtime\frida')) { Join-Path $Repo 'Runtime\frida' } else { Join-Path $Repo 'client\frida' }
$Game = if (Test-Path (Join-Path $Repo 'Game')) { Join-Path $Repo 'Game' } else { Join-Path $Repo 'game' }
$Exe = Join-Path $Game 'bin\client.exe'
# game/ is usually a link to the real install (e.g. ..\Reawakening). Process
# paths can show either spelling, so match against both.
$GameRoots = New-Object System.Collections.Generic.List[string]
$GameRoots.Add(((Resolve-Path -LiteralPath $Game -ErrorAction SilentlyContinue).Path) -as [string])
try {
    $gi = Get-Item -LiteralPath $Game -ErrorAction Stop
    if ($gi.LinkType -and $gi.Target) {
        foreach ($t in @($gi.Target)) {
            $tp = if ([System.IO.Path]::IsPathRooted($t)) { $t } else { Join-Path (Split-Path $Game -Parent) $t }
            $GameRoots.Add(((Resolve-Path -LiteralPath $tp -ErrorAction SilentlyContinue).Path) -as [string])
        }
    }
} catch {}
$CrashDumps = $null
$Runtime = if (Test-Path (Join-Path $Repo 'Runtime\runtime')) { Join-Path $Repo 'Runtime\runtime' } else { Join-Path $Repo 'client\runtime' }
$Log = Join-Path $Runtime 'lobby_full.log'
$StatusPath = Join-Path $Runtime 'offline_lobby_status.json'
$AttachStatus = Join-Path $Runtime 'frida_attach_status.txt'
$Hook = Join-Path $ClientFrida 'lobby_full.js'
$Payload = Join-Path $ClientFrida 'lobby_full_payload.py'
$OfflineServer = Join-Path $ClientFrida 'lobby_offline_server.py'
$AccountDb = Join-Path $ClientFrida 'offline_account_db.py'
$AttachPy = Join-Path $ClientFrida 'run_frida_attach.py'
$RevivalConfig = if (Test-Path (Join-Path $Repo 'Config\revival_config.env')) { Join-Path $Repo 'Config\revival_config.env' } else { Join-Path $Repo 'revival_config.env' }
$RevivalConfigExample = Join-Path $Repo 'revival_config.env.example'
$NativeBuild = if (Test-Path (Join-Path $Repo 'Runtime\native\script')) { Join-Path $Repo 'Runtime\native\script' } else { Join-Path $Repo 'client\native\build\script' }
$NativeBootJson = Join-Path $Runtime 'native_boot.json'
$IsNative = ($Boot -eq 'native')
$Python = $null
$script:StepLog = New-Object System.Collections.Generic.List[string]
$script:StartedProcesses = New-Object System.Collections.Generic.List[object]
$script:ServicePids = @{}
$started = Get-Date

# A second elevated launch used to tear down the first launch during its Frida
# arm wait, then overwrite the shared status file with a misleading port error.
# Keep startup single-owner until the first launcher reaches READY (or fails).
$script:LaunchMutex = New-Object System.Threading.Mutex($false, 'Global\CyberHunterOfflineLauncher')
$script:LaunchMutexHeld = $false
try {
    $script:LaunchMutexHeld = $script:LaunchMutex.WaitOne(0, $false)
} catch [System.Threading.AbandonedMutexException] {
    $script:LaunchMutexHeld = $true
}
if (-not $script:LaunchMutexHeld) {
    Write-Host 'Cyber Hunter offline startup is already running; this duplicate launch was ignored.' -ForegroundColor Yellow
    exit 0
}

function Get-RevivalSetting([string]$key, [string]$fallback) {
    # revival_config.env is the single source of truth for the server target.
    # Fall back to the tracked example so a clone works before it is copied.
    foreach ($path in @($RevivalConfig, $RevivalConfigExample)) {
        if (-not (Test-Path -LiteralPath $path)) { continue }
        foreach ($line in [System.IO.File]::ReadAllLines($path)) {
            $trimmed = $line.Trim()
            if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
            $split = $trimmed.IndexOf('=')
            if ($split -lt 1) { continue }
            if ($trimmed.Substring(0, $split).Trim() -ne $key) { continue }
            $value = $trimmed.Substring($split + 1).Trim()
            if ($value) { return $value }
        }
    }
    return $fallback
}

function Info($message) { Write-Host "  $message" -ForegroundColor DarkGray }
function Ok($message) { Write-Host "  OK  $message" -ForegroundColor Green }
function Write-Status($obj) {
    New-Item -ItemType Directory -Path $Runtime -Force | Out-Null
    $json = $obj | ConvertTo-Json -Depth 6
    $tmp = Join-Path $Runtime ('.offline_lobby_status.{0}.{1}.tmp' -f $PID, [guid]::NewGuid().ToString('N'))
    try {
        [System.IO.File]::WriteAllText($tmp, $json, [System.Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $tmp -Destination $StatusPath -Force
    } finally {
        if (Test-Path -LiteralPath $tmp) {
            Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        }
    }
}
function Stop-StartedProcesses {
    # Windows PowerShell 5.1 can throw "Argument types do not match" when its
    # array-subexpression binder expands List[object]. Take an explicit snapshot
    # so failure cleanup cannot hide the original launcher error.
    foreach ($startedProcess in $script:StartedProcesses.ToArray()) {
        if ($startedProcess -and -not $startedProcess.HasExited) {
            Stop-Process -Id $startedProcess.Id -Force -ErrorAction SilentlyContinue
        }
    }
}
function Fail($message) {
    Stop-StartedProcesses
    Write-Status @{
        status = 'failed'
        error = "$message"
        started = $started.ToString('o')
        steps = $script:StepLog.ToArray()
        finished = (Get-Date).ToString('o')
    }
    throw "FAIL: $message"
}
function Step($number, $message) {
    Write-Host "`n=== STEP $number : $message ===" -ForegroundColor Cyan
    $script:StepLog.Add("$number $message")
    Write-Status @{
        status = "step_$number"
        step = "$message"
        started = $started.ToString('o')
        steps = $script:StepLog.ToArray()
        updated = (Get-Date).ToString('o')
    }
}
function Test-Port([int]$port) {
    try {
        $client = New-Object Net.Sockets.TcpClient
        $client.Connect('127.0.0.1', $port)
        $client.Close()
        return $true
    } catch {
        return $false
    }
}
function Wait-Port([int]$port, [int]$tries = 40) {
    for ($i = 0; $i -lt $tries; $i++) {
        if (Test-Port $port) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}
function Get-OurClients {
    # Only OUR client.exe. Other software also ships a "client.exe"; the old
    # name-only match killed it in Step 2 and refused to Play in Step 4.
    $all = @(Get-CimInstance Win32_Process -Filter "Name='client.exe'" -ErrorAction SilentlyContinue)
    return @($all | Where-Object {
        $p = [string]$_.ExecutablePath
        if (-not $p) { return $true }   # elevated/protected: cannot tell, assume ours
        foreach ($r in $GameRoots) {
            if ($r -and $p.StartsWith($r, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
        }
        return $false
    })
}
function Test-RemotePort([string]$hostName, [int]$port, [int]$timeoutMs = 1500) {
    $client = New-Object Net.Sockets.TcpClient
    try {
        $iar = $client.BeginConnect($hostName, $port, $null, $null)
        if (-not $iar.AsyncWaitHandle.WaitOne($timeoutMs, $false)) { return $false }
        $client.EndConnect($iar)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}
function Enable-CrashDumps {
    # Native crashes that bypass UnhandledExceptionFilter (fast-fail, abort
    # from Py_FatalError) leave nothing in exit_trace.log. Windows Error
    # Reporting can still write a minidump; turn that on for client.exe only.
    try {
        $script:CrashDumps = Join-Path $Runtime 'crashdumps'
        New-Item -ItemType Directory -Path $script:CrashDumps -Force | Out-Null
        $key = 'HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps\client.exe'
        New-Item -Path $key -Force | Out-Null
        New-ItemProperty -Path $key -Name DumpFolder -PropertyType ExpandString -Value $script:CrashDumps -Force | Out-Null
        New-ItemProperty -Path $key -Name DumpType -PropertyType DWord -Value 1 -Force | Out-Null
        New-ItemProperty -Path $key -Name DumpCount -PropertyType DWord -Value 5 -Force | Out-Null
    } catch {
        Info "crash dumps not enabled: $($_.Exception.Message)"
    }
}
function Get-ExitDetail($proc) {
    $code = $null
    try { $proc.WaitForExit(2000) | Out-Null; $code = $proc.ExitCode } catch {}
    Start-Sleep -Milliseconds 1500   # let Frida print its detach/crash reason
    $parts = @()
    if ($null -ne $code -and "$code" -ne '') {
        $hex = '0x{0:X8}' -f [BitConverter]::ToUInt32([BitConverter]::GetBytes([int32]$code), 0)
        $known = @{
            '0xC0000005' = 'access violation (native crash)'
            '0xC0000409' = 'fast-fail / stack buffer overrun (native abort, usually Py_FatalError)'
            '0xC00000FD' = 'stack overflow'
            '0xC0000374' = 'heap corruption'
            '0x00000003' = 'abort()'
            '0x00000001' = 'TerminateProcess(1) after an unhandled exception'
            '0x00000000' = 'clean exit (game3d.exit / user closed the window)'
            '0xFFFFFFFF' = 'killed'
        }
        $why = $known[$hex]
        $parts += $(if ($why) { "exit code $hex - $why" } else { "exit code $hex" })
    } else {
        $parts += 'exit code unavailable'
    }
    $attachLog = Join-Path $Runtime 'frida_attach.out.log'
    $detach = @(Get-Content -LiteralPath $attachLog -ErrorAction SilentlyContinue | Where-Object { $_ -match 'DETACHED|crash' } | Select-Object -Last 2)
    if ($detach.Count) { $parts += ($detach -join ' / ') }
    $tail = @(Get-LogTail | Select-Object -Last 3)
    if ($tail.Count) { $parts += ('last log: ' + ($tail -join ' | ')) }
    if ($script:CrashDumps) {
        $dump = Get-ChildItem -LiteralPath $script:CrashDumps -Filter 'client.exe*.dmp' -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($dump -and $dump.LastWriteTime -gt $started) { $parts += "crash dump: $($dump.FullName)" }
    }
    return ($parts -join ' ; ')
}
function Reset-ForRetry {
    # Tear down this attempt (Frida attach + dead client) without touching the
    # http stub / services, clear the per-run gates, and relaunch.
    foreach ($p in $script:StartedProcesses.ToArray()) {
        if ($p -and ($p.Id -eq $clientProc.Id -or ($fridaProc -and $p.Id -eq $fridaProc.Id))) {
            if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
            [void]$script:StartedProcesses.Remove($p)
        }
    }
    foreach ($c in (Get-OurClients)) { Stop-Process -Id $c.ProcessId -Force -ErrorAction SilentlyContinue }
    foreach ($f in @('lf_stable.flag', 'lf_selfexec.flag')) {
        Remove-Item -LiteralPath (Join-Path $Runtime $f) -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}
function Get-LogTail {
    if (-not (Test-Path -LiteralPath $Log)) { return @() }
    return @(Get-Content -LiteralPath $Log -ErrorAction SilentlyContinue)
}
function Stop-KnownPythonProcesses {
    $privatePattern = [regex]::Escape($PrivateServer)
    $attachPattern = [regex]::Escape($AttachPy)
    Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.CommandLine -and ($_.CommandLine -match $privatePattern -or $_.CommandLine -match $attachPattern)
        } |
        ForEach-Object {
            Info "stopping prior Python offline process pid=$($_.ProcessId)"
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
}
function Stop-PortOwner([int]$port) {
    try {
        $lines = @(netstat -ano | Select-String "^\s*TCP\s+\S+:$port\s+\S+\s+LISTENING\s+(\d+)")
        foreach ($m in $lines) {
            if ($m.Matches.Count -gt 0 -and $m.Matches[0].Groups.Count -gt 1) {
                $pid_ = $m.Matches[0].Groups[1].Value
                if ($pid_ -and $pid_ -ne '0') {
                    Info "evicting PID $pid_ from port $port"
                    try {
                        Stop-Process -Id ([int]$pid_) -Force -ErrorAction SilentlyContinue
                    } catch {}
                    try {
                        Start-Process -FilePath 'taskkill.exe' -ArgumentList @('/PID', $pid_, '/F') -WindowStyle Hidden -Wait -ErrorAction SilentlyContinue
                    } catch {}
                }
            }
        }
    } catch {}
}
function Format-CliArg([string]$arg) {
    if ($arg -match '[\s"]') {
        $escaped = $arg.Trim('"') -replace '"', '\"'
        $escaped = $escaped -replace '(\\+)$', '$1$1'
        return '"{0}"' -f $escaped
    }
    return $arg
}
function Start-PythonService([string]$name, [string]$script, [string[]]$arguments, [int]$port) {
    if (Test-Port $port) {
        Fail "port $port is already in use; stop the unrelated listener and retry"
    }
    $stdout = Join-Path $Runtime ("$name.out.log")
    $stderr = Join-Path $Runtime ("$name.err.log")
    [System.IO.File]::WriteAllText($stdout, '', [System.Text.UTF8Encoding]::new($false))
    [System.IO.File]::WriteAllText($stderr, '', [System.Text.UTF8Encoding]::new($false))
    $rawArgs = @('-u', $script) + $arguments
    $argList = @($rawArgs | ForEach-Object { Format-CliArg $_ })
    $proc = Start-Process -FilePath $Python -ArgumentList $argList `
        -WorkingDirectory $PrivateServer -PassThru -WindowStyle Hidden `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if (-not $proc) { Fail "failed to start $name" }
    $script:StartedProcesses.Add($proc)
    $script:ServicePids[$name] = $proc.Id
    if (-not (Wait-Port $port 40)) {
        $detail = (Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue).Trim()
        Fail "$name did not open port $port. $detail"
    }
    Ok "$name pid=$($proc.Id) port=$port"
}

New-Item -ItemType Directory -Path $Runtime -Force | Out-Null
# Drop prior-session Frida gates so a new Play always cold-injects the payload.
# (lf_stable.flag left behind = peek/import skip the 17k payload → arm timeout.)
foreach ($staleFlag in @('lf_stable.flag', 'lf_selfexec.flag', 'dump_image.flag', 'navy_auto_play.flag')) {
    $fp = Join-Path $Runtime $staleFlag
    if (Test-Path -LiteralPath $fp) {
        Remove-Item -LiteralPath $fp -Force -ErrorAction SilentlyContinue
    }
}
Write-Status @{ status = 'starting'; started = $started.ToString('o'); steps = @() }

Step 0 'Preflight the single Python/Frida stack'
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) { Fail 'python was not found on PATH' }
$Python = $pythonCommand.Source

if (-not $ServerIp) { $ServerIp = Get-RevivalSetting 'REVIVAL_SERVER_IP' '127.0.0.1' }
$PatchPort = Get-RevivalSetting 'REVIVAL_PATCH_PORT' '443'
$GatewayPort = Get-RevivalSetting 'REVIVAL_GATEWAY_PORT' '10001'
$RefereePort = Get-RevivalSetting 'REVIVAL_REFEREE_PORT' '10777'
$IsRemote = ($ServerIp -ne '127.0.0.1' -and $ServerIp -ne 'localhost' -and $ServerIp -ne '')

$requiredPaths = if ($IsNative) {
    @($Exe, (Join-Path $NativeBuild 'reawakening\pack.nxs'), (Join-Path $NativeBuild 'common\logo_mgr.nxs'), (Join-Path $PrivateServer 'http_stub.py'))
} else {
    @($Exe, $Hook, $Payload, $OfflineServer, $AccountDb, $AttachPy, (Join-Path $PrivateServer 'http_stub.py'))
}
if (-not $IsRemote) {
    $requiredPaths += @(
        (Join-Path $PrivateServer 'patch_server.py'),
        (Join-Path $PrivateServer 'gateway_stub.py')
    )
}
foreach ($path in $requiredPaths) {
    if (-not (Test-Path -LiteralPath $path)) { Fail "missing required path: $path" }
}
if ($IsNative) {
    & $Python -c "import cryptography"
    if ($LASTEXITCODE -ne 0) { Fail 'Python package cryptography is required' }
} else {
    & $Python -c "import cryptography, frida"
    if ($LASTEXITCODE -ne 0) { Fail 'Python packages cryptography and frida are required' }
}
$profilePath = Join-Path $PrivateServer ("responses\$Profile.json")
if (-not $IsRemote -and -not (Test-Path -LiteralPath $profilePath)) { Fail "unknown patch profile: $Profile" }
Ok "python=$Python"
Ok 'canonical brain and Python services present'

# game/ is not in git, so every machine supplies its own ~11 GB of NPKs and a
# bad one is invisible to the repo. A script/data overlay under
# game/Documents/ replaces the client's own tables and black-screens the boot
# inside game_init.start_game() -- see tools/verify_game_files.py for the
# traceback. Repair it here rather than letting Play fail 240s later.
$verifyScript = Join-Path $Repo 'tools\verify_game_files.py'
if (Test-Path -LiteralPath $verifyScript) {
    & $Python $verifyScript
    if ($LASTEXITCODE -ne 0) { Fail 'verify_game_files.py failed' }
    Ok 'game script/data files checked'
}

# Same reason: game/ cannot travel in git, so nothing has ever verified that
# two developers are running the same client. client_manifest.json pins the
# identity of the reference build (entry-table hashes, ~0.5s to check).
# Missing content is reported and allowed; a base pack that disagrees is not,
# because that is the documented black screen and failing here beats timing
# out 240s later with no explanation.
$manifestScript = Join-Path $Repo 'tools\client_manifest.py'
if (Test-Path -LiteralPath $manifestScript) {
    & $Python $manifestScript
    if ($LASTEXITCODE -ne 0) {
        Fail 'game/ base packs do not match client_manifest.json - see docs\FRESH_CLONE_BOOT.md'
    }
    Ok 'client matches the reference manifest'
}

# Our compiled scripts (client/native/build/script) go into game/script/, a
# `script` root the engine searches before its own packs. Done in BOTH boot
# modes: in Frida mode reawakening.boot.start() reads native_boot.json and
# returns at once. Loose .py overrides of the same modules are set aside so
# exactly one copy can load.
if (Test-Path -LiteralPath $NativeBuild) {
    $scriptRoot = Join-Path $Game 'script'
    $copied = 0
    foreach ($f in @(Get-ChildItem -LiteralPath $NativeBuild -Recurse -File -Filter '*.nxs')) {
        $rel = $f.FullName.Substring($NativeBuild.Length).TrimStart('\')
        $dst = Join-Path $scriptRoot $rel
        $same = $false
        if (Test-Path -LiteralPath $dst) {
            $same = ((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash -eq (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash)
        }
        if (-not $same) {
            New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
            Copy-Item -LiteralPath $f.FullName -Destination $dst -Force
            $copied += 1
        }
        $py = [System.IO.Path]::ChangeExtension($dst, '.py')
        if (Test-Path -LiteralPath $py) {
            Move-Item -LiteralPath $py -Destination ($py + '.disabled_by_launcher') -Force
            Info "set aside $py (compiled copy installed)"
        }
    }
    # Phase 0 leftovers (2026-10-19): probe + a logo_mgr that shadows ours.
    foreach ($stale in @(
            (Join-Path $Game 'script\common\rw_probe.nxs'),
            (Join-Path $Game 'Documents\script\common\rw_probe.nxs'),
            (Join-Path $Game 'Documents\script\common\logo_mgr.nxs'))) {
        if (Test-Path -LiteralPath $stale) {
            Remove-Item -LiteralPath $stale -Force -ErrorAction SilentlyContinue
            Info "removed $stale"
        }
    }
    Ok "native scripts installed ($copied updated) - boot mode: $Boot"
} elseif ($IsNative) {
    Fail "native boot needs $NativeBuild - run tools\neox_script\build_native.py"
}

if ($IsRemote) {
    Ok "REMOTE mode - servers at $ServerIp (patch $PatchPort, gateway $GatewayPort, referee $RefereePort)"
    # Online-only: the lobby goes through the VPS. If none of its ports answer,
    # stop here instead of booting an offline lobby. The Launcher already
    # refuses Play in this case; this is the backstop for any other caller.
    $down = @()
    $probePorts = @([int]$PatchPort, [int]$GatewayPort, [int]$RefereePort)
    foreach ($pp in $probePorts) {
        if (-not (Test-RemotePort $ServerIp $pp)) { $down += $pp }
    }
    # Same port set the Launcher's gate uses, so the two never disagree.
    $anyUp = ($down.Count -lt $probePorts.Count)
    if (-not $anyUp) {
        foreach ($pp in @([int](Get-RevivalSetting 'REVIVAL_CONTROL_PANEL_PORT' '8888'), [int](Get-RevivalSetting 'REVIVAL_GAMEAPI_PORT' '3000'))) {
            if (Test-RemotePort $ServerIp $pp) { $anyUp = $true; break }
        }
    }
    if (-not $anyUp) {
        Fail "Can't connect. Please connect to the internet. (server $ServerIp not answering on $($down -join ', '))"
    }
    if ($down.Count) {
        Write-Host "  WARN  server $ServerIp not answering on port(s) $($down -join ', ') - online features will be unavailable (is the VPS up / firewall open?)" -ForegroundColor Yellow
        $script:RemoteDown = ($down -join ',')
    } else {
        Ok "server $ServerIp reachable"
    }
} else {
    Ok 'LOCAL mode - starting patch, http, gateway and referee on this PC'
}

Step 1 'Prepare local certificates and host redirects'
if ($IsRemote) {
    # The server generated its cert with its own IP in the SAN; regenerating
    # here would produce a different CA than the one the server presents.
    if (-not (Test-Path -LiteralPath (Join-Path $PrivateServer 'certs\ca.cert.pem'))) {
        Fail "remote mode needs the server's CA at tools\private_server\certs\ca.cert.pem - copy it from the server (it prints the path) and retry"
    }
    Info 'using the server CA already present (not regenerating)'
} else {
    $genCertPy = Join-Path $PrivateServer 'generate_certs.py'
    if (Test-Path -LiteralPath $genCertPy) {
        & $Python $genCertPy
        if ($LASTEXITCODE -ne 0) { Fail 'generate_certs.py failed' }
    }
}
& (Join-Path $PrivateServer 'setup_hosts.ps1') -ServerIp $ServerIp
& (Join-Path $PrivateServer 'setup_loopback_ips.ps1')
& (Join-Path $PrivateServer 'trust_ca.ps1')
& $Python (Join-Path $PrivateServer 'inject_game_ca.py')
if ($LASTEXITCODE -ne 0) { Fail 'inject_game_ca.py failed' }
Ok 'local CA, hosts, loopback, and game CA prepared'

Step 2 'Stop prior local Python/Frida processes'
# Remote mode only binds :80 here, so leave whatever owns 443/10001 alone
# (IIS, VPN clients, Docker...). Local mode needs all of them.
Stop-KnownPythonProcesses
if (Test-Port 80) { Stop-PortOwner 80 }
if (-not $IsRemote) {
    if (Test-Port ([int]$PatchPort)) { Stop-PortOwner ([int]$PatchPort) }
    if (Test-Port ([int]$GatewayPort)) { Stop-PortOwner ([int]$GatewayPort) }
    if (Test-Port ([int]$RefereePort)) { Stop-PortOwner ([int]$RefereePort) }
}
$killedPrior = $false
foreach ($c in (Get-OurClients)) {
    Info "stopping prior client pid=$($c.ProcessId)"
    Stop-Process -Id $c.ProcessId -Force -ErrorAction SilentlyContinue
    $killedPrior = $true
}
if ($killedPrior) { Start-Sleep -Milliseconds 1500 }
Ok 'clean Python/Frida launch state'

if ($IsRemote) {
    Step 3 'Skip local servers (remote mode) and serve only raw-IP telemetry'
    # setup_loopback_ips.ps1 pins dead NetEase LVS/CDN addresses onto loopback
    # because the client dials them by raw IP, which the hosts file cannot
    # redirect. Those dials must still be answered locally or the client sits
    # in SynSent for minutes on a cold start. This is client-side plumbing for
    # dead hosts, not the game server - all real traffic goes to $ServerIp.
    # ponytail: reuses http_stub as the sink; a dedicated one would earn nothing.
    Start-PythonService 'http_stub' (Join-Path $PrivateServer 'http_stub.py') @('--host', '127.0.0.1', '--port', '80', '-v') 80
    Info "patch and gateway are remote at $ServerIp - not started here"
} else {
    Step 3 'Start Python patch, HTTP, and gateway services'
    Start-PythonService 'patch_server' (Join-Path $PrivateServer 'patch_server.py') @('--profile', $Profile, '--port', $PatchPort, '--sig-line', 'local', '-v') ([int]$PatchPort)
    Start-PythonService 'http_stub' (Join-Path $PrivateServer 'http_stub.py') @('--port', '80', '-v') 80
    Start-PythonService 'gateway_stub' (Join-Path $PrivateServer 'gateway_stub.py') @('--port', $GatewayPort) ([int]$GatewayPort)
    Start-PythonService 'referee_server' (Join-Path $PrivateServer 'referee_server.py') @('--port', $RefereePort) ([int]$RefereePort)
}

$attempt = 0
$lastCrash = ''
:launch while ($true) {
$attempt += 1
$fridaProc = $null
if ($attempt -gt 1) {
    Write-Host "`n  RETRY $attempt/$MaxAttempts after: $lastCrash" -ForegroundColor Yellow
    Write-Status @{
        status = 'retrying'
        step = "relaunching client (attempt $attempt of $MaxAttempts)"
        last_crash = $lastCrash
        started = $started.ToString('o')
        steps = $script:StepLog.ToArray()
        updated = (Get-Date).ToString('o')
    }
}
Step 4 'Launch client.exe from game working directory'
# init._check_multi_instances(1) calls game3d.single_run('lz0'); the second
# client to start loses it, shows the multi-open warning and calls game3d.exit
# -- and the FIRST one is taken down with it. A double Play therefore reads as
# "the game closes by itself" with a clean log and no crash dump. Never make
# that condition: if a client is already up, this launch has nothing to do.
$existing = @(Get-OurClients)
if ($existing.Count -gt 0) {
    Fail ("client.exe already running (pid $($existing[0].ProcessId)); " +
          'close it before starting Play again')
}
[System.IO.File]::WriteAllText($Log, '', [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($AttachStatus, '', [System.Text.UTF8Encoding]::new($false))
# Read by reawakening.boot inside the client: only "native" makes it run the
# offline brain; "frida" leaves that to lobby_full.js. Rewritten every attempt.
$nativeCfg = [ordered]@{
    mode = $Boot
    run_id = [guid]::NewGuid().ToString('N')
    root = $Repo
    runtime = $Runtime
    server_ip = $ServerIp
    remote = [bool]$IsRemote
    written = (Get-Date).ToString('o')
    launcher_auth = $true
    boot_ticket = [guid]::NewGuid().ToString('N')
}
[System.IO.File]::WriteAllText($NativeBootJson, ($nativeCfg | ConvertTo-Json), [System.Text.UTF8Encoding]::new($false))
Enable-CrashDumps
# Keep the Process object Start-Process hands back. The old code re-found the
# client with Get-Process; that object holds no handle from creation, so its
# ExitCode was always empty ("client exited during lobby wait: ") and it could
# pick an unrelated client.exe.
$clientProc = $null
try {
    $clientProc = Start-Process -FilePath $Exe -WorkingDirectory $Game -PassThru
    $null = $clientProc.Handle   # open the handle now so ExitCode survives exit
} catch {
    Fail "client.exe failed to start: $($_.Exception.Message)"
}
if (-not $clientProc) { Fail 'client.exe failed to start' }
$script:StartedProcesses.Add($clientProc)
Ok "client pid=$($clientProc.Id)"

if ($IsNative) {
Step 5 'Native boot - no Frida (client loads reawakening.boot itself)'
} else {
Step 5 "Wait ${AttachDelay}s and attach lobby_full.js"
Start-Sleep -Seconds $AttachDelay
if (-not (Get-Process -Id $clientProc.Id -ErrorAction SilentlyContinue)) {
    $why = "client pid $($clientProc.Id) exited before Frida attach"
    if ($attempt -lt $MaxAttempts) { $lastCrash = $why; Reset-ForRetry; continue launch }
    Fail $why
}
# Optional sanity probe. A player build that left it out used to Fail here
# ("Frida cannot see client") and kill client.exe on every Play.
$probePy = Join-Path $ClientFrida 'frida_see_probe.py'
if (Test-Path -LiteralPath $probePy) {
    $seen = & $Python -u $probePy $clientProc.Id 2>&1
    if ($LASTEXITCODE -ne 0) {
        Fail "Frida cannot see client pid $($clientProc.Id): $(@($seen) -join ' ')"
    }
}
$fridaOut = Join-Path $Runtime 'frida_attach.out.log'
$fridaErr = Join-Path $Runtime 'frida_attach.err.log'
[System.IO.File]::WriteAllText($fridaOut, '', [System.Text.UTF8Encoding]::new($false))
$rawFridaArgs = @('-u', $AttachPy, '--pid', "$($clientProc.Id)", "$AttachWait", $Hook)
$fridaArgs = @($rawFridaArgs | ForEach-Object { Format-CliArg $_ })
$fridaProc = Start-Process -FilePath $Python `
    -ArgumentList $fridaArgs `
    -WorkingDirectory $Repo -PassThru -WindowStyle Hidden `
    -RedirectStandardOutput $fridaOut -RedirectStandardError $fridaErr
if (-not $fridaProc) { Fail 'failed to start Frida attach process' }
$script:StartedProcesses.Add($fridaProc)
Ok "Frida attach pid=$($fridaProc.Id)"
}

Step 6 "Wait for canonical payload arm (max ${ArmedTimeout}s)"
$armed = $false
$armedDeadline = (Get-Date).AddSeconds($ArmedTimeout)
while ((Get-Date) -lt $armedDeadline) {
    $joined = ((Get-LogTail) -join "`n")
    if ($joined -match 'armed lobby_full') { $armed = $true; break }
    if (-not $IsNative) {
        $attachText = Get-Content -LiteralPath $AttachStatus -Raw -ErrorAction SilentlyContinue
        if ($attachText -match 'failed|not running') { Fail "Frida attach failed: $($attachText.Trim())" }
    }
    if ($clientProc.HasExited) {
        $why = "client exited during payload arm wait: $(Get-ExitDetail $clientProc)"
        if ($attempt -lt $MaxAttempts) { $lastCrash = $why; Reset-ForRetry; continue launch }
        Fail ("$why (after $attempt attempts)")
    }
    Start-Sleep -Milliseconds 500
}
if (-not $armed) {
    $tail = (Get-LogTail | Select-Object -Last 20) -join ' | '
    Fail "payload did not arm within ${ArmedTimeout}s: $tail"
}
Ok $(if ($IsNative) { 'native boot armed (no Frida)' } else { 'client/frida/lobby_full.js armed' })

Step 7 "Wait for lobby ready (max ${LobbyTimeout}s)"
$ready = $false
$deadline = (Get-Date).AddSeconds($LobbyTimeout)
while ((Get-Date) -lt $deadline) {
    $joined = ((Get-LogTail) -join "`n")
    $ready = ($joined -match 'lobby ready' -or
        ($joined -match 'IN_GAME OK' -and $joined -match 'scene_enter id=101 active=True') -or
        $joined -match 'LOBBY_RETURN ok' -or
        $joined -match 'MAIN MENU ready')
    if ($ready) { break }
    if ($clientProc.HasExited) {
        $why = "client exited during lobby wait: $(Get-ExitDetail $clientProc)"
        if ($attempt -lt $MaxAttempts) { $lastCrash = $why; Reset-ForRetry; continue launch }
        Fail ("$why (after $attempt attempts)")
    }
    Start-Sleep -Milliseconds 500
}
if (-not $ready) {
    # The client is alive; we simply did not see a lobby marker in the log.
    # The old code called Fail here, which KILLED a running game. Leave it up.
    $tail = (Get-LogTail | Select-Object -Last 10) -join ' | '
    Write-Host "  WARN  no lobby marker within ${LobbyTimeout}s; client is still running, leaving it up" -ForegroundColor Yellow
    Write-Status @{
        status = 'running'
        warning = "lobby marker not seen within ${LobbyTimeout}s: $tail"
        mode = $(if ($IsRemote) { 'remote' } else { 'local' })
        server_ip = $ServerIp
        client_pid = $clientProc.Id
        frida_pid = $fridaProc.Id
        started = $started.ToString('o')
        updated = (Get-Date).ToString('o')
        steps = $script:StepLog.ToArray()
    }
    exit 0
}
break launch
}  # end :launch

Write-Status @{
    status = 'lobby_ready'
    boot = $Boot
    mode = $(if ($IsRemote) { 'remote' } else { 'local' })
    server_ip = $ServerIp
    server_lobby_ready = $true
    server_unreachable_ports = $script:RemoteDown
    client_pid = $clientProc.Id
    frida_pid = $fridaProc.Id
    service_pids = $script:ServicePids
    armed = $armed
    ready = $ready
    started = $started.ToString('o')
    ready_at = (Get-Date).ToString('o')
    finished = (Get-Date).ToString('o')
    steps = $script:StepLog.ToArray()
}

Ok 'LOBBY READY - Python + Frida only'
Write-Host "  Log: $Log" -ForegroundColor Green
Write-Host "  Commands: .\client\frida\cmd.ps1 stuck | unstick | fixctrl" -ForegroundColor Cyan
Write-Host "  Cleanup: tools\private_server\remove_hosts.ps1 and untrust_ca.ps1" -ForegroundColor DarkGray
