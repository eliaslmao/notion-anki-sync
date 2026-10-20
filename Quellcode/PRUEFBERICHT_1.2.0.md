# Prüfbericht 1.2.0 – 20.10.2026

## Ergebnis

Die ausdrücklich angegebene Notion-Testseite wurde unverändert gelesen. Ein separater lesender Abruf mit dem neuen Parser ergibt **7 Notizen / 8 Karten**. Es wurde dafür keine Anki-Sammlung geöffnet. Notion-Inhalte und Anki-Skill wurden nicht verändert.

## Isolierte automatisierte Prüfungen

- `test_core.py`: 11 Tests bestanden (bisherige Aufteilung/Hierarchie/Validierung/Planung).
- `test_transport.py`: 7 Tests bestanden (Dosierung, Retry-After inklusive >60 Sekunden, derselbe Pagination-Cursor, begrenzte Wiederholungen, Rechte-/Tokenfehler, Abbruch, unvollständige Antworten).
- `test_integration.py`: 12 Tests bestanden (vorhandene Funktionen einschließlich großer Importe, Undo, Migration alter IDs, lesbare Stapelnamen und Quellenschutz).
- `test_types.py`: 8 Tests bestanden (sieben Formate → 7 Notizen/8 Karten; identischer Sync; neue/entfernte Cloze-/Masken-IDs; IDs/Lernfortschritt; freigabepflichtige Typwechsel; unsichere Migration ohne bleibende Änderungen; Bildlücken→Bildlücke mit ID 2 und Undo).
- `test_ui.py`: Qt-Tests für Konfiguration, Menü-Klick, Seitenauswahl, Abbruch, unvollständigen Abruf ohne Sammlungsschreiben, Diagnose, Fortschritt und Hauptthread-Zugriffe bestanden.

## Tatsächlicher Reviewer

`test_reviewer.py` startet ein eigenes AnkiQt mit eigener Instanzkennung und einem neu erstellten synthetischen Profil. Qt läuft unsichtbar; die tatsächlichen Reviewer-/Scheduler- und Chromium-Webview-Komponenten werden verwendet.

Geprüft: native Eingabefelder, eingegebene Antworten und natives positives Vergleichsergebnis; Cloze-Eingabe; native Bildverdeckung mit Originalbild und Canvas; aktive/inaktive Masken pixelweise auf Frage und Rückseite; beide Bildlücken-Modi; prozentuale Ausrichtung bei verkleinertem Bild; Bildfolge 2→1→0; normale Bewertung dieser gesamten Karte über eine echte Scheduler-Warteschlange; gemeinsame lokale Maskenvorschau mit einem Originalbild für drei Aufgaben.

## Umgebung und Grenzen

Offizielle Python-Pakete Anki/aqt 26.09.3, Qt-Laufzeit 6.11.2, Python 3.12.14, Windows. Headless-Qt/Chromium meldet fehlende GPU-Kontexte und verwendet Software-Fallback; die Funktionsprüfungen bestehen. Es wurde keine manuelle visuelle Desktop-Abnahme durchgeführt.

Offen: der genaue Desktop-Build 29bb700b mit Python 3.13.15; AnkiMobile/AnkiDroid; Mediensync und Offline-Review auf einem zweiten Gerät. Diese Kompatibilität wird nicht behauptet. Die persönliche Sammlung war kein Testdatenbestand. Kein produktiver Sync wurde ausgeführt.
