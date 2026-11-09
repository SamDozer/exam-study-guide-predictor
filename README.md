# Exam Study Guide & Predictor — a Claude Skill

**Predict the paper → build the study guide → learn how to answer it → (optionally) drill it until exam day.**

A [Claude Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that turns *your own* course material — the doctor's booklet, lecture slides, professor transcripts (English or Arabic), past papers (even phone photos), model answers, lab manuals, notes — into:

1. a **study guide** organized for fast recall,
2. an **evidence-ranked prediction** of what the exam will actually ask,
3. an **exam operating manual**: how to recognize each question type, what to write for full marks, the traps, and how to check yourself,
4. **optional retention** — Anki flashcards or coached spaced repetition with the bundled **Enhanced Learn FASTER** kit. Always offered, never done without your yes.

Built for **biology-family courses** and **Egyptian university midterms and finals**, but every section is conditional, so it adapts to the material you give it.

> This repository replaces the former **ExamForge** project: its solving layer and Learn FASTER kit were merged in here, and its outdated prediction method was dropped in favour of the improved one below.

## Key features

- **Purple vs red.** What the professor *said* is on the exam (a fact: quoted, Arabic translated, dated, sourced) is kept visually and logically separate from what the skill *predicts* (an inference, confidence-tagged). Second-hand claims ("my friend said the Dr said…") are shown as *reported*, weaker than recorded ones, and a later statement overrides an earlier one ("coming" → "dropped").
- **Evidence-weighted prediction.** Past papers (recency-weighted, with recurrence and rotation) → model answers and the doctor's booklet → slide repetition and formatting → verbal emphasis → your insider tips → textbook last. A relevance rubric lets topics reach HIGH even with no past papers, and every prediction names its signals.
- **Reads Arabic — even messy Arabic.** Catches spoken cues like *"ده مهم للامتحان"*, *"حطوا عليها نجمة"*, *"دي جت السنة اللي فاتت"*, scope cues like *"محذوف / برا المنهج"*, Franco-Arabic group messages (*"da mohem lel emte7an"*), and repairs garbled speech-to-text transcripts.
- **Marks-driven.** Total marks and their split drive how many questions are predicted (a coverage budget of about 1.5–2× the real marks), how deep each answer goes (about one point per mark), and how your revision time is divided.
- **Reads slide formatting.** `scripts/extract_emphasis.py` finds text the professor made **bold**, underlined, red or another colour, or highlighted, in PDFs and PowerPoints — and keeps your own highlights from being mistaken for the professor's.
- **Built for Egyptian exams.** Per-doctor analysis when a course is split between doctors; an exam-scope ledger so nothing dropped gets predicted; past papers transcribed from photos into a year-by-year ledger; questions written with the real stems (Give reasons, Write short notes, Compare, ✓/✗ with correction…).
- **Executable.** IF I SEE THIS → IT MEANS THIS → I SHOULD DO THIS recognition tables, solving procedures, answer templates with MUST / GOOD / UNNECESSARY parts, a distractor bank, stuck-recovery, a time budget and an exam-room plan.
- **Conditional sections.** Calculations, visual/spot-ID tables, and protocol breakdowns activate only when the material contains them, and a "Checked and Skipped" list shows what was left out and why.
- **Source-faithful.** Bound to your materials, with a source tag on every claim (`L3 s12`, `Booklet p45`, `Final 2023 Q2`). The professor's terms and methods are preserved; outside knowledge only for central-but-poorly-explained points, always flagged; conflicts between sources are shown, not hidden.

## Install the skill

1. **claude.ai / Claude app** — download [`dist/exam-study-guide-predictor.skill`](dist/exam-study-guide-predictor.skill) and upload it in **Customize → Skills → Add → Upload skill** (or **Replace** on an existing copy).
2. **Claude Code** — copy the `exam-study-guide-predictor/` folder into your skills directory (e.g. `~/.claude/skills/`).

Then say *"predict my biochemistry final from these slides"* and attach your files. The skill interviews you first: course, exam type and format, marks, doctors, scope, sources, time left, and whether you want flashcards or coached review.

The emphasis script and Anki importer need Python 3.10+; the emphasis script also needs `pip install pymupdf python-pptx` (the skill installs them when it can, or falls back to looking at page images).

## Optional: Enhanced Learn FASTER (spaced repetition)

True spaced repetition needs memory across days, which a chat skill doesn't have. Two options, both optional:

- **Anki.** The skill turns the predicted questions into atomic cards (front in exam wording, source tag on the back, tagged by course/doctor/lecture/confidence). It hands you a CSV, or — with Anki desktop and the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on — pushes them into a deck with `scripts/anki_import.py` (dry run first, `--push` after you approve). For making single cards while you study in Claude Code, the separate [anki-skill](https://github.com/doasfrancisco/anki-skill) works well alongside it (not bundled — it has no license file).
- **Enhanced Learn FASTER kit** (`learn-faster-kit/`, Claude Code or Codex). It ingests your materials with the same method as the skill, predicts the paper, and drills it on a spaced schedule. Needs [`uv`](https://docs.astral.sh/uv/):

  ```bash
  git clone https://github.com/SamDozer/exam-study-guide-predictor
  uv tool install learn-faster --from ./exam-study-guide-predictor/learn-faster-kit
  learn-faster            # in a new folder; choose Exam-Oriented mode
  ```

  Then in Claude Code: `/ingest-materials` → `/predict-exam` → `/review` daily → `/generate-exam` for a printable mock. If you started in chat, ask the skill for a `learn-faster-handoff.md` and drop it in the folder first.

## Repository layout

```
exam-study-guide-predictor/                 # the skill (source of truth)
├── SKILL.md                                # workflow + intake interview
├── references/
│   ├── prediction-and-analysis.md          # signals, scope & doctors, past-paper ledger, Arabic cues, rubric, Egyptian stems
│   ├── solving-layer.md                    # how to answer: recognition, procedures, templates, distractors, time budget
│   ├── output-format.md                    # section catalog, colour coding, HTML/.docx templates
│   └── spaced-repetition.md                # optional Anki / Learn FASTER retention
└── scripts/
    ├── extract_emphasis.py                 # bold/underline/colour/highlight extractor (PDF + PPTX)
    └── anki_import.py                      # push flashcards into Anki via AnkiConnect (stdlib only)
learn-faster-kit/                           # Enhanced Learn FASTER (MIT © Hugo Lau, extended)
dist/exam-study-guide-predictor.skill       # packaged, installable skill
tools/sync_kit.py                           # copies the skill's references/scripts into the kit
tests/                                      # sync, Anki importer, and emphasis extractor tests
docs/how-it-fits.md                         # how the skill and the kit share one method
NOTICE.md                                   # component attribution
```

## Development

The skill is the source of truth. After editing anything in `exam-study-guide-predictor/references/` or `scripts/`:

```bash
python tools/sync_kit.py          # copy into the kit
python -m pytest tests            # sync check, Anki importer, emphasis extractor
```

Then rebuild `dist/exam-study-guide-predictor.skill` (a zip of the `exam-study-guide-predictor/` folder).

## Credit & license

MIT — see [LICENSE](LICENSE). Prediction method derived from exam-prep prompts by Hossam Mahmoud, Abdelrahman El-Dbeky and Ahmed Hussein (Eddie). The spaced-repetition kit is **Learn FASTER**, MIT © 2025 Hugo Lau, bundled and extended under `learn-faster-kit/`. See [NOTICE.md](NOTICE.md).
