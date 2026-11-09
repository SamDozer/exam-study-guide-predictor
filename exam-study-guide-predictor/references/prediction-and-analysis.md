# Prediction & Analysis Method

This is the intellectual core: how to reverse-engineer what the exam will ask and how confident to be. Read after intake, before building output.

## 0. Explicit-marker extraction pass (run first)

Before weighting anything, scan transcripts and notes for statements where the professor *explicitly and unequivocally* flagged exam material. This pass produces **facts**, not inferences, and feeds the purple "Professor's Explicit Exam Statements" section.

For each hit, capture: the verbatim statement (original Arabic *and* an English translation if spoken in Arabic), the exact topic/concept it points to, and the source location (which lecture/slide). Do not paraphrase away the professor's wording — the point is fidelity.

**Large transcripts (100+ pages):** run this scan first as a lightweight pass over the whole file, logging hits with their line/section, then chunk-read the rest of the document section by section for the deeper synthesis. Never try to hold the entire transcript in one reasoning pass.

**Purple vs red — keep them distinct:**
- **Purple** = the professor literally said this is on the exam. A *fact*. Highest study priority, quoted.
- **Red** = a HIGH-confidence *prediction* (from past papers / convergent signals) or an exam trap. An *inference* or a warning.

A topic can be both (professor flagged it *and* it's in past papers) — show the purple statement and the red prediction together.

## 0b. Formatting-emphasis pass (always run on slides)

Professors mark what matters by *styling* it: **bold**, underline, red or other off-palette colours, highlighter. Plain text extraction erases all of that, so reading a slide PDF as text alone misses one of the best signals in the material. Run this pass on **every** slide file (PDF or PPTX), right after §0.

**How:**

1. Run the bundled script on all slide files at once:
   `python scripts/extract_emphasis.py lecture1.pdf lecture2.pdf deck.pptx --out emphasis.md --render-dir emphasis_pages`
   (needs `pip install pymupdf python-pptx`). It compares every word against the document's own normal body style and lists each phrase that differs (`BOLD`, `UNDERLINE`, `HIGHLIGHT`, `COLOR:<name> <hex>`) with page/slide number and the surrounding line. It already ignores slide titles, headers/footers repeated on most pages, grey template text, and hyperlinks. It also tables phrases emphasized more than once.
2. **If the script can't run** (no Python, install blocked), render the slide pages to images and inspect them visually for the same cues. Never skip the pass silently; say which method was used.
3. **Scanned / image-only pages** (listed as `no_text_pages`, rendered to `--render-dir`): look at those images directly — the script can't see styling in pictures.
4. If the student has the original `.pptx`, prefer it over the PDF export: formatting is stored exactly there.

**How to weigh what it finds:**

- **Normalize first.** Check `body_color` and `bold_is_normal_text` in the report. If a template makes *everything* bold or blue, that style is the norm, not emphasis — the script handles bold; judge colour themes by eye.
- **Red / highlighted / underlined** body text is the strongest formatting cue — professors use it as a written "exam alert." Treat as a MEDIUM signal on its own, HIGH when it converges with another signal (repeated, verbally flagged, in a past paper).
- **Bold** is weaker: slides often bold definitions and key terms. Bold = "this is a term you must know"; that makes it a prime candidate for definition/MCQ questions.
- **Emphasized more than once** (across slides or lectures) is far stronger than a single hit.
- **A colour used consistently for one purpose** (e.g., every enzyme in red, every exception in orange) is a code: decode it and say so in the guide ("red on these slides = rate-limiting enzymes").
- **Context matters.** Read the line around the hit: an emphasized number, exception, "not", or "only" is a classic trap/MCQ target.

This is still an **inference**, not a purple fact — formatting says "important," not "on the exam." Feed every hit into §1 (signal #3) and the §1a *structural emphasis* axis, and mark emphasized terms in the guide with 🖍 so the student sees which points the professor styled.

## 1. Signal-weighting hierarchy

Rank every candidate topic by the evidence behind it. Signals from strongest to weakest:

1. **Past exam papers (strongest).** If a topic, question stem, or figure appeared in a previous paper, weight it heavily. Professors recycle and lightly rephrase. Note whether the item repeats across *multiple* past papers — a recurring past question is close to a guarantee. Track the exact phrasing; predict the rephrase.
2. **Official model answers.** Reveal the depth and wording that earn full marks. If a model answer is long/structured, the exam expects a long/structured answer.
3. **Repetition and formatting emphasis on the slides.** A concept restated on many slides, given its own summary/objectives slide, or styled differently from normal text (bold, underline, red/other colour, highlight — from the §0b pass). Count both repetitions and emphasis hits.
4. **Professor verbal emphasis (transcripts / notes).** Explicit spoken exam cues — see the Arabic + English cue tables below. Treat "this is important for the exam" as a near-guarantee even if the topic looks minor on the slides.
5. **Student-provided insider info.** "The Dr said the calculation is coming" — treat as high-value verbal emphasis. Always ask the student for this.
6. **Content-based relevance score (works with zero past papers — see §1a).** Every concept's inherent examinability, scored on the rubric below. This is a full prediction engine, not a footnote — run it on *every* course, even ones with rich past papers, because it catches new material the professor added this year that no past paper could show.
7. **Textbook prominence (weakest).** Only relevant if it aligns with a higher signal. Do not predict something *just* because a textbook stresses it — the professor may not.

**Combining signals:** a topic backed by multiple independent signals (e.g., in a past paper AND verbally emphasized AND red on the slides) is the highest-priority prediction. Isolated single-signal topics are lower confidence. A topic can reach HIGH through §1a alone, without any past paper.

## 1a. Content-based relevance scoring (no past papers required)

Use this whenever past papers and/or model answers are missing, thin, or outdated (syllabus changed). Don't fall back to vague low-confidence guessing — score every concept explicitly so the student still gets a ranked, justified prediction.

**Step 1 — extract candidate concepts.** Pull every named concept, process, structure, term, comparison, and formula from the sources into a flat list before scoring. Don't pre-filter by "feels important" — the scoring does that.

**Step 2 — score each concept on five axes (0–2 each, 10 max):**

| Axis | 0 | 1 | 2 |
|---|---|---|---|
| **Testability** — can it become a clean, objectively gradable question? | Vague, purely descriptive | Can be asked, but the answer is fuzzy | Naturally a definition, mechanism, comparison, calculation, or labeling question |
| **Structural emphasis** — does the material's own formatting flag it? (use the §0b report) | Plain body text, no visual weight | Bold only, or a normal bullet | Red/off-palette colour, underline or highlight; emphasized on 2+ slides; or restated on a "summary"/"objectives"/"learning outcomes" slide |
| **Coverage depth** — how much space/time does it get? | One passing mention | A few lines or one slide | Its own slide(s)/section, a worked example, or multiple sub-points |
| **Cross-source recurrence** — does it appear independently in more than one source type? | One place only | Two source types (e.g., slides + manual) | Three or more (slides + manual + textbook + transcript…) |
| **Archetype fit** — does it match a question shape this discipline reliably uses (§3a)? | No common archetype | Loosely fits one | Cleanly fits one or more |

**Step 3 — map the total to a confidence tier** (content-only, before folding in papers/transcripts):

- **8–10 → HIGH.** Reachable without a past paper: a clean testable mechanism, styled by the professor, deeply covered, confirmed across sources, is a fair "expect this."
- **5–7 → MEDIUM.** Solidly plausible, missing one or two axes.
- **2–4 → LOW.** Present but weakly examinable or thinly covered.
- **0–1 → drop.** Not worth a predicted question.

When the §1a score and other §1 signals fire on the same concept, they compound — name the convergence in the justification (e.g., "9/10 relevance; red + underlined on slides 4 and 11; verbally flagged in lecture 3").

**Step 4 — check against the mark distribution.** A HIGH-scoring concept in a 2-mark section shouldn't spawn five predicted questions; one in the 25-mark section should. The relevance score decides *whether* to predict a question; the marks decide *how many* and *how deep*.

## 2. Confidence tagging

Every predicted question carries a tag with a one-line justification naming the signals:

- 🔴 **HIGH** — appeared in past exam(s), or explicitly flagged by the professor as exam material, or multiple strong signals converge, **or scored 8–10 on the §1a rubric**. Phrase these as "expect this."
- 🟡 **MEDIUM** — repeated or colour/underline-emphasized on slides, or a single verbal emphasis, but not confirmed by a past paper; **or scored 5–7 on §1a**. "Likely."
- 🟢 **LOW** — plausible from the syllabus/marks but weak signal, **or scored 2–4 on §1a**. "Possible; cover if time allows."

Never inflate confidence. A student allocating scarce revision time is relying on this being honest. A past paper is the *easiest* route to HIGH, not the only one — don't cap a well-scored §1a topic at MEDIUM just because no past paper confirms it; give the rubric score as the justification.

## 3. Reverse-engineering the professor's question style

Before writing predicted questions, extract the *pattern* from past exams + model answers:

- **Question stems** the professor favors ("Compare…", "Explain the mechanism…", "Given the following data, calculate…", "Identify the organism/medium in the photo and justify…").
- **Depth expected** — do short-answer questions want 2 lines or 10? Infer from model answers.
- **Recurring structures** — e.g., every paper has one calculation, one diagram-ID, one compare/contrast. Predict the *slots*, then fill them with this year's likely content.
- **Distractor style** for MCQs — how the professor builds wrong options (common misconceptions, near-synonyms, unit traps).

Then generate predicted questions that mirror this style and phrasing, each with a model answer written to the depth the marks imply (a 2-mark answer ≠ a 10-mark answer).

**No past papers?** Choose question shapes from the discipline archetypes in §3a, and set depth from the exam format given at intake (MCQ / short answer / essay / OSPE) instead of model answers. Say plainly in the output that the phrasing is templated from common archetypes, not reverse-engineered from this professor's papers — the student should know that difference in certainty.

## 3a. Discipline question archetypes

When there's no past-paper style to reverse-engineer, use the question shapes that reliably recur in biology-family courses. Use them both to score *archetype fit* in §1a and to phrase the predicted question:

| Content shape in the material | Reliable question archetype |
|---|---|
| Named process/pathway with ordered steps | "Describe/outline the steps of X", step ordering, fill-the-blank |
| Two or more related structures/organisms/molecules | "Compare and contrast X and Y" |
| A structure or organism with a labeled diagram/photo | Spot/diagram labeling, "identify and justify" |
| A mechanism with a clear cause → effect chain | "Explain how X leads to Y", or "what would happen if…" |
| A formula or quantitative method (dilutions, CFU/mL, molarity, enzyme kinetics, statistics) | Calculation with a worked numeric example |
| A classification (types of X, categories of Y) | "List and describe the types of X", matching/table question |
| A named exception, limitation, or common error | Trap-style "what can go wrong / what is the exception" |
| A term with a precise technical definition (often **bold** on slides) | Straight definition, or MCQ with near-synonym distractors |
| An emphasized number, "not", "only", "except" (often red/underlined) | True/false or MCQ trap built on that exact detail |
| A slide titled "Objectives" / "Learning outcomes" | Treat each outcome as a near-literal draft question — professors often write these as the skeleton they examine from |

If a concept fits no archetype, it's usually lower priority even if it scores well elsewhere — note that rather than forcing an artificial question.

## 4. Parsing professor transcripts (Arabic & code-switched)

Transcripts are often spoken Arabic with English technical terms mixed in. Read them for meaning, then surface spoken exam cues. Output stays English; attribute as "professor's verbal emphasis."

**Arabic exam-cue phrases to scan for** (dialectal variants included):

| Arabic cue | Meaning | Treat as |
|---|---|---|
| ده مهم للامتحان / دي مهمة في الامتحان | this is important for the exam | HIGH signal |
| هييجي في الامتحان / ده جاي / متوقع ييجي | this is coming in the exam | HIGH signal |
| ركزوا على / خدوا بالكم من | focus on / pay attention to | HIGH/MEDIUM |
| لازم تعرفوا / لازم تعرفوا دي | you must know this | HIGH signal |
| متوقع سؤال / في سؤال على ده | expect a question on this | HIGH signal |
| احفظوا / دي محفوظة | memorize this | must-memorize |
| ده أساسي / دي نقطة أساسية | this is fundamental / key point | MEDIUM/HIGH |
| النقطة دي مهمة | this point is important | MEDIUM |
| اللي فات ده مش مهم / سيبوا ده | skip this / not important | de-prioritize |

**English cues** (for English transcripts): "important for the exam," "this will be on the test," "you must know this," "expect a question," "key concept for the exam," "focus your study on," "the most critical part here for the exam is," "guaranteed," "exam alert."

When a cue fires, capture: the exact topic it points to, translate/paraphrase the professor's statement into English, and log it as a prediction signal with its topic linked back to the relevant slide.

## 5. Faithfulness rule

- Default: build only from the student's sources; preserve the professor's exact terminology, naming, and phrasing (do not "correct" it into standard textbook language — the exam grades *their* terms).
- Outside knowledge is permitted **only** when a concept is (a) central to the material and (b) mentioned/repeated by slides or professor but explained too poorly to study from. In that case add the minimum clarification and mark it explicitly, e.g. `[Outside-source clarification: …]` in the HTML "outside" style. Never let external content dominate a section or introduce topics the professor never raised.
- If asked to verify a fact against the live web, do it only on explicit request; by default web search is OFF because the exam tests the professor's material, not the literature.
