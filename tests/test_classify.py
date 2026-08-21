import unittest

from outage_probe.layers import classify_http

AUTH_SPEC = {
    "ok_pattern": "session|invalid credentials",
    "classifiers": [
        {"outcome": "db_alloc_failure", "pattern": "QUOTA-91|allocation pool exhausted"},
        {"outcome": "rate_limited", "pattern": "too many attempts"},
    ],
}


class Classification(unittest.TestCase):
    def test_transport_when_no_status(self):
        outcome, evidence = classify_http(None, "connection refused", {})
        self.assertEqual(outcome, "transport")
        self.assertIn("refused", evidence)

    def test_known_fault_is_named_and_evidence_kept_verbatim(self):
        body = ("<fault><detail>Could not allocate space: "
                "QUOTA-91, allocation pool exhausted in shard 7 obj 0x4F2</detail></fault>")
        outcome, evidence = classify_http(500, body, AUTH_SPEC)
        self.assertEqual(outcome, "known_fault:db_alloc_failure")
        self.assertIn("QUOTA-91, allocation pool exhausted in shard 7 obj 0x4F2", evidence,
                      "the excerpt is the evidence; keep it verbatim")

    def test_fault_string_wins_over_a_courtesy_200(self):
        body = "session established -- background job: QUOTA-91, allocation pool exhausted"
        outcome, _ = classify_http(200, body, AUTH_SPEC)
        self.assertEqual(outcome, "known_fault:db_alloc_failure")

    def test_ok_needs_both_status_and_pattern_when_declared(self):
        outcome, _ = classify_http(200, "invalid credentials", AUTH_SPEC)
        self.assertEqual(outcome, "ok")
        outcome, _ = classify_http(200, "<html>maintenance page</html>", AUTH_SPEC)
        self.assertEqual(outcome, "other_fault")

    def test_plain_http_layer_uses_expect_status(self):
        outcome, _ = classify_http(200, "anything", {"expect_status": [200]})
        self.assertEqual(outcome, "ok")
        outcome, evidence = classify_http(503, "upstream unavailable", {"expect_status": [200]})
        self.assertEqual(outcome, "other_fault")
        self.assertIn("HTTP 503", evidence)


if __name__ == "__main__":
    unittest.main()
