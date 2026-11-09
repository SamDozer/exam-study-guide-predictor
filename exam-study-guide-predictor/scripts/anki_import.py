#!/usr/bin/env python3
"""Push exam flashcards from a CSV into Anki through the AnkiConnect add-on.

Dry run by default: it checks the connection and shows what would be added.
Nothing is written to the student's collection unless --push is given.

Usage:
    python anki_import.py flashcards.csv --deck "Exams::Biochemistry"            # preview
    python anki_import.py flashcards.csv --deck "Exams::Biochemistry" --push     # add cards
        [--tags extra,tags] [--model Basic] [--url http://localhost:8765]

CSV: UTF-8 with a header row "Front","Back"[, "Tags"] (tags comma-separated).

Requires Anki desktop running with AnkiConnect (add-on code 2055492159).
Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_URL = "http://localhost:8765"


class AnkiError(RuntimeError):
    pass


def call(url: str, action: str, **params):
    body = json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            reply = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, ConnectionError, TimeoutError) as exc:
        raise AnkiError(f"cannot reach AnkiConnect at {url} ({exc}). "
                        "Is Anki desktop open with the AnkiConnect add-on installed?") from exc
    if reply.get("error"):
        raise AnkiError(f"AnkiConnect error on {action}: {reply['error']}")
    return reply.get("result")


def read_cards(path: Path, extra_tags: list[str]) -> list[dict]:
    cards = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields = {f.lower(): f for f in (reader.fieldnames or [])}
        if "front" not in fields or "back" not in fields:
            sys.exit(f"{path}: header must include Front and Back columns (found {reader.fieldnames})")
        for row in reader:
            front = (row.get(fields["front"]) or "").strip()
            back = (row.get(fields["back"]) or "").strip()
            if not front or not back:
                continue
            raw_tags = row.get(fields["tags"], "") if "tags" in fields else ""
            tags = [t.strip().replace(" ", "-") for t in (raw_tags or "").split(",")]
            cards.append({"front": front, "back": back,
                          "tags": sorted({t for t in tags + extra_tags if t})})
    return cards


def to_note(card: dict, deck: str, model: str) -> dict:
    return {"deckName": deck, "modelName": model,
            "fields": {"Front": card["front"], "Back": card["back"]},
            "tags": card["tags"], "options": {"allowDuplicate": False}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", type=Path)
    ap.add_argument("--deck", required=True)
    ap.add_argument("--model", default="Basic", help="note type with Front/Back fields (default: Basic)")
    ap.add_argument("--tags", default="", help="extra tags added to every card, comma-separated")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--push", action="store_true", help="actually add the cards (default is a dry run)")
    a = ap.parse_args()

    extra = [t.strip().replace(" ", "-") for t in a.tags.split(",") if t.strip()]
    cards = read_cards(a.csv, extra)
    if not cards:
        sys.exit("no cards found in the CSV")

    try:
        version = call(a.url, "version")
        if a.model not in call(a.url, "modelNames"):
            sys.exit(f"note type '{a.model}' not found in Anki; pass --model with one that has Front/Back fields")
        notes = [to_note(c, a.deck, a.model) for c in cards]
        if a.deck in call(a.url, "deckNames"):
            addable = call(a.url, "canAddNotes", notes=notes)
        else:
            addable = [True] * len(notes)  # new deck: nothing in it can be a duplicate yet
    except AnkiError as exc:
        sys.exit(f"{exc}\nFall back to importing the CSV by hand (File → Import in Anki).")

    new = [n for n, ok in zip(notes, addable) if ok]
    dupes = len(notes) - len(new)
    print(f"AnkiConnect v{version} reachable. Deck: {a.deck}")
    print(f"{len(cards)} cards in CSV → {len(new)} new, {dupes} already in Anki (skipped)")
    for n in new[:5]:
        print(f"  • {n['fields']['Front'][:90]}")
    if len(new) > 5:
        print(f"  … and {len(new) - 5} more")

    if not a.push:
        print("Dry run only — nothing was added. Re-run with --push to add these cards.")
        return
    if not new:
        print("Nothing to add.")
        return

    try:
        call(a.url, "createDeck", deck=a.deck)
        ids = call(a.url, "addNotes", notes=new)
    except AnkiError as exc:
        sys.exit(str(exc))
    added = sum(1 for i in ids if i)
    print(f"Added {added} cards to '{a.deck}'. Failed: {len(new) - added}. Skipped duplicates: {dupes}.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
