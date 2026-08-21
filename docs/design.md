---
type: Reference
title: Design notes
description: How the pieces fit together.
---

# Design notes

## What this is

During a real incident the question is never "is it up". The question is
"what changed" — which layer failed, whether the failure mode moved, when
recovery started, and whether recovery held. An up/down monitor averages
all of that into a single bit. This probe is the instrument you start when
the status page is green, the vendor is guessing, and you need answers
with timestamps and evidence.

The scenario it grew from: a web tier that serves pages normally while one
path behind it fails on a specific backend error. Every layer of a generic
monitor says healthy. The users say otherwise.

## How it works

```
 probe.json               probe.py loop (monotonic slots)
 layers:                       |
   dns    ----------------> run each layer, classify the outcome
   web (GET)                   |
   canary (GET)                v
   auth (POST + classifiers)  results.jsonl   one line per round
                               |
                               v
                          report.py     boundaries, transitions, downtime
                          checkin.py    operator notes on the same timeline
```

Each round is one JSON line: a timestamp, every layer's classified
outcome, and a verdict against the first round's baseline.

```json
{"ts":"2026-03-09T15:25:11+00:00","round":7,"verdict":"DOWN",
 "layers":[{"name":"dns","outcome":"ok","latency_ms":2.1},
           {"name":"web","outcome":"ok","latency_ms":88.0},
           {"name":"auth","outcome":"known_fault:db_alloc_failure",
            "latency_ms":902.5,"evidence":"QUOTA-91, allocation pool..."}]}
```

Layers are a differential diagnosis. Each one exists to rule something out
before blaming the next. `dns` rules out resolution. `web` answers whether
the front door serves at all. `canary` watches a request that kept working
during the incident — when the canary dies, the backend is getting worse.
`auth` posts throwaway values at the path under suspicion, and it is the
only layer with fault classifiers:

```json
{"name": "auth", "kind": "http_post", "url": "https://.../api/login",
 "ok_pattern": "session|invalid credentials",
 "classifiers": [
   {"outcome": "db_alloc_failure", "pattern": "QUOTA-91|allocation pool exhausted"}]}
```

Note `ok_pattern`: "invalid credentials" from a live backend is an `ok`
outcome. The probe measures the path, never a real credential.

## Worked example

Real report output over a seven-round window where the auth layer failed
three times and then recovered:

```
7 rounds, 2026-03-09T15:00:00+00:00 -> 2026-03-09T15:30:00+00:00
current verdict: RECOVERED

[web]
  ok x7 from 2026-03-09T15:00:00+00:00

[auth]
  known_fault:db_alloc_failure x3 from 2026-03-09T15:00:00+00:00
  ok x4 from 2026-03-09T15:15:00+00:00
  recovered 2026-03-09T15:15:00+00:00 after 900s down; held for 4 rounds
```

Runs of identical outcomes collapse, because the reader's question is the
boundary, not the bulk. The report names the recovery minute, the
downtime, and how long recovery has held.

Every rule and its citation: [rules.md](rules.md). Limits and provenance:
[lineage.md](lineage.md).
