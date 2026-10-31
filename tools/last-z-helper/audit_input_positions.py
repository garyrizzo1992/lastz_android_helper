"""Guard the helper's metadata-only input boundary; not a general proof of UI correctness."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
LEGACY = ("tapAnchored", "tapCanvas", "tapRaw", "tapFast", "nativeTap", "numericField", "displayScale", "logicalHeight", "FrameChecks", "LayoutMath", "PixelRules")


def violations(name: str, text: str) -> list[str]:
    issues = []
    for token in LEGACY:
        if re.search(r"\b" + token + r"\b", text):
            issues.append(f"{name}: retired coordinate API {token}")
    if name.endswith(".java"):
        if re.search(r'\.put\("action",\s*"(?:tap|swipe|pinch|native-tap|native-swipe)"\)', text):
            issues.append(f"{name}: raw coordinate action")
        if re.search(r'\.put\("(?:x|y|endX|endY)",\s*[-+]?\d', text):
            issues.append(f"{name}: literal input endpoint")
        if re.search(r'"/system/bin/input"\s*,\s*"(?:tap|swipe)"', text):
            issues.append(f"{name}: shell coordinate input")
        if re.search(r'\bint\[\]\[\]\s+route\b', text):
            issues.append(f"{name}: pixel scan route")
    if name.endswith(".js"):
        if re.search(r'\b(?:mapY|scale|anchor)\s*=|\bfunction\s+mapY\b|\b(?:540|960)\b', text):
            # Surface compatibility limits are dimensions, not reference-canvas mapping.
            without_limits = re.sub(r'const compatible=.*?;', '', text)
            if re.search(r'\b(?:mapY|scale|anchor)\s*=|\bfunction\s+mapY\b|\b(?:540|960)\b', without_limits):
                issues.append(f"{name}: reference-canvas coordinate mapping")
    return issues


def audit() -> list[str]:
    errors = []
    paths = list((ROOT / "src").rglob("*.java")) + [ROOT / f for f in ("unity-ui.js", "gesture-geometry.js", "scene-geometry.js", "input-agent-tail.js")]
    for path in paths:
        errors.extend(violations(str(path.relative_to(ROOT)), path.read_text(encoding="utf-8")))
    if any((ROOT / "assets/templates").glob("*")):
        errors.append("Retired coordinate-template assets still present")
    device = (ROOT / "src/dev/codex/lastzhelper/DeviceInput.java").read_text(encoding="utf-8")
    if '"map-gesture"' not in device or '"ui-swipe"' not in device:
        errors.append("Missing live geometry input API")
    tail = (ROOT / "input-agent-tail.js").read_text(encoding="utf-8")
    if "unityMapRegion(v=>" not in tail or "checkMap();" not in tail:
        errors.append("Missing fresh map geometry/context guard")
    controller = (ROOT / "src/dev/codex/lastzhelper/AutomationController.java").read_text(encoding="utf-8")
    group_route = controller.split(" void groupTruckShare(", 1)[1].split("\n void ", 1)[0]
    errors.extend(group_route_violations(group_route))
    maintenance = (ROOT / "src/dev/codex/lastzhelper/MaintenanceController.java").read_text(encoding="utf-8")
    errors.extend(maintenance_preflight_violations(maintenance))
    return errors


def maintenance_preflight_violations(body: str) -> list[str]:
    """Require the expected-character rejection before injected foreground inspection."""
    gate = body.find('options.has("expectedAccountUid")')
    reject = body.find('throw new IOException("Expected maintenance character is not active")')
    inspection = body.find("legacy.input.foreground();")
    if gate < 0 or reject < gate or inspection < reject:
        return ["Maintenance must reject unexpected UID before injected foreground inspection"]
    return []


def group_route_violations(body: str) -> list[str]:
    if any(token in body for token in ("goBtn", "waitMapTruck", "verifyMapTruck", "attackFromMap", "attackTruck")):
        return ["Truck group sharing must use the initial blue Share button, never map/Plunder navigation"]
    if "truckShare();" not in body:
        return ["Truck group sharing is missing the direct truck Share action"]
    return []


if __name__ == "__main__":
    errors = audit()
    if errors:
        raise SystemExit("\n".join(errors))
    print("Input-position source audit passed")
