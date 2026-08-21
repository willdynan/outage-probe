"""Read the results, answer the incident questions.

What changed, when, and how long was the suspect layer down. The report
compresses timelines to runs of identical outcomes — a long stretch of
RECOVERED rounds is one line, because the reader's question is the
boundary, not the bulk.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path


def load(path) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def outcomes_by_layer(rounds: list[dict]) -> dict[str, list[tuple]]:
    layers: dict[str, list[tuple]] = {}
    for record in rounds:
        for layer in record["layers"]:
            layers.setdefault(layer["name"], []).append((record["ts"], layer["outcome"]))
    return layers


def transitions(rounds: list[dict]) -> list[dict]:
    found = []
    for name, series in outcomes_by_layer(rounds).items():
        for (_, prev), (ts, curr) in zip(series, series[1:]):
            if prev != curr:
                found.append({"ts": ts, "layer": name, "from": prev, "to": curr})
    return sorted(found, key=lambda t: t["ts"])


def recovery(rounds: list[dict], layer: str) -> dict | None:
    series = outcomes_by_layer(rounds).get(layer)
    if not series:
        return None
    first_failing = next((ts for ts, out in series if out != "ok"), None)
    if first_failing is None:
        return {"status": "never_failed"}
    recovered = None
    for ts, out in series:
        if ts <= first_failing:
            continue
        if out == "ok" and recovered is None:
            recovered = ts
        elif out != "ok":
            recovered = None  # a relapse resets the claim
    if recovered is None:
        return {"status": "still_failing", "first_failing": first_failing}
    downtime = (datetime.fromisoformat(recovered) - datetime.fromisoformat(first_failing)).total_seconds()
    held = sum(1 for ts, out in series if ts >= recovered and out == "ok")
    return {"status": "recovered", "first_failing": first_failing,
            "recovered": recovered, "downtime_seconds": downtime, "held_rounds": held}


def compress(series: list[tuple]) -> list[str]:
    runs = []
    for ts, outcome in series:
        if runs and runs[-1][0] == outcome:
            runs[-1][2] += 1
        else:
            runs.append([outcome, ts, 1])
    return [f"{outcome} x{count} from {ts}" for outcome, ts, count in runs]


def summary(rounds: list[dict]) -> str:
    lines = [f"{len(rounds)} rounds, {rounds[0]['ts']} -> {rounds[-1]['ts']}",
             f"current verdict: {rounds[-1]['verdict']}"]
    for name, series in outcomes_by_layer(rounds).items():
        lines.append(f"\n[{name}]")
        lines.extend("  " + run for run in compress(series))
        rec = recovery(rounds, name)
        if rec and rec.get("status") == "recovered":
            lines.append(f"  recovered {rec['recovered']} after {rec['downtime_seconds']:.0f}s down; "
                         f"held for {rec['held_rounds']} rounds")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(prog="outage_probe.report")
    parser.add_argument("results")
    args = parser.parse_args()
    rounds = load(args.results)
    if not rounds:
        print("no rounds recorded")
        return
    print(summary(rounds))


if __name__ == "__main__":
    main()
