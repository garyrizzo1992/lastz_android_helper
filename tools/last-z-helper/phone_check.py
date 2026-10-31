"""Run bounded dry-only checks on the connected OnePlus. No credentials or posts."""
from pathlib import Path
import argparse
import json
import shlex
import subprocess

root = Path(__file__).resolve().parents[2]
adb = str(root / "scrcpy/adb.exe")
parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=["prepare", "inspect", "map-region", "map-move", "ui-metadata", "wanted-entry-tree", "wanted-claim-reject", "wanted-viewport-check", "wanted-reward-clear", "wanted-reward-dismiss", "mail-coverage-tabs", "xlua-metadata", "xlua-scene-metadata", "chest-reference-names", "chest-preview", "ui-texts", "ui-bounds", "ui-state", "ui-click", "ui-search", "ui-coordinates", "world", "roundtrip", "trucks", "trucks-open", "truck-pick", "group-preview", "group-scroll-preview", "bounty", "bounty-data", "bounty-view", "bounty-pick", "bounty-menu", "bounty-confirm", "bounty-dismiss", "chat-private", "app-trucks", "app-group", "app-bounty", "dm-preview", "attack-reject", "query"])
parser.add_argument("--serial", default="f7c5e6fe")
parser.add_argument("--state", type=int, default=64)
parser.add_argument("--path", default="UIManagerInstance")
parser.add_argument("--child", default="")
parser.add_argument("--parent", type=int, default=0)
parser.add_argument("--pattern", default=".*")
parser.add_argument("--depth", type=int, default=0)
parser.add_argument("--screenshot", action="store_true", help="Explicitly retain before.png for a PhoneCheck diagnostic; off by default")
args = parser.parse_args()
if args.screenshot and args.mode in ("prepare", "query", "app-trucks", "app-group", "app-bounty"):
    parser.error("--screenshot applies only to PhoneCheck diagnostics")
device = [adb, "-s", args.serial]
folder = "/data/local/tmp/lastz-phone-check"

def command(text, timeout=30):
    return subprocess.run(device + ["shell", "su -c " + shlex.quote(text)], check=True, timeout=timeout)

if args.mode == "prepare":
    command("mkdir -p " + folder + "; chown 2000:2000 " + folder)
    for source, target in [
        (root / "runtime/helper-build/dex/classes.dex", "helper.dex"),
        (root / "tools/last-z-helper/assets/injector-arm64.dat", "injector"),
        (root / "tools/last-z-helper/assets/input-agent.js", "input-agent.js"),
    ]:
        destination = folder + "/" if source.is_dir() else folder + "/" + target
        subprocess.run(device + ["push", str(source), destination], check=True)
    command("chmod 700 " + folder + "/injector")
elif args.mode == "query":
    command(f"CLASSPATH={folder}/helper.dex app_process /system/bin dev.codex.lastzhelper.MemoryQuery {folder}/probe-cache.txt " + " ".join(shlex.quote(str(s)) for s in [args.path,args.depth,args.pattern]))
elif args.mode in ("app-trucks", "app-group", "app-bounty"):
    options = {"dryRun": True, "maxRefreshes": 0, "start": 17, "end": 64,
               "skipTruckState": 0, "attackPowerM": 440}
    mode="truck-world"
    if args.mode=="app-group":
        mode="truck-dm"
    if args.mode=="app-bounty":
        mode="bounties"
        options.update(start=args.state,end=args.state,resume=False,scanSteps=1,stateLimit=1)
    command("am start-foreground-service -n dev.codex.lastzhelper/.HelperService "
            "-a " + mode + " --es options " + shlex.quote(json.dumps(options)))
else:
    command("rm -f " + folder + "/stop-request")
    values=shlex.quote(args.path)+" "+shlex.quote(args.child)+" "+str(args.parent) if args.mode in ("ui-bounds","ui-state","ui-click","wanted-entry-tree") else str(args.state)
    text = f"CLASSPATH={folder}/helper.dex app_process /system/bin dev.codex.lastzhelper.PhoneCheck {folder} {args.mode} {values}"
    if args.screenshot:
        text += " --screenshot"
    command(text, timeout=600)
