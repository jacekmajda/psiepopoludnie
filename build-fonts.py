#!/usr/bin/env python3
"""
Przygotowanie krojów pisma dla strony psiepopoludnie.pl
=======================================================

Pobiera z Google Fonts krój zmienny ograniczony do znaków, które
faktycznie występują na stronie, wycina z niego statyczne wersje
w potrzebnych grubościach i zapisuje je w katalogu `fonts/`.
Na końcu generuje `fonts/fonts.css` z regułami @font-face.

Efekt: strona nie odpytuje serwerów Google (prywatność + szybkość),
a każdy krój waży ~10 KB zamiast ~30 KB.

Użycie:
    python3 build-fonts.py          # zbuduj kroje
    python3 build-fonts.py --check  # pokaż tylko listę znaków

Po większej zmianie tekstów na stronie uruchom skrypt ponownie -
inaczej nowe znaki (np. rzadki symbol) nie będą miały swojego kształtu.
Wymaga: python3 -m pip install fonttools brotli
"""

import html as htmllib
import os
import re
import subprocess
import sys
import urllib.parse

HTML_FILE = "index.html"
OUT_DIR = "fonts"
CSS_FILE = os.path.join(OUT_DIR, "fonts.css")

# (rodzina, [grubości], nazwa pliku)
FAMILIES = [
    ("Montserrat", [600, 700, 800], "Montserrat"),
    ("Open Sans", [400, 600], "OpenSans"),
]

# Znaki zawsze dołączane, nawet jeśli akurat nie ma ich w treści -
# przydają się przy drobnych korektach tekstu.
ALWAYS = (
    "aąbcćdeęfghijklłmnńoópqrsśtuvwxyzźż"
    "AĄBCĆDEĘFGHIJKLŁMNŃOÓPQRSŚTUVWXYZŹŻ"
    "0123456789"
    " .,:;!?'\"()[]{}-–—_/\\|@#%&*+=<>~^$"
    "€°·•…«»„”“‘’×"
)

UA_WOFF2 = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def page_text(path):
    raw = open(path, encoding="utf-8").read()
    # wytnij <style>, <script> i komentarze - to nie jest widoczny tekst
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.S)
    raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.S)
    raw = re.sub(r"<!--.*?-->", " ", raw, flags=re.S)
    # teksty widoczne pochodzące z atrybutów
    attrs = " ".join(re.findall(r'(?:alt|title|placeholder|aria-label|content)="([^"]*)"', raw))
    raw = re.sub(r"<[^>]+>", " ", raw)
    return htmllib.unescape(raw + " " + attrs)


def charset(path):
    chars = set(ALWAYS) | set(page_text(path))
    # pomiń białe znaki poza spacją oraz emoji (te rysuje font systemowy)
    chars = {c for c in chars if c.isprintable() and ord(c) < 0x2200}
    chars.add(" ")
    return "".join(sorted(chars))


def curl(url, out=None, ua=None):
    args = ["curl", "-fsSL"]
    if ua:
        args += ["-H", f"User-Agent: {ua}"]
    if out:
        args += ["-o", out]
    result = subprocess.run(args + [url], capture_output=True, text=(out is None))
    if result.returncode != 0:
        raise RuntimeError(f"curl {url} -> kod {result.returncode}")
    return result.stdout


def fetch_variable(family, weights, text, dest):
    """Pobiera zmienny krój ograniczony do podanych znaków."""
    api = (
        "https://fonts.googleapis.com/css2?family="
        + urllib.parse.quote(family)
        + f":wght@{min(weights)}..{max(weights)}&text="
        + urllib.parse.quote(text)
        + "&display=swap"
    )
    css = curl(api, ua=UA_WOFF2)
    match = re.search(r"url\((https://[^)]+)\)", css)
    if not match:
        raise RuntimeError(f"{family}: brak adresu pliku w odpowiedzi Google Fonts")
    curl(match.group(1), out=dest)


def make_static(source, weight, text, dest):
    """Wycina z kroju zmiennego statyczną wersję o danej grubości."""
    from fontTools import subset
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont

    font = TTFont(source)
    if "fvar" in font:
        instantiateVariableFont(font, {"wght": weight}, inplace=True)

    options = subset.Options(layout_features=["*"], notdef_outline=True)
    options.drop_tables += ["DSIG"]
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)

    font.flavor = "woff2"
    font.save(dest)
    font.close()


def main():
    text = charset(HTML_FILE)
    print(f"Znaków do osadzenia: {len(text)}")
    if "--check" in sys.argv:
        print(text)
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    rules = []
    produced = set()
    total = 0

    for family, weights, slug in FAMILIES:
        source = os.path.join(OUT_DIR, f".{slug}-var.woff2")
        fetch_variable(family, weights, text, source)

        for weight in weights:
            name = f"{slug}-{weight}.woff2"
            path = os.path.join(OUT_DIR, name)
            make_static(source, weight, text, path)
            produced.add(name)
            size = os.path.getsize(path)
            total += size
            print(f"  {name}: {size / 1024:.1f} KB")
            rules.append(
                "@font-face {\n"
                f"    font-family: '{family}';\n"
                "    font-style: normal;\n"
                f"    font-weight: {weight};\n"
                "    font-display: swap;\n"
                f"    src: url({OUT_DIR}/{name}) format('woff2');\n"
                "}"
            )

        os.remove(source)

    # posprzątaj po poprzednich uruchomieniach
    produced.add(os.path.basename(CSS_FILE))
    for stale in os.listdir(OUT_DIR):
        if stale not in produced:
            os.remove(os.path.join(OUT_DIR, stale))
            print(f"  usunięto nieużywany {stale}")

    with open(CSS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(rules) + "\n")

    print(f"\nRazem: {total / 1024:.1f} KB")
    print(f"Reguły @font-face: {CSS_FILE} - wklej je w <style> w {HTML_FILE}")


if __name__ == "__main__":
    main()
