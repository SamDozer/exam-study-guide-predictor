"""Repository-level checks: kit/skill sync, Anki importer, emphasis extractor.

Run from the repo root:  python -m pytest tests
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "exam-study-guide-predictor" / "scripts"


def run(*args, **kw):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", **kw)


def test_kit_references_in_sync():
    r = run(ROOT / "tools" / "sync_kit.py", "--check")
    assert r.returncode == 0, r.stdout + r.stderr


def test_skill_frontmatter_fits_upload_limits():
    text = (ROOT / "exam-study-guide-predictor" / "SKILL.md").read_text(encoding="utf-8")
    front = text.split("---")[1]
    name = next(l.split(":", 1)[1].strip() for l in front.splitlines() if l.startswith("name:"))
    desc_lines = front.split("description:", 1)[1].splitlines()[1:]
    description = " ".join(l.strip() for l in desc_lines if l.startswith("  "))
    assert name == "exam-study-guide-predictor"
    assert 0 < len(description) <= 1024, f"description is {len(description)} chars (claude.ai limit 1024)"


def test_skill_references_exist():
    skill = (ROOT / "exam-study-guide-predictor" / "SKILL.md").read_text(encoding="utf-8")
    for ref in ["references/prediction-and-analysis.md", "references/output-format.md",
                "references/solving-layer.md", "references/spaced-repetition.md",
                "references/reading-images.md", "scripts/extract_emphasis.py",
                "scripts/anki_import.py", "scripts/enhance_scan.py"]:
        assert ref in skill, f"SKILL.md never mentions {ref}"
        assert (ROOT / "exam-study-guide-predictor" / ref).exists(), ref


# ---------------------------------------------------------------- Anki importer

class FakeAnki(BaseHTTPRequestHandler):
    decks: list = []
    existing_fronts = {"Already there?"}
    added: list = []

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        p, a = req.get("params", {}), req["action"]
        result = {
            "version": lambda: 6,
            "modelNames": lambda: ["Basic", "Cloze"],
            "deckNames": lambda: self.decks,
            "canAddNotes": lambda: [n["fields"]["Front"] not in self.existing_fronts for n in p["notes"]],
            "createDeck": lambda: self.decks.append(p["deck"]) or 1,
            "addNotes": lambda: [self.added.append(n) or i + 100 for i, n in enumerate(p["notes"])],
        }[a]()
        body = json.dumps({"result": result, "error": None}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@pytest.fixture
def anki():
    FakeAnki.decks, FakeAnki.added = ["Default", "Exams::Bio"], []
    srv = HTTPServer(("127.0.0.1", 0), FakeAnki)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


@pytest.fixture
def cards_csv(tmp_path):
    p = tmp_path / "flashcards.csv"
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_ALL)
        w.writerow(["Front", "Back", "Tags"])
        w.writerow(["Give reason: PFK-1 is rate-limiting.", "First committed step.<br>L3 s12", "bio,l3,high"])
        w.writerow(["Already there?", "yes", "bio"])
        w.writerow(["Define glycolysis.", "Glucose → 2 pyruvate.", ""])
    return p


def test_anki_dry_run_adds_nothing(anki, cards_csv):
    r = run(SCRIPTS / "anki_import.py", cards_csv, "--deck", "Exams::Bio", "--url", anki)
    assert r.returncode == 0, r.stderr
    assert "2 new, 1 already in Anki" in r.stdout and "Dry run" in r.stdout
    assert FakeAnki.added == []


def test_anki_push_adds_new_cards_with_tags(anki, cards_csv):
    r = run(SCRIPTS / "anki_import.py", cards_csv, "--deck", "Exams::Bio", "--url", anki,
            "--push", "--tags", "dr ahmed")
    assert r.returncode == 0, r.stderr
    assert "Added 2 cards" in r.stdout
    fronts = [n["fields"]["Front"] for n in FakeAnki.added]
    assert fronts == ["Give reason: PFK-1 is rate-limiting.", "Define glycolysis."]
    assert FakeAnki.added[0]["tags"] == ["bio", "dr-ahmed", "high", "l3"]
    assert FakeAnki.added[1]["tags"] == ["dr-ahmed"]


def test_anki_unreachable_falls_back(cards_csv):
    r = run(SCRIPTS / "anki_import.py", cards_csv, "--deck", "X", "--url", "http://127.0.0.1:9")
    assert r.returncode != 0
    assert "cannot reach AnkiConnect" in r.stderr and "import" in r.stderr.lower()


# ---------------------------------------------------------------- phone-photo enhancer

def make_degraded_photo(path: Path) -> None:
    """A tilted exam page on a dark desk, with a shadow, blue pen, red marking, faint pencil, blur, JPEG."""
    import cv2
    import numpy as np

    page = np.full((1400, 1000, 3), 238, np.uint8)
    font = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
    cv2.putText(page, "Q1 Give reason: PFK-1 is rate limiting", (40, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (30, 30, 30), 2)
    for i, line in enumerate(["It catalyses the committed step", "inhibited by ATP and citrate", "activated by AMP"]):
        cv2.putText(page, line, (60, 230 + 90 * i), font, 1.6, (170, 60, 20), 3)           # blue pen (BGR)
    cv2.putText(page, "3/5", (800, 230), font, 2.2, (30, 30, 210), 4)                       # red marking
    cv2.putText(page, "see lecture 3 slide 12", (60, 600), font, 1.4, (150, 150, 150), 2)  # faint pencil
    canvas = np.full((2000, 1600, 3), (40, 55, 70), np.uint8)                                # dark desk
    src = np.float32([[0, 0], [999, 0], [999, 1399], [0, 1399]])
    dst = np.float32([[260, 180], [1300, 260], [1380, 1820], [180, 1700]])
    m = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(page, m, (1600, 2000))
    mask = cv2.warpPerspective(np.full((1400, 1000), 255, np.uint8), m, (1600, 2000))
    canvas[mask > 0] = warped[mask > 0]
    shade = np.tile(np.linspace(1.0, 0.45, 1600, dtype=np.float32), (2000, 1))[:, :, None]  # shadow across
    photo = np.clip(canvas * shade + np.random.default_rng(1).normal(0, 6, canvas.shape), 0, 255).astype(np.uint8)
    photo = cv2.GaussianBlur(photo, (3, 3), 0)
    cv2.imwrite(str(path), photo, [cv2.IMWRITE_JPEG_QUALITY, 70])


def test_enhance_scan_on_degraded_phone_photo(tmp_path):
    pytest.importorskip("cv2")
    import cv2
    import numpy as np

    photo = tmp_path / "exam_photo.jpg"
    make_degraded_photo(photo)
    r = run(SCRIPTS / "enhance_scan.py", photo, "--out", tmp_path / "scans", "--json")
    assert r.returncode == 0, r.stderr
    rep = json.loads(r.stdout)[0]
    assert rep["page_found"], rep
    for name in ["01_page.jpg", "02_flat_color.jpg", "03_contrast.png", "04_faint_boost.png",
                 "05_bw_sauvola.png", "06_bw_adaptive.png", "07_sharp.jpg", "contact_sheet.jpg"]:
        assert (tmp_path / "scans" / "exam_photo" / name).exists(), name
    # perspective corrected back to roughly the page's 1000x1400 portrait shape
    w, h = rep["size"]
    assert 1.25 < h / w < 1.55, rep["size"]
    # shadow removed: the paper is evenly bright left-to-right after flattening
    flat = cv2.imread(str(tmp_path / "scans" / "exam_photo" / "02_flat_color.jpg"), cv2.IMREAD_GRAYSCALE)
    left, right = np.median(flat[:, : w // 6]), np.median(flat[:, -w // 6:])
    assert abs(float(left) - float(right)) < 25, (left, right)
    # blue pen and red marking separated into their own layers
    assert "blue" in rep["ink_colors"] and "red" in rep["ink_colors"], rep["ink_colors"]


def test_enhance_scan_flags_blurry_photo(tmp_path):
    pytest.importorskip("cv2")
    import cv2

    photo = tmp_path / "blurry.jpg"
    make_degraded_photo(photo)
    cv2.imwrite(str(photo), cv2.GaussianBlur(cv2.imread(str(photo)), (0, 0), 6))
    rep = json.loads(run(SCRIPTS / "enhance_scan.py", photo, "--out", tmp_path / "s", "--json").stdout)[0]
    assert any("blurry" in w for w in rep["warnings"]), rep["warnings"]


def text_page(w: int = 1700, h: int = 2200, paper: int = 255, ink=(20, 20, 20), x0: int = 90,
              line: str = "The enzyme catalyses the committed step of glycolysis 0.25 mM"):
    """A plain printed page (a clean scan when paper=255)."""
    import cv2
    import numpy as np

    page = np.full((h, w, 3), paper, np.uint8)
    words = line.split()
    for i, y in enumerate(range(150, h - 120, 70)):
        text = " ".join(words[i % len(words):] + words[:i % len(words)])  # vary lines like a real page
        cv2.putText(page, f"{i + 1}. {text}", (x0, y), cv2.FONT_HERSHEY_SIMPLEX, 1.25, ink, 2, cv2.LINE_AA)
    return page


def scan_report(tmp_path: Path, img, name: str, *extra) -> dict:
    import cv2

    p = tmp_path / f"{name}.png"
    cv2.imwrite(str(p), img)
    r = run(SCRIPTS / "enhance_scan.py", p, "--out", tmp_path / "scans", "--json", *extra)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)[0]


def warned(rep: dict, word: str) -> bool:
    return any(word in w for w in rep["warnings"])


def test_scan_clean_scan_raises_no_false_alarms(tmp_path):
    pytest.importorskip("cv2")
    rep = scan_report(tmp_path, text_page(), "clean", "--no-warp")
    assert rep["warnings"] == [], rep["warnings"]
    assert rep["quality"]["glare"] == 0 and abs(rep["skew_deg"]) < 0.7


def test_scan_detects_real_glare_not_white_paper(tmp_path):
    pytest.importorskip("cv2")
    import cv2

    img = text_page(paper=200)
    cv2.ellipse(img, (1200, 900), (260, 170), 20, 0, 360, (255, 255, 255), -1)
    img = cv2.GaussianBlur(img, (0, 0), 3)
    rep = scan_report(tmp_path, img, "glare", "--no-warp")
    assert warned(rep, "glare"), rep["warnings"]


def test_scan_detects_finger_over_page(tmp_path):
    pytest.importorskip("cv2")
    import cv2

    img = text_page(paper=215)
    cv2.ellipse(img, (900, 2200), (230, 420), 0, 0, 360, (130, 160, 205), -1)  # skin tone, from the bottom edge
    rep = scan_report(tmp_path, cv2.GaussianBlur(img, (0, 0), 2), "finger", "--no-warp")
    assert warned(rep, "covers part of the page"), rep["warnings"]


def test_scan_small_image_warns_and_still_gets_tiles(tmp_path):
    pytest.importorskip("cv2")
    import cv2

    small = cv2.resize(text_page(), (600, 776), interpolation=cv2.INTER_AREA)
    rep = scan_report(tmp_path, small, "small", "--no-warp")
    assert warned(rep, "low resolution"), rep["warnings"]
    assert any(o.startswith("tiles/") for o in rep["outputs"]), rep["outputs"]


def test_scan_finds_light_red_grader_marks(tmp_path):
    pytest.importorskip("cv2")
    import cv2

    img = text_page()
    for y in range(200, 1400, 300):  # light red ticks and a score
        cv2.line(img, (1450, y), (1480, y + 30), (90, 90, 235), 3)
        cv2.line(img, (1480, y + 30), (1540, y - 40), (90, 90, 235), 3)
    cv2.putText(img, "8/10", (1300, 1700), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (90, 90, 235), 3)
    rep = scan_report(tmp_path, img, "ticks", "--no-warp")
    assert "red" in rep["ink_colors"], rep["ink_colors"]
    assert "orange" not in rep["ink_colors"], rep["ink_colors"]


def test_scan_warns_when_text_runs_off_the_edge(tmp_path):
    pytest.importorskip("cv2")
    rep = scan_report(tmp_path, text_page(x0=700), "cutoff", "--no-warp")
    assert "right" in rep["quality"]["text_at_edges"], rep["quality"]
    assert warned(rep, "cut off")


def test_scan_measures_and_corrects_tilt(tmp_path):
    pytest.importorskip("cv2")
    import cv2

    img = text_page()
    m = cv2.getRotationMatrix2D((850, 1100), 6, 1.0)
    tilted = cv2.warpAffine(img, m, (1700, 2200), borderValue=(255, 255, 255))
    rep = scan_report(tmp_path, tilted, "tilt", "--no-warp")
    assert 5.0 <= abs(rep["skew_deg"]) <= 7.0, rep["skew_deg"]
    assert rep["deskewed"] and warned(rep, "tilted")
    page = cv2.imread(str(tmp_path / "scans" / "tilt" / "01_page.jpg"))
    sys.path.insert(0, str(SCRIPTS))
    import enhance_scan
    assert abs(enhance_scan.estimate_skew(page)) < 1.0


def test_scan_flags_moire_pattern(tmp_path):
    pytest.importorskip("cv2")
    import numpy as np

    img = text_page().astype(np.float32)
    yy, xx = np.mgrid[0:2200, 0:1700]
    img += (28 * np.sin(2 * np.pi * (0.21 * xx + 0.17 * yy)))[:, :, None]
    rep = scan_report(tmp_path, np.clip(img, 0, 255).astype(np.uint8), "moire", "--no-warp")
    assert warned(rep, "moir"), (rep["quality"]["moire"], rep["warnings"])


def test_scan_finds_faint_thin_pink_grader_marks(tmp_path):
    pytest.importorskip("cv2")
    import cv2

    img = text_page()
    cv2.line(img, (1450, 300), (1470, 320), (175, 150, 245), 1)   # faded pink tick, 1 px wide
    cv2.line(img, (1470, 320), (1510, 270), (175, 150, 245), 1)
    cv2.circle(img, (1480, 700), 28, (175, 150, 245), 1)          # circled score
    rep = scan_report(tmp_path, img, "faint_ticks", "--no-warp")
    assert "red" in rep["ink_colors"], rep["ink_colors"]


def test_scan_rejects_empty_area_picked_as_page(tmp_path):
    """Like the PDF page whose photo covers only part of it: the empty white margin must not win."""
    pytest.importorskip("cv2")
    import cv2
    import numpy as np

    canvas = np.full((3000, 2200, 3), 120, np.uint8)
    cv2.rectangle(canvas, (100, 80), (2100, 1350), (250, 250, 250), -1)           # big empty white area
    canvas[1450:2950, 300:1900] = cv2.resize(text_page(paper=230), (1600, 1500))  # the real page, smaller
    rep = scan_report(tmp_path, canvas, "margin")
    assert not any("BLANK" in w for w in rep["warnings"]), rep["warnings"]
    bw = cv2.imread(str(tmp_path / "scans" / "margin" / "05_bw_sauvola.png"), cv2.IMREAD_GRAYSCALE)
    assert (bw < 128).mean() > 0.005  # writing survived


def test_scan_warns_loudly_on_blank_output(tmp_path):
    pytest.importorskip("cv2")
    import numpy as np

    rep = scan_report(tmp_path, np.full((1600, 1200, 3), 235, np.uint8), "blank", "--no-warp")
    assert any("BLANK" in w for w in rep["warnings"]), rep["warnings"]


def test_scan_pdf_takes_partial_photo_on_textless_page(tmp_path):
    pytest.importorskip("cv2")
    pymupdf = pytest.importorskip("pymupdf")
    import cv2

    ok, jpg = cv2.imencode(".jpg", cv2.resize(text_page(paper=225), (900, 1160)))
    doc = pymupdf.open()
    p = doc.new_page(width=595, height=842)
    p.insert_image(pymupdf.Rect(150, 420, 445, 800), stream=jpg.tobytes())  # ~22% of the page
    pdf = tmp_path / "quiz.pdf"
    doc.save(pdf)
    r = run(SCRIPTS / "enhance_scan.py", pdf, "--out", tmp_path / "scans", "--json")
    rep = json.loads(r.stdout)[0]
    assert rep["source"].startswith("embedded photo") and rep["native_size"] == [900, 1160], rep
    assert not any("BLANK" in w for w in rep["warnings"]), rep["warnings"]


def test_scan_pdf_uses_embedded_photo_at_full_resolution(tmp_path):
    pytest.importorskip("cv2")
    pymupdf = pytest.importorskip("pymupdf")
    import cv2
    import numpy as np

    photo = cv2.resize(text_page(paper=225), (1200, 1553), interpolation=cv2.INTER_AREA)
    ok, jpg = cv2.imencode(".jpg", photo)
    doc = pymupdf.open()
    p1 = doc.new_page(width=595, height=770)                      # page = one embedded phone photo
    p1.insert_image(p1.rect, stream=jpg.tobytes())
    p2 = doc.new_page(width=595, height=842)                      # vector text only
    p2.insert_text((72, 100), "Typed question sheet", fontsize=14)
    # Phone photo stored sideways in the file, displayed upright by the PDF (common for scanner apps).
    ok, sideways = cv2.imencode(".jpg", np.ascontiguousarray(np.rot90(photo)))
    for rot in (90, 270):
        p3 = doc.new_page(width=595, height=770)
        p3.insert_image(p3.rect, stream=sideways.tobytes(), rotate=rot)
        pix = p3.get_pixmap(dpi=40)
        g = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, 0] < 128
        if g.sum(1).var() > g.sum(0).var():  # keep the rotation that displays text upright
            break
        doc.delete_page(-1)
    pdf = tmp_path / "exam.pdf"
    doc.save(pdf)

    r = run(SCRIPTS / "enhance_scan.py", pdf, "--out", tmp_path / "scans", "--json", "--no-warp")
    assert r.returncode == 0, r.stderr
    reps = {x["name"]: x for x in json.loads(r.stdout)}
    assert reps["exam_p1"]["source"].startswith("embedded photo") and reps["exam_p1"]["native_size"] == [1200, 1553]
    assert reps["exam_p2"]["source"].startswith("page rendered")
    assert reps["exam_p3"]["native_size"] == [1200, 1553], reps["exam_p3"]  # turned back upright
    bw = cv2.imread(str(tmp_path / "scans" / "exam_p3" / "05_bw_sauvola.png"), cv2.IMREAD_GRAYSCALE) < 128
    assert bw.sum(1).var() > bw.sum(0).var()  # text lines run horizontally: orientation restored


# ---------------------------------------------------------------- emphasis extractor

def test_emphasis_extractor_on_synthetic_pdf(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    doc = pymupdf.open()
    page = doc.new_page(width=720, height=540)
    for i in range(3):
        page.insert_text((40, 150 + 40 * i), "Plain body text that sets the normal style for this page.", fontsize=16)
    page.insert_text((40, 300), "rate-limiting step", fontsize=16, fontname="hebo")
    page.insert_text((40, 340), "phosphofructokinase-1", fontsize=16, color=(0.8, 0, 0))
    page.insert_text((40, 380), "student highlight", fontsize=16)
    page.add_highlight_annot(page.search_for("student highlight")[0])
    pdf = tmp_path / "l1.pdf"
    doc.save(pdf)

    out = run(SCRIPTS / "extract_emphasis.py", pdf, "--json")
    assert out.returncode == 0, out.stderr
    hits = {h["text"]: h["tags"] for h in json.loads(out.stdout)["hits"]}
    assert hits["rate-limiting step"] == ["BOLD"]
    assert hits["phosphofructokinase-1"][0].startswith("COLOR:red")
    assert hits["student highlight"] == ["ANNOT-HIGHLIGHT"]

    out = run(SCRIPTS / "extract_emphasis.py", pdf, "--json", "--ignore-annotations")
    assert "student highlight" not in {h["text"] for h in json.loads(out.stdout)["hits"]}
