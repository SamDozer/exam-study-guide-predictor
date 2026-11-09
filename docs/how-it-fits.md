# How the skill and the kit fit together

One method, two runtimes.

## The shared method

Both use the same files:

| File in the skill (source of truth) | Copy in the kit (installed to `.learning/references/` or `.learning/scripts/`) |
|---|---|
| `references/prediction-and-analysis.md` | `exam_prediction.md` |
| `references/solving-layer.md` | `exam_solving.md` |
| `references/spaced-repetition.md` | `exam_retention.md` |
| `scripts/extract_emphasis.py` | `extract_emphasis.py` |
| `scripts/anki_import.py` | `anki_import.py` |

Edit the skill's files, then run `python tools/sync_kit.py`. `tests/test_repo.py` fails if the kit's copies drift.

## Two runtimes

**The skill** (claude.ai or Claude Code) — zero setup, one session. Reads the materials, produces the HTML/.docx guide, prediction, and operating manual. Optionally a flashcard CSV, a push into Anki, or a hand-off file for the kit. It has no memory between chats, so it can't schedule reviews itself.

**The Enhanced Learn FASTER kit** (Claude Code or Codex) — installed into a project, keeps state in `.learning/` across days. `/ingest-materials` stores the sources and runs the scope, past-paper, purple, and emphasis passes; `/predict-exam` builds the guide and **seeds the review scheduler** with the predicted questions (and optionally Anki); `/review` drills them on a spaced schedule; `/generate-exam` prints a mock.

## The seam

A student who starts in chat and wants ongoing review asks the skill for `learn-faster-handoff.md` (scope, doctors, purple statements, the predicted question bank, and the cards). Put it in a kit-initialized folder and `/ingest-materials` starts from it instead of re-asking.

## Why keep both

Spaced repetition needs state that persists across days. Chat skills don't have it; Claude Code projects do. Putting everything in the chat skill would break the spaced repetition; putting everything in the CLI would lose the zero-setup path. Hence: one method, one optional hand-off, and the retention layer offered only when the student wants it.
