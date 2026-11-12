---
name: exam-study-guide-predictor
description: >-
  Turn a student's own course material into a study guide, a prediction of
  what the exam will ask, and a manual for answering it, optimized for marks.
  Use when the user wants to prepare for an exam, midterm, final, practical,
  OSPE, or quiz from slides, the professor's booklet, Arabic or English lecture
  transcripts, past papers (even photos), model answers, lab manuals, or notes
  — even if they just say "help me study for X", "predict my exam", or upload
  lecture files. Also use for how to answer exam questions (question types,
  structuring answers for marks, distractors, limited hours left) or for exam
  flashcards, Anki, or spaced repetition. Built for biology-family courses and
  Egyptian university exams; adapts to any material. Do NOT use for writing an
  exam, cheating during a live exam, or tutoring unrelated to an upcoming
  assessment.
---

# Exam Study Guide & Predictor

From the student's **own** course material, produce:

1. **A study guide** — organized for fast recall under time pressure.
2. **An exam prediction** — what will most likely be asked, and how, ranked by evidence.
3. **An exam operating manual** — for each likely question type: how to recognize it, what to do, what to write, the trap, how to check.
4. **Optional, only if the student says yes: retention** — flashcards pushed into Anki, or a hand-off to the Enhanced Learn FASTER kit for coached spaced repetition until exam day.

The objective is **scoring on this specific exam**, not comprehensive mastery. Prioritize what the *professor* and the *past papers* signal, not what a textbook considers important.

## Core principles

- **Purple vs red — fact vs inference, never blurred.** What the professor *said* is on the exam is a **fact**: quote it verbatim (Arabic original + English translation), with its source and date, in **purple**. What you *predict* is an **inference**: confidence-tagged, in **red/amber/green**. A fact heard second-hand ("my friend said the Dr said…") is a *reported* fact, shown as purple-outline, weaker than a recorded one. A later statement overrides an earlier one ("it's coming" in week 3, "dropped" in week 9 → dropped). Details: `references/prediction-and-analysis.md` §0.
- **Evidence-weighted prediction.** Rank every topic by the signals behind it: past papers (recency-weighted) → model answers and the professor's booklet → slide repetition and formatting → verbal emphasis → insider tips → textbook last. A relevance rubric lets topics reach HIGH even with no past papers. Every prediction names the signals that fired. §1–§2.
- **Reads Arabic — including messy transcripts.** Transcripts may be Egyptian Arabic, code-switched with English terms, auto-transcribed with errors, or written in Franco-Arabic (Arabizi) in class-group messages. Catch the exam cues in all of them and fold their substance into English output. §4.
- **Marks-driven.** Total marks and their split drive everything: how many questions to predict, how deep each answer goes (about one markable point per mark), and how revision time is divided. If the marks are unknown, read them off past papers or ask. §1b.
- **Read the slides' formatting, not just their words.** Bold, underlined, red/off-palette, or highlighted text usually carries exam weight and is lost in plain text extraction. Always run `scripts/extract_emphasis.py` on every slide/booklet file. §0b.
- **Photos get extra care.** Phone photos and scans (past papers, handwritten notes, model answers) are enhanced with `scripts/enhance_scan.py` (shadow removal, perspective, contrast, black-and-white, ink-colour layers, zoomed tiles), read twice from different versions, and checked character by character for digits, units, symbols, and scientific plausibility. A misread digit is worse than a missing one. `references/reading-images.md`.
- **Scope and doctors first.** Know where the exam stops, what was dropped (محذوف / برا المنهج), and which doctor owns which lectures before predicting anything. Nothing dropped ever gets a predicted question. §0a.
- **Executable, not just informative.** Prediction says *what* is asked; the solving layer (`references/solving-layer.md`) says *how to answer it*. Never stop at "here is what this concept means."
- **Conditional sections.** Build only the sections the material justifies; never force lab machinery (calculations, spot-ID tables, protocols) onto material that doesn't contain it. List what was checked and skipped so the student knows nothing was missed silently. `references/output-format.md`.
- **Source-faithful and traceable.** Build from the student's sources; preserve the professor's exact terminology and methods. Every fact, prediction, and worked example carries a source tag (`L3 s12`, `Booklet p45`, `Final 2023 Q2`). Outside knowledge only for central-but-poorly-explained points, always visibly flagged. Never substitute generic web questions when real materials exist. §5.
- **Handle large inputs.** Transcripts can run 100+ pages: do the cheap marker scans first, then chunk-read section by section.

## Workflow

### Step 1 — Intake (infer first, ask little)

**Never block on a long interview.** First work out everything the files and conversation already answer (course, format, marks, doctors, scope, sources) and state those as assumptions in one short list. Then ask **at most 3 questions**, and only ones whose answers would change the plan (typically: total marks/split if unknown, exam scope or anything dropped, and whether they want flashcards). Start working on everything that doesn't depend on the answers.

**Fast mode** — if the exam is less than about 24 hours away (or the student says it's tomorrow): ask nothing beyond one combined question if truly needed, skip the optional retention offer, read once except where the double-check rule in `reading-images.md` §3 applies, and lead the deliverable with the top predicted questions, the final-minute sheet, and the time plan.

The full checklist below is what to *know*, not a script to recite:

1. **Course & discipline.**
2. **Exam type** — midterm / final / quiz; written / practical / OSPE / oral (viva) / mixed.
3. **Exam format** — MCQ, true/false, short answer, essay, spot/photo ID, calculations, diagram labeling, viva. If unknown, proceed and say the guide isn't format-tuned.
4. **Total marks & distribution** — total, per section, per question type. Push for it.
5. **Doctors** — who teaches which lectures, and each doctor's share of the marks.
6. **Exam scope** — where the material stops; anything dropped (محذوف / برا المنهج / مش مقرر) or "read only" (اقروها بس).
7. **Sources they have** — run the checklist below. Explicitly ask for **past exam papers** (photos are fine), **model answers**, and the **professor's booklet/book**.
8. **Own markings** — have they highlighted their own PDF copies? (Then run the emphasis script with `--ignore-annotations`.)
9. **Time left & current level** — days/hours until the exam, and whether they're comfortable, shaky, or starting near zero. Drives the time budget and how much of the solving layer to front-load.
10. **Deliverable** — study guide, prediction, both (default), or **strict extract** (only what the professor explicitly flagged).
11. **Depth** — deep guide, rapid-revision sheet, or both.
12. **Output format** — HTML (default) or Word .docx. Ask each time.
13. **Images** — does the exam include photo/diagram/spot identification? If yes, activate visual ID and ask for the images.
14. **Enhanced Learn FASTER (optional — always ask, never assume).** Offer, with one line each: (a) **no**, the guide is enough (default); (b) **flashcards** — Anki cards from the predicted questions, pushed straight into Anki if it's running with AnkiConnect, else an importable CSV; (c) **coached spaced repetition** — a hand-off pack for the Enhanced Learn FASTER kit in Claude Code, which drills the predicted paper on a schedule until exam day. Do nothing for (b) or (c) without a clear yes. Details: `references/spaced-repetition.md`.

**Source checklist** (tell them each source's role so they know what's worth digging up):

| Source | Optimizes | Why it matters |
|---|---|---|
| **Past exam papers** (photos/scans from student groups are fine) | Prediction (strongest) | Real question style, recycled items, real depth. Note year and doctor. |
| **Professor's booklet / book** (المذكرة / كتاب الدكتور) | Guide + prediction (very strong) | In many Egyptian courses questions come almost verbatim from it. |
| Official model answers (نموذج إجابة) | Guide + prediction | Expected phrasing and how much earns full marks. |
| Lecture slides (original `.pptx` if available, else PDF) | Guide + prediction | Ground truth; repetition and bold/underline/coloured text = signal. |
| Professor audio / voice-note transcripts (Ar/En) | Prediction (strong) | Spoken "exam alerts" never written on slides. |
| Class-group announcements (WhatsApp/Telegram, often Franco-Arabic) | Scope + prediction | Where "dropped" and "this is coming" usually get posted. |
| Lab / practical manuals | Protocols, calculations, ID | Practical-exam workflow and spot questions. |
| Class / classmate notes | Prediction | Verbal emphasis the student may have missed. |
| Student's own insider info ("the Dr said…") | Prediction | High-value, but a *reported* fact — ask who heard it and when. |
| Textbook chapters | Guide | Fills gaps; secondary to the professor's material. |

After intake, read `references/prediction-and-analysis.md` before doing anything else.

### Step 2 — Ingest and analyze

1. **Scope and doctors** (§0a). Write the scope ledger (cutoff, dropped, read-only) and tag every source and topic with its doctor.
2. **Past-paper ledger** (§0c). Transcribe every past paper — including phone photos — into one table: year, midterm/final, doctor, question, stem type, marks, topic, exact wording. For any photo or scan (past papers, handwritten notes, photographed model answers), first run `python scripts/enhance_scan.py <photos> --out scans` and follow `references/reading-images.md`: check quality, read in two independent passes from different versions, verify every digit, unit and symbol, check spelling against the course vocabulary, and give each item a reading status (checked / corrected / uncertain / illegible). Unreadable parts are `[illegible]`, never guessed.
3. **Purple pass** (§0). Scan transcripts, notes and announcements for explicit exam statements; capture each verbatim with translation, topic, source location, date, and whether it's recorded or reported.
4. **Formatting-emphasis pass** (§0b). Run `python scripts/extract_emphasis.py <all slide and booklet PDFs/PPTXs> --out emphasis.md --render-dir emphasis_pages` (install `pymupdf python-pptx` if missing; add `--ignore-annotations` if the student marked up their copies). If it can't run, inspect page images instead, and say which method was used.
5. **Read everything else fully**, chunking large files. Cross-link instead of summarizing each source alone: lecture → booklet → practical step → how it was asked (ledger) → expected answer (model answer).
6. **Signal map.** One row per topic with every signal, its source tag, and the doctor, before writing anything.

### Step 3 — Predict the exam

Follow `references/prediction-and-analysis.md`: signal weighting with recency, the relevance rubric, the marks-driven coverage budget, confidence tagging, and question style per doctor (the doctor's own stems first, else the Egyptian stems in §3b). Predicted questions mirror the professor's phrasing; model answers carry one markable point per mark.

### Step 4 — Build the solving layer

Read `references/solving-layer.md` and build the execution half: question-type recognition (**IF I SEE THIS → IT MEANS THIS → I SHOULD DO THIS**, in the professor's real wording), solving procedures, worked examples tagged with their source, answer templates with **MUST / GOOD / UNNECESSARY** parts, the distractor bank, sanity checks, stuck-recovery, and difficulty layering. If the student gave a time limit or the exam is close, add the time budget and the exam-room plan. Run the error-and-contradiction audit here.

### Step 5 — Build the deliverable

**HTML (default): start from `assets/guide-template.html` and follow `references/study-guide-design.md`.** That is the house style: stain-named colours with one fixed meaning each, a tonight's plan built from the real clock, and per-lecture **slide cards** (the real slide rendered with `scripts/slide_images.py`, then its exam angle, decoded labels and numbered steps). It also has interactive past-paper and practice banks. Read `references/output-format.md` for the section catalog (what activates when) and the .docx route. Assemble only the justified sections, ordered by marks, grouped by doctor when several teach the course.

### Step 6 — Self-check and coverage audit

Before delivering, verify:
- no predicted question touches dropped or out-of-scope material;
- every purple item is verbatim, sourced, dated, and marked recorded/reported; superseded statements are shown as superseded;
- every prediction names its signals and source tags; confidence isn't inflated;
- predicted marks cover the paper per the coverage budget (§1b), split per doctor where relevant;
- **coverage count matches:** the number of source pages in (every PDF page + every photo) equals the number of pages in the ledger, each with a status (read / partly illegible / BLANK-checked). `enhance_scan.py` prints and saves this count (`scans/_inventory.json`); **stop and fix any mismatch or any BLANK page before delivering** — never let a page disappear silently;
- every slide file went through the emphasis pass; student annotations weren't counted as the professor's;
- **every answer used as a key has a provenance tag** (official key / graded correct / student's own / derived from slides), and only the first two were treated as correct answers;
- repeat counts are per **distinct exam sitting** (versions 2a/2b of one quiz and copies on revision sheets count once);
- every photographed page was enhanced, and pages needing it were read twice (see `reading-images.md` §3); every uncertain or illegible reading is listed for the student with its photo and tile name; no HIGH prediction rests on an unconfirmed reading; scientific errors found on a page are in the audit, not silently fixed;
- every outside-source addition is flagged;
- the solving-layer coverage audit (`solving-layer.md` §17) passes; where a topic has no real example, say so instead of inventing one;
- the "Checked and skipped" list names every section that didn't activate.

Then save the file and present it. Keep the closing message short: sections built, top HIGH predictions, and the one extra source that would most improve the prediction.

### Step 7 — Retention (only if the student said yes in intake)

Follow `references/spaced-repetition.md`: build atomic cards from the HIGH/MEDIUM predictions and purple facts, show a sample, and on approval push them into Anki with `scripts/anki_import.py` (or hand over the CSV); or write `learn-faster-handoff.md` for the Enhanced Learn FASTER kit. If the student didn't opt in, skip this step entirely.

## What good output looks like

- A student can revise from it under time pressure and walk in knowing what to expect and how to answer it.
- Predictions are honest about confidence — no bluffing a weak signal as guaranteed — and every claim can be traced to a slide, page, or past question.
- The professor's own words, methods, and terminology are preserved, not paraphrased into textbook language.
