"""HTML report (report.py), without QGIS.  python3 -m pytest tests/test_report.py -v"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "voro_teryt_qa"))
import report  # noqa: E402

META = {"Data kontroli": "2026-10-22 21:30", "Warstwa gmin": "gminy", "Liczba gmin": 2479}


def test_pass_report_says_no_findings():
    html = report.render([], {"c6_known_exceptions_applied": 1}, "PASS", META)
    assert html.startswith("<!doctype html>")
    assert 'class="status PASS"' in html
    assert "Brak znalezisk." in html
    assert "Czego ta kontrola nie sprawdza" in html


def test_counts_per_check_and_municipalities():
    findings = [
        {"check": "C5", "teryt": "0201011", "severity": "wysoka", "detail": "szczelina 12.0 m2"},
        {"check": "C5", "teryt": "0201011", "severity": "wysoka", "detail": "nakladanie z 0201022: 30.0 m2"},
        {"check": "C5", "teryt": "0201022", "severity": "wysoka", "detail": "nakladanie z 0201011: 30.0 m2"},
        {"check": "C4", "teryt": None, "severity": "krytyczna", "detail": "CRS EPSG:4326 zamiast EPSG:2180"},
    ]
    html = report.render(findings, {}, "REJECT", META, {"0201011": "Bolesławiec"})
    assert "C5 · Nakładania i szczeliny między gminami (3)" in html
    assert '<td class="n">3</td><td class="n">2</td>' in html  # C5: 3 findings, 2 municipalities
    assert "cały zbiór" in html
    assert "Bolesławiec" in html
    assert "gminy ze znaleziskami: <b>2</b>" in html


def test_html_is_escaped():
    findings = [{"check": "C6", "teryt": "0201011", "severity": "srednia",
                 "detail": "nazwa '<script>x</script>' != TERC 'A&B'"}]
    html = report.render(findings, {}, "REVIEW", META)
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html and "A&amp;B" in html


def test_polish_characters_survive_utf8(tmp_path):
    html = report.render([], {}, "PASS", {"Warstwa gmin": "gminy — Łódź, Gdańsk"})
    path = tmp_path / "r.html"
    path.write_text(html, encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    assert '<meta charset="utf-8">' in text and "Łódź, Gdańsk" in text


def test_status_text_covers_all_statuses():
    # 0.1.1: STATUS_TEXT is built from pairs (Bandit B105); the keys must stay the same
    assert set(report.STATUS_TEXT) == {"PASS", "REVIEW", "REJECT"}


def test_c7_row_and_border_diagnostics():
    findings = [{"check": "C7", "teryt": "0201011", "severity": "wysoka",
                 "detail": "kawalek Polski bez gminy: 6751.3 m2"}]
    diag = {"c7_pieces_total": 7438, "c7_known_exceptions_applied": 1}
    html = report.render(findings, diag, "REVIEW", META, params={"c7_border_tol_m2": 150.0})
    assert "C7 · Pokrycie granicy państwa (1)" in html
    assert "C7: użyte znane wyjątki (morze)" in html
    assert "C7: próg kawałka przy granicy państwa [m²]" in html
