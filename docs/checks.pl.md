[English](checks.md) | **Polski**

# Kontrole po kolei

Każda kontrola jest opisana tak, jak działa w kodzie. Rysunki mają ten sam układ co testy automatyczne: dwa powiaty po cztery gminy. Progi pochodzą z [`params.json`](../voro_teryt_qa/params.json) i są takie same jak w voro-gis-qa.

Gmina może mieć kilka znalezisk. Status całego zbioru to **REJECT**, jeśli jest choć jedno znalezisko krytyczne, **REVIEW**, jeśli są znaleziska, ale żadne krytyczne, i **PASS**, jeśli nie ma żadnych.

## C1 · Geometria (krytyczna)

![C1](img/checks/c1.png)

- Pusta geometria: znalezisko „pusta geometria”.
- Geometria niepoprawna według reguł GEOS (samoprzecięcie, pierścień przecinający inny pierścień itd.): znalezisko z przyczyną podaną przez QGIS.
- Gminy z niepoprawną geometrią nie biorą udziału w C5, bo na nich nie da się zmierzyć nakładań i szczelin. Ich miejsce pojawia się jako szczelina przy sąsiadach.

## C2 · Kod TERYT (krytyczna)

![C2](img/checks/c2.png)

- Kod musi mieć dokładnie 7 cyfr.
- Ten sam kod może wystąpić tylko raz.
- Ostatnia cyfra to rodzaj gminy i musi być 1, 2 albo 3 (miejska, wiejska, miejsko-wiejska).

## C3 · Gmina w swoim powiecie (krytyczna)

![C3](img/checks/c3.png)

- Pierwsze 4 cyfry TERYT to kod powiatu. Taki powiat musi istnieć w warstwie powiatów.
- Punkt na powierzchni gminy musi leżeć w tym powiecie, z tolerancją 1 m (`c3_buffer_m`).

## C4 · Układ współrzędnych i zasięg Polski (krytyczna)

![C4](img/checks/c4.png)

- Warstwa musi być w EPSG:2180. Jeśli nie jest, powstaje jedno znalezisko dla całego zbioru, a C3 i C5 są pomijane, bo odległości i powierzchnie nie miałyby sensu.
- Prostokąt otaczający każdej gminy musi leżeć w prostokącie Polski (14,07–24,16 E, 49,00–54,84 N, przeliczonym do EPSG:2180) powiększonym o 20 km (`c4_margin_m`). Gmina zapisana w stopniach w warstwie w metrach ląduje daleko i zostaje tu wyłapana.

## C5 · Nakładania i szczeliny (wysoka)

![C5](img/checks/c5.png)

- **Nakładanie:** dwie gminy, które mają wspólną powierzchnię większą niż 1 m² (`c5_overlap_tol_m2`). Znalezisko dostają obie.
- **Szczelina:** dziura w sumie wszystkich gmin większa niż 1 m² (`c5_gap_tol_m2`). Znalezisko dostaje każda gmina w odległości do 1 m od dziury.
- Poniżej progów nic nie jest zgłaszane, ale liczby trafiają do diagnostyki (ile par sprawdzono, ile drobnych kawałków było poniżej progu, jaki był największy).

## C6 · Nazwa zgodna z TERC (średnia)

![C6](img/checks/c6.png)

- Nazwa nie może być pusta.
- Kod musi istnieć w TERC.
- Nazwa musi być równa nazwie z TERC, litera w literę, po połączeniu powtórzonych spacji.
- Znane wyjątki ([`known_exceptions.json`](../voro_teryt_qa/known_exceptions.json)) działają tylko dla dokładnej pary nazw. Dziś jest jeden: Słupia (Jędrzejowska) w PRG to Słupia w TERC.

## Czego nie sprawdza

Granicy państwa (C7, w planie), samych powiatów i województw, zgodności granic z terenem albo z dokumentami prawnymi.
