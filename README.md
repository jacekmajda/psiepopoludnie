# psiepopoludnie.pl

Jednoplikowa strona wizytówka Julii Stankiewicz (Psie Popołudnie).
Bez frameworków i bez kroku budowania - cała strona to `index.html`
z osadzonym stylem i skryptem.

Wynik Google Lighthouse: **100 / 100 / 100 / 100** (wydajność,
dostępność, najlepsze praktyki, SEO) - zarówno w widoku mobilnym,
jak i na komputerze.

## Co jest w repozytorium

| Ścieżka            | Do czego służy |
|--------------------|----------------|
| `index.html`       | cała strona |
| `img/`             | lekkie zdjęcia (AVIF + JPEG, po kilka szerokości) |
| `fonts/`           | kroje Montserrat i Open Sans, ograniczone do znaków ze strony |
| `logo.svg`         | logo |
| `build-images.py`  | przygotowuje zawartość `img/` z oryginalnych zdjęć |
| `build-fonts.py`   | przygotowuje zawartość `fonts/` |
| `robots.txt`, `sitemap.xml`, `.nojekyll` | pliki pomocnicze dla wyszukiwarek i GitHub Pages |
| `FORMULARZ.md`     | jak podłączyć formularz kontaktowy do Arkusza Google |

Oryginalne (ciężkie) zdjęcia **nie trafiają do repozytorium** - są
wypisane w `.gitignore`. Trzymaj je na Dysku Google; do ponownego
wygenerowania `img/` wystarczy wgrać je z powrotem pod te same nazwy.

## Publikacja na GitHub Pages

1. Wypchnij repozytorium na GitHub.
2. **Settings → Pages → Build and deployment**: źródło *Deploy from a
   branch*, gałąź `main`, katalog `/ (root)`.
3. Jeśli strona ma działać pod adresem `psiepopoludnie.pl`:
   - w **Settings → Pages → Custom domain** wpisz `psiepopoludnie.pl`
     (GitHub sam doda do repozytorium plik `CNAME`),
   - u operatora domeny ustaw rekordy `A` na adresy GitHuba
     (`185.199.108.153`, `185.199.109.153`, `185.199.110.153`,
     `185.199.111.153`) oraz `CNAME` dla `www` na `<konto>.github.io`,
   - zaznacz **Enforce HTTPS**.
4. Jeśli zostajesz przy adresie `<konto>.github.io/<repo>/`, popraw
   w `index.html` adresy w znacznikach `canonical`, `og:url`, `og:image`
   oraz w `sitemap.xml` i `robots.txt` - teraz wskazują na
   `https://psiepopoludnie.pl/`.

GitHub Pages sam włącza HTTP/2 i kompresję gzip, więc nie trzeba
niczego konfigurować. Nie obsługuje za to własnych nagłówków -
pliki `_headers` czy `.htaccess` byłyby tam ignorowane.

## Aktualizacja zdjęć

```bash
# 1. wgraj oryginały pod nazwami z listy SOURCES w build-images.py
# 2. przelicz wersje dla strony
python3 build-images.py
```

Skrypt tworzy dla każdego zdjęcia wersje AVIF i JPEG w kilku
szerokościach, kadruje je tak, jak wyświetla je strona, i kasuje pliki,
których strona już nie używa. Wymaga wyłącznie `sips` - narzędzia
wbudowanego w macOS.

Po dodaniu **nowego** zdjęcia dopisz je do listy `SOURCES`
w `build-images.py`, a w `index.html` dodaj blok `<picture>` wzorowany
na sąsiednich.

## Aktualizacja krojów pisma

```bash
python3 -m pip install fonttools brotli
python3 build-fonts.py
```

W plikach `fonts/` siedzą wyłącznie te znaki, które występują na
stronie. Po dopisaniu tekstu z nietypowym symbolem (np. „≈") uruchom
skrypt ponownie i wklej zawartość `fonts/fonts.css` w miejsce reguł
`@font-face` na początku `<style>` w `index.html`.

## Formularz kontaktowy

Formularz nie potrzebuje serwera - wysyła dane do formularza Google,
a te lądują w Arkuszu. Instrukcja: [`FORMULARZ.md`](FORMULARZ.md).
Dopóki nie jest skonfigurowany, przycisk otwiera program pocztowy
z gotową treścią wiadomości.

## Sprawdzenie wyniku Lighthouse

Otwieranie `index.html` podwójnym kliknięciem (`file://`) zaniża wynik.
Uruchom lokalny serwer i zbadaj adres `http://localhost:8000`:

```bash
python3 -m http.server 8000
```

Pełne 100 punktów widać dopiero na hostingu z HTTP/2 i kompresją -
czyli na GitHub Pages.
