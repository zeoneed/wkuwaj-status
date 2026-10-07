# Dostępność Wkuwaj.pl

Zewnętrzny monitor publicznej sondy `https://wkuwaj.pl/health.php`: poprawny certyfikat HTTPS, bez przekierowań, HTTP 200 i dokładnie `{"status":"ok"}`. Kontrola planowana co 5 minut; timeout 10 sekund. Alarm po dwóch kolejnych błędach, powrót po dwóch kolejnych poprawnych kontrolach. Stan jest zapisany w `state/production.json`.

Alarm i powrót trafiają do właściciela `@zeoneed` przez powiadomienia GitHub o zgłoszeniu i wzmiance. Nie ma powiadomień po każdej próbie. Odbiorca ustala adres e-mail w istniejących ustawieniach GitHub. Logi każdego wykonania są w zakładce Actions. Nie są pobierane konta, materiały, klucze ani dane klientów; repozytorium nie zawiera kodu aplikacji.

Harmonogram jest włączony przez zmienną repozytorium `MONITOR_ENABLED=true`. Wydanie publiczne uruchomiono 7.10.2026 o 20:05 UTC; dwie ręczne kontrole produkcyjnej sondy po wdrożeniu zwróciły HTTP 200 i poprawny JSON (Actions #3, próby 1 i 2). Ręczne tryby `test-failure` (nieistniejący adres) i `test-recovery` (publiczna strona główna) korzystają z osobnego stanu i służą sprawdzeniu dostarczenia alarmu bez wyłączania strony.

GitHub może opóźnić albo pominąć planowaną kontrolę. Nie gwarantuje alarmu w ciągu 10 minut ani dostępności monitoringu podczas awarii GitHub. Publiczne harmonogramy mogą zostać wyłączone po 60 dniach bez aktywności; zapis stanu ma miesięczny znacznik utrzymania, ale właściciel powinien raz w miesiącu sprawdzić, że Actions nadal wykonuje kontrole i dostarcza alarmy. Standardowe maszyny GitHub w publicznym repozytorium są bezpłatne.

Po alarmie sprawdź wynik sondy, czas ostatniego wdrożenia, panel hostingu i prywatny log PHP. W zgłoszeniu publicznym nie zamieszczaj kluczy, SQL ani danych klientów.

Dokumentacja: [harmonogramy i ograniczenia](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [powiadomienia](https://docs.github.com/en/subscriptions-and-notifications/how-tos/managing-github-actions-notifications), [rozliczenia](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
