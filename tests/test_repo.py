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


def test_skill_references_exist():
    skill = (ROOT / "exam-study-guide-predictor" / "SKILL.md").read_text(encoding="utf-8")
    for ref in ["references/prediction-and-analysis.md", "references/output-format.md",
                "references/solving-layer.md", "references/spaced-repetition.md",
                "scripts/extract_emphasis.py", "scripts/anki_import.py"]:
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
