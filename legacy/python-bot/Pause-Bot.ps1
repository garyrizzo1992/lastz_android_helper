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
import os
import subprocess
from pathlib import Path

label = 'com.garyrizzo.lastz'
domain = f'gui/{os.getuid()}'
service = f'{domain}/{label}'
plist = Path.home() / 'Library' / 'LaunchAgents' / f'{label}.plist'
if not plist.is_file():
    raise SystemExit(f'LaunchAgent not found: {plist}')

def launchctl(*args):
    return subprocess.run(['/bin/launchctl', *args], capture_output=True, text=True, timeout=25)

if launchctl('print', service).returncode == 0:
    result = launchctl('bootout', service)
    if result.returncode and launchctl('print', service).returncode == 0:
        raise SystemExit('Could not stop bot: ' + result.stderr.strip())
if launchctl('print', service).returncode == 0:
    raise SystemExit('Bot service is still loaded; pause was not confirmed.')
print('Current bot stopped. LaunchAgent startup settings are unchanged. Run Resume-Bot.ps1 to start it again.')
'@

$remoteScript | & $ssh @sshArgs "${MacUser}@${MacHost}" '/usr/bin/python3 -'
if ($LASTEXITCODE -ne 0) { throw "Pausing the Mac bot failed (SSH exit $LASTEXITCODE)." }
