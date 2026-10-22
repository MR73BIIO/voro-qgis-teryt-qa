[English](README.md) | **Polski**

# voro-qgis-teryt-qa

Wtyczka QGIS do kontroli jakości granic gmin z PRG względem urzędowego rejestru TERC.

Dodaje jeden algorytm Processing: **VORO TERYT QA → Sprawdź granice gmin z TERC**. Podajesz warstwę gmin, warstwę powiatów i plik TERC. Wynik to warstwa znalezisk, jeden wiersz na problem, z geometrią gminy, więc błędy widać na mapie. Opcjonalnie powstaje raport HTML.

Kontrole zbudowałem i zmierzyłem najpierw w Pythonie, w [voro-gis-qa](https://github.com/MR73BIIO/voro-gis-qa). Wtyczka przenosi je do QGIS bez zmiany reguł i progów.

## Co sprawdza

| Kontrola | Co sprawdza | Waga |
|---|---|---|
| C1 | geometria pusta lub niepoprawna | krytyczna |
| C2 | TERYT: format, duplikaty, rodzaj gminy 1/2/3 | krytyczna |
| C3 | gmina leży w swoim powiecie | krytyczna |
| C4 | deklarowany układ współrzędnych, geometria w zasięgu Polski | krytyczna |
| C5 | nakładania i szczeliny między gminami | wysoka |
| C6 | nazwa obecna i zgodna z TERC | średnia |

Status całego zbioru: **PASS** (brak znalezisk), **REVIEW** (są znaleziska, żadne krytyczne), **REJECT** (co najmniej jedno krytyczne).

W tej wersji nie są sprawdzane: granica państwa (C7), same powiaty i województwa, zgodność granic z terenem albo z dokumentami prawnymi.

## Instalacja

Dopóki wtyczki nie ma w oficjalnym repozytorium QGIS: pobierz ZIP ze strony Releases, a potem w QGIS *Wtyczki → Zarządzanie wtyczkami → Instaluj z pliku ZIP*.

Wymagania: QGIS 3.40 lub nowszy, także QGIS 4. Bez dodatkowych pakietów Pythona.

## Użycie

1. Wczytaj warstwy gmin i powiatów (np. z PRG) w EPSG:2180.
2. Otwórz Panel algorytmów i uruchom *VORO TERYT QA → Sprawdź granice gmin z TERC*.
3. Wybierz warstwy, pola TERYT i nazwy oraz plik TERC (CSV z GUS).
4. Opcjonalnie wskaż plik raportu HTML.
5. Nie włączaj „iteracji po tej warstwie”. Nakładania, szczeliny i duplikaty istnieją tylko między gminami.

Na pełnej warstwie PRG (2479 gmin) przebieg trwa około minuty.

Interfejs jest po polsku, gdy QGIS działa po polsku, a w innych językach po angielsku. Raport HTML jest po polsku.

## Jak było testowane

Przewidywanie dla wersji 0.1 zapisałem w `PREDICTION.md` przed napisaniem kodu wtyczki. Wyniki:

- **Złoty zbiór** (2479 gmin, 380 powiatów): 0 znalezisk, status PASS. 7075 par gmin sprawdzonych pod kątem nakładania, tyle samo co w voro-gis-qa.
- **`seed_42`** z voro-gis-qa (160 wstrzykniętych błędów, po 20 każdego typu): wykryte 160 ze 160 właściwą kontrolą, 0 fałszywych alarmów.
- **Te same odpowiedzi co voro-gis-qa:** 2335 par (kontrola, TERYT) na `seed_42`, identycznych. Jedna różnica w diagnostyce, bez wpływu na znaleziska, jest opisana w `docs/differences.md`.

Testy automatyczne przy każdym pushu (GitHub Actions): 23 testy logiki, raportu i tłumaczeń bez QGIS oraz 13 testów całej wtyczki w QGIS 3.40, 3.44 i 4.2 na Linuksie. Ręcznie: QGIS 3.44.15 na Windowsie.

## Licencja

GPL-2.0 lub nowsza.

---

Marcin Ruszczak · MR73BIIO · polski, niemiecki, rosyjski, angielski
