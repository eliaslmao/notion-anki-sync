# Notion Safe Sync 1.5.0

## Installation

`Notion_Safe_Sync.ankiaddon` installieren und Anki neu starten. Beim Öffnen des Profils aktualisiert das Add-on seine eigenen Kartenvorlagen. Ein Notion-Abruf ist dafür nicht nötig. Vorhandene Notizinhalte, Maskenkorrekturen, Karten-IDs und Lernfortschritte bleiben erhalten. Das alte Add-on `576859862` bleibt deaktiviert.

## Zwei Bildvarianten

- **Bildmasken:** Die markierten Bereiche werden einzeln abgefragt.
- **Bildreihenfolge:** Die Bereiche werden Schritt für Schritt in ihrer vorgegebenen Reihenfolge aufgedeckt.

Diese Bezeichnungen erscheinen in der Bildauswahl und als Überschrift im Bearbeitungsfenster. Technische Kartentypen, erzeugte Kartenanzahlen und ID-Listen werden dort nicht mehr angezeigt. Die Nummern direkt auf den Masken helfen weiterhin bei Auswahl und Reihenfolge.

## Bilder bearbeiten

Über **Extras → Notion Safe Sync: Bildmasken bearbeiten** wählst du die gewünschten Bildaufgaben aus. Einzel-/Mehrfachauswahl und „Alle auswählen“ bleiben verfügbar. Auf der Lernkarte öffnet **„Masken bearbeiten“** direkt die aktuelle Aufgabe. Beide Einstiege arbeiten lokal und benötigen keine Notion-Verbindung.

Im Fenster stehen die Überschrift, die Aufgabe und das Bild im Mittelpunkt:

- Ziehen verschiebt eine Maske; die Griffe ändern ihre Größe.
- Die Liste „Maske auswählen“ wählt einen Bereich auch per Tastatur aus.
- Pfeiltasten verschieben; Umschalt + Pfeiltasten ändert die Größe. Strg bewegt in größeren Schritten.
- Rechtsklick oder Entf entfernt eine Maske. Mindestens eine muss bleiben.
- „Rückgängig“ / „Wiederholen“ und Strg+Z / Strg+Y bleiben verfügbar.
- „Hilfe“ zeigt die Bedienhinweise bei Bedarf.

**„Übernehmen“** bestätigt den Entwurf. Bei mehreren Aufgaben werden alle Entwürfe gemeinsam gespeichert, nachdem alle Fenster bestätigt wurden. Abbrechen verwirft die Entwürfe des gesamten Aufrufs. Unverändertes Übernehmen schreibt nichts. Entfällt durch eine Maskenlöschung eine Lernkarte, erscheint weiterhin eine ausdrückliche Bestätigung mit den betroffenen Karten und ihrem Lernfortschritt.

## Einheitliche Darstellung

Alle sieben eigenen Kartentypen verwenden dieselbe Systemschrift, ruhige Abstände, konsistente Schaltflächen sowie passende Farben für Ankis helle und dunkle Darstellung. Lerninhalte bleiben linksbündig in einer begrenzten Lesebreite. Eingaben, Rückmeldungen und Links sind klar erkennbar; der Header bleibt hinten unter „Mehr …“ geschlossen. Die Bildreihenfolge behält ihren Aufdeckknopf, jetzt mit der kürzeren Bezeichnung „Weiter aufdecken“.

Auch verwaltete ältere Karten erhalten im Desktop-Reviewer dieselbe Grundgestaltung. Ihre möglicherweise mit fremden Notizen geteilten Notiztypen werden dabei nicht geändert. Außerhalb des Desktop-Reviewers behalten solche Altkarten ihre bisherigen Vorlagen. Die eigenen aktuellen Vorlagen enthalten die neue Gestaltung direkt.

Die bestehenden Notion-Marker und internen Notiztypen bleiben kompatibel. Es ist keine Umbenennung deiner Inhalte nötig. Lokale Korrekturen bleiben bei unveränderter Quelle erhalten. Notion-Inhalte und der separate Anki-Skill wurden nicht geändert.

## Prüfung und Grenzen

66 automatisierte Unit-/Integrationstests sowie Qt-Bedienungs- und echte AnkiQt-Reviewer-Prüfungen mit synthetischen Profilen bestanden. Geprüft wurden helle/dunkle Ansichten, Editorfenster in zwei Größen, simulierte 100/125/200 % Skalierung sowie Karten bei 320/768/1100 Pixel Breite und 150 % Textgröße. Textkontraste der definierten Paletten erfüllen mindestens 4,5:1; Schaltflächen sind mindestens 44 Pixel hoch. Native Bildschirmaufnahmen wurden visuell geprüft.

Testumgebung: Anki/aqt 26.09.3, Qt 6.11.2, Python 3.12.14. Direkt offen bleiben dein Python-3.13.15-Build, manuelle Bedienung auf dem tatsächlichen Display, echte Windows-DPI-/Monitorwechsel, Screenreader-/Hochkontrast-Abnahme und mobile Clients. Es wurde keine produktive Sammlung oder Synchronisation verwendet. Details und geänderte UI-Dateien stehen in `PRUEFBERICHT_1.5.0.md`.
