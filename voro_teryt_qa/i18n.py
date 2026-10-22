"""
Translations without Qt .ts/.qm files (no compiled files in the plugin).
Polish when QGIS runs in Polish, English otherwise. Pure Python; QGIS is asked
for the locale only when it is available, so the module can be tested without QGIS.
"""

PL = {
    # algorithm
    "Check boundaries against TERC": "Sprawdź granice gmin z TERC",
    "Municipalities (gminy)": "Gminy",
    "Municipality TERYT field": "Pole TERYT gminy",
    "Municipality name field": "Pole nazwy gminy",
    "Counties (powiaty)": "Powiaty",
    "County TERYT field": "Pole TERYT powiatu",
    "TERC register (CSV)": "Rejestr TERC (CSV)",
    "Findings": "Znaleziska",
    "HTML report": "Raport HTML",
    "HTML files (*.html)": "Pliki HTML (*.html)",
    "TERC file not found: {}": "Nie znaleziono pliku TERC: {}",
    # progress and log
    "Reading counties": "Odczyt powiatów",
    "Measuring municipalities": "Pomiar gmin",
    "Overlaps between municipalities": "Nakładania między gminami",
    "Gaps: holes in the union of municipalities": "Szczeliny: dziury w sumie gmin",
    "Municipalities: {} | counties: {} | CRS: {} | TERC municipalities: {}":
        "Gminy: {} | powiaty: {} | układ: {} | gminy w TERC: {}",
    "Dataset status: {}": "Status zbioru: {}",
    "  {}: {} findings": "  {}: {} znalezisk",
    "Diagnostics: {}": "Diagnostyka: {}",
    "Findings total: {}": "Znaleziska razem: {}",
    "HTML report: {}": "Raport HTML: {}",
}

HELP = {
    "en": (
        "Checks municipality polygons (PRG) against county polygons and the TERC register. "
        "Output: one row per finding with the fields check, teryt, severity, detail, "
        "and the geometry of the municipality.\n\n"
        "Checks: C1 geometry, C2 TERYT codes, C3 municipality inside its own county, "
        "C4 CRS and extent of Poland, C5 overlaps and gaps between municipalities, "
        "C6 names against TERC.\n\n"
        "Optional: an HTML report (UTF-8, in Polish) with the status, counts per check, "
        "diagnostics, thresholds and the list of findings.\n\n"
        "Thresholds and known exceptions come from voro-gis-qa and are not set here.\n\n"
        "Do not use 'iterate over this layer': overlaps, gaps and duplicates exist only "
        "between municipalities."
    ),
    "pl": (
        "Sprawdza poligony gmin (PRG) względem poligonów powiatów i rejestru TERC. "
        "Wynik: jeden wiersz na znalezisko z polami check, teryt, severity, detail "
        "oraz geometrią gminy.\n\n"
        "Kontrole: C1 geometria, C2 kody TERYT, C3 gmina w swoim powiecie, "
        "C4 układ współrzędnych i zasięg Polski, C5 nakładania i szczeliny między gminami, "
        "C6 nazwy zgodne z TERC.\n\n"
        "Opcjonalnie: raport HTML (UTF-8, po polsku) ze statusem, liczbami według kontroli, "
        "diagnostyką, progami i listą znalezisk.\n\n"
        "Progi i znane wyjątki pochodzą z voro-gis-qa i nie ustawia się ich tutaj.\n\n"
        "Nie używaj „iteracji po tej warstwie”: nakładania, szczeliny i duplikaty istnieją "
        "tylko między gminami."
    ),
}


def language():
    try:
        from qgis.core import QgsApplication
        loc = QgsApplication.locale() or ""
    except Exception:  # noqa: BLE001 - no QGIS (tests) or not initialised
        loc = ""
    return "pl" if str(loc).lower().startswith("pl") else "en"


def tr(text, lang=None):
    lang = lang or language()
    return PL.get(text, text) if lang == "pl" else text


def help_text(lang=None):
    return HELP[lang or language()]
