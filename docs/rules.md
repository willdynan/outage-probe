---
type: Reference
title: Rules
description: The reasoning behind every rule.
---

# The rules, with their citations

Every rule exists because the easy version fails in a specific way. The
test file after each rule is the citation.

## Outcomes carry a class, never a boolean (`tests/test_classify.py`)

The probe classifies each result: `ok`, a named known fault from regex
rules over the response body, `other_fault`, or `transport`. A different
failure is meaningful change, so `other_fault` means investigate. A change
in failure mode must stay visible, never averaged into "still down".

## A fault string beats a courtesy 200 (`tests/test_classify.py`)

Classifiers run before the ok check, because backends wrap real errors in
polite status codes. A 200 whose body carries a known fault classifies as
that fault. The evidence — the matched slice of the response, with
context — lands in the record verbatim. The excerpt goes in the vendor
case, and a paraphrase is not evidence.

## Verdicts answer the incident question (`tests/test_schedule.py`)

Each round rolls up against the first round's baseline. `RECOVERED`: all
layers ok. `DOWN`: failing exactly as baseline. `PARTIAL`: some baseline
failures cleared. `CHANGED`: a failure mode moved, or a healthy layer
started failing. `CHANGED` is the signal an up/down monitor destroys, and
the one that says the incident is evolving.

## Slots do not drift (`tests/test_schedule.py`)

Sleeping the interval after each round makes the true period
interval-plus-duration, and the drift grows every cycle. Slots anchor to
the monotonic clock instead. An overrun skips ahead to the next future
slot. A probe never replays a backlog of stale rounds, because a
measurement taken late is a different measurement.

## Recovery means it stayed up (`tests/test_report.py`)

Downtime measures first failure to recovery. A relapse resets the claim
entirely. A blip up in the middle of an outage is not a recovery, and
reporting it as one misleads whoever decides on the vendor case. Held-for
rounds say how much weight the recovery bears.

## Notes share the timeline (`outage_probe/checkin.py`)

Who said what, when the ticket moved, when the vendor called back. The
human observations land in the same JSONL timeline as the probe data.
The postmortem then reads as one sequence.

## Extending it

- **A new layer kind** is one branch in `run_layer()` returning
  `{"name", "outcome", "latency_ms", "evidence"?}`. TCP connect checks and
  certificate expiry probes both fit the shape.
- **New verdicts** belong in `rollup()`, a pure function of two dicts with
  five pinning tests.
- **Dashboards**: `results.jsonl` is append-only and one line per round.
  Anything that tails JSONL can render it live.
