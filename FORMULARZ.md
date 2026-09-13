# Formularz kontaktowy → Arkusz Google

Formularz na stronie nie potrzebuje żadnego serwera. Wiadomości wysyła
po cichu do formularza Google, a te lądują w Arkuszu Google.

**Stan teraz:** formularz działa w trybie awaryjnym – po kliknięciu
„Wyślij wiadomość" otwiera program pocztowy z gotową treścią.
Po wykonaniu poniższych kroków zacznie zapisywać wiadomości w Arkuszu.

---

## Krok 1. Utwórz formularz Google

1. Wejdź na <https://forms.new>
2. Nazwij go np. **Kontakt – psiepopoludnie.pl**
3. Dodaj dokładnie **trzy pytania**, wszystkie typu *Krótka odpowiedź*
   (ostatnie może być *Długa odpowiedź*), w tej kolejności:

   | # | Pytanie                  |
   |---|--------------------------|
   | 1 | Imię i nazwisko          |
   | 2 | Adres e-mail / Telefon   |
   | 3 | Wiadomość                |

4. Zakładka **Odpowiedzi** → ikona Arkuszy → *Utwórz arkusz kalkulacyjny*.
5. W zakładce **Odpowiedzi** włącz **Otrzymuj powiadomienia e-mail
   o nowych odpowiedziach** – dostaniesz maila przy każdym zgłoszeniu.

## Krok 2. Znajdź trzy identyfikatory pól

1. Kliknij **Wyślij** → zakładka z ikoną łańcucha (link) → skopiuj adres.
   Wygląda tak:
   `https://docs.google.com/forms/d/e/1FAIpQLSxxxxxxxxxxxxxxxxxxxx/viewform`
   Fragment `1FAIpQLSxxxxxxxxxxxxxxxxxxxx` to **ID formularza**.
2. Otwórz ten adres w przeglądarce, kliknij prawym przyciskiem myszy
   w dowolnym miejscu → **Pokaż źródło strony** (Ctrl/Cmd + U).
3. Wyszukaj (Ctrl/Cmd + F) tekst `entry.` – znajdziesz trzy liczby,
   np. `entry.1234567890`, `entry.9876543210`, `entry.1122334455`.
   Występują w tej samej kolejności co pytania w formularzu.

> Jeśli wolisz, po prostu prześlij mi link z punktu 1 – odczytam
> identyfikatory i wpiszę je za Ciebie.

## Krok 3. Wklej wartości do `index.html`

Znajdź w pliku `index.html` blok `const GOOGLE_FORM = {` (blisko końca,
w sekcji `<script>`) i podmień cztery wartości:

```js
const GOOGLE_FORM = {
    action: 'https://docs.google.com/forms/d/e/1FAIpQLSxxxxxxxxxxxxxxxxxxxx/formResponse',
    name:    'entry.1234567890',
    contact: 'entry.9876543210',
    message: 'entry.1122334455'
};
```

Uwaga: adres kończy się na **`/formResponse`**, a nie `/viewform`.

## Krok 4. Sprawdź

1. Otwórz stronę, wypełnij formularz, kliknij **Wyślij wiadomość**.
2. Powinien pojawić się zielony komunikat „Dziękuję za wiadomość!".
3. Zajrzyj do Arkusza Google – wiersz z Twoim testem już tam jest.

---

## Dobrze wiedzieć

- **Formularz musi przyjmować odpowiedzi** (zakładka *Odpowiedzi* →
  przełącznik *Przyjmowanie odpowiedzi* włączony).
- **Nie zaznaczaj** w ustawieniach formularza opcji „Ogranicz do 1 odpowiedzi"
  ani „Zbieraj adresy e-mail" – obie wymagają logowania w Google
  i zablokują wysyłkę ze strony.
- Wysyłka działa w tzw. trybie `no-cors`: przeglądarka nie może odczytać
  odpowiedzi Google, więc strona zakłada sukces, o ile nie zerwało
  połączenia. To standardowe zachowanie przy tym rozwiązaniu.
- Ukryte pole „company" to pułapka na boty – jeśli zostanie wypełnione,
  wiadomość nie jest wysyłana. Nie usuwaj go.
- Adres awaryjny (`julia@psiepopoludnie.pl`) jest w `index.html`
  w stałej `CONTACT_EMAIL`.
