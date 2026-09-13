#!/usr/bin/env python3
"""
Przygotowanie zdjęć dla strony psiepopoludnie.pl
================================================

Bierze oryginalne (duże) zdjęcia i tworzy w katalogu `img/` lekkie
wersje w dwóch rozmiarach i dwóch formatach: AVIF (nowoczesny, mały)
oraz JPEG (dla starszych przeglądarek).

Użycie:
    python3 build-images.py

Po wgraniu nowych oryginałów (np. z Dysku Google) wystarczy podmienić
pliki źródłowe pod tymi samymi nazwami i uruchomić skrypt ponownie.
Wymaga wyłącznie `sips` - narzędzia wbudowanego w macOS.
"""

import os
import shutil
import subprocess
import sys

OUT_DIR = "img"

# (plik źródłowy, nazwa wyjściowa, [szerokości], proporcje kadru, jakość AVIF)
#
# Dwa ostatnie pola są opcjonalne.
#
# Proporcje podaje się jako szerokość/wysokość. Kadr jest wycinany ze
# środka zdjęcia - dokładnie tak, jak zrobiłaby to przeglądarka przy
# `object-fit: cover`. Dzięki temu nie wysyłamy pikseli, które i tak
# zostałyby przycięte.
SOURCES = [
    # --- kolaż na stronie głównej ---
    # kolaż jest przyciemniony filtrem i przykryty napisem, więc znosi
    # mocniejszą kompresję niż zdjęcia oglądane wprost
    # duży kafelek: na komputerze prawie kwadrat, na telefonie szeroki pas
    ("1.jpeg", "collage-1-sq", [560, 1120], 1.03, 48),
    # kadr 1.6 zamiast szerszego - przy 2.29 kadr ze środka ucinał psu
    # czubek głowy; na telefonie kafelek ma dokładnie te proporcje
    ("1.jpeg", "collage-1-wide", [480, 760, 1040], 1.6, 48),
    # pozostałe kafelki mają w obu układach proporcje bliskie kwadratu
    ("2.jpeg", "collage-2", [240, 360, 560], 1.0, 48),
    ("3.jpeg", "collage-3", [240, 360, 560], 1.0, 48),
    ("4.jpeg", "collage-4", [240, 360, 560], 1.0, 48),
    ("5.jpeg", "collage-5", [240, 360, 560], 1.0, 48),
    ("6.jpeg", "collage-6", [240, 360, 560], 1.0, 48),
    ("7.jpeg", "collage-7", [240, 360, 560], 1.0, 48),

    # --- o mnie ---
    ("julia.jpeg", "julia", [400, 760, 960]),

    # --- moje stado ---
    ("kora.jpeg", "kora", [480, 960]),
    ("aria.jpeg", "aria", [480, 960]),
    ("tori.jpeg", "tori", [480, 960]),

    # --- oferta ---
    ("zdjęcia/zdjęcie na samej górze.jpg", "oferta-wstep", [640, 1280]),
    ("zdjęcia/konsultacje i treningi indywidualne.jpeg", "oferta-konsultacje", [640, 1280]),
    ("zdjęcia/tr med 2.jpg", "oferta-medyczny", [640, 1280]),
    ("zdjęcia/spac kom.jpeg", "oferta-spacery-kom", [640, 1280]),
    ("zdjęcia/psie popoludnie 1.jpeg", "oferta-psie-popoludnia", [640, 1280]),
    ("zdjęcia/sp trening.jpeg", "oferta-spacery-tren", [640, 1280]),
    ("zdjęcia/tr gr.jpeg", "oferta-grupowe", [640, 1280]),
    ("zdjęcia/obozy i wyjazdy.jpeg", "oferta-obozy", [640, 1280]),

    # --- vouchery (miniatury; pełny podgląd kopiowany niżej jako PNG) ---
    ("VOUCHER elegancki - konsultacja.png", "voucher-elegancki", [600, 1200]),
    ("VOUCHER luzacki - spotkania.png", "voucher-luzacki", [600, 1200]),
    ("VOUCHER świąteczny - spacery.png", "voucher-swiateczny", [600, 1200]),
]

AVIF_QUALITY = 60
JPEG_QUALITY = 72
# grafiki z tekstem znoszą kompresję gorzej niż zdjęcia
GRAPHIC_AVIF_QUALITY = 75
GRAPHIC_JPEG_QUALITY = 85


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def dimensions(path):
    out = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
        capture_output=True, text=True, check=True,
    ).stdout
    values = {}
    for line in out.splitlines():
        line = line.strip()
        for key in ("pixelWidth", "pixelHeight"):
            if line.startswith(key + ":"):
                values[key] = int(line.split(":")[1])
    return values["pixelWidth"], values["pixelHeight"]


def crop_box(src_w, src_h, aspect):
    """Największy kadr o zadanych proporcjach, wycięty ze środka zdjęcia."""
    if src_w / src_h > aspect:
        return round(src_h * aspect), src_h
    return src_w, round(src_w / aspect)


def build(source, base, widths, aspect=None, avif_quality=None):
    src_w, src_h = dimensions(source)
    if aspect:
        src_w, src_h = crop_box(src_w, src_h, aspect)
    is_graphic = source.lower().endswith(".png")
    made = []

    for width in widths:
        # nie powiększamy ponad oryginał
        target = min(width, src_w)
        height = round(src_h * target / src_w)

        for fmt, quality in (
            ("avif", avif_quality or (GRAPHIC_AVIF_QUALITY if is_graphic else AVIF_QUALITY)),
            ("jpeg", GRAPHIC_JPEG_QUALITY if is_graphic else JPEG_QUALITY),
        ):
            ext = "jpg" if fmt == "jpeg" else fmt
            out_path = os.path.join(OUT_DIR, f"{base}-{width}.{ext}")
            args = ["sips", "-s", "format", fmt, "-s", "formatOptions", str(quality)]
            if aspect:
                # sips oczekuje kolejności: wysokość, szerokość
                args += ["-c", str(src_h), str(src_w)]
            args += ["--resampleWidth", str(target), source, "--out", out_path]
            run(args)
            made.append((out_path, target, height, os.path.getsize(out_path)))

    return made


# Pliki kopiowane bez zmian - tylko pod bezpieczną nazwą (bez spacji
# i polskich znaków), bo adresy z nimi bywają zawodne na hostingach.
COPIES = [
    ("VOUCHER elegancki - konsultacja.png", "voucher-elegancki-full.png"),
    ("VOUCHER luzacki - spotkania.png", "voucher-luzacki-full.png"),
    ("VOUCHER świąteczny - spacery.png", "voucher-swiateczny-full.png"),
]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    missing = [entry[0] for entry in SOURCES if not os.path.exists(entry[0])]
    if missing:
        print("Brakuje plików źródłowych:", file=sys.stderr)
        for item in missing:
            print("  -", item, file=sys.stderr)
        print("\nWgraj je i uruchom skrypt ponownie.", file=sys.stderr)

    total_src = 0
    total_out = 0
    produced = set()

    for entry in SOURCES:
        source, base, widths = entry[0], entry[1], entry[2]
        aspect = entry[3] if len(entry) > 3 else None
        avif_quality = entry[4] if len(entry) > 4 else None
        if not os.path.exists(source):
            continue
        total_src += os.path.getsize(source)
        made = build(source, base, widths, aspect, avif_quality)
        produced.update(os.path.basename(m[0]) for m in made)
        total_out += sum(m[3] for m in made)
        sizes = ", ".join(
            f"{os.path.basename(p)} {w}x{h} {kb // 1024}KB" for p, w, h, kb in made
        )
        print(f"{base}: {sizes}")

    for source, name in COPIES:
        if not os.path.exists(source):
            continue
        shutil.copyfile(source, os.path.join(OUT_DIR, name))
        produced.add(name)
        print(f"{name}: kopia 1:1 ({os.path.getsize(source) // 1024} KB)")

    # skasuj pliki z poprzednich uruchomień (np. po zmianie listy szerokości)
    for stale in sorted(os.listdir(OUT_DIR)):
        if stale not in produced:
            os.remove(os.path.join(OUT_DIR, stale))
            print(f"usunięto nieużywany {stale}")

    print()
    print(f"Źródła:  {total_src / 1_048_576:.1f} MB")
    print(f"Wynik:   {total_out / 1_048_576:.1f} MB")


if __name__ == "__main__":
    main()
