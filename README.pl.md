[English](README.md) | **Polski**

# VORO TERYT QA

[![tests](https://github.com/MR73BIIO/voro-qgis-teryt-qa/actions/workflows/tests.yml/badge.svg)](https://github.com/MR73BIIO/voro-qgis-teryt-qa/actions/workflows/tests.yml)
![QGIS](https://img.shields.io/badge/QGIS-3.40%20%7C%203.44%20%7C%204.2-589632)
![Licencja](https://img.shields.io/badge/licencja-GPL--2.0%20lub%20nowsza-blue)
[![DOI](https://zenodo.org/badge/1429926843.svg)](https://doi.org/10.5281/zenodo.23578393)

**Wtyczka QGIS, która sprawdza granice gmin z PRG względem urzędowego rejestru TERC i pokazuje każdy problem na mapie.**

![Znaleziska na zbiorze testowym seed_42](docs/img/map_findings.png)

Dane granic często odbiera się po obejrzeniu mapy. Ta wtyczka daje kontrolę, którą można powtórzyć: te same reguły, te same progi, ten sam wynik na każdym komputerze. Powstała z [voro-gis-qa](https://github.com/MR73BIIO/voro-gis-qa), gdzie reguły zmierzyłem najpierw w Pythonie, i daje te same znaleziska.

## Co sprawdza

| Kontrola | Co sprawdza | Waga |
|---|---|---|
| C1 | geometria pusta lub niepoprawna | krytyczna |
| C2 | TERYT: format, duplikaty, rodzaj gminy 1/2/3 | krytyczna |
| C3 | gmina leży w swoim powiecie | krytyczna |
| C4 | deklarowany układ współrzędnych, geometria w zasięgu Polski | krytyczna |
| C5 | nakładania i szczeliny między gminami | wysoka |
| C6 | nazwa obecna i zgodna z TERC | średnia |
| C7 | granica państwa: kawałki Polski bez gminy, części gmin poza Polską (tylko z opcjonalną warstwą granicy państwa) | wysoka |

Status całego zbioru: **PASS** (brak znalezisk), **REVIEW** (są znaleziska, żadne krytyczne), **REJECT** (co najmniej jedno krytyczne).

Jak działa każda kontrola, z rysunkami: [`docs/checks.pl.md`](docs/checks.pl.md).

## Co dostajesz

Algorytm Processing, po polsku albo po angielsku, zależnie od języka QGIS. Na czystej warstwie PRG zwraca PASS:

![Algorytm w QGIS: złoty zbiór, status PASS](docs/img/dialog_pass.png)

Warstwę znalezisk, jeden wiersz na problem, z geometrią gminy (mapa powyżej). A jeśli chcesz, raport HTML po polsku, który można wydrukować albo wysłać:

![Raport HTML](docs/img/report.png)

## Wypróbuj w dwie minuty

Folder [`sample_data/`](sample_data/) zawiera mały wycinek prawdziwych danych PRG, pasujące wiersze TERC i kopię z jednym wstrzykniętym błędem każdego typu. Pobierz repozytorium, przeciągnij `sample_broken.gpkg` do QGIS i uruchom algorytm z `terc_sample.csv`. Oczekiwany wynik, policzony przez voro-gis-qa, jest zapisany w [`sample_data/README.md`](sample_data/README.md). Testy automatyczne uruchamiają wtyczkę na tych samych plikach.

## Instalacja

Pobierz `voro_teryt_qa-0.2.0.zip` ze strony [Releases](https://github.com/MR73BIIO/voro-qgis-teryt-qa/releases). W QGIS: *Wtyczki → Zarządzanie wtyczkami → Instaluj z pliku ZIP*.

![Wtyczka w menedżerze wtyczek QGIS](docs/img/plugin_manager.png)

Wymagania: QGIS 3.40 lub nowszy, także QGIS 4. Bez dodatkowych pakietów Pythona.

## Użycie

1. Wczytaj warstwy gmin i powiatów (np. z PRG) w EPSG:2180.
2. Uruchom z Panelu algorytmów *VORO TERYT QA → Sprawdź granice gmin z TERC*.
3. Wybierz warstwy, pola TERYT i nazwy oraz plik TERC (CSV z GUS).
4. Dla C7 (opcjonalnie): wybierz warstwę granicy państwa (PRG `A00_Granice_panstwa`) i warstwę znanych obszarów bez gmin, czyli morze. voro-gis-qa robi tę warstwę z tej samej paczki PRG (`known_uncovered` w jej złotym zbiorze). Bez warstwy państwa C7 jest pomijana.
5. Opcjonalnie wskaż plik raportu HTML.
6. Nie włączaj „iteracji po tej warstwie”. Nakładania, szczeliny i duplikaty istnieją tylko między gminami.

Na pełnej warstwie PRG (2479 gmin) przebieg trwa około minuty, z C7 od 53 do 76 sekund (QGIS 3.44.15 na Windowsie).

## Jak było testowane

Każde przewidywanie zapisałem przed napisaniem kodu: wersję 0.1 w [`PREDICTION.md`](PREDICTION.md), kontrolę C7 w [`PREDICTION_v0.2.md`](PREDICTION_v0.2.md). Wszystkie części się sprawdziły:

| Przewidywanie | Wynik |
|---|---|
| P1: złoty zbiór (2479 gmin) nie daje znalezisk | 0 znalezisk, PASS. Sprawdzone 7075 par gmin, tyle samo co w voro-gis-qa |
| P2: wszystkie wstrzyknięte błędy wykryte, bez fałszywych alarmów | `seed_42`, 160 błędów (po 20 każdego typu): wykryte 160 ze 160, 0 fałszywych alarmów |
| P3: te same odpowiedzi co voro-gis-qa | 2335 z 2335 par (kontrola, TERYT) identycznych. Jedna różnica w diagnostyce, bez wpływu: [`docs/differences.md`](docs/differences.md) |
| P4: z granicą państwa i morzem złoty zbiór nadal nie daje znalezisk | 0 znalezisk, PASS, wyjątek morza użyty raz |
| P5: C1–C6 nie zmieniają się po dodaniu C7 | identyczne pary C1–C6; bez warstwy państwa wynik taki sam jak w 0.1.1 |
| P6: szczeliny przy granicy państwa wykryte | `seed_9`, 20 szczelin wyciętych przy granicy państwa: wykryte 20 z 20, 0 fałszywych alarmów |
| P7: C7 daje te same odpowiedzi co voro-gis-qa | 1752 z 1752 par C7 na `seed_42` identycznych, także na złotym zbiorze i `seed_9` |
| P8: dziura przy brzegu zostaje lokalna | test w QGIS przechodzi |

Szczegóły pomiaru C7: [`docs/results_v0.2.md`](docs/results_v0.2.md).

Automatyczne sprawdzanie przy każdym pushu: kontrola kodu (ruff), 32 testy logiki, raportu i tłumaczeń oraz 22 testy całej wtyczki w QGIS 3.40, 3.44 i 4.2 na Linuksie, w tym trzy na prawdziwych danych z `sample_data/`, porównywane ze znaleziskami voro-gis-qa. Ręcznie: QGIS 3.44.15 na Windowsie.

## Czego nie sprawdza

Samych powiatów i województw ani zgodności granic z terenem albo z dokumentami prawnymi. Kontrola porównuje dane między sobą, z rejestrem TERC i, jeśli ją podasz, z granicą państwa.

## Licencja

GPL-2.0 lub nowsza. DOI (wszystkie wersje): [10.5281/zenodo.23578393](https://doi.org/10.5281/zenodo.23578393), wersja 0.1.0: [10.5281/zenodo.23578394](https://doi.org/10.5281/zenodo.23578394). Dane do cytowania: [`CITATION.cff`](CITATION.cff). Zmiany: [`CHANGELOG.md`](CHANGELOG.md).

---

Marcin Ruszczak · MR73BIIO · polski, niemiecki, rosyjski, angielski
