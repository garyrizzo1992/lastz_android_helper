# Raspberry Pi deployment

The Raspberry Pi runs `lastz-bot.service`.  Its launcher is
`/home/gary/git_sync.sh`, which force-syncs `/home/gary/lastz` to `origin/main`
each time the service starts, then launches `main_scrcpy.py` with the Pi virtual
environment.

## Verification

On the Pi:

```bash
grep '^BRANCH=' /home/gary/git_sync.sh
cd /home/gary/lastz && git status --short --branch
systemctl status lastz-bot.service --no-pager
journalctl -u lastz-bot.service -n 50 --no-pager
```

Restart after a deployment change:

```bash
sudo systemctl restart lastz-bot.service
```

The bot requires its Android device to be connected to the Pi. Verify it with
`adb devices -l`; if no device is listed, the service will exit and systemd will
retry it.
