# Remote phone on the Mac

Double-click **Open Remote Phone.cmd**. It pauses the Mac bot service, opens
scrcpy on Windows, and restores the service when the phone window closes.
Resuming restarts the bot, so it can recover from the screen left by manual use.
If the bot was already stopped, it stays stopped.

No phone Wi-Fi debugging or public ADB ports are required. Both forwarding ports
bind only to Windows loopback, through key-authenticated SSH. The SSH host key is
remembered on first connection and a changed key is rejected.

The Mac watchdog restores the bot on normal closure, SSH EOF, or 30 seconds
without heartbeats (including forced launcher closure). It prevents overlapping
sessions. This cannot guarantee recovery if the Mac itself crashes, its guardian
is force-killed, or launchd refuses to start the service; check the Mac in those cases.

Prerequisites: Windows OpenSSH, scrcpy with its bundled adb.exe, the configured
SSH key, and a USB-authorized phone on the Mac. Defaults target
`garyrizzo@192.168.1.10`, device `f7c5e6fe`, and the existing scrcpy installation
under `C:\Users\Gary\Desktop\scrcpy-win64-v3.3.4`.

Read-only check (does not stop the bot):

```powershell
.\Open-RemotePhone.ps1 -CheckOnly
```

Parameters include `-MacHost`, `-MacUser`, `-IdentityFile`, `-Device`,
`-ScrcpyPath`, `-AdbPort`, and `-VideoPort`. `-TestSessionSeconds 10` opens
the viewer for a bounded integration test, then restores the service.

These files live in the bot repository's `LastZRemotePhone/` folder as an
explicitly requested remote-access utility. The Windows launcher finds its
helper relative to its own location, so moving this folder does not break it.
It installs the helper at `~/.local/share/lastz-remote-phone/mac_lease.py` on the
Mac, outside the application checkout. It does not modify the bot or deployment.
