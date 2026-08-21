import json
import tempfile
import unittest
from pathlib import Path

from outage_probe.probe import loop, next_slot, rollup


class Slots(unittest.TestCase):
    def test_on_time_sleeps_to_the_anchored_slot(self):
        delay, n = next_slot(start=0.0, interval=300.0, n=1, now=100.0)
        self.assertEqual((delay, n), (200.0, 1))

    def test_no_drift_when_rounds_take_time(self):
        # Each round takes 40s; the slot boundaries stay 300s apart regardless.
        for i in range(1, 5):
            delay, n = next_slot(0.0, 300.0, i, now=(i - 1) * 300.0 + 40.0)
            self.assertEqual(delay, 260.0)
            self.assertEqual(n, i)

    def test_overrun_skips_ahead_instead_of_queueing(self):
        delay, n = next_slot(start=0.0, interval=300.0, n=1, now=650.0)
        self.assertEqual(n, 3, "slots at 300 and 600 are gone; do not replay them")
        self.assertEqual(delay, 250.0)


class Rollup(unittest.TestCase):
    BASE = {"web": "ok", "auth": "known_fault:db_alloc_failure", "canary": "ok"}

    def test_all_ok_is_recovered(self):
        self.assertEqual(rollup(self.BASE, {"web": "ok", "auth": "ok", "canary": "ok"}),
                         "RECOVERED")

    def test_same_failure_is_down(self):
        self.assertEqual(rollup(self.BASE, dict(self.BASE)), "DOWN")

    def test_new_failure_mode_is_changed(self):
        current = dict(self.BASE, auth="other_fault")
        self.assertEqual(rollup(self.BASE, current), "CHANGED")

    def test_previously_healthy_layer_failing_is_changed(self):
        current = dict(self.BASE, canary="transport")
        self.assertEqual(rollup(self.BASE, current), "CHANGED",
                         "the canary dying means it is getting worse, not staying down")

    def test_partial_recovery(self):
        base = dict(self.BASE, web="other_fault")
        current = dict(base, web="ok")
        self.assertEqual(rollup(base, current), "PARTIAL")


class Loop(unittest.TestCase):
    def test_rounds_land_with_verdicts_against_the_first_baseline(self):
        # One layer, so loop() calls the runner once per round.
        script = iter(["known_fault:db_alloc_failure", "known_fault:db_alloc_failure", "ok"])

        def runner(spec):
            return {"name": spec["name"], "outcome": next(script), "latency_ms": 1.0}

        clock = [0.0]
        config = {"interval_seconds": 300,
                  "layers": [{"name": "auth", "kind": "dns", "host": "x"}]}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "results.jsonl"
            count = loop(config, out, runner=runner,
                         clock=lambda: clock[0],
                         sleeper=lambda s: clock.__setitem__(0, clock[0] + s),
                         max_rounds=3)
            records = [json.loads(line) for line in out.read_text().splitlines()]
        self.assertEqual(count, 3)
        self.assertEqual([r["round"] for r in records], [0, 1, 2])
        self.assertEqual([r["verdict"] for r in records],
                         ["DOWN", "DOWN", "RECOVERED"],
                         "round one is the baseline; the incident ends on record")


if __name__ == "__main__":
    unittest.main()
