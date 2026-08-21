import unittest

from outage_probe.report import compress, recovery, summary, transitions


def mk(ts, auth, web="ok"):
    return {"ts": ts, "verdict": "x",
            "layers": [{"name": "auth", "outcome": auth},
                       {"name": "web", "outcome": web}]}


ROUNDS = [
    mk("2026-03-09T15:00:00+00:00", "known_fault:db_alloc_failure"),
    mk("2026-03-09T15:05:00+00:00", "known_fault:db_alloc_failure"),
    mk("2026-03-09T15:10:00+00:00", "ok"),
    mk("2026-03-09T15:15:00+00:00", "ok"),
]


class Transitions(unittest.TestCase):
    def test_only_boundaries_are_reported(self):
        found = transitions(ROUNDS)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["layer"], "auth")
        self.assertEqual(found[0]["from"], "known_fault:db_alloc_failure")
        self.assertEqual(found[0]["to"], "ok")
        self.assertEqual(found[0]["ts"], "2026-03-09T15:10:00+00:00")


class Recovery(unittest.TestCase):
    def test_downtime_is_measured_from_first_failure_to_recovery(self):
        rec = recovery(ROUNDS, "auth")
        self.assertEqual(rec["status"], "recovered")
        self.assertEqual(rec["downtime_seconds"], 600.0)
        self.assertEqual(rec["held_rounds"], 2)

    def test_a_relapse_resets_the_recovery_claim(self):
        rounds = [
            mk("2026-03-09T15:00:00+00:00", "other_fault"),
            mk("2026-03-09T15:05:00+00:00", "ok"),
            mk("2026-03-09T15:10:00+00:00", "other_fault"),
            mk("2026-03-09T15:15:00+00:00", "ok"),
        ]
        rec = recovery(rounds, "auth")
        self.assertEqual(rec["recovered"], "2026-03-09T15:15:00+00:00",
                         "recovery means it stayed up, not that it blipped up")

    def test_still_failing_and_never_failed(self):
        self.assertEqual(recovery(ROUNDS, "web")["status"], "never_failed")
        rounds = [mk("2026-03-09T15:00:00+00:00", "other_fault")]
        self.assertEqual(recovery(rounds, "auth")["status"], "still_failing")


class Compression(unittest.TestCase):
    def test_runs_collapse(self):
        series = [(r["ts"], r["layers"][0]["outcome"]) for r in ROUNDS]
        runs = compress(series)
        self.assertEqual(len(runs), 2)
        self.assertIn("x2", runs[0])

    def test_summary_names_the_recovery(self):
        text = summary(ROUNDS)
        self.assertIn("recovered", text)
        self.assertIn("600s down", text.replace("600.0", "600"))


if __name__ == "__main__":
    unittest.main()
