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
    "State border (optional, for C7)": "Granica państwa (opcjonalnie, dla C7)",
    "Known areas without municipalities, e.g. the sea (optional, for C7)":
        "Znane obszary bez gmin, np. morze (opcjonalnie, dla C7)",
    "State border layer has no CRS": "Warstwa granicy państwa nie ma układu współrzędnych",
    "Layer of known areas without municipalities has no CRS":
        "Warstwa znanych obszarów bez gmin nie ma układu współrzędnych",
    "C7: state layer not used, the municipalities are not in {}":
        "C7: warstwa granicy państwa nieużyta, gminy nie są w {}",
    "C7: known areas layer given without the state layer, C7 is skipped":
        "C7: podano znane obszary bez warstwy granicy państwa, C7 pominięta",
    # progress and log
    "Reading counties": "Odczyt powiatów",
    "Measuring municipalities": "Pomiar gmin",
    "Overlaps between municipalities": "Nakładania między gminami",
    "Gaps: holes in the union of municipalities": "Szczeliny: dziury w sumie gmin",
    "State border": "Granica państwa",
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
        "C6 names against TERC, C7 state border.\n\n"
        "C7 runs only when the state border layer (PRG A00_Granice_panstwa) is given. "
        "Give also the layer of known areas without municipalities (the sea, e.g. the layer "
        "known_uncovered of the golden dataset of voro-gis-qa): without it a hole at the coast "
        "is reported at every coastal municipality. The sea exception is an area measured on "
        "one PRG edition; with another edition C7 gives one finding for the whole dataset.\n\n"
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
        "C6 nazwy zgodne z TERC, C7 granica państwa.\n\n"
        "C7 działa tylko, gdy podana jest warstwa granicy państwa (PRG A00_Granice_panstwa). "
        "Podaj też warstwę znanych obszarów bez gmin (morze, np. warstwa known_uncovered "
        "złotego zbioru voro-gis-qa): bez niej dziura przy brzegu jest zgłaszana przy każdej "
        "gminie nadmorskiej. Wyjątek morza to powierzchnia zmierzona na jednym wydaniu PRG; "
        "przy innym wydaniu C7 daje jedno znalezisko dla całego zbioru.\n\n"
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
