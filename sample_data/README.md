# Sample data / Dane przykładowe

A small cut of real data: 25 municipalities in the counties 1601, 1602, 1603, 1604, 1605.
Mały wycinek prawdziwych danych: 25 gmin w powiatach 1601, 1602, 1603, 1604, 1605.

| File / Plik | What / Co |
|---|---|
| `sample_clean.gpkg` | layers `gminy`, `powiaty` from PRG, unchanged / bez zmian |
| `sample_broken.gpkg` | the same, with one injected error of each type / z jednym wstrzykniętym błędem każdego typu |
| `terc_sample.csv` | TERC rows for these counties / wiersze TERC dla tych powiatów |
| `expected.json` | findings computed by voro-gis-qa / znaleziska policzone przez voro-gis-qa |

## Try it / Wypróbuj

1. Drag `sample_broken.gpkg` into QGIS, add both layers. / Przeciągnij `sample_broken.gpkg` do QGIS, dodaj obie warstwy.
2. Run *VORO TERYT QA → Check boundaries against TERC* with `terc_sample.csv`. / Uruchom algorytm z `terc_sample.csv`.
3. Expected / Oczekiwany wynik: **REJECT, 72 findings / znalezisk**.
   On / Na `sample_clean.gpkg`: **PASS, 0**.

| Check | Findings on sample_broken |
|---|---|
| C1 | 1 |
| C2 | 1 |
| C3 | 2 |
| C4 | 1 |
| C5 | 63 |
| C6 | 4 |

Injected errors (seed 7) / Wstrzyknięte błędy:

| Error | TERYT | Detail |
|---|---|---|
| E1 | 1604023 | zamiana wierzcholkow 2192/2193 |
| E2 | 1601022 | skopiowany TERYT gminy 1601022 |
| E3 | 1699043 | powiat 1601 -> 1699 |
| E4 | 1603062 | geometria w EPSG:4326 w warstwie EPSG:2180 |
| E5 | 1605013 | przesuniecie 47.0 m |
| E6 | 1602033 | szczelina r=23.5 m przy granicy z 1602013 |
| E7 | 1601033 | 'Grodków' -> 'Grodkow' |
| E8 | 1605033 | usunieto nazwe 'Strzeleczki' |

voro-gis-qa finds 8 of 8 with 0 false alarms. The automatic tests check that the plugin
gives exactly the same pairs (check, TERYT) as voro-gis-qa on both files, in QGIS 3.40, 3.44 and 4.2.

## Source / Źródło

Boundaries: Państwowy Rejestr Granic (PRG), Główny Urząd Geodezji i Kartografii, geoportal.gov.pl.
TERC: Krajowy Rejestr Urzędowy Podziału Terytorialnego Kraju (TERYT), Główny Urząd Statystyczny.
Made on 2026-10-22 with `scripts/make_sample_data.py`.
