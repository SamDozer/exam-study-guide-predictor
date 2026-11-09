---
description: Ingest the student's own course materials (slides, transcripts, past papers) for source-grounded exam prediction
---

## Context

- Existing learning state: !`ls .learning/ 2>/dev/null`
- Reference: read `.learning/references/exam_prediction.md` before proceeding.

## Your Task

Load the student's real course materials into the learning state so later prediction and review are grounded in *their* professor's content — not generic online examples.

### Step 1 — Ask what they have

If a `learn-faster-handoff.md` from the exam-study-guide-predictor skill is in the project, read it first: it already holds the scope, doctors, purple statements, and predicted question bank — confirm them with the student instead of re-asking, and still ingest any source files present.

Ask the student which materials they can provide (accept file paths or pasted text): the professor's booklet/book (المذكرة), lecture slides (original `.pptx` if they have it), professor audio/voice-note transcripts (English or Arabic), past exam papers (phone photos are fine), official model answers, class-group announcements, lab/practical manuals, textbook chapters, class notes. Explicitly request the strongest prediction sources: **past exam papers**, **model answers**, and **the booklet**. Also ask for: the course name; exam type (midterm/final, written/practical/OSPE/oral); exam date; total marks + distribution; **which doctor teaches which lectures and their share of the marks**; **the exam scope** (cutoff, anything dropped / محذوف, anything "read only"); whether they highlighted their own PDF copies; and whether the exam includes image/spot identification.

### Step 2 — Store materials

Create `.learning/<topic-slug>/materials/` and save or reference each source there. Record an inventory in `.learning/<topic-slug>/materials/inventory.json` (source type, filename, language, doctor).

### Step 3 — Scope ledger and past-paper ledger

Following `exam_prediction.md` §0a and §0c: write `.learning/<topic-slug>/materials/scope.md` (cutoff, dropped, read-only, doctors and their lectures/marks), and transcribe every past paper — including photos — into `.learning/<topic-slug>/materials/past_papers.md` (year, midterm/final, doctor, Q no., stem type, marks, topic, exact wording; `[illegible]` instead of guesses).

### Step 4 — Explicit-marker extraction pass

Following `exam_prediction.md` §0 and §4, scan transcripts, notes, and announcements (including Franco-Arabic messages and auto-transcribed Arabic) for statements where the professor *explicitly* flagged exam material. Capture verbatim quote + English translation + topic + source location + date + doctor + recorded/reported. Later statements supersede earlier ones; "not on the exam" statements go into `scope.md`. Save to `.learning/<topic-slug>/materials/exam_statements.md` (the "purple" facts). On large transcripts (100+ pages) run this as a lightweight first pass, then chunk-read.

### Step 5 — Formatting-emphasis pass

Run `python3 .learning/scripts/extract_emphasis.py <slide and booklet files> --out .learning/<topic-slug>/materials/emphasis.md --render-dir .learning/<topic-slug>/materials/emphasis_pages` (add `--ignore-annotations` if the student marked up their copies; `pip install pymupdf python-pptx` if missing). Weigh the hits per `exam_prediction.md` §0b.

### Step 6 — Build the signal map

Log every topic with its evidence (past-paper hits with years, booklet/model-answer depth, slide repetition and emphasis hits, verbal emphasis, relevance-rubric score), its doctor, and its source tags to `.learning/<topic-slug>/materials/signal_map.json`. Leave out anything dropped from scope. This feeds `/predict-exam`.

### Step 7 — Confirm

Summarize: sources ingested, scope and doctors, past papers transcribed (and any illegible parts), count of explicit professor exam statements found, and the top-weighted topics per doctor. Tell the student to run `/predict-exam` next.

**Do not** fabricate materials or pull generic exam questions from the web at this stage. Only ingest and analyze what the student provides.
