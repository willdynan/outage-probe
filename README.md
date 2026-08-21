# outage-probe

The status page is green, the vendor is guessing, and your users can't
log in. "Is it up?" was never the question. Mid-incident the questions
that matter are: which layer is failing, did the failure mode change,
when did recovery start, and did it hold — and an up/down monitor
averages all four into a single useless bit.

This probe answers them. Layers work like a differential diagnosis: DNS
rules out resolution, a plain GET proves the front door serves, a canary
watches the request that still works (its death means things are getting
worse), and an auth-shaped POST with throwaway credentials exercises the
path under suspicion. Outcomes carry a class, never a boolean — a named
fault, a *different* fault, and a dead transport are three different
stories. The matching slice of the response is kept verbatim, because
that excerpt is what goes in the vendor case, and a paraphrase is not
evidence.

Rounds fire on monotonic slots that cannot drift. Each one lands as a
line of JSONL, and the report compresses it all to what a responder
needs: transitions, downtime, and how much weight the recovery bears.

## Quickstart

```
python3 -m unittest discover -s tests                     # no dependencies
python3 -m outage_probe.probe example.probe.json results.jsonl --rounds 4
python3 -m outage_probe.report results.jsonl
python3 -m outage_probe.checkin notes.jsonl "vendor CSM reached, ETA 30m"
```

## Going deeper

[docs/design.md](docs/design.md) walks the pieces with captured output.
[docs/rules.md](docs/rules.md) gives every rule its reason and its test.
[docs/lineage.md](docs/lineage.md) holds the honest limits and provenance.

Born in the middle of a real outage, August 2026, because nothing on hand
could answer "what changed". The commit log starts at the distillation.
