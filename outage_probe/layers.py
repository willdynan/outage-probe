"""Probe layers and outcome classes.

Each layer exists to rule something out before blaming the next: DNS rules out
resolution, a plain GET answers "is the front door serving at all", a canary
watches a request that kept working during the incident (its death means the
backend is getting worse), and the auth-shaped POST is the path under
suspicion.

Every outcome carries a class, never a boolean: `ok`, a named known fault,
`other_fault` (a different failure — meaningful change, investigate), or
`transport`. The probe keeps the matched response excerpt verbatim, because
the excerpt is the evidence, and the evidence is what goes in the vendor case.
"""

import re
import socket
import urllib.error
import urllib.request
from time import perf_counter

TIMEOUT = 10.0
EVIDENCE_CHARS = 400


def classify_http(status: int | None, body: str, spec: dict):
    """Pure classify step: (outcome, evidence). None status means transport."""
    if status is None:
        return "transport", body[:EVIDENCE_CHARS]
    for rule in spec.get("classifiers", []):
        match = re.search(rule["pattern"], body, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 80)
            return f"known_fault:{rule['outcome']}", body[start:start + EVIDENCE_CHARS]
    ok_pattern = spec.get("ok_pattern")
    expected = spec.get("expect_status", [200])
    if status in expected and (ok_pattern is None or re.search(ok_pattern, body, re.IGNORECASE)):
        return "ok", ""
    return "other_fault", f"HTTP {status}: {body[:EVIDENCE_CHARS]}"


def _fetch(spec: dict):
    data = spec.get("body", "").encode("utf-8") if spec["kind"] == "http_post" else None
    request = urllib.request.Request(spec["url"], data=data)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, str(exc)


def run_layer(spec: dict) -> dict:
    started = perf_counter()
    if spec["kind"] == "dns":
        try:
            socket.getaddrinfo(spec["host"], None)
            outcome, evidence = "ok", ""
        except OSError as exc:
            outcome, evidence = "transport", str(exc)
    else:
        status, body = _fetch(spec)
        outcome, evidence = classify_http(status, body, spec)
    result = {
        "name": spec["name"],
        "outcome": outcome,
        "latency_ms": round((perf_counter() - started) * 1000, 1),
    }
    if evidence:
        result["evidence"] = evidence
    return result
