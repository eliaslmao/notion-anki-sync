# Prüfbericht 1.4.0 – 20.10.2026

## Änderung

Lokale Auswahl und Bearbeitung verwalteter Bildnotizen ohne Netzwerk, gemeinsame validierte Speicherung für Menü und Reviewer, gezielte Desktop-JS-Brücke, Ersatz des nativen Toggle-Masks-Buttons, reparierter Qt-Zeichenbereich und deutlicher abgesetzter Header. Neue Module: `local_masks.py`, `local_mask_ui.py`, `reviewer_masks.py`.

Beide Einstiege erzeugen Entwürfe. Alle ausgewählten Notizen werden vor dem ersten Schreibvorgang erneut gelesen und validiert. Nur Maskengeometrie und davon abgeleitete Felder/Herkunftsdaten werden geschrieben. Bei unverändertem Speichern gibt es weder Notizschreibvorgänge noch einen neuen Undo-Eintrag. Kartenlöschungen erfordern die genaue Freigabe der betroffenen Karten-IDs. Undo-Anker werden fortlaufend zusammengeführt; ein Fehler führt zur gemeinsamen Rücknahme. Keine behauptete Absturz-Atomarität.

## Automatisierte Tests

**60 Unit-/Integrationstests bestanden**:

- Die bisherigen 50 Tests in `test_core`, `test_transport`, `test_integration`, `test_types` und `test_features`.
- Zehn neue Prüfungen in `test_local_masks`: Offline-Auswahl mit Titel/Stapel/Typ und Alle/Keine/Einzelauswahl; Erhalt von Notiz-/Karten-IDs und Lernwerten; unveränderter Sync erhält lokale Korrekturen, geänderte Quelle erzwingt Kontrolle; genaue Löschfreigabe und Undo; Bildfolge-Schrittentfernung; fehlende/veränderte Medien; schreibfreies unverändertes Speichern; veraltete/mehrdeutige Entwürfe; absichtlicher Fehler bei zweiter Notiz mit vollständiger Rücknahme; Editor-Neuzeichnung und idempotentes Upgrade vorhandener 1.3-Vorlagen. Die beiden letzten Themen sind getrennte Tests; die ersten Auswahl-/Erhaltungstests decken jeweils mehrere Aspekte ab.

`test_ui.py` besteht weiterhin: sechs Menüaktionen, Konfiguration, Seitenauswahl, Abbruch ohne Netzwerk, unvollständiger Abruf ohne Anwendung, sichere Fehlerdiagnose, Fortschritt/Abbruch im Hauptthread.

## Tatsächlicher Anki-Desktop-Reviewer

`test_reviewer.py` startet eine separate AnkiQt-Instanz mit eindeutiger Instanzkennung und neuem synthetischem Profil im Arbeitsbereich. Kein persönliches Profil wird geöffnet. Verwendet werden echter Reviewer, Scheduler, Chromium, native Bildverdeckung und Qt-Editor; keine bloße Browser-Nachbildung.

Bestanden:

- Bisherige Reviewer-Prüfungen: Eingabe, Inline-Cloze-Felder, NFC/Leerraum, Tab/Enter, individuelle Rückmeldung/Reset, beide nativen Bildverdeckungsmodi, Bildfolge einschließlich normaler Bewertung, Header/Linkweiterleitung und getrennte Maskendialoge.
- Echte JS-Nachricht des neuen Buttons → lokale QueryOp → echter Qt-Dialog → CollectionOp für alle drei Bildtypen. Richtige Notiz und Vorauswahl der aktuellen Abdeckungs-ID bei Bildlücken. Kein Notion-Request/Fetcher erlaubt.
- Speichern auf Frage und Antwort behält dieselbe Karten-ID und Reviewer-Seite; `reps` bleibt unverändert. Abbrechen nach Geometrieänderung und unverändertes Bestätigen behalten den Sammlungsstand. Mehrere Karten derselben Notiz bleiben konsistent.
- Kartenlöschung aus dem Reviewer: Vorschau enthält die genaue Karten-ID, Ablehnen speichert nichts, Zustimmung entfernt nur die freigegebene Karte und erhält ihre gerade angezeigte Schwesterkarte. Beim ausdrücklichen Löschen der angezeigten Karte erscheint die Stapelübersicht mit Hinweis; ein testweise gesperrter `nextCard`-Aufruf wird nicht ausgelöst.
- Lokale Mehrfachauswahl mit echten Dialogen: jede Notiz einmal; Abbrechen des zweiten Editors verwirft auch den ersten Entwurf.
- Außerhalb des Desktop-Reviewer-Kontexts kein Bearbeiten-Button im gespeicherten Karten-HTML oder Preview-Render; unpassender Brückenkontext wird verworfen.
- Header bei allen sieben Typen auf der Frage abwesend, auf Antwort geschlossen; berechneter relativer Abstand und Trennlinie bei 540/1200 Pixel Fensterbreite und heller/dunkler Body-Darstellung. Ohne Header wird weiterhin kein Abschnitt erzeugt (bestehende Parser-/Vorlagentests).

## Qt-Zeichnen / Skalierung

Ursache: Eigene kosmetische Auswahlstifte und größenkonstante Griffe wurden außerhalb des ursprünglichen QGraphicsRectItem-Zeichenbereichs gezeichnet. Die Standardbegrenzung deckte ihre alten Positionen nicht zuverlässig ab. Der neue Zeichenbereich umfasst Griffe/Stifte auch bei Ansichtsänderungen. Geometrieänderungen werden Qt vor dem Skalieren mitgeteilt; FullViewportUpdate zeichnet den sichtbaren Bildbereich pro Frame vollständig neu, ohne wiederholtes Entfernen/Neuanlegen während des Ziehens.

Native Mausbewegungs-/Größenänderungstests bestehen weiterhin. Neue Rasterprüfungen vergleichen die aktuelle Darstellung mit einer erzwungenen Neuzeichnung und prüfen, dass keine blauen Auswahlpixel außerhalb aktueller Auswahlrahmen/Griffe liegen. Geprüft: Verschieben, Größenänderung, Auswahlwechsel, Undo, Redo, zusätzlicher Ansichtszoom und Fenstergrößen 600×500 / 1250×900. Bestanden bei Qt-Skalierungsfaktor 1, 1.25 und 2. Das simuliert Skalierung, ersetzt keine manuelle Windows-/DPI-Abnahme. Synthetische Editor-Screenshots liegen nur in `work/`, nicht im Installationspaket.

## Umgebung / Grenzen

Windows, Anki/aqt 26.09.3, Python 3.12.14, Qt 6.11.2. Qt/Chromium offscreen mit Software-Fallback; GPU-/Offscreen-Warnungen verhindern die Tests nicht. Für lesbare native Testdialoge lädt der Test bei Bedarf die vorhandene Windows-Schrift Arial; dies ändert weder Add-on noch Systemkonfiguration.

Direkt offen: Python 3.13.15 im Nutzer-Desktop-Build, manuelle Bedienung/visuelle Abnahme auf dem tatsächlichen Display, echte Windows-DPI- und Monitorwechsel, AnkiMobile/AnkiDroid sowie Mediensync und Offlinebetrieb eines zweiten Geräts. Subjektiv sichtbares Flackern ist durch die unsichtbare Laufzeit nicht manuell beurteilbar.

Wird die aktuell angezeigte Karte ausdrücklich entfernt, wechselt die Oberfläche zur Stapelübersicht mit Hinweis. Keine Bewertung und kein Aufruf der nächsten Karte. Mindestens eine Maske pro Notiz bleibt erforderlich. Filterstapel oder über mehrere Stapel verteilte Karten werden vor lokaler Bearbeitung abgewiesen.

Keine produktive Synchronisation, keine persönliche Sammlung, keine Änderungen an Notion oder dem separaten Anki-Skill. Pakete enthalten leere Konfiguration statt Zugangsdaten sowie keine synthetischen Profilbestände oder Testbilder. Das Quellcodearchiv enthält Tests, Dokumentation und das Buildskript.

## Paketprüfung

Installationspaket und Quellcode-ZIP wurden auf ZIP-Integrität, Manifestversion, leere Konfiguration und erwartete Dateien geprüft. Das Installationspaket enthält keine Tests, Medien oder Profilbestände. Der vollständige Quellcode wurde separat entpackt und mit seinem mitgelieferten Buildskript neu gebaut; die Einträge des resultierenden Installationspakets sind inhaltlich identisch. Alte Versionsarchive bleiben erhalten.
