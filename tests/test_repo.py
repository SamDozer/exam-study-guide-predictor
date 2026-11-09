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
