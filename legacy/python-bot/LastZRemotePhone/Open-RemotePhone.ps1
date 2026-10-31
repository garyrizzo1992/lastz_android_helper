[CmdletBinding()]
param(
    [string]$MacHost = '192.168.1.10',
    [string]$MacUser = 'garyrizzo',
    [string]$IdentityFile = "$env:USERPROFILE\.ssh\id_ed25519",
    [ValidatePattern('^[a-zA-Z0-9._:-]+$')][string]$Device = 'f7c5e6fe',
    [string]$ScrcpyPath = 'C:\Users\Gary\Desktop\scrcpy-win64-v3.3.4\scrcpy.exe',
    [ValidateRange(1024,65535)][int]$AdbPort = 5038,
    [ValidateRange(1024,65535)][int]$VideoPort = 27183,
    [switch]$CheckOnly,
    [ValidateRange(0,86400)][int]$TestSessionSeconds = 0
)

$ErrorActionPreference = 'Stop'
$remote = "${MacUser}@${MacHost}"
$ssh = (Get-Command ssh.exe -ErrorAction Stop).Source
$scp = (Get-Command scp.exe -ErrorAction Stop).Source
$adb = Join-Path (Split-Path $ScrcpyPath) 'adb.exe'
$sshArgs = @('-i', $IdentityFile, '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8',
             '-o', 'StrictHostKeyChecking=accept-new', '-o', 'ServerAliveInterval=5',
             '-o', 'ServerAliveCountMax=3')
$lease = $null
$viewer = $null
$oldSocket = $env:ADB_SERVER_SOCKET
$oldAdb = $env:ADB
$oldAdbPort = $env:ANDROID_ADB_SERVER_PORT
$mutex = $null
$ownsMutex = $false
$remoteHelper = '.local/share/lastz-remote-phone/mac_lease.py'

function Quote-ProcessArgument([string]$Value) {
    # Windows CreateProcess escaping; preserves spaces, quotes and trailing backslashes.
    return '"' + [regex]::Replace([regex]::Replace($Value, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1') + '"'
}

function Start-CapturedProcess([string]$File, [string[]]$Arguments) {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $File
    $info.Arguments = (($Arguments | ForEach-Object { Quote-ProcessArgument $_ }) -join ' ')
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $info
    [void]$proc.Start()
    return $proc
}

try {
    foreach ($file in @($IdentityFile, $ScrcpyPath, $adb, (Join-Path $PSScriptRoot 'mac_lease.py'))) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Required file not found: $file" }
    }
    if ($MacUser -notmatch '^[a-zA-Z0-9._-]+$' -or $MacHost -notmatch '^[a-zA-Z0-9.-]+$') {
        throw 'Invalid SSH host or username.'
    }
    $mutex = New-Object System.Threading.Mutex($false, 'Local\LastZRemotePhone')
    try { $ownsMutex = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $ownsMutex = $true }
    if (-not $ownsMutex) { throw 'A remote-phone launcher is already running.' }
    Write-Host "Checking phone on $remote..."
    & $ssh @sshArgs $remote '/opt/homebrew/bin/adb start-server && /opt/homebrew/bin/adb devices'
    if ($LASTEXITCODE -ne 0) { throw 'Mac SSH/ADB preflight failed.' }
    $state = & $ssh @sshArgs $remote "/opt/homebrew/bin/adb -s $Device get-state"
    if ($LASTEXITCODE -ne 0 -or "$state".Trim() -ne 'device') { throw 'The selected phone is not ready on the Mac.' }
    if ($CheckOnly) {
        Write-Host 'Preflight passed. Bot was not paused.' -ForegroundColor Green
        return
    }
    if ($AdbPort -eq $VideoPort) { throw 'ADB and video tunnel ports must differ.' }
    foreach ($port in @($AdbPort, $VideoPort)) {
        $listener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $port)
        try { $listener.Start() } catch { throw "Local port $port is already in use." } finally { $listener.Stop() }
    }
    & $ssh @sshArgs $remote 'mkdir -p .local/share/lastz-remote-phone'
    if ($LASTEXITCODE -ne 0) { throw 'Could not prepare Mac session directory.' }
    & $scp @sshArgs (Join-Path $PSScriptRoot 'mac_lease.py') "${remote}:$remoteHelper"
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the remote watchdog.' }

    Write-Host 'Pausing Mac bot and opening secure tunnels...'
    $tunnelArgs = $sshArgs + @('-T', '-o', 'ExitOnForwardFailure=yes',
        '-L', "127.0.0.1:${AdbPort}:127.0.0.1:5037",
        '-L', "127.0.0.1:${VideoPort}:127.0.0.1:${VideoPort}",
        $remote, "/usr/bin/python3 -u $remoteHelper")
    $lease = Start-CapturedProcess $ssh $tunnelArgs
    $leaseErrors = $lease.StandardError.ReadToEndAsync()
    $ready = $lease.StandardOutput.ReadLineAsync()
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    while (-not $ready.IsCompleted -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 100 }
    if (-not $ready.IsCompleted) { throw 'Timed out waiting for the Mac to pause the bot.' }
    $readyLine = $ready.Result
    if ($readyLine -notlike 'READY *') { throw "Mac session failed: $readyLine $($leaseErrors.Result)" }
    Write-Host $readyLine -ForegroundColor Yellow

    $env:ADB_SERVER_SOCKET = "tcp:127.0.0.1:$AdbPort"
    $env:ANDROID_ADB_SERVER_PORT = "$AdbPort"
    $env:ADB = $adb
    & $adb -s $Device get-state
    if ($LASTEXITCODE -ne 0) { throw 'The phone could not be reached through the SSH tunnel.' }

    Write-Host 'Close the phone window to resume the bot. Closing this console also triggers recovery.'
    $viewerArgs = @('--serial', $Device, '--force-adb-forward', '--port', "$VideoPort",
                    '--tunnel-host', '127.0.0.1', '--tunnel-port', "$VideoPort",
                    '--max-size', '1600', '--max-fps', '30', '--no-audio',
                    '--window-title', 'LastZ phone on Mac - close to resume bot')
    # Do not capture scrcpy pipes: its long-lived adb shell child can inherit
    # those handles and prevent ReadToEnd/WaitForExit from finishing on close.
    $viewerCommandLine = (($viewerArgs | ForEach-Object { Quote-ProcessArgument $_ }) -join ' ')
    $viewer = Start-Process -FilePath $ScrcpyPath -ArgumentList $viewerCommandLine -NoNewWindow -PassThru
    $sessionStarted = [DateTime]::UtcNow
    while (-not $viewer.HasExited) {
        if ($lease.HasExited) { throw 'Mac watchdog connection closed unexpectedly.' }
        $lease.StandardInput.WriteLine('PING')
        $lease.StandardInput.Flush()
        if ($TestSessionSeconds -gt 0 -and ([DateTime]::UtcNow - $sessionStarted).TotalSeconds -ge $TestSessionSeconds) {
            $viewer.Kill()
            break
        }
        Start-Sleep -Seconds 1
    }
    $viewer.WaitForExit()
    if ($viewer.ExitCode -ne 0 -and $TestSessionSeconds -eq 0) { throw "scrcpy exited with code $($viewer.ExitCode)." }
}
finally {
    if ($viewer -and -not $viewer.HasExited) { $viewer.Kill(); $viewer.WaitForExit() }
    if ($lease) {
        Write-Host 'Restoring Mac bot service...'
        if (-not $lease.HasExited) {
            try { $lease.StandardInput.WriteLine('QUIT'); $lease.StandardInput.Close() } catch { }
            if (-not $lease.WaitForExit(20000)) { $lease.Kill(); $lease.WaitForExit() }
        }
        $remaining = $lease.StandardOutput.ReadToEnd()
        Write-Host $remaining
        if ($remaining -notmatch 'RESTORED ') {
            Write-Warning 'Resume was not acknowledged. The Mac watchdog restores the bot after 30 seconds without heartbeats; verify the service if SSH is unavailable.'
        }
        if ($leaseErrors.IsCompleted) { $errors = $leaseErrors.Result; if ($errors) { Write-Warning $errors } }
        $lease.Dispose()
    }
    $env:ADB_SERVER_SOCKET = $oldSocket
    $env:ADB = $oldAdb
    $env:ANDROID_ADB_SERVER_PORT = $oldAdbPort
    if ($ownsMutex) { $mutex.ReleaseMutex() }
    if ($mutex) { $mutex.Dispose() }
}
