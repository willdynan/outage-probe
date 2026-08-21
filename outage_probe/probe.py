"""The probe loop: classified rounds on a drift-free schedule.

The verdict answers "WHAT recovered", not "is it up": RECOVERED (all layers
ok), PARTIAL (some baseline failures cleared), CHANGED (a failure mode is
different from baseline — the most important signal, and the one an up/down
monitor averages away), DOWN (failing exactly as baseline).

Scheduling anchors to the monotonic clock. Sleeping the interval after each
round makes the true period interval-plus-round-duration and drifts further
every cycle; anchored slots do not. An overrun skips ahead to the next future
slot — a probe never queues a backlog of stale rounds.
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .layers import run_layer


def rollup(baseline: dict, current: dict) -> str:
    failing = {name: out for name, out in current.items() if out != "ok"}
    if not failing:
        return "RECOVERED"
    changed = any(baseline.get(name) != out for name, out in failing.items())
    if changed:
        return "CHANGED"
    if any(base != "ok" and current.get(name) == "ok" for name, base in baseline.items()):
        return "PARTIAL"
    return "DOWN"


def next_slot(start: float, interval: float, n: int, now: float):
    """(sleep_seconds, next_n) for slot n anchored at start. Skips missed slots."""
    target = start + n * interval
    if now <= target:
        return target - now, n
    missed = int((now - start) // interval) + 1
    return start + missed * interval - now, missed


def run_round(config: dict, runner=run_layer) -> dict:
    results = [runner(spec) for spec in config["layers"]]
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "layers": results,
    }


def loop(config: dict, out_path, runner=run_layer, clock=time.monotonic,
         sleeper=time.sleep, max_rounds=None) -> int:
    interval = config["interval_seconds"]
    out = Path(out_path)
    start = clock()
    baseline = None
    n = 0
    rounds = 0
    while max_rounds is None or rounds < max_rounds:
        record = run_round(config, runner)
        outcomes = {r["name"]: r["outcome"] for r in record["layers"]}
        if baseline is None:
            baseline = outcomes
        record["round"] = rounds
        record["verdict"] = rollup(baseline, outcomes)
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
        rounds += 1
        n += 1
        delay, n = next_slot(start, interval, n, clock())
        if (max_rounds is None or rounds < max_rounds) and delay > 0:
            sleeper(delay)
    return rounds


def main():
    parser = argparse.ArgumentParser(prog="outage_probe.probe")
    parser.add_argument("config")
    parser.add_argument("out", help="results JSONL, appended")
    parser.add_argument("--rounds", type=int, default=None)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    count = loop(config, args.out, max_rounds=args.rounds)
    print(f"{count} rounds -> {args.out}")


if __name__ == "__main__":
    main()
