# Enhanced Learn FASTER — optional retention

The guide and prediction tell the student *what* to learn. This optional layer helps them *keep* it until exam day: flashcards in Anki, or coached spaced repetition in the Enhanced Learn FASTER kit.

**Always optional, always asked.** Offer it in intake (question 14) and build nothing here without a clear yes. Pushing cards into Anki writes into the student's own collection, so ask again right before doing it, after they've seen sample cards. If they said no, don't mention it again unless they ask.

## 1. Which path

| Student wants | Path | Needs |
|---|---|---|
| Nothing beyond the guide | none (default) | — |
| Flashcards, quick | **A. CSV** — `flashcards.csv` to import into Anki by hand | Anki (any device) |
| Flashcards, straight into Anki | **B. Push** — `scripts/anki_import.py` adds them through AnkiConnect | Anki desktop running + the AnkiConnect add-on (code `2055492159`) |
| Cards while studying, one at a time | **C. Anki skill** — the companion [anki-skill](https://github.com/doasfrancisco/anki-skill) for Claude Code proposes single cards as the student learns | Claude Code + that skill installed (not bundled here) |
| A coach that drills the predicted paper daily | **D. Learn FASTER hand-off** — `learn-faster-handoff.md` for the kit in this repo | Claude Code or Codex + the kit |

A–C can be combined with D. In a claude.ai chat, only A (and the D hand-off file) can be produced; B and C need a local machine with Anki.

## 2. Building the cards (all paths)

Build from the analysis, never from outside material:

- **What becomes a card, in order:** purple statements' content → HIGH predictions → MEDIUM predictions → must-memorize items (🖍-marked terms, definitions, numbers, confused pairs from Exam Traps). LOW predictions only if the student asks.
- **One fact per card.** If the answer contains "and", split it. A 5-mark "Write short notes on X" becomes several small cards (definition, key feature, function, example), not one essay card.
- **Front in exam wording.** Phrase the front the way the doctor asks: "Give reason: …", "Define …", "Compare X and Y in [one point]", "✓/✗: [statement]". Then the card trains recall *and* recognition of the stem.
- **Short back.** The answer the marks require, in the professor's terms, plus a source tag on its own line (`L3 s12`, `Booklet p45`, `Final 2023 Q2`). No paragraphs.
- **Lists.** Short lists (≤ 4 items, e.g. "the 4 phases of X") can be one card with a numbered back; longer lists become one card per item ("Phase 3 of X?"), so a single forgotten item doesn't fail the whole card.
- **Diagrams and spots.** If the exam has image questions and the student supplied images, front = the image (or "Label the structure at arrow B on [diagram]"), back = the label and its distinguishing feature.
- **Tags** (lowercase, comma-separated): course, doctor, lecture, confidence, and `purple` where it applies — e.g. `biochem,dr-ahmed,l3,high,purple`. They let the student study one doctor's part or only the HIGH cards first.
- **Deck name:** `Exams::<Course>::<Doctor>` (or `Exams::<Course>` for a single doctor).
- **How many.** Cap by the days left: about `days_left × 25` new cards at most, filled in priority order. Too many new cards a few days before an exam won't get reviewed — fewer, high-yield cards beat a huge deck.
- **Preview first.** Show the student 5 representative cards and the total count per deck and confidence before producing or pushing anything.

## 3. Path A — CSV

`flashcards.csv`, UTF-8, comma-separated, every field quoted, header row:

```
"Front","Back","Tags"
"Give reason: PFK-1 is the rate-limiting step of glycolysis.","It catalyses the first committed, irreversible step and is allosterically regulated (ATP, AMP, citrate).<br>L3 s12","biochem,l3,high"
```

Use `<br>` for line breaks inside a field. Import in Anki: File → Import → choose the file → note type *Basic*, field separator *Comma*, tick *Allow HTML*, map the third column to *Tags*.

## 4. Path B — push into Anki with `scripts/anki_import.py`

Only after the student approved the preview and Anki desktop is open with AnkiConnect installed.

```bash
python scripts/anki_import.py flashcards.csv --deck "Exams::Biochemistry::Dr Ahmed"            # dry run: checks connection, shows what would be added
python scripts/anki_import.py flashcards.csv --deck "Exams::Biochemistry::Dr Ahmed" --push     # actually adds the cards
```

It creates the deck if missing, skips cards already in the collection (duplicates by front), and reports added / skipped / failed. It uses only the Python standard library. If it can't reach AnkiConnect, fall back to Path A and tell the student why (Anki closed, add-on missing, or a firewall blocking `localhost:8765`).

**Exam-date tip.** Anki's normal schedule can push a review past the exam date. If the exam is within about two weeks, tell the student to raise *New cards/day* so every card is introduced at least 3 days before the exam, and to use *Custom Study → Review ahead* in the last days.

## 5. Path C — the companion Anki skill

For students who study in Claude Code and want cards created on the fly (one at a time, each approved), point them to [doasfrancisco/anki-skill](https://github.com/doasfrancisco/anki-skill). It is a separate project and is not bundled in this repository (it has no license file, so its code can't be copied here). Install it by following its README. The card rules in §2 still apply to anything created for this exam.

## 6. Path D — Enhanced Learn FASTER hand-off

A chat skill has no memory between days, so it cannot run spaced repetition itself. The **Enhanced Learn FASTER** kit (in this repository under `learn-faster-kit/`, extended from Learn FASTER by Hugo Lau) runs in Claude Code or Codex, keeps state in a `.learning/` folder, and drills the predicted paper on a spaced schedule.

Produce `learn-faster-handoff.md` containing:

1. **Course header** — course, exam type and date, total marks, doctors and their mark shares, scope (cutoff, dropped, read-only).
2. **Topic list by exam weight** — each topic with marks, confidence, doctor, and source tags (seeds its syllabus and `/learn` flow).
3. **Purple statements** — verbatim, translated, dated, recorded/reported (so its exam mode prioritizes them).
4. **Question bank** — every HIGH/MEDIUM predicted question with its model answer, confidence, stem type, marks, and source tags (seeds review items).
5. **The cards from §2** — so the kit and Anki stay consistent if the student uses both.

Then tell the student how to run it (needs [`uv`](https://docs.astral.sh/uv/)):

```bash
git clone https://github.com/SamDozer/exam-study-guide-predictor
uv tool install learn-faster --from ./exam-study-guide-predictor/learn-faster-kit
learn-faster            # choose Exam-Oriented mode, in a new project folder
```

Inside Claude Code in that folder: put the hand-off file and the course files there, then `/ingest-materials` → `/predict-exam` (seeds the review scheduler with the predicted questions) → `/review` daily → `/generate-exam` for a printable mock.

Be honest about the split: the skill prepares the material; the kit (or Anki) does the scheduling.
