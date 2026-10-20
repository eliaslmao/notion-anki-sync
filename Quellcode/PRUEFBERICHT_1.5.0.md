# Prüfbericht 1.5.0 – 20.10.2026

## Gestaltung und Quellen

Angewendet: der persönliche Skill `apple-like-ui`, insbesondere seine lokale `references/apple-hig-synthesis.md` und der `apple-hig-source-index.md`. Als Gestaltungsgrundlage dienen deren Zusammenfassungen zu Hierarchie, nativen Controls, Typografie, semantischen Farben, Barrierefreiheit und knappen Beschriftungen. Offizielle Referenzen: [Layout](https://developer.apple.com/design/human-interface-guidelines/layout), [Typography](https://developer.apple.com/design/human-interface-guidelines/typography), [Color](https://developer.apple.com/design/human-interface-guidelines/color), [Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons), [Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility). Der vorhandene lokale Referenzbestand wurde verwendet; keine Aussage über aktuell neueste HIG-Details und keine behauptete Apple-Konformität.

Zieloberflächen: native Qt-Dialoge unter Windows/Anki und die HTML-Kartenvorlagen in Ankis Reviewer. Keine neuen Abhängigkeiten, Apple-Marken, proprietären Schriften, dekorativen Glasflächen oder Animationen.

## Geänderte UI-Dateien

- `ui_style.py` (neu): gemeinsame, auf die eigenen Dialoge begrenzte Qt-Palette, native Systemschrift, Überschriften, Abstände, Formfelder, Auswahl-/Fokus-/Buttonzustände und deutsche Aktionsnamen.
- `card_style.py` (neu): gemeinsame adaptive Kartengestaltung mit semantischen Farbvariablen, heller/dunkler Darstellung, begrenzter Lesebreite, Systemschrift, Eingabe-/Feedback-/Header-/Bild-/Buttonstilen sowie Reduced-Motion- und Forced-Colors-Regeln.
- `mask_editor.py`: sichtbare Überschrift „Bildmasken bearbeiten“ oder „Bildreihenfolge bearbeiten“, kurze Aufgabenzeile, reduzierte Zusatztexte, aufklappbare Hilfe, Maskenauswahl, Tastaturbearbeitung und Erhalt der Auswahl bei Undo/Redo. Keine sichtbare Kartenanzahl, internen Typnamen oder technischen ID-Listen.
- `local_mask_ui.py`: einheitliche Auswahl mit den Spalten „Aufgabe“, „Stapel“, „Variante“, nur zwei sichtbaren Varianten und klarer Primäraktion „Bearbeiten“.
- `ui.py`: Gestaltung von Seitenauswahl, Verbindungseinstellungen und Fehlerdiagnose; kürzere Feldtexte und deutsche, bedarfsbezogene Sync-Zusammenfassung. Sicherheitsrelevante Löschinformationen bleiben enthalten.
- `card_extras.py`: idempotentes Design-Upgrade eigener Vorlagen und kürzere Inline-Rückmeldungen mit ausführlicher zugänglicher Beschriftung. Vergleichsregeln bleiben unverändert.
- `reviewer_masks.py`: einheitlicher Bearbeitungsbereich; verwaltete Altkarten erhalten die Gestaltung nur in ihrer aktuellen Desktop-Anzeige, ohne fremde Notizen oder gemeinsam verwendete Notiztypen zu ändern.

Zusätzlich: `diagnostics.py`, Versionsmanifest, Anleitung, Formatspezifikation und Tests aktualisiert. Parser, Transport, Synchronisationsplanung und lokale Speicherlogik wurden nicht umgebaut. Die drei internen Bildtypen bleiben für Kompatibilität und stabile Identität bestehen; ihre sichtbaren Bezeichnungen sind ausschließlich **Bildmasken** und **Bildreihenfolge**.

## Funktion und Identität

Eigene Vorlagen werden beim Profilöffnen ohne Notion-Abruf aktualisiert. Notizfelder, Quell-/Korrekturmasken und bestehende Notiz-/Kartenidentitäten werden durch das Design-Upgrade nicht verändert. Der bestehende native Cloze-/Bildmasken-Renderer, Inline-Eingaben, Aufdecken nach Reihenfolge, Header, Linkweiterleitung, Seitenauswahl, Retry-/Abbruchlogik, lokale Speicherung, ausdrückliche Löschbestätigung und Undo bleiben erhalten.

Wichtige technische Trennung: Layout und zusätzliche zugängliche Beschriftungen werden in Vorlagen/CSS/Qt geändert, nicht in der gespeicherten Bildfolge-/Maskenquelle. Dadurch bleiben bestehende lokale Bildnotizen ohne erneuten Notion-Abruf lesbar. Gemeinsame ältere Notiztypen werden nicht global umgestaltet; unverwaltete Notizen bleiben unangetastet.

## Automatisierte Prüfung

**66 Unit-/Integrationstests bestanden**: die bisherigen 60 plus sechs neue Prüfungen in `test_design.py`:

1. Genau zwei sichtbare Bildvarianten und klare Überschriften ohne technische Karten-/ID-Texte.
2. Textkontrast der semantischen hellen/dunklen Paletten: mindestens 4,5:1 für Haupt-/Nebentext, Akzent- und Warntext sowie Primärbuttons.
3. Tastaturauswahl, Verschieben, Größenänderung, Undo, Hilfe per Tastatur und zugängliche Namen/Beschreibungen.
4. Native Editorfenster bei 600×700 und 1000×860 Pixel in hell/dunkel sowie größerer Schrift, ohne abgeschnittene Hauptbereiche; Buttons mindestens 44 Pixel hoch.
5. Upgrade aus der bisherigen Darstellung bei allen sieben Typen: idempotent, unveränderte Felder, Notiz-/Karten-IDs und Lernwerte.
6. Lokale Auswahl zeigt ausschließlich „Bildmasken“ und „Bildreihenfolge“.

Die bestehende `test_ui.py` besteht: Menüs, Konfiguration, Seitenauswahl, Abbrechen ohne Netzwerk, unvollständiger Abruf ohne Anwendung, sichere Diagnose und Fortschritts-/Abbruchsignale.

Editor-Spurprüfung und neue Fensterprüfung zusätzlich bei `QT_SCALE_FACTOR=1.25` und `2` bestanden. Dies sind simulierte Qt-Skalierungen und keine reale Windows-DPI-Abnahme. Die frühere Spur-/Randgriffe-Prüfung bleibt erhalten.

## Tatsächlicher Reviewer und visuelle Prüfung

`test_reviewer.py` startet eine eigene AnkiQt-Instanz mit eindeutiger Kennung und neuem synthetischem Profil. Verwendet werden echter Reviewer, Scheduler, Chromium, native Bildmasken und Qt-Dialoge. Die bisherigen Eingabe-, Cloze-, Vergleichs-, Bildmodus-, Aufdeck-, Link-, Header-, Speicher-/Abbruch- und Löschprüfungen bleiben erfolgreich.

Zusätzlich geprüft: alle sieben eigenen Kartentypen in hell/dunkel; tatsächliche Hintergrundfarben und mindestens 4,5:1 Haupttextkontrast; Viewportbreiten 320/768/1100 Pixel mit 20/30 Pixel Textgröße ohne horizontales Überlaufen; mindestens 44 Pixel große Bearbeitungsbuttons; kompakte Bildreihenfolge-Schaltfläche „Weiter aufdecken“ und keine funktionslosen Masken in der Tab-Reihenfolge. Eine migrierte Altkarte erhält dieselbe Desktop-Grundgestaltung, während ihr gemeinsamer alter Notiztyp und eine fremde Notiz unverändert bleiben.

Native Qt-Bildschirmaufnahmen der Bildauswahl, beider Bildvarianten, hell/dunkel und kleiner/großer Fenster sowie Aufnahmen aus dem tatsächlichen Reviewer wurden erzeugt. Visuelle Stichproben wurden direkt als Bilder kontrolliert und die Gestaltung anschließend angepasst: klare Überschrift, keine Textkollisionen, ruhige Hierarchie, sichtbarer Fokus, besser gruppierte Inline-Rückmeldung und einheitliche Bild-/Buttondarstellung. Die Aufnahmen verwenden ausschließlich anonyme Fixtures; keine produktiven Inhalte.

## Umgebung und offene Grenzen

Windows, Anki/aqt 26.09.3, Qt 6.11.2, Python 3.12.14. Unsichtbare Qt-/Chromium-Laufzeit mit Software-Fallback; GPU-/Offscreen-Warnungen sind bekannt. Native Testdialoge laden bei Bedarf die auf Windows vorhandene Arial-Schrift für lesbare Aufnahmen. Im Produkt bleibt die native Systemschrift erhalten.

Nicht direkt abgenommen: Nutzer-Build mit Python 3.13.15; subjektive Bedienung/Flackern auf dem tatsächlichen Display; echte Windows-DPI-/Monitorwechsel; Screenreader, Betriebssystem-Hochkontrastmodus und vollständige Assistenztechnik-Prüfung; AnkiMobile/AnkiDroid; Mediensync und Offlinebetrieb auf einem zweiten Gerät. Forced-Colors-/Reduced-Motion-Fallbacks sind implementiert, aber nicht mit entsprechenden Betriebssystemeinstellungen manuell geprüft. Mobilgerätesimulation durch schmale Reviewer-Viewports ist kein Mobilclient-Kompatibilitätsnachweis. Verwaltete gemeinsame Altnotiztypen behalten außerhalb des Desktop-Reviewers ihre alten Vorlagen.

Keine produktive Sammlung oder produktive Synchronisation verwendet. Keine Änderungen an Notion, dem separat erstellten Anki-Skill, Zugangsdaten oder Nutzerkonfiguration. Versionsarchive bleiben erhalten.

## Paketprüfung

Installationspaket und Quellcodearchiv: ZIP-Integrität, Versionsmanifest und leere Paketkonfiguration geprüft; keine Testprofile, Zugangsdaten oder Medien im Installationspaket. Das separat entpackte vollständige Quellcodearchiv lässt sich mit dem enthaltenen Buildskript zu einem Paket mit inhaltlich identischen Einträgen neu bauen.
