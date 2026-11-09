---
description: Produce a source-grounded exam prediction + study guide from ingested materials, and seed the spaced-repetition scheduler
---

## Context

- Learning state: !`ls .learning/ 2>/dev/null`
- References: read `.learning/references/exam_prediction.md` and `.learning/references/exam_solving.md` before proceeding (and `.learning/references/exam_retention.md` when seeding reviews or making Anki cards). These are the same method files as the exam-study-guide-predictor skill.
- Use `.learning/<topic-slug>/materials/scope.md` and `past_papers.md` from `/ingest-materials`: predict per doctor, follow the marks-driven coverage budget (§1b), use the doctor's stems or the Egyptian stems (§3b), and never predict dropped material.

## Your Task

Turn the ingested materials into (1) a study guide + (2) an evidence-ranked prediction of the actual exam, then seed the review scheduler so daily drills use the predicted paper.

### Step 1 — Load ingested state

Read from `.learning/<topic-slug>/materials/`: `inventory.json`, `exam_statements.md` (purple facts), and `signal_map.json`. If these don't exist, tell the student to run `/ingest-materials` first and stop.

### Step 2 — Predict, using the signal hierarchy

Following `exam_prediction.md`:
- Rank topics by evidence (past papers strongest → model answers → slide repetition → verbal emphasis → insider info → textbook).
- Reverse-engineer the professor's question style and paper structure from past papers + model answers.
- Generate predicted questions with model answers, each tagged 🔴HIGH / 🟡MEDIUM / 🟢LOW with a one-line signal justification, mirroring the professor's phrasing and answering to the mark depth.
- Keep **purple** (professor said it) visually and logically distinct from **red** (predicted).

### Step 2.5 — Build the solving layer

Following `exam_solving.md`, construct the execution half so the guide works as an exam operating manual: question-type recognition (**IF I SEE THIS → IT MEANS THIS → I SHOULD DO THIS**, in the professor's real wording), numbered solving procedures (*Given → Identify → Choose method → Execute → Interpret → Check*), source-tagged worked examples, answer templates with **MUST/GOOD/UNNECESSARY** components, the distractor bank, sanity checks, stuck-recovery protocols, and difficulty layering. Preserve the professor's own methods and notation over textbook convention. Run the error-and-contradiction audit here.

### Step 3 — Build the guide

Ask the student: deep no-missing-detail guide, ultra-condensed rapid sheet, both, or strict-extract (professor's flagged points only). Ask output format (HTML default, or Markdown). Build only the sections the material justifies — activate calculations, visual/data-ID, and protocol sections only when the content is present; keep the image machinery available for image-heavy courses. Save to `.learning/<topic-slug>/exam_guide.html` (or `.md`).

### Step 3.5 — Anki (optional — ask first)

Ask whether the student also wants the predicted questions as Anki cards. Only on a yes: build cards per `exam_retention.md` §2, show 5 sample cards and the totals, then write `flashcards.csv` and — if Anki desktop is open with AnkiConnect — run `python3 .learning/scripts/anki_import.py flashcards.csv --deck "Exams::<Course>"` (dry run), and add `--push` only after the student confirms.

### Step 4 — Seed the review scheduler (the merge payoff)

Convert HIGH/MEDIUM predicted questions and the purple must-know facts into review items and register them with the existing scheduler, e.g.:
```
python3 .learning/scripts/review_scheduler.py --add --topic "<topic-slug>" --from-guide
```
If the script has no such flag, write the items into the topic's `review_schedule.json` in the same shape the scheduler already reads (mirror an existing entry), prioritizing by confidence tag and exam marks. This makes the spaced-repetition drills the *actual predicted paper*, not generic questions.

### Step 4.5 — Coverage audit

Run `exam_solving.md` §17 before reporting: every past-exam question type covered, every professor cue covered, every major procedure demonstrated with a source-tagged example, source errors flagged, no important topic without a "how to solve." Where no real example exists for a topic, say so explicitly instead of inventing one.

### Step 5 — Report

Summarize the top HIGH-confidence predictions, note which extra source (usually more past papers) would most improve accuracy, and tell the student that `/review` will now drill these on a spaced schedule and `/generate-exam` will build a printable mock from them.

**Faithfulness:** stay bound to the student's materials; flag any outside-source clarification; never substitute generic web questions when real materials exist.
