# outage-probe

A layered diagnostic probe for the question that matters during an
incident: what recovered — not "is it up".

Built for outages where the status page is green and the vendor is
guessing. The web tier serves pages while one path behind it fails on a
specific backend error. An up/down monitor averages that into noise. This
probe classifies it, timestamps it, and keeps the evidence.

## Quickstart

```
python3 -m unittest discover -s tests                     # no dependencies
python3 -m outage_probe.probe example.probe.json results.jsonl --rounds 4
python3 -m outage_probe.report results.jsonl
python3 -m outage_probe.checkin notes.jsonl "vendor CSM reached, ETA 30m"
```

Edit example.probe.json for your incident: hosts, expected statuses, and
the fault strings you are watching for.

## Layout

```
outage_probe/layers.py   classify outcomes, keep evidence verbatim
outage_probe/probe.py    verdicts against a baseline, drift-free slots
outage_probe/report.py   boundaries, transitions, downtime
outage_probe/checkin.py  operator notes on the same timeline
```

The walkthrough: [docs/design.md](docs/design.md). The rules:
[docs/rules.md](docs/rules.md). Limits and provenance:
[docs/lineage.md](docs/lineage.md). Distilled August 2026 from an
incident-born original. The commit log starts at distillation.
