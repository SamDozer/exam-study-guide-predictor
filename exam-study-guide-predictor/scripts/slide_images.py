#!/usr/bin/env python3
"""Turn lecture slides into compressed images for the study guide's slide cards.

Renders the chosen pages of a lecture PDF (export PowerPoint to PDF first) to
JPEGs small enough to embed, and writes a slide-card HTML stub for each one
(image as a data URI + a caption skeleton to fill in).

    python slide_images.py "Lecture 1.pdf" --pages 2,4,7-10,30 --lecture 1 --out slides/
        [--width 1400] [--quality 78] [--no-html]

Outputs in --out:
    L1_s030.jpg            the slide image
    L1_s030.html           <figure class="fig"> stub with the image embedded
    manifest.json          [{lecture, slide, file, bytes, width, height, text}]
The page's own text is included in the manifest so captions can quote the
slide's exact wording.

Keep only slides that earn their place: diagrams, labelled structures, life
cycles, tables, and slides that were asked about. A text-only slide is usually
better summarised than pictured. Aim for <= ~120 KB per image.

Requires: pymupdf, opencv-python-headless, numpy.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    sys.exit("needs OpenCV and numpy: pip install opencv-python-headless numpy")


def parse_pages(spec: str, n: int) -> list[int]:
    pages: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = (int(x) for x in part.split("-", 1))
            pages.update(range(a, b + 1))
        else:
            pages.add(int(part))
    bad = [p for p in pages if p < 1 or p > n]
    if bad:
        sys.exit(f"pages out of range 1-{n}: {sorted(bad)}")
    return sorted(pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--pages", default="all", help="e.g. 2,4,7-10 (1-based); default all")
    ap.add_argument("--lecture", default="1", help="lecture number or short name used in labels")
    ap.add_argument("--out", type=Path, default=Path("slides"))
    ap.add_argument("--width", type=int, default=1400, help="image width in px (1200-1600 reads well)")
    ap.add_argument("--quality", type=int, default=78, help="JPEG quality")
    ap.add_argument("--no-html", action="store_true", help="skip the slide-card HTML stubs")
    a = ap.parse_args()
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz  # older PyMuPDF releases
        except ImportError:
            sys.exit("needs PyMuPDF: pip install pymupdf")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    doc = fitz.open(a.pdf)
    pages = list(range(1, len(doc) + 1)) if a.pages == "all" else parse_pages(a.pages, len(doc))
    a.out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for n in pages:
        page = doc[n - 1]
        zoom = a.width / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        arr = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
        img = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR) if pix.n == 3 else cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, a.quality, cv2.IMWRITE_JPEG_OPTIMIZE, 1])
        name = f"L{a.lecture}_s{n:03d}"
        (a.out / f"{name}.jpg").write_bytes(buf.tobytes())
        text = " ".join(page.get_text().split())
        manifest.append({"lecture": a.lecture, "slide": n, "file": f"{name}.jpg", "bytes": len(buf),
                         "width": int(img.shape[1]), "height": int(img.shape[0]), "text": text})
        if not a.no_html:
            uri = "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()
            alt = html.escape(text[:120] or f"Lecture {a.lecture} slide {n}", quote=True)
            stub = (f'<figure class="fig"><img src="{uri}" alt="{alt}">\n'
                    f'<figcaption><span class="src">LECTURE {html.escape(str(a.lecture))} · SLIDE {n} · [TOPIC]</span>'
                    f'[Exam angle: what is tested here and how. Decode every label/number below.]\n'
                    f'<dl class="labels"><dt>[label]</dt><dd>[meaning]</dd></dl>\n</figcaption></figure>\n')
            (a.out / f"{name}.html").write_text(stub, encoding="utf-8")
    (a.out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    total = sum(m["bytes"] for m in manifest)
    print(f"{len(manifest)} slides -> {a.out} ({total / 1024:.0f} KB total, "
          f"{total / max(1, len(manifest)) / 1024:.0f} KB each)")
    big = [m["file"] for m in manifest if m["bytes"] > 160_000]
    if big:
        print(f"! large images (>160 KB): {', '.join(big)}: lower --width or --quality, or drop text-only slides")


if __name__ == "__main__":
    main()
