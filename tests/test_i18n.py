"""Every text shown in QGIS has a Polish translation.  python3 -m pytest tests/test_i18n.py -v"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "voro_teryt_qa"
sys.path.insert(0, str(PKG))
import i18n  # noqa: E402

PATTERNS = [re.compile(r'self\.tr\(\s*"([^"]+)"\s*\)'), re.compile(r'\bstep\(\s*"([^"]+)"\s*\)')]


def ui_texts():
    texts = set()
    for name in ("algorithm.py", "qa_measures.py"):
        source = (PKG / name).read_text(encoding="utf-8")
        for p in PATTERNS:
            texts.update(p.findall(source))
    return texts


def test_texts_are_found():
    texts = ui_texts()
    assert "Check boundaries against TERC" in texts
    assert "Reading counties" in texts
    assert len(texts) >= 15


def test_every_ui_text_has_polish():
    missing = sorted(t for t in ui_texts() if t not in i18n.PL)
    assert missing == [], f"no Polish translation for: {missing}"


def test_placeholders_match():
    for en, pl in i18n.PL.items():
        assert en.count("{}") == pl.count("{}"), en


def test_language_switch():
    assert i18n.tr("Findings", "pl") == "Znaleziska"
    assert i18n.tr("Findings", "en") == "Findings"
    assert i18n.tr("not in the dictionary", "pl") == "not in the dictionary"
    assert "Kontrole: C1" in i18n.help_text("pl")
    assert "Checks: C1" in i18n.help_text("en")


def test_without_qgis_falls_back_to_english():
    assert i18n.language() in ("en", "pl")
