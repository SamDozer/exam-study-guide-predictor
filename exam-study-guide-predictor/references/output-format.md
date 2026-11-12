# Output Format & Section Catalog

Read before building the deliverable. Covers: which sections activate, color coding, and the HTML / .docx templates.

## Section catalog — activation rules

Build a section only if its trigger is met. Order sections by the mark distribution (highest-mark topics first within the guide), but keep the fixed scaffold below.

| Section | Activate when | Notes |
|---|---|---|
| 1. Table of Contents | Always | Clickable anchors in HTML. |
| 2. Exam Blueprint | Always | Exam type, total marks, per-section marks, question types, predicted paper structure (e.g., "Q1 short notes ×3, Q2 give reasons ×4…"). **Scope:** cutoff, a "Dropped — skip" list, and "Read only" items. **Doctors:** when several teach the course, one row per doctor with their lectures, their marks, and their favourite stems. The prioritization map. |
| 2b. Asked Before | Past papers provided | From the past-paper ledger: each topic that has appeared, with years, doctor, the stems used, and marks. Repeat topics first. Note any `[illegible]` gaps. |
| 3. Professor's Explicit Exam Statements | Transcripts/notes/announcements contain explicit markers | **Purple.** Verbatim quotes (Arabic + English translation) of everything the professor said is (or isn't) on the exam: topic, doctor, source tag, date. Recorded statements solid purple; reported ones purple-outline with who reported them; superseded ones struck through next to the statement that replaced them. This is the strict-extract deliverable on its own. |
| 3b. Slide Emphasis Map | Formatting-emphasis pass found hits | Compact table of what the professor styled: phrase • how (bold/underline/red/highlight) • slide(s) • times emphasized • which predicted question it feeds. Put repeated and red/underlined/highlighted hits first; decode any consistent colour code ("red = enzymes"). |
| 4. High-Yield Concepts & Frameworks | Always | The must-know core, sorted by confidence + marks. Tag must-memorize vs must-understand. Include mnemonics/memory triggers. Mark terms the professor styled on the slides with 🖍. |
| 5. Core Mechanisms & Frameworks | Concept/process content present | WHY & HOW, not just WHAT — covers wet-lab mechanisms, analytical frameworks, and algorithmic/bioinformatics logic alike. Common-misunderstanding traps. Blue styling. |
| 6. Applied Methodologies / Workflows | Lab manual or protocol/code/pipeline present, OR practical/OSPE exam | Step → reason-for-step → critical-error point → result interpretation. Covers wet-lab protocols and computational/analysis pipelines. |
| 7. Visual / Data Interpretation | Image/graph/code-based exam, OR user uploaded visuals | Table: item • purpose/function • distinguishing features • expected result • "how it appears in the exam." Covers specimens, plates, gels, graphs, code blocks, maps, diagrams. Keep this machinery available even when dormant. |
| 8. Analytical / Calculations | Quantitative or formula content present (CFU/mL, dilutions, BOD, COD, enzyme activity/units, % solubilization, molarity, Beer–Lambert, yield, statistical tests, etc.) | Formula/framework + every variable defined + ≥2 solved step-by-step examples from the actual sources/past papers + common mistakes. |
| 9. Predicted Exam Questions + Model Answers | Always (unless strict-extract) | Core deliverable. Grouped by doctor when more than one teaches the course. Each tagged HIGH/MEDIUM/LOW with signal justification and source tags. Use the doctor's own stems (or the Egyptian stems in `prediction-and-analysis.md` §3b); write each model answer as markable points, as many points as the marks. Total predicted marks per section follow the coverage budget (§1b). Nothing from dropped material. |
| 9a. Question-Type Recognition | Always (unless strict-extract) | **IF I SEE THIS → IT MEANS THIS → I SHOULD DO THIS**, one row per question type present, using the professor's real past-exam wording. `solving-layer.md` §1. |
| 9b. Solving Procedures & Worked Examples | Procedural/calculation/practical content present | Numbered *Given → Identify → Choose method → Execute → Interpret → Check* procedures and escalated worked examples, each source-tagged (e.g. *Midterm 2024, Q3*). Blue. §2–4, §14. |
| 9c. Answer Templates & Mark-Earning Structure | Written questions expected (**skip entirely when the exam is all MCQ / true-false / matching** — use 9d's elimination rules and traps instead) | Exam-ready answer skeletons plus **MUST INCLUDE / GOOD TO INCLUDE / UNNECESSARY DETAIL** per question type. §5–6. |
| 9d. Distractor Bank | MCQ / true-false on the exam | **QUESTION → TEMPTING WRONG ANSWER → WHY IT LOOKS RIGHT → WHY IT IS WRONG → CORRECT RULE**, using real past-exam distractors. §8. |
| 9e. Sanity Checks & Stuck-Recovery | Procedural/calculation content present | **ANSWER → QUICK CHECK** table plus the per-type recovery protocol. §7, §9. |
| 9f. Reusable Question Patterns | Same structure recurs across sources | Lecture → booklet → past exam → model answer mapping, with the invariant solving structure named. §10. |
| 10. Exam Traps & Common Mistakes | Always | Confused-pair contrasts, unit traps, misread mechanisms, the swapped words behind ✓/✗ and "correct the underlined" questions. |
| 10a. Source Errors & Contradictions | Audit found confirmed issues | **SOURCE SAYS → PROBLEM → EVIDENCE → WHAT TO FOLLOW FOR THE EXAM.** §12. |
| 10b. Difficulty Self-Check | Always (unless strict-extract) | Per topic: Recognition / Basic / Application / Trap / Written — so the student sees where they're weak. §13. |
| 10c. Time Budget & Exam-Room Plan | Student gave a time limit, or exam is close | **TIME AVAILABLE → TOPICS → EXACT TASK**, plus a format-specific in-room plan using minutes-per-mark. §15–16. |
| 11. Rapid Revision Sheet | User chose "rapid" or "both" | Ultra-condensed one-pager: memory triggers, mnemonics, must-memorize list, formula strip, top predicted Qs. |
| 11a. Final-Minute Sheet | User chose "rapid" or "both", or exam is close | The tightest layer: formulas, decisive rules/distinctions, top traps, answer templates, recognition cues. Introduces nothing new. |
| 12. Checked and Skipped | Always | One line per section that did *not* activate and why ("Calculations — no quantitative content in L1–L6"), plus any source that couldn't be read. So the student knows nothing was skipped silently. |

If a triggered section has no real content in the sources, omit it rather than padding — and list it under "Checked and Skipped."

## Four revision layers

The guide is built as nested compressions; each later layer is derived from the one before and introduces nothing new:

1. **Full explanation** — for learning the topic (sections 4–8).
2. **Exam procedure** — for learning how to answer it (sections 9a–9f).
3. **High-density recall** — the one-page rapid sheet (11).
4. **Final-minute sheet** — formulas, rules, traps, templates, recognition cues only (11a).

## Color coding (consistent across HTML and docx)

> **HTML guides use the stain palette in `study-guide-design.md` §2** (giemsa purple = professor's statements and official keys, eosin = repeated / HIGH, methylene blue = must know, iodine amber = trap, grey = low yield, dashed = outside slides). The list below is the same scheme in plain colour names, for .docx and older guides.

- 🟣 **Purple (solid)** — the professor's *recorded* explicit exam statements, quoted verbatim. Facts, not predictions. Highest priority.
- 🟣 **Purple (outline)** — *reported* statements ("a classmate says the Dr said…"), with who reported them. Superseded statements are struck through.
- 🔴 **Red** — Exam Alerts, Traps, HIGH-confidence *predictions*, "we think this is coming."
- 🟢 **Green** — Key concepts / must-know facts.
- 🔵 **Blue** — Mechanisms & frameworks *and* solving procedures — the WHY, HOW, and HOW-TO-DO-IT.
- ⚫ **Grey (solid)** — supporting explanation or background from the course material.
- ⚪ **Grey/italic dashed** — Outside-source clarifications (must be visually distinct so the student knows it wasn't from the professor).

Never let these blur: a prediction must never look like a professor statement (red ≠ purple), a reported statement must never look like a recorded one (outline ≠ solid), and outside knowledge must never look like course material (dashed ≠ solid grey).
- 🖍 **Marker** — inline tag on any term the professor styled on the slides (bold, underline, red/other colour, highlight). Shows *where* the emphasis came from; it is not itself a confidence level.

**Strict-extract deliverable:** if the user chose "strict extract," output *only* Section 3 (Professor's Explicit Exam Statements) plus a one-line blueprint — no predictions, no synthesis, ultra-condensed. This mirrors the "extract only what the professor explicitly flagged" objective.

## HTML template

**Use `assets/guide-template.html`** (the house template: colours, slide cards, plan, quiz engine with retry and saved progress, print layout, zoomable lightbox) together with `study-guide-design.md`. The skeleton below is only a minimal fallback for environments where the template file isn't available. Self-contained single file, internal CSS, collapsible sections, sticky clickable TOC:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[COURSE] — Exam Master Guide</title>
<style>
  :root{
    --exam:#7c3aed; --exam-bg:#f3edfd;
    --alert:#c0392b; --alert-bg:#fdecea;
    --key:#1e8449;   --key-bg:#eafaf1;
    --mech:#1f6feb;  --mech-bg:#eaf2fd;
    --outside:#6b7280; --ink:#1a1a1a; --line:#e5e7eb; --bg:#ffffff;
  }
  *{box-sizing:border-box} 
  body{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:var(--ink);
       max-width:900px;margin:0 auto;padding:24px;line-height:1.55;background:var(--bg)}
  h1{border-bottom:3px solid var(--ink);padding-bottom:8px}
  h2{margin-top:36px;border-left:6px solid var(--ink);padding-left:10px}
  nav{position:sticky;top:0;background:var(--bg);border:1px solid var(--line);
      border-radius:10px;padding:14px 18px;margin:16px 0;box-shadow:0 1px 4px rgba(0,0,0,.05)}
  nav a{display:inline-block;margin:4px 10px 4px 0;text-decoration:none;color:var(--mech)}
  table{border-collapse:collapse;width:100%;margin:14px 0}
  th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
  th{background:#f5f6f8}
  .exam{background:var(--exam-bg);border-left:5px solid var(--exam);padding:10px 14px;border-radius:6px;margin:12px 0}
  .exam blockquote{margin:6px 0;padding-left:10px;border-left:3px solid var(--exam);color:#4c1d95}
  .alert{background:var(--alert-bg);border-left:5px solid var(--alert);padding:10px 14px;border-radius:6px;margin:12px 0}
  .key{background:var(--key-bg);border-left:5px solid var(--key);padding:10px 14px;border-radius:6px;margin:12px 0}
  .mech{background:var(--mech-bg);border-left:5px solid var(--mech);padding:10px 14px;border-radius:6px;margin:12px 0}
  .outside{color:var(--outside);font-style:italic;border-left:3px dashed var(--outside);padding-left:10px;margin:10px 0}
  .exam.reported{background:transparent;border:2px dashed var(--exam);border-left-width:5px}
  .superseded{text-decoration:line-through;opacity:.6}
  .proc{background:var(--mech-bg);border-left:5px solid var(--mech);padding:10px 14px;border-radius:6px;margin:12px 0}
  .proc ol{margin:6px 0 0 18px}
  .bg{background:#f5f6f8;border-left:5px solid #9ca3af;padding:10px 14px;border-radius:6px;margin:12px 0;color:#374151}
  .src{font-size:.8em;color:var(--mech);font-weight:700;letter-spacing:.3px}
  .must{color:var(--alert);font-weight:700} .good{color:#d68910;font-weight:700} .skip{color:var(--outside)}
  .recog th:first-child{width:32%} .recog td:nth-child(2){font-style:italic}
  .tag{font-size:.75em;font-weight:700;padding:2px 8px;border-radius:20px;color:#fff}
  .high{background:var(--alert)} .med{background:#d68910} .low{background:var(--key)}
  details{border:1px solid var(--line);border-radius:8px;margin:10px 0;padding:6px 12px}
  summary{cursor:pointer;font-weight:600;padding:6px 0}
  .qa{border:1px solid var(--line);border-radius:8px;padding:12px;margin:12px 0}
  .marks{float:right;font-weight:700;color:var(--mech)}
  code,.formula{background:#f5f6f8;padding:2px 6px;border-radius:4px;font-family:Menlo,Consolas,monospace}
</style>
</head>
<body>
  <h1>[COURSE] — Exam Master Guide</h1>
  <p><em>[exam type] · Total: [marks] · [date if known]</em></p>

  <nav id="toc"><strong>Contents</strong><br>
    <!-- one <a href="#sec-N"> per active section -->
  </nav>

  <!-- SECTION PATTERN -->
  <h2 id="sec-2">2 · Exam Blueprint</h2>
  <!-- marks table + predicted paper structure -->

  <h2 id="sec-8">8 · Predicted Questions</h2>
  <div class="qa">
    <span class="marks">[X marks]</span>
    <span class="tag high">HIGH</span>
    <p><strong>Q:</strong> [predicted question in professor's style]</p>
    <p><em>Signal: appeared in 2023 & 2024 papers; verbally emphasized.</em></p>
    <details><summary>Model answer</summary>[answer to mark depth]</details>
  </div>

  <!-- Callout examples -->
  <div class="exam">🟣 Professor said (exam): <blockquote>"[verbatim quote]" — [English translation if Arabic]</blockquote>→ points to: [topic]</div>
  <div class="alert">⚠️ Exam alert: …</div>
  <div class="key">✅ Key: …</div>
  <div class="mech">🔵 Mechanism: …</div>
  <div class="outside">[Outside-source clarification: …]</div>
  <div class="exam reported">🟣 Reported (via [classmate / group msg, date]): "[quote]" → [topic]</div>
  <div class="exam"><span class="superseded">"[earlier statement]" — [date]</span><br>Superseded by: "[later statement]" — [date, source]</div>

  <h2 id="sec-9a">9a · Question-Type Recognition</h2>
  <table class="recog"><tr><th>If I see this</th><th>It means this</th><th>I should do this</th></tr>
    <tr><td>[professor's actual stem wording]</td><td>[what's really being tested]</td><td>[method + sequence]</td></tr>
  </table>

  <div class="proc">
    <span class="src">Source: [Midterm 2024, Q3]</span>
    <p><strong>Procedure — [question type]</strong></p>
    <ol><li>Given: …</li><li>Identify: …</li><li>Choose method: …</li><li>Execute: …</li><li>Interpret: …</li><li>Check: …</li></ol>
    <p><span class="must">MUST INCLUDE</span> … · <span class="good">GOOD</span> … · <span class="skip">UNNECESSARY</span> …</p>
  </div>

  <div class="bg">⚫ Background (course material, [source tag]): …</div>
</body>
</html>
```

Fill every `[...]` placeholder. Remove sections that didn't activate and their TOC links. Keep the file fully self-contained (no external assets); embed uploaded images as base64 in `<img>` if the visual-ID section is active.

## Word (.docx) output

If the user picks docx, build it with the environment's Word/docx skill if one is available (on claude.ai: `/mnt/skills/public/docx/SKILL.md`). Map the same color coding to shaded paragraph/heading styles, keep the same section catalog and predicted-question tagging, and use a real Word table of contents.

## Retention extras (only if the student opted in)

Flashcards, Anki import, and the Enhanced Learn FASTER hand-off are **optional** and only built after an explicit yes in intake. Everything about them — card rules, the CSV format, pushing into Anki, and the hand-off pack — lives in `references/spaced-repetition.md`.

## Delivery

Save the file where the environment expects outputs (on claude.ai: `/mnt/user-data/outputs/`, then present it; in Claude Code: the working directory) and tell the student where it is. Keep any closing message short: name the sections built, the top few HIGH-confidence predictions, and what extra source (usually past papers) would most improve the prediction next time.
