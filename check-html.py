#!/usr/bin/env python3
"""
Kontrola pliku po minifikacji
=============================

Minifikator potrafi po cichu zjeść spację między dwoma znacznikami
(np. `<strong>Tekst</strong> <a>link</a>`) i skleić wyrazy albo urwać
zawartość `<style>`. Efekt widać dopiero na żywej stronie, więc przed
publikacją porównujemy plik przed i po minifikacji:

  * czy widoczny tekst jest identyczny (po sprowadzeniu białych znaków
    do pojedynczych spacji),
  * czy zgadzają się wszystkie adresy (`href`, `src`, `srcset`),
  * czy liczba znaczników jest taka sama,
  * czy style i skrypty nie zostały opróżnione,
  * czy wszystkie znaczniki są domknięte.

Użycie:
    python3 check-html.py oryginal.html zminifikowany.html

Kod wyjścia 1 oznacza, że minifikacja coś popsuła - przepływ w GitHub
Actions przerwie wtedy publikację.
"""

import re
import sys
from html.parser import HTMLParser

# znaczniki, które w HTML nie mają zamknięcia
VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# tu nie ma tekstu widocznego dla czytelnika
INVISIBLE = {"script", "style"}


class Analyzer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.urls = []
        self.tags = {}
        self.stack = []
        self.errors = []
        self.inline_css = 0
        self.inline_js = 0
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        self.tags[tag] = self.tags.get(tag, 0) + 1
        for name, value in attrs:
            if name in ("href", "src", "srcset", "imagesrcset") and value:
                self.urls.append(value.strip())
        if tag in INVISIBLE:
            self._skip += 1
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        self.tags[tag] = self.tags.get(tag, 0) + 1
        for name, value in attrs:
            if name in ("href", "src", "srcset", "imagesrcset") and value:
                self.urls.append(value.strip())

    def handle_endtag(self, tag):
        if tag in INVISIBLE and self._skip:
            self._skip -= 1
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for unclosed, pos in self.stack[i + 1:]:
                    self.errors.append(f"niedomknięty <{unclosed}> z wiersza {pos[0]}")
                del self.stack[i:]
                return
        self.errors.append(f"</{tag}> bez otwarcia (wiersz {self.getpos()[0]})")

    def handle_data(self, data):
        if self._skip:
            stripped = data.strip()
            if stripped:
                if self.stack and self.stack[-1][0] == "style":
                    self.inline_css += len(stripped)
                else:
                    self.inline_js += len(stripped)
            return
        self.text.append(data)

    def finish(self):
        for unclosed, pos in self.stack:
            self.errors.append(f"niedomknięty <{unclosed}> z wiersza {pos[0]}")
        return self


def analyze(path):
    parser = Analyzer()
    with open(path, encoding="utf-8") as handle:
        parser.feed(handle.read())
    return parser.finish()


def normalize(chunks):
    return re.sub(r"\s+", " ", "".join(chunks)).strip()


def first_difference(a, b):
    """Fragment wokół pierwszej różnicy - żeby dało się ją znaleźć w pliku."""
    limit = min(len(a), len(b))
    i = 0
    while i < limit and a[i] == b[i]:
        i += 1
    start = max(0, i - 60)
    return a[start:i + 60], b[start:i + 60]


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    src_path, min_path = sys.argv[1], sys.argv[2]
    src, mini = analyze(src_path), analyze(min_path)
    problems = []

    if mini.errors:
        problems.append("Zminifikowany plik ma błędy składni:\n  - " + "\n  - ".join(mini.errors[:10]))

    src_text, min_text = normalize(src.text), normalize(mini.text)
    if src_text != min_text:
        before, after = first_difference(src_text, min_text)
        problems.append(
            "Zmienił się widoczny tekst.\n"
            f"  przed: ...{before}...\n"
            f"  po:    ...{after}..."
        )

    lost = sorted(set(src.urls) - set(mini.urls))
    if lost:
        problems.append("Zniknęły adresy:\n  - " + "\n  - ".join(lost[:10]))

    for tag in sorted(set(src.tags) | set(mini.tags)):
        before, after = src.tags.get(tag, 0), mini.tags.get(tag, 0)
        if before != after:
            problems.append(f"Liczba znaczników <{tag}>: {before} -> {after}")

    # próg z zapasem: minifikator ścina style o jakieś 25%, a skrypty
    # (ze zmianą nazw zmiennych) nawet o 60% - poniżej 1/5 oryginału
    # to już nie minifikacja, tylko utrata treści
    if src.inline_css and mini.inline_css < src.inline_css * 0.2:
        problems.append(f"Style skurczyły się podejrzanie mocno: {src.inline_css} -> {mini.inline_css} znaków")
    if src.inline_js and mini.inline_js < src.inline_js * 0.2:
        problems.append(f"Skrypty skurczyły się podejrzanie mocno: {src.inline_js} -> {mini.inline_js} znaków")

    if problems:
        print("MINIFIKACJA USZKODZIŁA STRONĘ:\n", file=sys.stderr)
        for problem in problems:
            print("* " + problem + "\n", file=sys.stderr)
        return 1

    import os
    before_kb = os.path.getsize(src_path) / 1024
    after_kb = os.path.getsize(min_path) / 1024
    saved = 100 - after_kb / before_kb * 100
    print(f"HTML w porządku: {before_kb:.0f} KB -> {after_kb:.0f} KB (-{saved:.0f}%)")
    print(f"  tekst, {len(set(src.urls))} adresów i wszystkie znaczniki bez zmian")
    return 0


if __name__ == "__main__":
    sys.exit(main())
