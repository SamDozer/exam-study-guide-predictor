#!/usr/bin/env python3
"""Make phone photos and scans of exam papers and handwritten notes readable.

For each photo (or each page of a scanned PDF) it writes several differently
processed versions, because each one fails on different damage (shadows,
glare, faint pencil, coloured ink, blur, tilt), plus a quality report that
says what is wrong with the photo. Read the page in more than one version and
compare — see references/reading-images.md.

    python enhance_scan.py photo1.jpg scanned_exam.pdf --out scans/
        [--no-warp] [--tiles auto|RxC|0] [--max-side 3000] [--pdf-dpi 200]

PDFs: for each page, the original embedded photo is pulled out at its full
resolution (like `pdfimages -all`); pages without one are rendered at --pdf-dpi.

Per photo / page, in scans/<name>/ (read in this order):
    01_page.jpg            page found, flattened (perspective) and deskewed
    02_flat_color.jpg      shadows / uneven light removed, ink colours kept
    03_contrast.png        grayscale with local contrast (CLAHE)
    04_faint_boost.png     darkened + strong contrast, for faint pencil / faded ink
    05_bw_sauvola.png      black & white, Sauvola threshold (best for handwriting)
    06_bw_adaptive.png     black & white, adaptive Gaussian threshold (second opinion)
    07_sharp.jpg           sharpened colour, for slightly blurred photos
    ink_red.png            red / pink ink (grader ticks, scores, corrections), found by hue
    ink_<colour>.png       other ink colours when there is more than one (blue pen, pencil…)
    tiles/                 overlapping zoomed crops (small images are upscaled first)
    contact_sheet.jpg      all versions side by side
    report.json            source, resolution, quality checks, warnings, file list

Checks reported: resolution, blur, darkness, ink-vs-paper contrast, glare
(bright colourless patches brighter than the paper), something covering the
page (e.g. a finger), moiré / screen pattern, text running off an edge, tilt.

Requires: opencv-python-headless, numpy  (pip install opencv-python-headless numpy)
PDFs also need pymupdf. HEIC photos need pillow + pillow-heif, or convert them first.

Techniques (independent implementations of standard methods): four-corner
perspective correction; projection-profile deskew; background division for
shadow removal; CLAHE; Sauvola binarization; k-means ink-colour separation
(the idea behind mzucker/noteshrink).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
except ImportError:
    sys.exit("needs OpenCV and numpy: pip install opencv-python-headless numpy")

LOW_RES = 1000          # long side below this: warn, small writing may be unreadable
WORK_MIN = 1400         # small images are upscaled to at least this for processing


def odd(n: float) -> int:
    n = int(n)
    return n if n % 2 else n + 1


# ---------------------------------------------------------------- loading

def load_image(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)  # applies EXIF orientation
    if img is None:
        try:  # HEIC and other formats through Pillow, if available
            from PIL import Image, ImageOps
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except ImportError:
                pass
            pil = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(f"cannot read {path} ({exc}); convert it to JPG or PNG") from exc
    return img


def _pix_to_bgr(pix) -> np.ndarray:
    arr = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 1:
        return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
    if pix.n == 4:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def _extract_xref(doc, xref, fitz) -> np.ndarray | None:
    try:
        data = doc.extract_image(xref)["image"]
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            return img
    except Exception:  # noqa: BLE001
        pass
    try:
        pix = fitz.Pixmap(doc, xref)
        if pix.n - pix.alpha >= 4:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        if pix.alpha:
            pix = fitz.Pixmap(pix, 0)
        return _pix_to_bgr(pix)
    except Exception:  # noqa: BLE001
        return None


def _match_orientation(page, rect, img: np.ndarray) -> np.ndarray:
    """Rotate an extracted image to how it is displayed on the page (compares with a small render)."""
    ref = cv2.cvtColor(_pix_to_bgr(page.get_pixmap(clip=rect, dpi=36)), cv2.COLOR_BGR2GRAY).astype(np.float32)
    if min(ref.shape) < 8:
        return img
    best, best_score = img, -2.0
    for k in range(4):
        cand = np.ascontiguousarray(np.rot90(img, k))
        g = cv2.resize(cv2.cvtColor(cand, cv2.COLOR_BGR2GRAY), (ref.shape[1], ref.shape[0]),
                       interpolation=cv2.INTER_AREA).astype(np.float32)
        a, b = g - g.mean(), ref - ref.mean()
        score = float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-6))
        aspect_ok = (cand.shape[1] >= cand.shape[0]) == (ref.shape[1] >= ref.shape[0])
        score += 0.2 if aspect_ok else -0.2
        if score > best_score:
            best, best_score = cand, score
    return best


def load_pdf(path: Path, dpi: int) -> list[tuple[str, np.ndarray, str]]:
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz  # older PyMuPDF releases
        except ImportError:
            sys.exit("reading PDFs needs PyMuPDF: pip install pymupdf")
    doc = fitz.open(path)
    out = []
    for pno, page in enumerate(doc, start=1):
        name = f"{path.stem}_p{pno}"
        parea = page.rect.width * page.rect.height
        best = None
        for info in page.get_images(full=True):
            try:
                rects = page.get_image_rects(info[0])
            except Exception:  # noqa: BLE001
                continue
            for r in rects:
                cover = fitz.Rect(r).intersect(page.rect).get_area() / parea
                if best is None or cover > best[0]:
                    best = (cover, info[0], fitz.Rect(r).intersect(page.rect))
        # A page with no text layer is just a photo on a blank sheet: take the photo even when it
        # covers only part of the page (rendering would hand page detection an empty margin).
        min_cover = 0.15 if not page.get_text().strip() else 0.5
        if best and best[0] >= min_cover:
            img = _extract_xref(doc, best[1], fitz)
            if img is not None:
                img = _match_orientation(page, best[2], img)
                out.append((name, img, f"embedded photo, original {img.shape[1]}x{img.shape[0]} px"))
                continue
        out.append((name, _pix_to_bgr(page.get_pixmap(dpi=dpi)), f"page rendered at {dpi} dpi (no embedded photo)"))
    return out


def load_inputs(path: Path, pdf_dpi: int) -> list[tuple[str, np.ndarray, str]]:
    if path.suffix.lower() == ".pdf":
        return load_pdf(path, pdf_dpi)
    return [(path.stem, load_image(path), "photo")]


# ---------------------------------------------------------------- page / perspective / skew

def order_corners(pts: np.ndarray) -> np.ndarray:
    pts = pts.reshape(4, 2).astype("float32")
    s, d = pts.sum(1), np.diff(pts, axis=1).ravel()
    return np.array([pts[s.argmin()], pts[d.argmin()], pts[s.argmax()], pts[d.argmax()]], dtype="float32")


def find_page(img: np.ndarray) -> np.ndarray | None:
    """Return the 4 page corners (in img coordinates) or None."""
    h, w = img.shape[:2]
    k = 900 / max(h, w)
    small = cv2.resize(img, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
    gray = cv2.GaussianBlur(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    area = small.shape[0] * small.shape[1]
    candidates = []
    edges = cv2.dilate(cv2.Canny(gray, 40, 140), np.ones((3, 3), np.uint8), iterations=2)
    _, bright = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    for mask in (edges, bright):
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:5]:
            if cv2.contourArea(c) < 0.25 * area:
                break
            approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
            if len(approx) == 4 and cv2.isContourConvex(approx):
                candidates.append(approx)
                break
    if not candidates:
        return None
    best = max(candidates, key=cv2.contourArea)
    if cv2.contourArea(best) > 0.98 * area:  # the "page" is just the whole frame
        return None
    return order_corners(best) / k


def warp(img: np.ndarray, corners: np.ndarray) -> np.ndarray:
    tl, tr, br, bl = corners
    w = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    h = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")
    return cv2.warpPerspective(img, cv2.getPerspectiveTransform(corners, dst), (w, h), flags=cv2.INTER_CUBIC)


def text_mask(gray: np.ndarray) -> np.ndarray:
    """Character-sized dark marks only (drops page edges, background, big blobs)."""
    h, w = gray.shape
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV,
                               odd(max(15, max(h, w) // 40)), 15)
    n, cc, st, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    keep = ((st[:, cv2.CC_STAT_HEIGHT] < 0.08 * h) & (st[:, cv2.CC_STAT_WIDTH] < 0.3 * w)
            & (st[:, cv2.CC_STAT_AREA] >= 4))
    keep[0] = False
    return keep[cc] & (bw > 0)


def estimate_skew(img: np.ndarray) -> float:
    """Text-line angle in degrees (projection profile); rotating by it makes lines horizontal."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    k = 1000 / max(gray.shape)
    if k < 1:
        gray = cv2.resize(gray, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    ys, xs = np.nonzero(text_mask(gray))
    if len(xs) < 300:
        return 0.0
    xs = xs - xs.mean()
    ys = ys - ys.mean()

    def score(a: float) -> float:
        t = np.deg2rad(a)
        y2 = -xs * np.sin(t) + ys * np.cos(t)
        hist = np.bincount((y2 - y2.min()).astype(np.int64))
        return float((hist.astype(np.float64) ** 2).sum())

    coarse = max(np.arange(-15, 15.01, 0.5), key=score)
    fine = max(np.arange(coarse - 0.5, coarse + 0.51, 0.1), key=score)
    return round(float(fine), 1)


def rotate_bound(img: np.ndarray, angle: float) -> np.ndarray:
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    cos, sin = abs(m[0, 0]), abs(m[0, 1])
    nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
    m[0, 2] += nw / 2 - w / 2
    m[1, 2] += nh / 2 - h / 2
    # fill the new corners with the paper colour (copying edge pixels smears streaks)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    paper_px = img[gray >= np.percentile(gray, 80)]
    fill = tuple(int(c) for c in np.median(paper_px, axis=0)) if len(paper_px) else (255, 255, 255)
    return cv2.warpAffine(img, m, (nw, nh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT,
                          borderValue=fill)


def ink_fraction(img: np.ndarray) -> float:
    """Share of the image covered by character-sized dark marks (≈0 means blank)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    k = 1000 / max(gray.shape)
    if k < 1:
        gray = cv2.resize(gray, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    return float(text_mask(gray).mean())


# ---------------------------------------------------------------- enhancement

def flatten_illumination(img: np.ndarray) -> np.ndarray:
    """Divide each channel by its estimated paper background: removes shadows, keeps ink colour."""
    long_side = max(img.shape[:2])
    k = odd(max(15, long_side // 60))  # wider than any pen stroke
    out = np.empty_like(img)
    for i in range(3):
        ch = img[:, :, i]
        bg = cv2.medianBlur(cv2.dilate(ch, np.ones((k, k), np.uint8)), odd(min(255, 2 * k + 1)))
        out[:, :, i] = np.clip(ch.astype(np.float32) / np.maximum(bg, 1) * 255.0, 0, 255).astype(np.uint8)
    return stretch(out)


def stretch(img: np.ndarray, lo: float = 0.5, hi: float = 99.5) -> np.ndarray:
    a, b = np.percentile(img, (lo, hi))
    if b - a < 1:
        return img
    return np.clip((img.astype(np.float32) - a) * 255.0 / (b - a), 0, 255).astype(np.uint8)


def sauvola(gray: np.ndarray, window: int, k: float = 0.2, r: float = 128.0) -> np.ndarray:
    g = gray.astype(np.float64)
    mean = cv2.boxFilter(g, -1, (window, window), borderType=cv2.BORDER_REPLICATE)
    sq = cv2.boxFilter(g * g, -1, (window, window), borderType=cv2.BORDER_REPLICATE)
    std = np.sqrt(np.maximum(sq - mean * mean, 0))
    thresh = mean * (1 + k * (std / r - 1))
    return np.where(g > thresh, 255, 0).astype(np.uint8)


def colour_name(lab_center) -> str:
    """Name an ink colour. Uses Lab chroma first: HSV saturation is unreliable for dark ink."""
    lum, a, b = (float(x) for x in lab_center)
    chroma = float(np.hypot(a - 128, b - 128))
    if chroma < 20 or (lum < 80 and chroma < 30):
        return "black" if lum < 110 else "pencil-grey"
    bgr = cv2.cvtColor(np.uint8([[lab_center]]), cv2.COLOR_LAB2BGR)[0, 0]
    hue = int(cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0, 0, 0]) * 2
    # red pen often reads as pink once its edges blend with the paper, so pink counts as red
    for limit, name in ((15, "red"), (40, "orange"), (70, "yellow"), (160, "green"),
                        (200, "cyan"), (260, "blue"), (295, "purple"), (361, "red")):
        if hue < limit:
            return name
    return "red"


def red_ink(flat: np.ndarray) -> np.ndarray:
    """Red / pink marks (grader ticks, scores, corrections) found directly by hue."""
    hsv = cv2.cvtColor(flat, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(flat, cv2.COLOR_BGR2LAB).astype(np.int16)
    chroma = np.hypot(lab[:, :, 1] - 128, lab[:, :, 2] - 128)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    # Loose on purpose: red pen fades to pink and thin lines in phone photos. No erosion,
    # because thin ticks would disappear.
    return ((h <= 12) | (h >= 155)) & (s >= 35) & (v >= 50) & (chroma >= 15)


def ink_layers(flat: np.ndarray, binary: np.ndarray, max_k: int = 4) -> dict[str, np.ndarray]:
    """One layer per ink colour, each = that ink in black on white.

    Red is detected directly by hue (grader marks are often light and thin);
    the remaining inks are grouped by k-means, and every connected stroke gets
    the colour most of its pixels have.
    """
    masks: dict[str, np.ndarray] = {}
    red = red_ink(flat)
    if red.sum() >= 30:
        masks["red"] = red
    ink = (binary == 0) & ~red
    n = int(ink.sum())
    if n >= 200:
        lab = cv2.cvtColor(flat, cv2.COLOR_BGR2LAB)
        pixels = lab[ink].astype(np.float32)
        sample = pixels[np.random.default_rng(0).choice(n, min(n, 60000), replace=False)]
        k = min(max_k, len(sample))
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
        _, _, centers = cv2.kmeans(sample, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
        labels = np.linalg.norm(pixels[:, None, :] - centers[None, :, :], axis=2).argmin(1)
        n_cc, cc = cv2.connectedComponents(ink.astype(np.uint8), connectivity=8)
        comp = cc[ink]
        votes = np.bincount(comp * k + labels, minlength=n_cc * k).reshape(n_cc, k)
        comp_label = votes.argmax(1)
        # Tiny marks (i-dots, decimal points, minus signs) take the colour of the nearest stroke.
        sizes = votes.sum(1)
        big = sizes >= max(12, int(0.00004 * binary.size))
        big[0] = False
        if big.any() and (~big[1:]).any():
            big_px = big[cc] & ink
            _, nearest = cv2.distanceTransformWithLabels((~big_px).astype(np.uint8), cv2.DIST_L2, 5,
                                                         labelType=cv2.DIST_LABEL_PIXEL)
            ys, xs = np.nonzero(big_px)
            seed_label = np.zeros(nearest.max() + 1, np.int64)
            seed_label[nearest[ys, xs]] = comp_label[cc[ys, xs]]
            pix_label = comp_label[cc].copy()
            small_px = ink & ~big[cc]
            pix_label[small_px] = seed_label[nearest[small_px]]
            labels = pix_label[ink]
        else:
            labels = comp_label[comp]
        for i, c in enumerate(centers):
            if float((labels == i).mean()) < 0.03:
                continue
            name = colour_name(c)
            m = np.zeros(binary.shape, bool)
            m[ink] = labels == i
            masks[name] = masks.get(name, np.zeros(binary.shape, bool)) | m
    if len(masks) < 2 and "red" not in masks:  # a single ink colour: the B/W versions already show it
        return {}
    layers = {}
    for name, m in masks.items():
        layer = np.full(binary.shape, 255, np.uint8)
        layer[m] = 0
        layers[name] = layer
    return layers


# ---------------------------------------------------------------- quality checks

def where(mask: np.ndarray) -> str:
    ys, xs = np.nonzero(mask)
    h, w = mask.shape
    cy, cx = ys.mean() / h, xs.mean() / w
    v = "top" if cy < 0.33 else "bottom" if cy > 0.67 else "middle"
    hz = "left" if cx < 0.33 else "right" if cx > 0.67 else "centre"
    return f"{v}-{hz}"


def check_glare(img: np.ndarray) -> tuple[float, str | None]:
    """Blown-out, colourless patches clearly brighter than the paper. Clean white scans don't count."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    s, v = hsv[:, :, 1], hsv[:, :, 2]
    paper = float(np.percentile(v, 75))
    if paper >= 238:  # paper already near white (scan or bright photo): glare can't be told apart
        return 0.0, None
    mask = ((v >= 248) & (s <= 40) & (v.astype(np.int16) >= paper + 12)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, cc, st, _ = cv2.connectedComponentsWithStats(mask)
    keep = st[:, cv2.CC_STAT_AREA] >= 0.001 * mask.size
    keep[0] = False
    blobs = keep[cc]
    frac = float(blobs.mean())
    return round(frac, 4), (where(blobs) if frac > 0 else None)


def check_occlusion(img: np.ndarray) -> tuple[float, str | None]:
    """A large skin-coloured blob touching the edge: usually a finger or hand over the page."""
    ycc = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = ycc[:, :, 0], ycc[:, :, 1], ycc[:, :, 2]
    mask = ((cr >= 138) & (cr <= 178) & (cb >= 80) & (cb <= 125) & (y >= 50)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, cc, st, _ = cv2.connectedComponentsWithStats(mask)
    h, w = mask.shape
    best = np.zeros(mask.shape, bool)
    for i in range(1, n):
        x, yy, bw, bh, area = st[i]
        touches = x == 0 or yy == 0 or x + bw >= w or yy + bh >= h
        solid = area / float(bw * bh) > 0.35
        if touches and solid and area >= 0.01 * mask.size:
            best |= cc == i
    frac = float(best.mean())
    return round(frac, 4), (where(best) if frac > 0 else None)


def check_moire(gray: np.ndarray, n: int = 512) -> float:
    """How sharply one fine-grained frequency stands out from its neighbours (screen photos, halftone moiré).

    Measured on full-resolution crops: shrinking the page first would filter the pattern out.
    Text, even very regular text, spreads its energy; a moiré pattern is a narrow spike.
    """
    h, w = gray.shape
    if min(h, w) < n:
        gray = cv2.resize(gray, (max(w, n), max(h, n)), interpolation=cv2.INTER_CUBIC)
        h, w = gray.shape
    yy, xx = np.mgrid[-n // 2:n // 2, -n // 2:n // 2]
    r = np.hypot(yy, xx)
    band = (r > 0.25 * n / 2) & (r < 0.95 * n / 2) & (np.abs(xx) > 6) & (np.abs(yy) > 6)
    window = np.outer(np.hanning(n), np.hanning(n))
    best = 0.0
    for fy, fx in ((1 / 3, 1 / 3), (1 / 3, 2 / 3), (2 / 3, 1 / 3), (2 / 3, 2 / 3), (1 / 2, 1 / 2)):
        y0 = int(min(h - n, max(0, fy * h - n / 2)))
        x0 = int(min(w - n, max(0, fx * w - n / 2)))
        g = gray[y0:y0 + n, x0:x0 + n].astype(np.float32)
        mag = np.abs(np.fft.fftshift(np.fft.fft2((g - g.mean()) * window)))
        spike = np.where(band, mag / (cv2.blur(mag, (15, 15)) + 1e-6), 0)
        best = max(best, float(spike.max()))
    return round(best, 1)


def check_edges(binary: np.ndarray) -> list[str]:
    """Edges where several character-sized marks touch the border: text probably cut off."""
    h, w = binary.shape
    n, cc, st, _ = cv2.connectedComponentsWithStats((binary == 0).astype(np.uint8), connectivity=8)
    x, y, bw, bh, area = st[:, 0], st[:, 1], st[:, 2], st[:, 3], st[:, 4]
    text = (bh >= 0.004 * h) & (bh <= 0.06 * h) & (bw <= 0.25 * w) & (area >= max(6, 0.00001 * h * w))
    text[0] = False
    hits = {"left": (x == 0), "right": (x + bw >= w), "top": (y == 0), "bottom": (y + bh >= h)}
    return [edge for edge, m in hits.items() if int((m & text).sum()) >= 2]


def quality(native: np.ndarray, page: np.ndarray, binary: np.ndarray, skew: float,
            page_found: bool, warp_tried: bool, residual: float = 0.0) -> tuple[dict, list[str]]:
    gray_native = cv2.cvtColor(native, cv2.COLOR_BGR2GRAY)
    k = 1000 / max(gray_native.shape)
    g = cv2.resize(gray_native, None, fx=k, fy=k, interpolation=cv2.INTER_AREA) if k < 1 else gray_native
    gp = cv2.cvtColor(page, cv2.COLOR_BGR2GRAY)
    paper = float(np.percentile(gp, 90))
    ink = float(np.percentile(gp, 1))
    glare, glare_at = check_glare(page)
    occl, occl_at = check_occlusion(page)
    moire = check_moire(gp)
    edges = check_edges(binary)
    long_side = max(native.shape[:2])
    q = {"long_side_px": int(long_side), "blur": round(float(cv2.Laplacian(g, cv2.CV_64F).var()), 1),
         "paper_level": round(paper, 1), "ink_contrast": round(paper - ink, 1),
         "glare": glare, "covered": occl, "moire": moire, "skew_deg": skew, "text_at_edges": edges}
    warn = []
    if long_side < LOW_RES:
        warn.append(f"low resolution ({native.shape[1]}x{native.shape[0]} px): small writing may be unreadable "
                    "and the blur score is unreliable at this size; ask for the original photo "
                    "(not a screenshot or WhatsApp copy) and read from the zoomed tiles")
    elif q["blur"] < 60:
        warn.append("very blurry: ask for a retake (hold steady, tap to focus, more light)")
    elif q["blur"] < 150:
        warn.append("somewhat blurry: use 07_sharp and the tiles; double-check every number")
    if paper < 120:
        warn.append("dark photo: rely on 02_flat_color and 04_faint_boost")
    if q["ink_contrast"] < 70:
        warn.append("low ink contrast (faint pencil or faded print): rely on 04_faint_boost and 05_bw_sauvola")
    if glare >= 0.003:
        warn.append(f"glare at {glare_at} ({glare:.1%} of the page): text there may be washed out; "
                    "ask for a retake without flash if words are missing")
    if occl > 0:
        warn.append(f"something covers part of the page at {occl_at} (finger or hand?): "
                    "text under it is missing, mark it [illegible]")
    if moire >= 20:
        warn.append("moiré / screen pattern detected (photo of a screen or halftone): "
                    "fine detail may be distorted; ask for the original file if possible")
    elif moire >= 8:
        warn.append("possible moiré / screen pattern: check small characters closely in the tiles")
    if edges:
        warn.append(f"text touches the {', '.join(edges)} edge: words there may be cut off; "
                    "mark partial words [cut off] and ask for a wider photo")
    if abs(skew) > 3 and abs(residual) > 2:
        warn.append(f"page tilted {skew:+.1f} deg and only partly corrected (about {abs(residual):.0f} deg remains: "
                    "the page was also photographed at an angle); lines near the edges are the least reliable")
    elif abs(skew) > 3:
        warn.append(f"page tilted {skew:+.1f} deg (corrected in these versions); check lines near the edges")
    if not page_found and warp_tried:
        warn.append("page edges not found: perspective not corrected (fine for flat scans/screenshots)")
    return q, warn


# ---------------------------------------------------------------- outputs

def tiles(img: np.ndarray, spec: str) -> list[tuple[str, np.ndarray]]:
    """Overlapping zoomed crops. Small images are upscaled first, so they always get tiles."""
    if spec == "0":
        return []
    h, w = img.shape[:2]
    up = min(3.0, max(1.0, 1800 / max(h, w)))
    if up > 1:
        img = cv2.resize(img, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC)
        h, w = img.shape[:2]
    if spec == "auto":  # ~1000 px tiles; vision models downscale whole pages
        cols, rows = max(1, round(w / 1000)), max(1, round(h / 1000))
    else:
        rows, cols = (int(x) for x in spec.lower().split("x"))
    if rows * cols == 1:
        return [("full", img)]
    ov = 0.12
    th, tw = int(h / (rows - (rows - 1) * ov)), int(w / (cols - (cols - 1) * ov))
    out = []
    for r in range(rows):
        for c in range(cols):
            y0 = min(int(r * th * (1 - ov)), h - th)
            x0 = min(int(c * tw * (1 - ov)), w - tw)
            out.append((f"r{r + 1}c{c + 1}", img[y0:y0 + th, x0:x0 + tw]))
    return out


def contact_sheet(items: list[tuple[str, np.ndarray]], width: int = 420) -> np.ndarray:
    thumbs = []
    for name, im in items:
        im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR) if im.ndim == 2 else im
        t = cv2.resize(im, (width, int(im.shape[0] * width / im.shape[1])), interpolation=cv2.INTER_AREA)
        bar = np.full((28, width, 3), 40, np.uint8)
        cv2.putText(bar, name, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        thumbs.append(np.vstack([bar, t]))
    hmax = max(t.shape[0] for t in thumbs)
    thumbs = [np.vstack([t, np.full((hmax - t.shape[0], width, 3), 255, np.uint8)]) for t in thumbs]
    rows = [np.hstack(thumbs[i:i + 4] + [np.full((hmax, width, 3), 255, np.uint8)] * (4 - len(thumbs[i:i + 4])))
            for i in range(0, len(thumbs), 4)]
    return np.vstack(rows)


def process(name: str, native: np.ndarray, source: str, out_root: Path, args) -> dict:
    img = native
    h, w = img.shape[:2]
    if max(h, w) > args.max_side:
        s = args.max_side / max(h, w)
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    elif max(h, w) < WORK_MIN:  # small images: upscale so the filters work at a sensible scale
        s = min(3.0, WORK_MIN / max(h, w))
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_CUBIC)

    notes = []
    corners = None if args.no_warp else find_page(img)
    page = warp(img, corners) if corners is not None else img
    img_ink = ink_fraction(img)
    if corners is not None and img_ink > 0.0005 and ink_fraction(page) < 0.25 * img_ink:
        # the detected "page" is an empty area (e.g. the white margin above a photo): ignore it
        corners, page = None, img
        notes.append("page detection picked an empty area; redone on the whole photo")
    skew = estimate_skew(page)
    residual = 0.0
    if 0.7 <= abs(skew) <= 15:
        page = rotate_bound(page, skew)
        residual = estimate_skew(page)
    if ink_fraction(page) < 0.0005:
        notes.append("OUTPUT LOOKS BLANK: no writing was found on this page. Check the original photo "
                     "before treating the page as empty; never skip it silently")

    flat = flatten_illumination(page)
    gray = cv2.cvtColor(flat, cv2.COLOR_BGR2GRAY)
    long_side = max(gray.shape)
    contrast = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    darker = np.clip(255.0 * (gray / 255.0) ** 1.8, 0, 255).astype(np.uint8)
    faint = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8)).apply(darker)
    bw_s = sauvola(gray, odd(max(25, long_side // 40)))
    bw_a = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                                 odd(max(25, long_side // 50)), 12)
    sharp = cv2.addWeighted(flat, 1.7, cv2.GaussianBlur(flat, (0, 0), 2.5), -0.7, 0)
    inks = ink_layers(flat, bw_s)
    q, warnings = quality(native, page, bw_s, skew, corners is not None, not args.no_warp, residual)
    warnings = notes + warnings
    q["skew_remaining_deg"] = residual

    d = out_root / name
    (d / "tiles").mkdir(parents=True, exist_ok=True)
    variants = [("01_page.jpg", page), ("02_flat_color.jpg", flat), ("03_contrast.png", contrast),
                ("04_faint_boost.png", faint), ("05_bw_sauvola.png", bw_s), ("06_bw_adaptive.png", bw_a),
                ("07_sharp.jpg", sharp)] + [(f"ink_{n}.png", m) for n, m in inks.items()]
    written = []
    for fname, im in variants:
        params = [cv2.IMWRITE_JPEG_QUALITY, 92] if fname.endswith(".jpg") else []
        cv2.imwrite(str(d / fname), im, params)
        written.append(fname)
    for tname, t in tiles(flat, args.tiles):
        cv2.imwrite(str(d / "tiles" / f"flat_{tname}.jpg"), t, [cv2.IMWRITE_JPEG_QUALITY, 92])
        written.append(f"tiles/flat_{tname}.jpg")
    cv2.imwrite(str(d / "contact_sheet.jpg"), contact_sheet([(n, im) for n, im in variants]),
                [cv2.IMWRITE_JPEG_QUALITY, 85])
    written.append("contact_sheet.jpg")

    report = {"name": name, "source": source, "folder": str(d),
              "native_size": [int(native.shape[1]), int(native.shape[0])], "page_found": corners is not None,
              "size": [int(page.shape[1]), int(page.shape[0])], "skew_deg": skew, "deskewed": 0.7 <= abs(skew) <= 15,
              "quality": q, "warnings": warnings, "ink_colors": list(inks), "outputs": written}
    (d / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+", type=Path, help="photos (jpg/png/heic…) and/or scanned PDFs")
    ap.add_argument("--out", type=Path, default=Path("scans"))
    ap.add_argument("--no-warp", action="store_true", help="skip page detection (flat scans, screenshots)")
    ap.add_argument("--tiles", default="auto", help="auto, RxC (e.g. 3x2), or 0 for none")
    ap.add_argument("--max-side", type=int, default=3000)
    ap.add_argument("--pdf-dpi", type=int, default=200, help="render dpi for PDF pages with no embedded photo")
    ap.add_argument("--json", action="store_true", help="print the reports as JSON")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    reports, inputs = [], []
    for p in a.images:
        pages = load_inputs(p, a.pdf_dpi)
        inputs.append({"file": str(p), "pages": len(pages)})
        for name, img, source in pages:
            reports.append(process(name, img, source, a.out, a))

    # Coverage inventory: every source page must come out, and blank outputs are listed by name,
    # so a lost page can't disappear silently. The ledger must have the same page count.
    pages_in = sum(i["pages"] for i in inputs)
    blank = [r["name"] for r in reports if any(w.startswith("OUTPUT LOOKS BLANK") for w in r["warnings"])]
    flagged = [r["name"] for r in reports if r["warnings"]]
    inventory = {"inputs": inputs, "pages_in": pages_in, "pages_processed": len(reports),
                 "pages": [r["name"] for r in reports], "blank": blank, "with_warnings": flagged,
                 "ok": pages_in == len(reports) and not blank}
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "_inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    summary = (f"COVERAGE: {pages_in} source pages in, {len(reports)} processed, {len(blank)} blank"
               + (f" ({', '.join(blank)})" if blank else "")
               + f", {len(flagged)} with quality warnings. The ledger must list all {pages_in} pages.")
    if a.json:
        print(json.dumps(reports, indent=2))
        print(summary, file=sys.stderr)
        return
    for r in reports:
        q = r["quality"]
        print(f"{r['name']} ({r['source']}) -> {r['folder']}")
        print(f"  {q['long_side_px']} px | page found: {r['page_found']} | skew {r['skew_deg']:+.1f} deg | "
              f"blur {q['blur']} | ink contrast {q['ink_contrast']} | glare {q['glare']:.2%}")
        if r["ink_colors"]:
            print(f"  ink colours: {', '.join(r['ink_colors'])}")
        for w in r["warnings"]:
            print(f"  ! {w}")
        print(f"  {len(r['outputs'])} files; start with contact_sheet.jpg, then 02_flat_color.jpg and 05_bw_sauvola.png")
    print(summary)
    if not inventory["ok"]:
        print("STOP: fix the blank or missing pages above before building the ledger.")


if __name__ == "__main__":
    main()
