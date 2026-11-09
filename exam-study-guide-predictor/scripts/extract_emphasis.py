#!/usr/bin/env python3
"""Extract visually emphasized text from lecture slides (PDF or PPTX).

Professors flag exam material through formatting: bold, underline, red or
other off-palette colours, highlighter marks. Plain text extraction throws all
of that away, so this script reads the formatting directly and lists every
phrase whose style differs from the document's normal body text.

Usage:
    python extract_emphasis.py SLIDES.pdf [MORE.pdf DECK.pptx ...]
        [--out emphasis.md] [--json] [--include-titles]
        [--render-dir DIR]   # render pages that have no text layer to PNG

Requires: pymupdf (PDF) and/or python-pptx (PPTX).
    pip install pymupdf python-pptx
"""
from __future__ import annotations

import argparse
import colorsys
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------- helpers

BOLD_NAME = re.compile(r"bold|black|heavy|semibold|demi", re.I)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def rgb_of(value: int) -> tuple[int, int, int]:
    return (value >> 16) & 255, (value >> 8) & 255, value & 255


def hexcol(rgb) -> str:
    return "#%02x%02x%02x" % tuple(rgb)


def color_name(rgb) -> str:
    r, g, b = (c / 255 for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s < 0.25 or v < 0.2:
        return "grey" if 0.2 <= v < 0.85 else ("white" if v >= 0.85 else "black")
    deg = h * 360
    for limit, name in ((15, "red"), (45, "orange"), (70, "yellow"),
                        (170, "green"), (200, "cyan"), (255, "blue"),
                        (290, "purple"), (345, "pink/magenta"), (361, "red")):
        if deg < limit:
            return name
    return "red"


def is_chromatic(rgb) -> bool:
    _, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    return s >= 0.25 and v >= 0.2


def color_differs(rgb, body) -> bool:
    """True when rgb reads as a deliberate accent colour against body text."""
    if rgb == body:
        return False
    dist = sum((a - b) ** 2 for a, b in zip(rgb, body)) ** 0.5
    if is_chromatic(rgb):
        if not is_chromatic(body):
            return True
        bh = colorsys.rgb_to_hsv(*(c / 255 for c in body))[0] * 360
        rh = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))[0] * 360
        hue_gap = min(abs(bh - rh), 360 - abs(bh - rh))
        return hue_gap > 30 or dist > 80
    return False  # greys/blacks/whites are template tones, not emphasis


class Hit:
    __slots__ = ("file", "loc", "text", "tags", "context")

    def __init__(self, file, loc, text, tags, context):
        self.file, self.loc, self.text = file, loc, text
        self.tags, self.context = tags, context

    def as_dict(self):
        return {"file": self.file, "location": self.loc, "text": self.text,
                "tags": sorted(self.tags), "context": self.context}


# ---------------------------------------------------------------- PDF

def scan_pdf(path: Path, include_titles: bool, render_dir: Path | None):
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz  # older PyMuPDF releases
        except ImportError:
            sys.exit("pymupdf is not installed: pip install pymupdf")

    doc = fitz.open(path)
    pages, color_chars, bold_chars, total_chars, sizes = [], Counter(), 0, 0, []
    no_text_pages = []

    for pno, page in enumerate(doc, start=1):
        spans = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                line_text = norm("".join(s["text"] for s in line["spans"]))
                for s in line["spans"]:
                    t = norm(s["text"])
                    if not t:
                        continue
                    bold = bool(s["flags"] & 16) or bool(BOLD_NAME.search(s["font"]))
                    rgb = rgb_of(s["color"])
                    spans.append({"text": t, "bbox": fitz.Rect(s["bbox"]), "bold": bold,
                                  "rgb": rgb, "size": s["size"], "line": line_text})
                    n = len(t)
                    total_chars += n
                    color_chars[rgb] += n
                    bold_chars += n if bold else 0
                    sizes.extend([s["size"]] * min(n, 50))
        if not spans:
            no_text_pages.append(pno)
            if render_dir:
                render_dir.mkdir(parents=True, exist_ok=True)
                page.get_pixmap(dpi=110).save(render_dir / f"{path.stem}_p{pno}.png")
        pages.append((page, spans))

    if total_chars == 0:
        return [], {"file": path.name, "note": "no text layer (scanned/image-only PDF)",
                    "no_text_pages": no_text_pages}

    body_rgb = color_chars.most_common(1)[0][0]
    body_size = statistics.median(sizes)
    bold_is_normal = bold_chars / total_chars > 0.5

    hits, seen_on_pages = [], defaultdict(set)
    for pno, (page, spans) in enumerate(pages, start=1):
        link_rects = [fitz.Rect(l["from"]) for l in page.get_links()]
        # thin horizontal strokes = drawn underlines
        strokes = []
        for d in page.get_drawings():
            for item in d["items"]:
                if item[0] == "l":
                    p1, p2 = item[1], item[2]
                    if abs(p1.y - p2.y) < 1.5:
                        strokes.append(fitz.Rect(min(p1.x, p2.x), p1.y - 1, max(p1.x, p2.x), p1.y + 1))
                elif item[0] == "re" and item[1].height < 2.5 and item[1].width > 4:
                    strokes.append(item[1])
        # annotation marks (highlighter / underline / squiggly)
        annot_marks = []
        for a in page.annots() or []:
            kind = {8: "HIGHLIGHT", 9: "UNDERLINE", 10: "UNDERLINE"}.get(a.type[0])
            if kind:
                annot_marks.append((a.rect, kind))

        page_h = page.rect.height
        for s in spans:
            r, tags = s["bbox"], set()
            if s["bold"] and not bold_is_normal:
                tags.add("BOLD")
            # hyperlinks are coloured/underlined by convention, not for emphasis
            in_link = any(r.intersects(lr) for lr in link_rects)
            if color_differs(s["rgb"], body_rgb) and not in_link:
                tags.add(f"COLOR:{color_name(s['rgb'])} {hexcol(s['rgb'])}")
            if not in_link:
                for st in strokes:
                    overlap = min(r.x1, st.x1) - max(r.x0, st.x0)
                    if r.y1 - 3 <= st.y0 <= r.y1 + 3 and overlap > 0.6 * r.width:
                        tags.add("UNDERLINE")
                        break
            for ar, kind in annot_marks:
                inter = r & ar
                if not inter.is_empty and inter.get_area() > 0.4 * r.get_area():
                    tags.add(kind)
            if not tags:
                continue
            is_title = s["size"] >= 1.3 * body_size and r.y0 < 0.25 * page_h
            if is_title and not include_titles:
                continue
            hits.append(Hit(path.name, f"p{pno}", s["text"], tags, s["line"]))
            seen_on_pages[s["text"].lower()].add(pno)

    # Drop template text (same styled text on most pages: headers, footers, logos)
    n_pages = len(pages)
    template = {k for k, v in seen_on_pages.items() if n_pages >= 4 and len(v) >= 0.6 * n_pages}
    hits = [h for h in hits if h.text.lower() not in template]
    hits = merge_adjacent(hits)
    meta = {"file": path.name, "pages": n_pages, "body_color": f"{color_name(body_rgb)} {hexcol(body_rgb)}",
            "body_size": round(body_size, 1), "bold_is_normal_text": bold_is_normal,
            "template_text_dropped": sorted(template), "no_text_pages": no_text_pages}
    return hits, meta


def merge_adjacent(hits):
    """Join consecutive spans on the same line that share the same tags."""
    out = []
    for h in hits:
        if out and out[-1].loc == h.loc and out[-1].tags == h.tags and out[-1].context == h.context:
            out[-1].text = norm(out[-1].text + " " + h.text)
        else:
            out.append(h)
    return out


# ---------------------------------------------------------------- PPTX

def scan_pptx(path: Path, include_titles: bool):
    try:
        from pptx import Presentation
        from pptx.enum.dml import MSO_COLOR_TYPE, MSO_THEME_COLOR
        from pptx.enum.shapes import PP_PLACEHOLDER
    except ImportError:
        sys.exit("python-pptx is not installed: pip install python-pptx")

    prs = Presentation(path)
    normal_theme = {MSO_THEME_COLOR.TEXT_1, MSO_THEME_COLOR.DARK_1, MSO_THEME_COLOR.BACKGROUND_1,
                    MSO_THEME_COLOR.LIGHT_1, MSO_THEME_COLOR.TEXT_2, MSO_THEME_COLOR.DARK_2}
    title_types = {PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.SUBTITLE}

    runs, rgb_chars = [], Counter()
    for sno, slide in enumerate(prs.slides, start=1):
        for shape in iter_shapes(slide.shapes):
            if not shape.has_text_frame:
                continue
            is_title = shape.is_placeholder and shape.placeholder_format.type in title_types
            for para in shape.text_frame.paragraphs:
                ptext = norm("".join(r.text for r in para.runs))
                for run in para.runs:
                    t = norm(run.text)
                    if not t:
                        continue
                    f = run.font
                    rgb, theme = None, None
                    if f.color is not None and f.color.type == MSO_COLOR_TYPE.RGB:
                        rgb = tuple(f.color.rgb)
                        rgb_chars[rgb] += len(t)
                    elif f.color is not None and f.color.type == MSO_COLOR_TYPE.SCHEME:
                        theme = f.color.theme_color
                    else:
                        rgb_chars["inherited"] += len(t)  # template default text colour
                    highlight = run._r.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}highlight") is not None
                    runs.append((sno, t, ptext, f.bold, f.underline, rgb, theme, highlight, is_title))

    # Body colour: whichever explicit colour covers more text than the inherited
    # template default; otherwise assume the usual dark body text.
    top = rgb_chars.most_common(1)[0][0] if rgb_chars else "inherited"
    body_rgb = (0, 0, 0) if top == "inherited" else top
    hits = []
    for sno, t, ptext, bold, underline, rgb, theme, highlight, is_title in runs:
        if is_title and not include_titles:
            continue
        tags = set()
        if bold:
            tags.add("BOLD")
        if underline:
            tags.add("UNDERLINE")
        if highlight:
            tags.add("HIGHLIGHT")
        if rgb is not None and color_differs(rgb, body_rgb):
            tags.add(f"COLOR:{color_name(rgb)} {hexcol(rgb)}")
        if theme is not None and theme not in normal_theme:
            tags.add(f"COLOR:theme {theme.name.lower()}")
        if tags:
            hits.append(Hit(path.name, f"slide {sno}", t, tags, ptext))
    meta = {"file": path.name, "slides": len(prs.slides),
            "body_color": f"{color_name(body_rgb)} {hexcol(body_rgb)}"}
    return merge_adjacent(hits), meta


def iter_shapes(shapes):
    for sh in shapes:
        if sh.shape_type == 6:  # group
            yield from iter_shapes(sh.shapes)
        else:
            yield sh


# ---------------------------------------------------------------- report

def report_md(all_hits, metas) -> str:
    lines = ["# Formatting-emphasis extraction", ""]
    for m in metas:
        lines.append(f"- **{m['file']}** — " + ", ".join(f"{k}: {v}" for k, v in m.items() if k != "file" and v not in ([], None)))
    lines += ["", "Tags: BOLD, UNDERLINE, HIGHLIGHT (highlighter annotation), COLOR:<name> <hex> "
              "(off-palette colour vs. the normal body text). Template text repeated on most pages is dropped.", ""]

    freq = Counter(h.text.lower() for h in all_hits)
    repeated = [(t, c) for t, c in freq.most_common() if c > 1]
    if repeated:
        lines += ["## Emphasized more than once (strongest formatting signal)", "",
                  "| Phrase | Times emphasized |", "|---|---|"]
        lines += [f"| {esc(t)} | {c} |" for t, c in repeated[:60]]
        lines.append("")

    lines += ["## All emphasized phrases", "", "| File | Where | Phrase | Tags | Line context |", "|---|---|---|---|---|"]
    for h in all_hits:
        ctx = h.context if h.context != h.text else ""
        lines.append(f"| {h.file} | {h.loc} | {esc(h.text)} | {', '.join(sorted(h.tags))} | {esc(ctx)[:160]} |")
    return "\n".join(lines) + "\n"


def esc(s: str) -> str:
    return s.replace("|", "\\|")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--include-titles", action="store_true")
    ap.add_argument("--render-dir", type=Path)
    a = ap.parse_args()

    all_hits, metas = [], []
    for f in a.files:
        ext = f.suffix.lower()
        if ext == ".pdf":
            hits, meta = scan_pdf(f, a.include_titles, a.render_dir)
        elif ext == ".pptx":
            hits, meta = scan_pptx(f, a.include_titles)
        else:
            print(f"skipping {f} (only .pdf and .pptx are supported)", file=sys.stderr)
            continue
        all_hits += hits
        metas.append(meta)

    if a.json:
        text = json.dumps({"files": metas, "hits": [h.as_dict() for h in all_hits]}, ensure_ascii=False, indent=1)
    else:
        text = report_md(all_hits, metas)
    if a.out:
        a.out.write_text(text, encoding="utf-8")
        print(f"wrote {a.out} ({len(all_hits)} emphasized phrases)")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
