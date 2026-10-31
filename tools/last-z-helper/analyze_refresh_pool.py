"""Analyze observed truck UUID returns and roster cycles without assuming a fixed pool."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path


def parse_log(text: str) -> list[dict]:
    lines = text.splitlines()
    rows = []
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            # A live copy may end in the middle of its final append.
            if index == len(lines) - 1 and not text.endswith("\n"):
                break
            raise
    return rows


def identity(value) -> str:
    if isinstance(value, (float, bool)) or value is None:
        raise ValueError("Truck identities must retain exact integer/string precision")
    value = str(value)
    if not value:
        raise ValueError("Empty truck identity")
    return value


def analyze(rows: list[dict], block_size: int = 25) -> dict:
    headers = [r for r in rows if r.get("type") == "start"]
    if len(headers) > 1:
        raise ValueError("Analyze one recorded run at a time")
    header = headers[0] if headers else {}
    endings = [r for r in rows if r.get("type") == "end"]
    frames = [r for r in rows if r.get("type") == "observation"]
    if not frames:
        raise ValueError("No truck-list observations were captured")
    if block_size < 1:
        raise ValueError("Block size must be positive")

    seen: set[str] = set()
    owners: dict[str, set[str]] = defaultdict(set)
    owner_labels: dict[str, dict] = {}
    appearances: Counter = Counter()
    occurrences: dict[str, list[int]] = defaultdict(list)
    details = {}
    reward_states: dict[str, set[tuple]] = defaultdict(set)
    rosters: list[frozenset] = []
    roster_first: dict[tuple, int] = {}
    growth = []
    eligible_observations = 0
    rendered_seen: set[str] = set()
    rendered_observations = 0
    rendered_not_in_loaded = 0
    previous_refresh = None
    limit = header.get("powerLimit", 440_000_000)

    for frame in frames:
        refresh = int(frame["refresh"])
        if previous_refresh is not None and refresh != previous_refresh + 1:
            raise ValueError("Refresh indices must be consecutive; gaps or same-list samples cannot establish refresh lags")
        previous_refresh = refresh
        trucks = frame["trucks"]
        ids = [identity(t["id"]) for t in trucks]
        if not ids:
            raise ValueError("An empty loading roster is not a truck-pool sample")
        current = frozenset(ids)
        if len(current) != len(ids):
            raise ValueError("Duplicate UUID within a single roster")
        new = current - seen
        signature = tuple(sorted(current))
        earlier_roster = roster_first.get(signature)
        roster_first.setdefault(signature, refresh)
        growth.append({
            "refresh": refresh, "listSize": len(ids), "newIds": len(new),
            "returningIds": len(current & seen), "uniqueIds": len(seen | current),
            "overlapPrevious": len(current & rosters[-1]) if rosters else 0,
            "sameRosterAsRefresh": earlier_roster,
        })
        rosters.append(current)
        for truck, truck_id in zip(trucks, ids):
            appearances[truck_id] += 1
            occurrences[truck_id].append(refresh)
            details[truck_id] = truck
            owner_uid = str(truck.get("ownerUid", ""))
            owner_key = "uid:" + owner_uid if owner_uid else "name:" + str(truck.get("serverId")) + ":" + truck.get("owner", "")
            owners[owner_key].add(truck_id)
            owner_labels[owner_key] = {"ownerUid": owner_uid, "owner": truck.get("owner", ""), "server": truck.get("serverId")}
            quality, power = truck.get("quality", 0), truck.get("power", 0)
            slots, quantity = truck.get("orangeFragmentSlots", 0), truck.get("orangeFragmentQuantity", 0)
            reward_states[truck_id].add((quality, power, slots, quantity))
            if quality in (4, 5) and slots >= 3 and 0 < power < limit:
                eligible_observations += 1
        rendered = {identity(v) for v in frame.get("renderedIds", [])}
        rendered_observations += len(rendered)
        rendered_seen.update(rendered)
        rendered_not_in_loaded += len(rendered - current)
        seen.update(current)

    blocks = []
    for start in range(0, len(growth), block_size):
        part = growth[start:start + block_size]
        count = sum(r["listSize"] for r in part)
        returning = sum(r["returningIds"] for r in part)
        blocks.append({"firstRefresh": part[0]["refresh"], "lastRefresh": part[-1]["refresh"],
                       "lists": len(part), "observations": count,
                       "newIds": sum(r["newIds"] for r in part), "returningIds": returning,
                       "repeatPercent": 100 * returning / count if count else 0,
                       "cumulativeUnique": part[-1]["uniqueIds"]})

    lag_scores = []
    for lag in range(1, min(150, len(rosters) // 2) + 1):
        pairs = [(rosters[i], rosters[i - lag]) for i in range(lag, len(rosters))]
        if len(pairs) < 10:
            continue
        denominator = sum(len(a) for a, _ in pairs)
        exact = sum(a == b for a, b in pairs)
        lag_scores.append({"lag": lag, "pairs": len(pairs), "exactMatches": exact,
                           "exactPercent": 100 * exact / len(pairs),
                           "overlapPercent": 100 * sum(len(a & b) for a, b in pairs) / denominator if denominator else 0})
    strong_cycles = [r for r in lag_scores if r["exactPercent"] >= 80]
    cycle = min(strong_cycles, key=lambda r: r["lag"]) if strong_cycles else None
    observations = sum(appearances.values())
    repeats = observations - len(seen)
    enough_blocks = [b for b in blocks if b["lists"] >= min(block_size, 10)]
    tail = enough_blocks[-1] if enough_blocks else blocks[-1]
    if len(frames) < 10:
        conclusion = "Too few lists to assess a repeating pool."
    elif cycle:
        conclusion = f"Exact rosters recur at a {cycle['lag']}-refresh lag ({cycle['exactPercent']:.1f}% of comparable pairs), supporting a repeating cycle during this sample."
    elif repeats == 0:
        conclusion = "No UUID repeated in this sample. This does not rule out a larger finite pool."
    elif repeats / observations >= .5 and tail["repeatPercent"] >= 90:
        conclusion = "Strong truck reuse and few new UUIDs near the end support a limited active pool; no reliable full-roster restart period was found."
    else:
        conclusion = "Some truck UUIDs return, but no reliable full-roster restart cycle was found in this sample."

    repeated = []
    for truck_id, count in appearances.most_common(12):
        if count < 2:
            continue
        where = occurrences[truck_id]
        repeated.append({"id": truck_id, "appearances": count, "firstRefresh": where[0],
                         "lastRefresh": where[-1], "returnGaps": [b-a for a, b in zip(where, where[1:])],
                         "owner": details[truck_id].get("owner", ""), "server": details[truck_id].get("serverId")})
    repeated_owners = [{**owner_labels[key], "differentTruckIds": len(ids)} for key, ids in owners.items() if len(ids) > 1]
    repeated_owners.sort(key=lambda r: r["differentTruckIds"], reverse=True)
    first_size = len(rosters[0])
    return {
        "accountUid": header.get("accountUid"), "pid": header.get("pid"),
        "collectionEnded": bool(endings), "truncated": bool(endings and endings[-1].get("truncated")),
        "lists": len(frames), "firstRefresh": frames[0]["refresh"], "lastRefresh": frames[-1]["refresh"],
        "truckObservations": observations, "uniqueTruckIds": len(seen), "repeatObservations": repeats,
        "repeatPercentAfterInitial": 100 * repeats / (observations - first_size) if observations > first_size else 0,
        "distinctRosters": len(roster_first), "repeatedRosters": len(frames)-len(roster_first),
        "ownersWithMultipleTruckIds": len(repeated_owners), "ownerIdMissingObservations": sum(1 for f in frames for t in f["trucks"] if not t.get("ownerUid")),
        "trucksWithChangedRewardsOrPower": sum(len(states) > 1 for states in reward_states.values()),
        "listEligible3PlusObservations": eligible_observations,
        "renderedObservations": rendered_observations, "uniqueRenderedIds": len(rendered_seen), "renderedIdsOutsideLoadedList": rendered_not_in_loaded,
        "cycle": cycle, "bestLags": sorted(lag_scores, key=lambda r: (r["exactPercent"], r["overlapPercent"]), reverse=True)[:10],
        "blocks": blocks, "growth": growth, "mostRepeatedTrucks": repeated, "ownersWithDifferentTrucks": repeated_owners[:12],
        "conclusion": conclusion,
        "limits": "Observed loaded UUIDs on one account/time window, not the whole server pool. A returning owner can have a different truck UUID. List eligibility is rechecked on the map before any share.",
    }


def markdown(report: dict) -> str:
    lines = ["# Truck refresh pool observations", "", report["conclusion"], "",
             f"- Refresh range: {report['firstRefresh']}–{report['lastRefresh']} ({report['lists']} lists).",
             f"- Truck observations: {report['truckObservations']}; unique UUIDs: {report['uniqueTruckIds']}.",
             f"- Returning observations after the initial list: {report['repeatPercentAfterInitial']:.1f}%.",
             f"- Repeated whole rosters: {report['repeatedRosters']}.",
             f"- Owners with multiple different truck UUIDs: {report['ownersWithMultipleTruckIds']}.", "",
             "| Refreshes | New UUIDs | Returning entries | Repeat rate | Unique total |",
             "| --- | ---: | ---: | ---: | ---: |"]
    for b in report["blocks"]:
        lines.append(f"| {b['firstRefresh']}–{b['lastRefresh']} | {b['newIds']} | {b['returningIds']} | {b['repeatPercent']:.1f}% | {b['cumulativeUnique']} |")
    lines += ["", report["limits"], ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = analyze(parse_log(args.log.read_text(encoding="utf-8-sig")))
    if args.out:
        args.out.with_suffix(".json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        args.out.with_suffix(".md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("lists", "lastRefresh", "truckObservations", "uniqueTruckIds", "repeatPercentAfterInitial", "repeatedRosters", "cycle", "conclusion")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
