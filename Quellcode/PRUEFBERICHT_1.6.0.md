# Prüfbericht 1.6.0 – 20.10.2026

## Änderungen

- `card_style.py`: proportionale Bild-/Canvasdarstellung auch bei begrenzter Fensterhöhe, Vollbildgestaltung und idempotentes Upgrade der Vorlagen-Skripte. Begrenzte Höhe bei erzwungener Bildbreite kann trotz `height:auto` zu einem falschen Verhältnis führen; die Bildhöhe wird nun nicht separat durch konkurrierende Maximalhöhen gekappt. Die Vollbildansicht berechnet eine gemeinsame Einpassung anhand des natürlichen Seitenverhältnisses.
- `card_interactions.js` (neu): Bildvergrößerung per Klick für normale Bilder, native Bildmasken und Bildreihenfolge. Bild bzw. gesamter Bild-/Canvas-/Maskenbereich wird als derselbe DOM-Knoten in die vergrößerte Ansicht verschoben und anschließend zurückgesetzt. Keine unmaskierte Kopie, keine Medien-/Sammlungsänderung. Zugängliche Beschriftung, Schließen und Escape, proportionale Neuberechnung bei Größenänderungen.
- `reviewer_interactions.py` (neu): gezielte Desktop-Antwortsperre für verwaltete Bildreihenfolgen; asynchroner Schritt statt kompletter Antwort, Schutz gegen doppelte/veraltete Rückmeldungen und Tastenwiederholungen. Vollbild stellt Fensterzustand und sichtbare Werkzeug-/Bewertungsleisten wieder her. Normale Karten verwenden weiterhin Ankis bisherigen Antwortpfad.
- `reviewer_masks.py`: an die aktuelle Karte und den Reviewer gebundene Vollbild-Anbindung mit eigener zufälliger Kennung; veraltete/fremde Nachrichten werden nicht ausgeführt.
- `mask_editor.py`: keine Texte/Zahlen auf normalen Bildmasken; bei Bildreihenfolge ausschließlich laufende Schrittnummern entsprechend der wirksamen Reihenfolge. Die Auswahlbeschriftungen sind ebenfalls von internen IDs getrennt.
- `card_extras.py`: Vorlagen-Upgrade bleibt trotz neuer Präsentationsskripte schreibfrei, wenn der fertige Modellzustand unverändert ist.

Zusätzlich: Diagnose-Allowlist, Manifest, Dokumentation und Tests aktualisiert. Synchronisationsparser, Transport und lokale Speicherlogik bleiben unverändert. Die bisherigen Apple-like-UI-Regeln zu ruhiger Hierarchie, semantischen Farben und klaren Controls werden fortgeführt; keine neuen Abhängigkeiten oder Animationen.

## Standardverhalten / Einbindung

Das [Anki-Handbuch zum Lernen](https://docs.ankiweb.net/studying.html) beschreibt Leertaste/Enter als Auslöser für die Antwort. Für die add-on-eigene Bildreihenfolge wird deshalb Ankis tatsächlicher Desktop-Antwortpfad gezielt ergänzt. Geprüft wurden zusätzlich die lokal vorhandenen Reviewer-Methoden und Hooks in Anki/aqt 26.09.3. Der native untere Antwortknopf sowie die Tastatur erreichen dieselbe Sperre. Nach dem letzten Aufdeckschritt ist ein weiterer Aufruf nötig, um die Rückseite zu sehen; es gibt keine automatische Lernbewertung durch das Add-on.

Normale Bildverdeckung bleibt Ankis native Darstellung; Referenz: [Anki-Handbuch zur Bildverdeckung](https://docs.ankiweb.net/editing.html#image-occlusion). Die Bild-/Templateanpassung orientiert sich außerdem an [Styling & HTML](https://docs.ankiweb.net/templates/styling.html). Eine eingebaute allgemeine Einstellung zur erzwungenen add-on-eigenen Schrittfolge wird nicht vorausgesetzt.

## Erhalt von Daten

Nur Vorlagen, Styling und Laufzeitdarstellung ändern sich. Die gespeicherten Masken-/Bildfolgefelder werden für diese UI-Änderungen nicht umgeschrieben. Sichtbare Nummern werden aus der Reihenfolge abgeleitet, während Abdeckungs-IDs, Blockherkunft, Kartenidentitäten und lokale Quell-/Korrekturdaten unverändert bleiben. Deshalb bleiben ältere lokale Notizen ohne erneuten Notion-Abruf bearbeitbar. Bei Vollbild wird keine zusätzliche Bildkopie geladen und kein Lernfortschritt gespeichert.

## Isolierte Tests

**71 Unit-/Integrationstests bestanden**: die bisherigen 66 sowie fünf neue Prüfungen in `test_interactions.py`:

1. Der Qt-Zeichenpfad zeichnet nur bei Bildreihenfolge Nummern; nicht bei einer oder mehreren einzeln abgefragten Masken. Geänderte sichtbare Reihenfolge nummeriert nicht die gespeicherten IDs um.
2. Antwortanforderungen ergeben einzelne Schritte; auch nach dem letzten Schritt wird erst die nächste Anforderung zur Antwort.
3. Ausstehende bzw. veraltete asynchrone Rückmeldungen überspringen keine Schritte.
4. Andere Kartentypen behalten den nativen Antwort- und Auto-Advance-Pfad; Bildreihenfolge-Fragen werden nicht automatisch komplett aufgedeckt.
5. Gehaltene Space-/Enter-Tasten werden nur bei Reihenfolge-Fragen gegen Wiederholung geschützt.

Die bestehende Qt-Bedienungsprüfung besteht weiterhin. Neue Maskennummern-/Spur-/Layoutprüfungen wurden zusätzlich bei simulierter 200-%-Qt-Skalierung ausgeführt. Die weiterhin gültigen 1.5-Prüfungen decken helle/dunkle Gestaltung, Textkontraste, größere Schrift, idempotentes Vorlagen-Upgrade sowie stabile Felder, IDs und Lernwerte ab.

## Tatsächlicher Anki-Reviewer

`test_reviewer.py` startet eine unabhängige AnkiQt-Instanz mit eindeutigem Prozessschlüssel und neuem synthetischem Profil. Echter Reviewer, Scheduler, Chromium, native Bildmasken und Qt-Dialoge; kein persönliches Profil und kein produktiver Sync.

Die bisherigen Eingabe-, Cloze-, Vergleichs-, Bildmodus-, Bildfolge-, Header-/Link-, Speicher-/Abbruch-, Lösch- und responsive Designprüfungen bestehen.

Zusätzlich bestanden:

- Anonyme Bilder 1200×300 und 300×1200 bei Viewports 320×250, 520×340 und 1100×500. Das gemessene Bildseitenverhältnis bleibt erhalten; natives Canvas und Bild stimmen in Breite/Höhe überein.
- Normales Bild, Einzel-/Mehrfach-Bildmasken und Bildreihenfolge öffnen durch Bildklick die echte Desktop-Vollbildansicht. Das ganze Bild passt proportional in den Bereich. Escape schließt ohne Seitenwechsel/Bewertung und stellt den vorherigen Fensterzustand wieder her.
- Derselbe DOM-Knoten bleibt erhalten. Verdeckte native Bereiche werden anhand der Canvas-Pixel vor/während/nach Vollbild kontrolliert; teilweise aufgedeckte Bildreihenfolgen behalten ihren Schrittstand.
- Echte Qt-Tastaturereignisse für Leertaste, Return und Enter decken pro Tastendruck nur eine weitere Maske auf. Nach dem letzten Schritt bleibt der Reviewer auf „question“. Erst der nächste Tastendruck zeigt „answer“, ohne `reps` zu verändern.
- Unterer nativer Antwortknopf und direkter Reviewer-Antwortpfad umgehen die Sperre nicht. „Zurücksetzen“ verlangt die Schritte erneut. Simulierte autorepeat-KeyPress-Ereignisse überspringen keine Schritte.

Native Bildschirmaufnahmen aus Qt und dem tatsächlichen Reviewer wurden erzeugt und visuell stichprobenartig kontrolliert. Alle Inhalte sind anonym. Hoch-/Querformat und Vollbild werden zusätzlich anhand tatsächlicher DOM-Geometrie und sichtbarer Masken geprüft; die Tests beruhen nicht nur auf Screenshots.

## Grenzen

Umgebung: Windows, Anki/aqt 26.09.3, Qt 6.11.2, Python 3.12.14, unsichtbare Qt-/Chromium-Laufzeit mit Software-Fallback. Direkt offen: Nutzer-Build mit Python 3.13.15, manuelle Bedienung/Display-/Flackerprüfung, echte Windows-DPI-/Monitorwechsel, Screenreader und Betriebssystem-Hochkontrast, AnkiMobile/AnkiDroid sowie Mediensync/Offlinebetrieb eines zweiten Geräts.

Die starke Antwortsperre und das bildschirmfüllende native Fenster sind ausdrücklich Desktop-Funktionen. Andere Clients erhalten die Bild-/Sequenzskripte und eine Ansicht im Web-Viewport, sind aber nicht direkt getestet. Das Verhindern ihrer nativen Antwortaktionen und identisches Vollbildverhalten werden nicht behauptet. Im Qt-Maskeneditor bleibt ein Klick auf eine Maske eine Auswahl-/Bearbeitungsaktion; Bildklick-Vollbild betrifft die Lernkarten.

Keine Änderungen an Notion, dem separaten Anki-Skill, persönlichen Zugangsdaten oder produktiven Sammlungen. Alte Versionsarchive bleiben erhalten.

## Paketprüfung

Installationspaket und Quellcodearchiv wurden auf ZIP-Integrität, Versionsmanifest, leere Konfiguration und erforderliche Dateien einschließlich `card_interactions.js` geprüft. Keine Testprofile oder Testmedien im Installationspaket. Ein separater Build aus dem entpackten vollständigen Quellcodearchiv erzeugt inhaltlich identische Paketeinträge.
