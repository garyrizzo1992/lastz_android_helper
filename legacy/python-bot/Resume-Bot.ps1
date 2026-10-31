[CmdletBinding()]
param(
    [ValidatePattern('^[a-zA-Z0-9.-]+$')][string]$MacHost = '192.168.1.10',
    [ValidatePattern('^[a-zA-Z0-9._-]+$')][string]$MacUser = 'garyrizzo',
    [string]$IdentityFile = "$env:USERPROFILE\.ssh\id_ed25519"
)

$ErrorActionPreference = 'Stop'
$ssh = (Get-Command ssh.exe -ErrorAction Stop).Source
if (-not (Test-Path -LiteralPath $IdentityFile -PathType Leaf)) {
    throw "SSH identity not found: $IdentityFile"
}
$sshArgs = @('-i', $IdentityFile, '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8',
             '-o', 'StrictHostKeyChecking=yes', '-o', 'ServerAliveInterval=5',
             '-o', 'ServerAliveCountMax=3')
$remoteScript = @'
import fcntl
import os
import subprocess
import time
from pathlib import Path

label = 'com.garyrizzo.lastz'
domain = f'gui/{os.getuid()}'
service = f'{domain}/{label}'
plist = Path.home() / 'Library' / 'LaunchAgents' / f'{label}.plist'
if not plist.is_file():
    raise SystemExit(f'LaunchAgent not found: {plist}')

# The remote-phone viewer owns this lock while controlling the same handset.
lock = Path.home() / '.local' / 'share' / 'lastz-remote-phone' / 'session.lock'
lock.parent.mkdir(parents=True, exist_ok=True)
with lock.open('a+') as handle:
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Close the LastZ remote-phone session before resuming the bot.')

    def launchctl(*args):
        return subprocess.run(['/bin/launchctl', *args], capture_output=True, text=True, timeout=25)

    if launchctl('print', service).returncode:
        result = launchctl('bootstrap', domain, str(plist))
    else:
        result = launchctl('kickstart', service)
    if result.returncode:
        raise SystemExit('Could not start bot: ' + result.stderr.strip())
    for _ in range(20):
        result = launchctl('print', service)
        if result.returncode == 0 and 'state = running' in result.stdout:
            print('Bot resumed. LaunchAgent is running; startup settings are unchanged.')
            break
        time.sleep(1)
    else:
        raise SystemExit('Service did not reach running state; check the Mac worker logs.')
'@

$remoteScript | & $ssh @sshArgs "${MacUser}@${MacHost}" '/usr/bin/python3 -'
if ($LASTEXITCODE -ne 0) { throw "Resuming the Mac bot failed (SSH exit $LASTEXITCODE)." }
