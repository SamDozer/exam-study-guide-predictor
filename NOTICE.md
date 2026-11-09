# Components & attribution

This repository combines:

1. **exam-study-guide-predictor skill** (`exam-study-guide-predictor/`, `dist/`, `tools/`, `tests/`) — source-grounded study guides, exam prediction, the exam-solving layer, and optional retention. Derived and generalized from exam-prep prompts by Hossam Mahmoud, Abdelrahman El-Dbeky and Ahmed Hussein (Eddie). MIT. It absorbs the former **ExamForge** project (github.com/SamDozer/Exam-Forge) by the same author: its solving layer and Learn FASTER integration were merged here.

2. **Learn FASTER** (`learn-faster-kit/`) — a Claude Code / Codex spaced-repetition learning kit, MIT © 2025 Hugo Lau. Upstream: https://github.com/cheukyin175/learn-faster-kit. Its original `LICENSE` is retained in that directory.

   Modifications ("Enhanced Learn FASTER"), all within exam mode and the shared templates:
   - added `commands/ingest-materials.md` and `commands/predict-exam.md` (source-grounded ingestion and prediction, scope and doctors, past-paper ledger, formatting-emphasis pass, optional Anki step);
   - added `shared/references/exam_prediction.md`, `exam_solving.md`, `exam_retention.md` and `shared/scripts/extract_emphasis.py`, `anki_import.py` — copies of the skill's files, kept in sync by `tools/sync_kit.py`;
   - extended the Claude Code and Codex exam-mode system prompts to prefer the student's own materials over generic or online examples.

3. **Image-enhancement techniques** in `scripts/enhance_scan.py` are independent implementations of standard methods, chosen after reviewing open-source projects: four-corner perspective correction (as in vipul-sharma20/document-scanner and andrewdcampbell/OpenCV-Document-Scanner), background-division shadow removal (as surveyed in CV-Reimplementation/TraditionalDocumentShadowRemoval), Sauvola binarization (as in openpaperwork/libpillowfight), and ink-colour separation inspired by mzucker/noteshrink (MIT). No code from these projects is included.

4. **Not bundled:** [anki-skill](https://github.com/doasfrancisco/anki-skill) by doasfrancisco is recommended as an optional companion for creating single Anki cards in Claude Code. It has no license file, so none of its code is included here; `scripts/anki_import.py` is an independent implementation against the public AnkiConnect API.
