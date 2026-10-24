"""
HTML report of one run. Pure Python, no QGIS imports, so it can be tested outside QGIS.
One self-contained UTF-8 file: inline CSS, no scripts, prints well on A4.
"""
from collections import Counter, defaultdict
from html import escape

CHECKS = [
    ("C1", "Geometria pusta lub niepoprawna", "krytyczna"),
    ("C2", "TERYT: format, duplikaty, rodzaj gminy 1/2/3", "krytyczna"),
    ("C3", "Gmina leży w swoim powiecie", "krytyczna"),
    ("C4", "Deklarowany układ współrzędnych i zasięg Polski", "krytyczna"),
    ("C5", "Nakładania i szczeliny między gminami", "wysoka"),
    ("C6", "Nazwa obecna i zgodna z TERC", "srednia"),
    ("C7", "Pokrycie granicy państwa", "wysoka"),
]
# Built from pairs, not a dict literal: Bandit B105 reads a "PASS" key as a password
# (false positive in the plugins.qgis.org security scan). Same texts as before.
_STATUS_ROWS = (
    ("PASS", "Zbiór przeszedł kontrolę. Nie znaleziono błędów."),
    ("REVIEW", "Zbiór wymaga przejrzenia. Są znaleziska, ale żadne nie jest krytyczne."),
    ("REJECT", "Zbiór nie przeszedł kontroli. Są znaleziska krytyczne."),
)
STATUS_TEXT = dict(_STATUS_ROWS)
SEVERITY_LABEL = {"krytyczna": "krytyczna", "wysoka": "wysoka", "srednia": "średnia"}
DOI = "10.5281/zenodo.23104107"

CSS = """
body{font-family:Segoe UI,Arial,sans-serif;color:#1f2933;max-width:1000px;margin:24px auto;
     padding:0 16px;line-height:1.45}
h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:28px 0 8px;border-bottom:1px solid #d9dee3;padding-bottom:4px}
h3{font-size:15px;margin:18px 0 6px}
.sub{color:#5f6b76;margin:0 0 18px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:6px 0}
th,td{border:1px solid #d9dee3;padding:4px 8px;text-align:left;vertical-align:top}
th{background:#f3f5f7}
td.n{text-align:right;white-space:nowrap}
.status{display:inline-block;padding:6px 14px;border-radius:4px;font-weight:600;color:#fff}
.PASS{background:#2f7d4a}.REVIEW{background:#b7791f}.REJECT{background:#b42318}
.meta td:first-child{width:34%;color:#5f6b76}
.small{font-size:12px;color:#5f6b76}
@media print{body{margin:0}h2{page-break-after:avoid}tr{page-break-inside:avoid}}
"""


def _fmt_num(x):
    if isinstance(x, float) and x == 0:
        return "0"
    if isinstance(x, float):
        return f"{x:.3g}" if abs(x) < 0.01 and x != 0 else f"{x:,.2f}".replace(",", " ")
    if isinstance(x, int):
        return f"{x:,}".replace(",", " ")
    return str(x)


def render(findings, diagnostics, status, meta, names=None, params=None):
    """findings: list of dicts (check, teryt, severity, detail); names: teryt -> municipality name;
    meta: dict with labels -> values shown at the top (input layers, versions, date)."""
    names = names or {}
    params = params or {}
    per_check = Counter(f["check"] for f in findings)
    gminy_per_check = defaultdict(set)
    for f in findings:
        if f["teryt"] is not None:
            gminy_per_check[f["check"]].add(f["teryt"])
    affected = {f["teryt"] for f in findings if f["teryt"] is not None}

    out = ["<!doctype html>", '<html lang="pl"><head><meta charset="utf-8">',
           "<title>Raport kontroli granic gmin</title>", f"<style>{CSS}</style></head><body>"]
    out.append("<h1>Raport kontroli jakości granic gmin (PRG wobec TERC)</h1>")
    out.append(f'<p class="sub">{escape(str(meta.get("Data kontroli", "")))}</p>')
    out.append(f'<p><span class="status {escape(status)}">{escape(status)}</span> '
               f"&nbsp;{escape(STATUS_TEXT.get(status, ''))}</p>")
    out.append(f"<p>Znaleziska: <b>{_fmt_num(len(findings))}</b> · gminy ze znaleziskami: "
               f"<b>{_fmt_num(len(affected))}</b></p>")

    out.append("<h2>Dane wejściowe</h2><table class=\"meta\">")
    for k, v in meta.items():
        if k == "Data kontroli":
            continue
        out.append(f"<tr><td>{escape(str(k))}</td><td>{escape(str(v))}</td></tr>")
    out.append("</table>")

    out.append("<h2>Wynik według kontroli</h2><table><tr><th>Kontrola</th><th>Co sprawdza</th>"
               "<th>Waga</th><th>Znaleziska</th><th>Gminy</th></tr>")
    for cid, desc, sev in CHECKS:
        out.append(f"<tr><td>{cid}</td><td>{escape(desc)}</td><td>{SEVERITY_LABEL[sev]}</td>"
                   f'<td class="n">{_fmt_num(per_check.get(cid, 0))}</td>'
                   f'<td class="n">{_fmt_num(len(gminy_per_check.get(cid, ())))}</td></tr>')
    out.append("</table>")

    out.append("<h2>Diagnostyka</h2><table>")
    labels = {
        "c5_overlap_pairs_checked": "C5: pary gmin sprawdzone pod kątem nakładania",
        "c5_overlaps_below_tol": "C5: nakładania poniżej progu (nie są błędem)",
        "c5_overlap_max_below_tol_m2": "C5: największe nakładanie poniżej progu [m²]",
        "c5_gaps_total": "C5: szczeliny (dziury w sumie gmin)",
        "c5_gaps_below_tol": "C5: szczeliny poniżej progu (nie są błędem)",
        "c5_gap_max_below_tol_m2": "C5: największa szczelina poniżej progu [m²]",
        "c6_known_exceptions_applied": "C6: użyte znane wyjątki nazw",
        "c7": "C7",
        "c7_pieces_total": "C7: kawałki przy granicy państwa (bez gminy albo poza państwem)",
        "c7_pieces_below_tol": "C7: kawałki poniżej progu (nie są błędem)",
        "c7_max_below_tol_m2": "C7: największy kawałek poniżej progu [m²]",
        "c7_known_exceptions_applied": "C7: użyte znane wyjątki (morze)",
        "skipped": "Pominięte kontrole",
    }
    for k, v in diagnostics.items():
        out.append(f"<tr><td>{escape(labels.get(k, k))}</td><td class=\"n\">{escape(_fmt_num(v))}</td></tr>")
    out.append("</table>")

    if params:
        out.append("<h2>Progi</h2><table>")
        plabels = {"expected_crs": "Oczekiwany układ współrzędnych",
                   "c3_buffer_m": "C3: tolerancja odległości od powiatu [m]",
                   "c4_margin_m": "C4: margines wokół zasięgu Polski [m]",
                   "c5_overlap_tol_m2": "C5: próg nakładania [m²]",
                   "c5_gap_tol_m2": "C5: próg szczeliny [m²]",
                   "c7_border_tol_m2": "C7: próg kawałka przy granicy państwa [m²]"}
        for k, lab in plabels.items():
            if k in params:
                out.append(f"<tr><td>{escape(lab)}</td><td class=\"n\">{escape(_fmt_num(params[k]))}</td></tr>")
        out.append("</table>")

    out.append("<h2>Znaleziska</h2>")
    if not findings:
        out.append("<p>Brak znalezisk.</p>")
    by_check = defaultdict(list)
    for f in findings:
        by_check[f["check"]].append(f)
    for cid, desc, _sev in CHECKS:
        rows = by_check.get(cid)
        if not rows:
            continue
        out.append(f"<h3>{cid} · {escape(desc)} ({_fmt_num(len(rows))})</h3>")
        out.append("<table><tr><th>TERYT</th><th>Gmina</th><th>Opis</th></tr>")
        for f in sorted(rows, key=lambda r: (r["teryt"] is not None, r["teryt"] or "")):
            t = f["teryt"]
            out.append(f"<tr><td>{escape(t) if t else 'cały zbiór'}</td>"
                       f"<td>{escape(names.get(t, '')) if t else ''}</td>"
                       f"<td>{escape(str(f['detail']))}</td></tr>")
        out.append("</table>")

    out.append("<h2>Czego ta kontrola nie sprawdza</h2><ul>")
    for line in [
        "Granicy państwa (C7), jeśli nie podano warstwy granicy państwa.",
        "Zgodności przebiegu granic z rzeczywistością w terenie ani z dokumentami prawnymi. "
        "Kontrola porównuje dane między sobą i z rejestrem TERC.",
        "Samych powiatów i województw. Powiaty służą tylko jako odniesienie dla C3.",
        "Atrybutów innych niż TERYT i nazwa.",
    ]:
        out.append(f"<li>{escape(line)}</li>")
    out.append("</ul>")
    out.append(f'<p class="small">Reguły i progi pochodzą z voro-gis-qa (DOI {DOI}). '
               "Raport wygenerowała wtyczka QGIS VORO TERYT QA, Marcin Ruszczak (MR73BIIO).</p>")
    out.append("</body></html>")
    return "\n".join(out)
