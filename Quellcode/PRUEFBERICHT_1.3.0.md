# Prüfbericht 1.3.0 – 20.10.2026

## Umgesetzt

- Getrennte Bildmaskenkontrolle pro Notion-Block-ID, auch bei identischen Bildern/Koordinaten. Alle Karten einer Notiz werden zusammen kontrolliert. Herkunft, Typ, Bildinhalt und Quell-/Korrekturmasken liegen getrennt im lokalen Notizmetadatum.
- Nativer Qt-Maskeneditor mit Originalbildkoordinaten, Auswahl/IDs, Verschieben, acht Größen-Griffen, Kontextmenü, Undo/Redo, transaktionalem Bestätigen/Abbrechen und verständlichen Typ-/Modus-/Kartenangaben.
- Lokale Korrekturen werden bei unverändertem Quellstand wiederverwendet. Neue Bild-/Masken-/Typquelle erzwingt Prüfung und gegebenenfalls Konflikthinweis. Änderungen nur an Aufgabe/Metadaten verlieren passende Korrekturen nicht.
- Eigene Inline-Eingaben an jeder aktuellen Cloze-Stelle, mit definiertem NFC-/Leerraumvergleich und getrennten Rückmeldungen. Native Cloze-Karten-/Nummernidentität bleibt bestehen. Alte nicht ausgewählte 1.2-Notizen behalten ihren funktionsfähigen nativen Einzelfeld-Fallback.
- Optionaler sicherer `[Header]`-Abschnitt bei allen Typen; hinten geschlossenes „Mehr …“, native Linkweiterleitung, keine zusätzlichen Karten aus Cloze-ähnlichem Metadatentext.

## Isolierte Tests

50 Unit-/Integrationstests bestanden:

- 11 bestehende Parser-/Planungstests (`test_core.py`).
- 7 Transport-/Retry-/Abbruchtests (`test_transport.py`).
- 12 bisherige Integrationsprüfungen, einschließlich großer Importe, Undo, ID-/Lernplanungserhalt, lesbarer Stapelnamen und Quellenschutz (`test_integration.py`).
- 8 Kartentypprüfungen, darunter sieben Notizen/acht Karten, identischer Sync, individuelle Kartenlöschung und Typwechsel (`test_types.py`).
- 12 neue Prüfungen für getrennte Kontrollen, verweigerte Teilfreigabe, dauerhafte lokale Geometrie, Quellkonflikte, lokale Löschung mit erhaltenem Lernfortschritt, Abbrechen aller Entwürfe, Header bei allen Typen, sichere Links/Script-Text, Validierung, Header-Bildaufteilung, Legacy-Notiztypen und kompatibles Upgrade nicht ausgewählter Quellen (`test_features.py`). Native Mausbewegung und Größenänderung wurden bei zwei Fenster-/Bildskalierungen geprüft; Kontextmenüpfad und Undo/Redo ebenfalls.

`test_ui.py` prüft weiterhin Menüs, Konfiguration, Seitenauswahl, Abrufabbruch, sichere Diagnose und Fortschritt im Hauptthread.

## Tatsächlicher Anki-Reviewer

`test_reviewer.py` startet eine eigene AnkiQt-Instanz mit eindeutiger Instanzkennung und neuem temporärem synthetischem Profil. Es verwendet den echten Reviewer, Scheduler und Chromium. Qt läuft unsichtbar.

Geprüft: natives `[Eingabe]`; Inline-Feldposition innerhalb der Lücke; mehrere gleichzeitige Felder; Unicode-NFC und Leerraum; Tab/Enter; richtige/falsche individuelle Rückmeldungen; leere Eingaben beim nächsten Versuch; keine automatische Lernbewertung. Header wurde bei allen Typen auf der Frage verborgen und auf der Antwort zunächst geschlossen geprüft; Auf-/Zuklappen und Links laufen über Ankis vorgesehenen URL-Handler. Normale Bewertungsbuttons bleiben vorhanden. Script-ähnlicher Notion-Text wird nicht ausgeführt.

Vorhandene native Bildverdeckung, beide Modi und pixelweises Aufdecken, Skalierung und Bildfolge 2→1→0 mit normaler Bewertung wurden erneut geprüft. Drei Notizen mit identischem Originalbild öffneten drei eigenständige Qt-Maskeneditoren.

## Umgebung und offene Grenzen

Anki/aqt 26.09.3, Qt-Laufzeit 6.11.2, Python 3.12.14, Windows. Die unsichtbare Qt-/Chromium-Umgebung verwendet Software-Fallback bei GPU-Warnungen; die Funktionsprüfungen bestehen. Eine manuelle visuelle Abnahme auf dem Nutzergerät wurde nicht vorgenommen.

Noch direkt zu prüfen: Python 3.13.15 im Nutzer-Desktop-Build, AnkiMobile/AnkiDroid, Mediensync/Offline-Nutzung auf einem zweiten Gerät und manuelle Bedienung mit dessen Display-/DPI-Einstellungen. Inline-Vergleich und Bildfolge benötigen JavaScript. Mindestens eine Maske pro lokaler Bildnotiz bleibt erforderlich; eine vollständig maskenlose Notiz wird nicht gespeichert.

Keine persönliche Sammlung diente als Testbestand. Keine produktive Synchronisation, keine Änderungen an Notion oder am separat erstellten Anki-Skill. Paket enthält keine Zugangsdaten oder privaten Testseitenbilder.
