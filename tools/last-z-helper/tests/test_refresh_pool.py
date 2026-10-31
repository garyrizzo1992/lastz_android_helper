import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_refresh_pool import analyze, identity, parse_log


def frame(index, ids, owner="owner", slots=0):
    return {"type": "observation", "refresh": index,
            "trucks": [{"id": str(i), "ownerUid": owner, "owner": owner,
                        "serverId": 17, "quality": 4, "power": 100_000_000,
                        "orangeFragmentSlots": slots, "orangeFragmentQuantity": slots} for i in ids]}


class PoolTests(unittest.TestCase):
    def test_new_trucks_from_same_owner_are_not_uuid_repeats(self):
        report = analyze([frame(i, [2*i+1, 2*i+2]) for i in range(12)])
        self.assertEqual(report["uniqueTruckIds"], 24)
        self.assertEqual(report["repeatObservations"], 0)
        self.assertEqual(report["ownersWithMultipleTruckIds"], 1)
        self.assertIsNone(report["cycle"])

    def test_exact_two_refresh_cycle(self):
        report = analyze([frame(i, [1, 2] if i % 2 == 0 else [3, 4]) for i in range(12)])
        self.assertEqual(report["uniqueTruckIds"], 4)
        self.assertEqual(report["repeatObservations"], 20)
        self.assertEqual(report["cycle"]["lag"], 2)

    def test_one_common_truck_does_not_prove_a_roster_cycle(self):
        report = analyze([frame(i, [1, i+2]) for i in range(12)])
        self.assertEqual(report["repeatObservations"], 11)
        self.assertEqual(report["repeatedRosters"], 0)
        self.assertIsNone(report["cycle"])

    def test_repeated_uuid_can_have_changed_rewards(self):
        report = analyze([frame(0, [1], slots=3), frame(1, [1], slots=2)])
        self.assertEqual(report["trucksWithChangedRewardsOrPower"], 1)
        self.assertEqual(report["listEligible3PlusObservations"], 1)

    def test_duplicate_refresh_samples_are_rejected(self):
        with self.assertRaises(ValueError):
            analyze([frame(0, [1]), frame(0, [2])])

    def test_adjacent_large_uuids_stay_distinct(self):
        report = analyze([frame(0, [1430458630091584086, 1430458630091584087])])
        self.assertEqual(report["uniqueTruckIds"], 2)
        with self.assertRaises(ValueError):
            identity(1.430458630091584e18)

    def test_gaps_and_empty_loading_frames_cannot_prove_cycles(self):
        with self.assertRaises(ValueError):
            analyze([frame(0, [1]), frame(2, [1])])
        with self.assertRaises(ValueError):
            analyze([frame(0, [])])

    def test_only_incomplete_last_append_can_be_ignored(self):
        good = json.dumps(frame(0, [1]))
        self.assertEqual(len(parse_log(good + '\n{"type":')), 1)
        with self.assertRaises(json.JSONDecodeError):
            parse_log(good + '\n{"type":\n')


if __name__ == "__main__":
    unittest.main()
