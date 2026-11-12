# Study-guide design (house style)

The default HTML deliverable follows one proven design, taken from a guide students rated the best so far (BtBio 413 midterm, `docs/examples/btbio-413-midterm/` in the repository). Start from `assets/guide-template.html`: it already contains the colours, layout, slide cards, plan, quiz engine, print layout and lightbox. Fill it; don't redesign it.

## 1. Section order

Keep this order and drop sections that have no real content (list them under "Checked and skipped"):

1. **Header** — course, exam, one-line "what will be asked, and how", every source used, what is out of scope, the colour legend.
2. **Tonight's plan** — time blocks with tick boxes (§5).
3. **Exam brief** — 2–4 stat tiles (marks and likely paper shape, past items per lecture, number of repeated questions), **how this professor writes questions** (stems, distractor habits, wording rules), and **where the past papers came from** (each paper's code, date, marks, layout, and key provenance: official key / graded copy / student answers).
4. **Repeated questions** — ranked by **distinct exam sittings** (versions and copies count once), each as the answer phrased as a fact, how it was asked, and the source codes on their own line.
5. **One section per lecture** — subsections per topic, each built around **slide cards** (§3) followed by must-know / professor's key / trap boxes, with low-yield detail collapsed.
6. **Comparison tables** — side-by-side rows of exactly the features questions are built on.
7. **Traps** — the swapped words and distractors, each with its fix.
8. **Past-paper bank** — every in-scope past question, interactive, with the accepted answer and why.
9. **Practice questions** — new questions in the professor's style, confidence-tagged, aimed at slide facts not asked yet.
10. **Last 30 minutes** — the decisive facts only, two columns.
11. **Help me improve** — the questions whose answers would change the prediction.

## 2. Colours: one meaning each, named after lab stains

| Token | Colour | Means | Used for |
|---|---|---|---|
| `giemsa` | purple | **the professor said it / official answer key** (fact) | `b-key` boxes, `t-key` source tags, label letters |
| `eosin` | rose-red | **repeated in past papers / HIGH prediction** | `b-hot`, `t-hot`, ×n counts |
| `methylene` | blue | **must know** (core facts) | `b-must`, `t-must`, rapid-sheet headings |
| `iodine` | amber | **trap / distractor** | `b-trap`, `t-trap`, ⚠ flags in answers |
| `extra` | grey | **low yield** | collapsed `details.extra` |
| dashed outline | — | **outside the slides** | `b-out`, `t-out`; never styled like course material |
| `ok` / `bad` | green / red | quiz feedback only | right / wrong answers |

Rules:
- A colour never changes meaning inside a guide or between guides. Purple is reserved for things that came from the professor (said, written, or keyed); a prediction is never purple.
- Every coloured element also has a word (MUST KNOW, TRAP, ×3, HIGH), so the meaning survives printing in black and white and colour-blind reading.
- Both themes are required (the template switches automatically with the device's dark mode). Check contrast in both.

## 3. Slide cards: the real slide, explained for the exam

This is the guide's most valuable part. For each slide that matters, show the slide itself and then explain what it means for the exam.

**Which slides get a card:** diagrams, labelled structures, life cycles, flow charts, tables, specimen photos, and any slide a past question was built on. Text-only bullet slides are usually summarised in a box instead of pictured. A lecture typically yields 10–25 cards.

**Making the images:** `python scripts/slide_images.py "Lecture 1.pdf" --pages 2,4,7-10,30 --lecture 1 --out slides/` renders those pages as compressed JPEGs (about 1400 px wide, about 120 KB each) and writes an HTML stub per slide with the image embedded and a caption skeleton. `manifest.json` includes each slide's own text, so captions can quote its exact wording. Export PowerPoints to PDF first.

**Caption anatomy** (in this order):
1. **Source line** — `LECTURE 1 · SLIDE 30 · HOW IT INVADES` (mono, muted). The slide number lets the student find it in the original.
2. **Exam angle** — one or two lines saying what is tested here and how, with the answerable words in bold. Add to the slide; never just transcribe it.
3. **Label decoding** — every letter, abbreviation or number on the diagram, decoded (`<dl class="labels">`: `AD` adhesive disk, `MB` median bodies…). For numbered steps (life cycles, invasion stages) use `<dl class="labels steps">`, which renders readable numbered badges, and mark the infective (▲i) and diagnostic (▲d) stages.
4. **Where it was asked** — source tags (`t-key`) on the facts that appeared in past papers.
5. **Honesty notes** — if the slide only lists names and the meaning comes from notes or a textbook, say so ("The slide only lists the names; the definitions below come from your notes"), and mark any label decoding that isn't on the slide as outside-source.

**Around the card:**
- Paired structures (cyst vs trophozoite, two species) go side by side in a `figrow`.
- After a card, add the boxes the slide feeds: `b-must` (must know), `b-key` (the professor's accepted answer, with its evidence), `b-hot` ("Tested: …" with ✓/✗ for each option of a past question), `b-trap`.
- Long lists, history, and numbers nobody asks about go into a collapsed `details.extra`.
- Every image gets real alt text describing what the slide shows.

## 4. Question banks

Fill the data arrays at the bottom of the template; the engine renders tap-to-answer cards.

- **MCQ** `{q, o, a, s, n, w, f}`: options in the paper's own order and wording; `s` = source codes; `n` = distinct sittings; `w` = why, citing the slide; `f` = a ⚠ flag for anything uncertain (an unusual key, a student-written answer, a typo in the source).
- **True/False** `{s, t, u, fix, src, w, f}`: for a false statement, `u` is the exact words to underline and `fix` the correction (most Egyptian papers ask for this).
- **Matching** `{title, rows, x}`: `x` holds the distractors, including the ones that recur every year.
- **Practice** questions add `c: "HIGH" | "MEDIUM" | "LOW"`.
- Only official keys and graded-correct answers may be used as the answer (`reading-images.md` §3a); a student's ungraded answer goes in `f` as a warning, never as `a`.

The engine shows correct / wrong / not tried out of the total, remembers answers across reloads, has **Retry wrong ones** and **Show all answers**, and prints with every answer visible.

## 5. Tonight's plan

- Build it from the **real current time** and the exam time; never a generic schedule.
- Blocks of 20–55 minutes, each saying exactly what to do and linking to the sections; breaks every 60–90 minutes; a sleep block with the reason not to skip it; after waking, one timed practice block and a final light review.
- Order: repeated questions first (cheap marks), then lectures by marks and weakness, then the bank by doing (not reading), then traps and retrying wrong answers.
- Add a fallback line ("if the exam is earlier than …, do only …").

## 6. Quality checks before delivering

- Repeat counts use distinct sittings; source tags sit on their own line or have a space before them.
- Every slide card has a source line, an exam angle, and decoded labels; numbered diagrams use the step badges.
- Every colour is used only for its meaning; nothing from outside the slides is styled as course material.
- File size: aim for under 6 MB. Compress or drop slides if it's bigger; it must open quickly on a phone.
- Open the file once in light and dark mode and at phone width before delivering (no horizontal scrolling except tables).
