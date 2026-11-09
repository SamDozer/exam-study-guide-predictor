#!/usr/bin/env python3
"""Keep the Learn FASTER kit's exam references and scripts identical to the skill's.

The skill (exam-study-guide-predictor/) is the source of truth. The kit installs
its shared references/scripts into each project's .learning/ folder, so it gets
copies of the same files under the names its commands already use.

    python tools/sync_kit.py           # copy skill -> kit
    python tools/sync_kit.py --check   # exit 1 if the kit is out of date
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "exam-study-guide-predictor"
KIT_SHARED = ROOT / "learn-faster-kit" / "src" / "learn_faster" / "templates" / "shared"

PAIRS = [
    (SKILL / "references" / "prediction-and-analysis.md", KIT_SHARED / "references" / "exam_prediction.md"),
    (SKILL / "references" / "solving-layer.md", KIT_SHARED / "references" / "exam_solving.md"),
    (SKILL / "references" / "spaced-repetition.md", KIT_SHARED / "references" / "exam_retention.md"),
    (SKILL / "scripts" / "extract_emphasis.py", KIT_SHARED / "scripts" / "extract_emphasis.py"),
    (SKILL / "scripts" / "anki_import.py", KIT_SHARED / "scripts" / "anki_import.py"),
]


def stale() -> list[tuple[Path, Path]]:
    return [(s, d) for s, d in PAIRS if not d.exists() or d.read_bytes() != s.read_bytes()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    out_of_date = stale()
    if ap.parse_args().check:
        for s, d in out_of_date:
            print(f"out of date: {d.relative_to(ROOT)} (source: {s.relative_to(ROOT)})")
        return 1 if out_of_date else 0
    for s, d in out_of_date:
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_bytes(s.read_bytes())
        print(f"synced {d.relative_to(ROOT)}")
    if not out_of_date:
        print("kit already in sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
