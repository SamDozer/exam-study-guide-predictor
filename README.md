# Exam Study Guide & Predictor — a Claude Skill

A reusable [Claude Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) that turns your own course material into a **two-in-one deliverable**: a study guide *and* an evidence-ranked prediction of what the exam will actually ask, optimized for marks.

Built for **biology-family courses** — biotechnology, biology, biochemistry, bioinformatics, chemistry, microbiology, molecular biology, and related lab sciences — but every section is conditional, so it adapts to the material you give it.

## What it does

- **Study guide + exam prediction in one pass.** Not a generic summary — it links theory → practical step → how it was asked before → expected answer.
- **Evidence-weighted predictions.** Every predicted question is tagged **HIGH / MEDIUM / LOW** confidence with the signals that justify it. Past exam papers are the strongest signal, then model answers, slide repetition and formatting, professor verbal emphasis, your insider tips, and textbook prominence last.
- **Reads slide formatting.** Every slide PDF/PPTX goes through `scripts/extract_emphasis.py`, which finds the text the professor made **bold**, underlined, red or another off-palette colour, or highlighted. Those hits feed the prediction and show up in the guide as a 🖍 "Slide Emphasis Map". Titles, repeated headers/footers, grey template text and hyperlinks are ignored.
- **Built for Egyptian university exams.** Uses the doctor's booklet (المذكرة) as a primary source; splits analysis and marks per doctor when several teach a course; tracks the exam scope and anything dropped (محذوف / برا المنهج) so nothing out of scope gets predicted; transcribes past papers from phone photos into a year-by-year ledger; and writes questions with the usual stems (Give reasons, Write short notes, Compare, ✓/✗ with correction…) and point-per-mark model answers.
- **Works without past papers.** A relevance rubric scores every concept on testability, formatting emphasis, coverage depth, cross-source recurrence and question-archetype fit, so topics can reach HIGH confidence even when no past paper exists.
- **Reads Arabic professor transcripts.** Parses spoken Arabic (and code-switched Arabic + English) lecture transcripts, catches spoken exam cues like *"ده مهم للامتحان"* / *"هييجي في الامتحان"*, and folds them into the English output as verbal-emphasis signal.
- **Marks-driven prioritization.** Asks for the total marks and distribution, then allocates depth and predicted questions proportionally.
- **Conditional sections.** Lab machinery (CFU/BOD/COD/enzyme-activity calculations, media/specimen identification tables, protocol breakdowns, spot-photo ID) activates only when the material justifies it.
- **Source-faithful.** Builds from *your* sources and preserves the professor's exact terminology. Outside knowledge is used only for central-but-poorly-explained concepts and is always visibly flagged.
- **Two output formats.** Self-contained color-coded HTML (default) or a printable Word `.docx`.

## Install

Two ways:

1. **In the Claude app / claude.ai** — download `dist/exam-study-guide-predictor.skill` and use the **Save skill** button on the file card, or upload it in Settings → Capabilities → Skills (availability depends on your plan/org).
2. **Claude Code / API** — place the `exam-study-guide-predictor/` folder in your skills directory.

## Use

Once installed it triggers on prompts like:

- "Help me study for my microbiology final"
- "Predict my biochem midterm from these slides"
- "Make me a revision guide" (with lecture files attached)

It then interviews you on: course, exam type, format, total marks + distribution, which sources you have, deliverable (guide / prediction / both), depth (deep / rapid / both), and output format.

**Sources it can use:** lecture slides, professor audio/voice-note transcripts (English or Arabic), past exam papers, official model answers, lab/practical manuals, textbook chapters, class notes, and your own "the Dr said…" insider tips.

## Repository layout

```
exam-study-guide-predictor/
├── SKILL.md                              # workflow + intake interview
├── scripts/
│   └── extract_emphasis.py               # bold/underline/colour/highlight extractor (PDF + PPTX)
└── references/
    ├── prediction-and-analysis.md        # signal weighting, relevance rubric, Arabic cue tables, faithfulness rule
    └── output-format.md                  # section catalog + HTML/.docx templates
dist/
└── exam-study-guide-predictor.skill      # packaged, installable skill
```

## Credit

Derived from a set of exam-prep prompts by Hossam Mahmoud, Abdelrahman El-Dbeky and Ahmed Hussein (Eddie), generalized from a single Environmental Biotechnology course into a reusable, discipline-adaptive skill.

## License

MIT — see [LICENSE](LICENSE).
