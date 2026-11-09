# Reading photos, scans, and handwriting — with verification

Past papers, model answers, and notes often arrive as phone photos: tilted, shadowed, blurred, faint pencil, several ink colours, Arabic and English mixed. A single misread word or digit poisons everything downstream (the ledger, the predictions, the model answers), so photos get a stricter process than typed files. Use it for **every** photographed or scanned page.

## 1. Enhance first

Run all photos at once:

```bash
python scripts/enhance_scan.py photo1.jpg photo2.jpg … --out scans
```

(needs `pip install opencv-python-headless numpy`; HEIC also needs `pillow pillow-heif`, or ask for JPG.) For each photo it writes, in `scans/<name>/`:

| File | What it fixes | Use it for |
|---|---|---|
| `01_page.jpg` | page found and flattened (perspective), orientation fixed | layout, where things are |
| `02_flat_color.jpg` | shadows and uneven light removed, colours kept | **main reading copy** |
| `03_contrast.png` | local contrast boost | dim or washed-out areas |
| `04_faint_boost.png` | darkened + strong contrast | faint pencil, faded photocopies |
| `05_bw_sauvola.png` | black & white tuned for handwriting | **second, independent reading** |
| `06_bw_adaptive.png` | black & white, different method | tie-breaker when 02 and 05 disagree |
| `07_sharp.jpg` | sharpened | slightly blurred photos |
| `ink_<colour>.png` | one layer per ink colour | **who wrote what** — not for reading text |
| `tiles/` | overlapping 2× zoomed crops | small handwriting, numbers, subscripts |
| `report.json` | blur, brightness, contrast, glare, warnings | deciding whether to ask for a retake |

If the script can't run, do the same reading passes on the original image and say so.

**Scanned PDFs:** pass the PDF itself (`python scripts/enhance_scan.py exam.pdf --out scans`, needs `pip install pymupdf`). For each page it pulls out the original embedded photo at full resolution, turned upright (like `pdfimages -all`), instead of a low-resolution render; pages without a photo are rendered at `--pdf-dpi` (default 200). Don't screenshot or re-render scanned pages yourself.

## 2. Check quality before reading

Read `report.json` / the printed warnings:

- **very blurry** or **glare** with words actually missing → ask the student for a retake of that page (tips in §7) before relying on it. Don't guess the missing words.
- **somewhat blurry** → read numbers and technical terms only from `07_sharp` and the tiles.
- **OUTPUT LOOKS BLANK** → stop. Open the original photo or PDF page yourself: a blank-looking result usually means the processing lost the page, not that the page is empty. Never drop a page from the ledger because its versions look blank.
- **low resolution** (long side under 1000 px) → read only from the tiles (small images are upscaled for them); treat every digit and short word as needing confirmation, and ask for the original photo.
- **glare at …** (bright colourless patches, not white paper) or **something covers part of the page** (finger, hand) → text there is missing: mark it `[illegible]`, never fill it in.
- **moiré / screen pattern** → the photo is of a screen or halftone; fine strokes may be distorted, double-check small characters.
- **text touches the … edge** → words there may be cut off: mark partial words `[cut off]` and don't treat a cut-off answer as a key.
- **page tilted** → already straightened in the versions; lines near the edges are the least reliable. **Only partly corrected** means the page was also photographed at an angle: treat words at the far edges as uncertain.
- **possible moiré** → weaker sign of a screen pattern; check small characters in the tiles.
- **ink_red.png** holds red/pink marks found by colour (grader ticks, scores, corrections) even when they're faint.
- **page edges not found** → fine for flat scans; for a tilted photo, read from `02` anyway and expect some distortion at the edges.

## 3. Read twice where it matters

Reading every page twice is slow and expensive. **Do the second, independent pass only when a page has a quality warning** (blur, low resolution, glare, covered, moiré, cut-off text, tilt, low contrast), **or when the page supplies an answer key or a fact behind a HIGH prediction.** Clean pages get one careful pass from `02_flat_color` (tiles for small writing), plus a re-check of every number, unit, and symbol (§4).

1. Look at `contact_sheet.jpg` to see which versions are clearest for this page.
2. **Pass 1** — transcribe from `02_flat_color.jpg`. If the handwriting is small, read from the tiles instead of the whole page (whole pages get downscaled before you see them; tiles don't).
3. **Pass 2** — transcribe again, independently, from `05_bw_sauvola.png` (or `04_faint_boost.png` for pencil, `07_sharp.jpg` for blur).
4. **Compare.** Where the two passes agree, mark the text as checked. Where they differ, look at `06` and the tile; if still unsure, write both readings: `[? "citrate" / "nitrate"]`. Never pick one silently.
5. **Ink colours for attribution.** Use the `ink_*` layers to separate the printed question, the student's answer (often blue/black), and the grader's marks (often red: scores, ticks, corrections). A red "3/5" next to an answer tells you the answer was only partly right — record it. Never read text *only* from an ink layer: very thin marks (hyphens, decimal points) can end up on the wrong layer.

## 3a. Whose answer is it? (before using anything as a key)

Handwritten answers on a past paper are often the **student's own**, and often wrong. Tag every answer before using it:

| Tag | Evidence | Use as key? |
|---|---|---|
| **official key** | professor's model answer, printed key, or posted solution | yes |
| **graded correct** | grader's tick, full marks, or score that confirms this specific answer | yes |
| **student's own** | handwriting with no grading, or marked wrong / partial | **no** — check it against the slides; flag disagreements |
| **derived from slides** | no answer on the paper; worked out from the course material | as a prediction, with its source tag |

Use the ink layers and the grader's marks as evidence, but red-ink detection can miss faint marks: when grading isn't clearly visible, tag the answer **student's own**. Never teach a student's ungraded answer as correct.

## 4. Character traps — check every one

Numbers, units, and symbols are where photos lie most. For each, confirm in at least two versions (or a tile):

- **Digits vs letters:** 1 / 7 / l / I · 0 / O / o · 5 / S · 2 / Z · 6 / b · 9 / g / q · 8 / B
- **Units and prefixes:** µ / u / m (µL vs mL is a 1000× error) · x / × · mg / mL · °C
- **Signs and points:** minus vs hyphen vs dash · decimal point vs comma vs speck of dust (`0.25` vs `025`) · `10⁵` vs `105` vs `10-5`
- **Sub- and superscripts:** H₂O, CO₂, Ca²⁺, NH₄⁺, 10⁻³ — check position, not just the digit
- **Greek:** α / a · β / B / ß · γ / y · λ / A · Δ / A / triangle · µ / u
- **Eastern Arabic digits** (common on Egyptian papers): ٠ ١ ٢ ٣ ٤ ٥ ٦ ٧ ٨ ٩ — ٥ (5) looks like a Latin 0, ٠ (0) is just a dot, ٦ (6) looks like a 7, and ٧ (7) and ٨ (8) are each other's mirror images
- **Arabic letters** that differ only by dots: ب ت ث ن ي · ج ح خ · د ذ · ر ز · س ش · ص ض · ط ظ · ع غ · ف ق — check the dots in the tiles

## 5. Verify spelling and science

Separate two different problems: **you misread the page** vs **the page itself is wrong**.

**Your reading:**
- Match every technical word against the course's own vocabulary (slides, booklet, glossary). A near-miss of a known term ("phosphofructokinse", "Rhizobuim") is almost always a reading or spelling slip: write the course spelling, and note `[read as: …]`.
- Re-compute every calculation on the page. If the arithmetic only works with a different digit (a 1 that is really a 7), re-check that digit in the tiles and note it.
- Check marks: question marks should add up to the paper's total; a grader's score can't exceed the question's marks.

**The page itself:**
- Keep the original wording **verbatim** in the past-paper ledger — the exam's exact phrasing matters, even when it's odd.
- If what's written is scientifically wrong (a classmate's note, an unofficial model answer, even a past paper), do not silently fix it. Record: **"Page says X → Course material says Y (L3 s12) → Follow Y for the exam."** It goes into the error-and-contradiction audit (`solving-layer.md` §12).
- Plausibility checks: units match the quantity; values sit in possible ranges (pH 0–14, percentages ≤ 100, absorbance usually < 3, temperatures sensible for the method); formulas are dimensionally consistent; ionic charges balance; genus capitalized and species lowercase (*Escherichia coli*); enzyme and organism names exist in the course material.
- Trust order for handwritten sources: the professor's own writing or official model answer > a graded past answer with the grader's marks > a classmate's notes.

## 6. Record confidence and report it

Every transcribed item in the ledger gets a reading status:

- **checked** — two versions agree;
- **corrected** — a slip fixed against course vocabulary or arithmetic, with `[read as: …]`;
- **uncertain** — `[? reading A / reading B]`;
- **illegible** — `[illegible]`.

In the deliverable, list every uncertain and illegible item with its photo and tile name (e.g. `Final 2023 p2, tiles/flat_r2c1`), so the student can check it on the paper or send a better photo. Predictions resting on an uncertain reading can't be HIGH until it's confirmed.

## 7. Tips to give the student for retakes

- Paper flat on a dark, plain surface; daylight or a bright room; **no flash** (it causes glare).
- Phone parallel to the page, page filling the frame, one page per photo.
- Tap the text to focus; hold still; make sure the phone's shadow isn't on the page.
- A scanner app (Google Drive scan, Microsoft Lens, iPhone Notes) gives cleaner input than the plain camera.
- Send the original photo, not a WhatsApp-compressed copy, when possible (WhatsApp shrinks images and blurs small writing).
