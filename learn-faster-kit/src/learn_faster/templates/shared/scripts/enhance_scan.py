#!/usr/bin/env python3
"""Make phone photos of exam papers and handwritten notes readable.

For each photo it writes several differently-processed versions, because each
one fails on different damage (shadows, glare, faint pencil, coloured ink,
blur). Read the page in more than one version and compare — see
references/reading-images.md.

    python enhance_scan.py photo1.jpg photo2.png --out scans/
        [--no-warp] [--tiles auto|RxC|0] [--max-side 3000]

Per photo, in scans/<name>/ (read in this order):
    01_page.jpg            orientation fixed, page found and flattened (perspective)
    02_flat_color.jpg      shadows / uneven light removed, ink colours kept
    03_contrast.png        grayscale with local contrast (CLAHE)
    04_faint_boost.png     darkened + strong contrast, for faint pencil / faded ink
    05_bw_sauvola.png      black & white, Sauvola threshold (best for handwriting)
    06_bw_adaptive.png     black & white, adaptive Gaussian threshold (second opinion)
    07_sharp.jpg           sharpened colour, for slightly blurred photos
    ink_<colour>.png       one layer per ink colour found (e.g. blue pen, red marking, pencil)
    tiles/                 overlapping zoomed crops of 02 for small handwriting
    contact_sheet.jpg      all versions side by side
    report.json            quality scores, warnings, ink colours, file list

Requires: opencv-python-headless, numpy  (pip install opencv-python-headless numpy)
HEIC photos also need pillow + pillow-heif, or convert them to JPG first.

Techniques (independent implementations of standard methods): four-corner
perspective correction; background division for shadow removal; CLAHE;
Sauvola binarization; k-means ink-colour separation (the idea behind
mzucker/noteshrink).
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


def odd(n: float) -> int:
    n = int(n)
    return n if n % 2 else n + 1


# ---------------------------------------------------------------- loading

def load(path: Path, max_side: int) -> np.ndarray:
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
    h, w = img.shape[:2]
    scale = max_side / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


# ---------------------------------------------------------------- page / perspective

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


def hue_name(bgr) -> str:
    hsv = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0, 0]
    h, s, v = int(hsv[0]) * 2, int(hsv[1]), int(hsv[2])
    if s < 50 or v < 60:
        return "black" if v < 90 else "pencil-grey"
    # red pen often reads as pink once its edges blend with the paper, so pink counts as red
    for limit, name in ((15, "red"), (40, "orange"), (70, "yellow"), (160, "green"),
                        (200, "cyan"), (260, "blue"), (295, "purple"), (361, "red")):
        if h < limit:
            return name
    return "red"


def ink_layers(flat: np.ndarray, binary: np.ndarray, max_k: int = 4) -> dict[str, np.ndarray]:
    """Split ink pixels into colour groups; each layer = that ink in black on white."""
    ink = binary == 0
    n = int(ink.sum())
    if n < 200:
        return {}
    lab = cv2.cvtColor(flat, cv2.COLOR_BGR2LAB)
    pixels = lab[ink].astype(np.float32)
    sample = pixels[np.random.default_rng(0).choice(n, min(n, 60000), replace=False)]
    k = min(max_k, len(sample))
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    _, _, centers = cv2.kmeans(sample, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    dists = np.linalg.norm(pixels[:, None, :] - centers[None, :, :], axis=2)
    labels = dists.argmin(1)
    # Anti-aliased stroke edges blend with the paper and land in the wrong colour
    # group, so give every connected stroke the colour most of its pixels have.
    n_cc, cc = cv2.connectedComponents(ink.astype(np.uint8), connectivity=8)
    comp = cc[ink]
    votes = np.bincount(comp * k + labels, minlength=n_cc * k).reshape(n_cc, k)
    comp_label = votes.argmax(1)
    # Tiny marks (i-dots, decimal points, minus signs) are too small to vote
    # reliably: give each the colour of the nearest real stroke, so "0.25"
    # never loses its point in a colour layer.
    sizes = votes.sum(1)
    small_lim = max(12, int(0.00004 * binary.size))
    big = sizes >= small_lim
    big[0] = False
    if big.any() and (~big[1:]).any():
        big_px = big[cc] & ink
        _, nearest = cv2.distanceTransformWithLabels((~big_px).astype(np.uint8), cv2.DIST_L2, 5,
                                                     labelType=cv2.DIST_LABEL_PIXEL)
        ys, xs = np.nonzero(big_px)
        seed_label = np.zeros(nearest.max() + 1, np.int64)
        seed_label[nearest[ys, xs]] = comp_label[cc[ys, xs]]
        small_px = ink & ~big[cc]
        pix_label = comp_label[cc].copy()
        pix_label[small_px] = seed_label[nearest[small_px]]
        labels = pix_label[ink]
    else:
        labels = comp_label[comp]
    masks: dict[str, np.ndarray] = {}
    for i, c in enumerate(centers):
        if float((labels == i).mean()) < 0.03:
            continue
        bgr = cv2.cvtColor(np.uint8([[c]]), cv2.COLOR_LAB2BGR)[0, 0]
        name = hue_name(bgr)
        m = np.zeros(binary.shape, bool)
        m[ink] = labels == i
        masks[name] = masks.get(name, np.zeros(binary.shape, bool)) | m
    if len(masks) < 2:  # a single ink colour: the B/W versions already show it
        return {}
    layers = {}
    for name, m in masks.items():
        layer = np.full(binary.shape, 255, np.uint8)
        layer[m] = 0
        layers[name] = layer
    return layers


# ---------------------------------------------------------------- quality

def quality(img: np.ndarray) -> tuple[dict, list[str]]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    k = 1000 / max(gray.shape)
    g = cv2.resize(gray, None, fx=k, fy=k, interpolation=cv2.INTER_AREA) if k < 1 else gray
    q = {"blur": round(float(cv2.Laplacian(g, cv2.CV_64F).var()), 1),
         "brightness": round(float(g.mean()), 1),
         "contrast": round(float(g.std()), 1),
         "glare": round(float((g >= 250).mean()), 3)}
    warn = []
    if q["blur"] < 60:
        warn.append("very blurry: ask for a retake (hold steady, tap to focus, more light)")
    elif q["blur"] < 150:
        warn.append("somewhat blurry: use 07_sharp and the tiles; double-check every number")
    if q["brightness"] < 90:
        warn.append("dark photo: rely on 02_flat_color and 04_faint_boost")
    if q["glare"] > 0.04:
        warn.append("glare / blown-out areas: text there may be lost; ask for a retake without flash if words are missing")
    if q["contrast"] < 30:
        warn.append("low contrast (faint pencil or faded print): rely on 04_faint_boost and 05_bw_sauvola")
    return q, warn


# ---------------------------------------------------------------- outputs

def tiles(img: np.ndarray, spec: str) -> list[tuple[str, np.ndarray]]:
    h, w = img.shape[:2]
    if spec == "0":
        return []
    if spec == "auto":  # aim for ~900 px tiles; vision models downscale whole pages
        cols = max(1, round(w / 900))
        rows = max(1, round(h / 900))
        if rows * cols == 1:
            return []
    else:
        rows, cols = (int(x) for x in spec.lower().split("x"))
    ov = 0.12
    th, tw = int(h / (rows - (rows - 1) * ov)), int(w / (cols - (cols - 1) * ov))
    out = []
    for r in range(rows):
        for c in range(cols):
            y0 = min(int(r * th * (1 - ov)), h - th)
            x0 = min(int(c * tw * (1 - ov)), w - tw)
            t = img[y0:y0 + th, x0:x0 + tw]
            if max(t.shape[:2]) < 1000:
                t = cv2.resize(t, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            out.append((f"r{r + 1}c{c + 1}", t))
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


def process(path: Path, out_root: Path, args) -> dict:
    img = load(path, args.max_side)
    corners = None if args.no_warp else find_page(img)
    page = warp(img, corners) if corners is not None else img
    q, warnings = quality(page)
    if corners is None and not args.no_warp:
        warnings.append("page edges not found: perspective not corrected (fine for flat scans/screenshots)")

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

    d = out_root / path.stem
    (d / "tiles").mkdir(parents=True, exist_ok=True)
    variants = [("01_page.jpg", page), ("02_flat_color.jpg", flat), ("03_contrast.png", contrast),
                ("04_faint_boost.png", faint), ("05_bw_sauvola.png", bw_s), ("06_bw_adaptive.png", bw_a),
                ("07_sharp.jpg", sharp)] + [(f"ink_{n}.png", m) for n, m in inks.items()]
    written = []
    for name, im in variants:
        params = [cv2.IMWRITE_JPEG_QUALITY, 92] if name.endswith(".jpg") else []
        cv2.imwrite(str(d / name), im, params)
        written.append(name)
    for name, t in tiles(flat, args.tiles):
        cv2.imwrite(str(d / "tiles" / f"flat_{name}.jpg"), t, [cv2.IMWRITE_JPEG_QUALITY, 92])
        written.append(f"tiles/flat_{name}.jpg")
    cv2.imwrite(str(d / "contact_sheet.jpg"), contact_sheet([(n, im) for n, im in variants]),
                [cv2.IMWRITE_JPEG_QUALITY, 85])
    written.append("contact_sheet.jpg")

    report = {"file": str(path), "folder": str(d), "page_found": corners is not None,
              "size": [int(page.shape[1]), int(page.shape[0])], "quality": q, "warnings": warnings,
              "ink_colors": list(inks), "outputs": written}
    (d / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=Path("scans"))
    ap.add_argument("--no-warp", action="store_true", help="skip page detection (flat scans, screenshots)")
    ap.add_argument("--tiles", default="auto", help="auto, RxC (e.g. 3x2), or 0 for none")
    ap.add_argument("--max-side", type=int, default=3000)
    ap.add_argument("--json", action="store_true", help="print the reports as JSON")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    reports = [process(p, a.out, a) for p in a.images]
    if a.json:
        print(json.dumps(reports, indent=2))
        return
    for r in reports:
        q = r["quality"]
        print(f"{r['file']} -> {r['folder']}")
        print(f"  page found: {r['page_found']} | blur {q['blur']} | brightness {q['brightness']} "
              f"| contrast {q['contrast']} | glare {q['glare']}")
        if r["ink_colors"]:
            print(f"  ink colours: {', '.join(r['ink_colors'])}")
        for w in r["warnings"]:
            print(f"  ! {w}")
        print(f"  {len(r['outputs'])} files; start with contact_sheet.jpg, then 02_flat_color.jpg and 05_bw_sauvola.png")


if __name__ == "__main__":
    main()
