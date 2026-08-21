"""Operator check-in notes, appended beside the probe results.

    python3 -m outage_probe.checkin notes.jsonl "vendor says fix ETA 30m"

During a real incident the human observations — who said what, when the ticket
moved — belong on the same timeline as the probe data.
"""

import json
import sys
from datetime import datetime, timezone


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    path, note = sys.argv[1], sys.argv[2]
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "note": note}) + "\n")
    print("noted")


if __name__ == "__main__":
    main()
