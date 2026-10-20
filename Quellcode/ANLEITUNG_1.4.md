# Notion Safe Sync 1.4.0

## Installation

`Notion_Safe_Sync.ankiaddon` installieren und Anki neu starten. Konfiguration und bisherige Versionsarchive bleiben erhalten. Das alte Add-on `576859862` bleibt deaktiviert. Vorhandene eigene Kartenvorlagen werden beim Öffnen des Profils ohne Notion-Abruf aktualisiert; Notizinhalte und Lernplanung werden dabei nicht verändert. Zuerst in einem Testprofil ausprobieren.

## Vorhandene Masken ohne Notion bearbeiten

**Extras → Notion Safe Sync: Bildmasken bearbeiten** liest ausschließlich die lokale Sammlung und ihre Medien. Ein Token ist dafür nicht erforderlich. Die Liste zeigt Titel, Zielstapel und Bildkartentyp. Eine Zeile anklicken; Strg/Shift ermöglicht Mehrfachauswahl. „Alle auswählen“ und „Auswahl aufheben“ stehen ebenfalls bereit.

Nach OK öffnet jede ausgewählte Notiz genau einen Editor mit allen Abdeckungen, auch wenn sie mehrere Karten besitzt. Unterstützt werden Bildlücke, Bildlücken und Bildfolge. Verschieben, acht Größen-Griffe, Entfernen per Rechtsklick und Rückgängig/Wiederholen bleiben verfügbar. Mindestens eine Maske muss erhalten bleiben. IDs werden nicht neu nummeriert.

„Bestätigen“ hält zunächst einen Entwurf fest. Erst nach Abschluss aller Editoren wird gemeinsam gespeichert. Das Abbrechen eines Editors verwirft alle Entwürfe dieses Aufrufs. Unverändertes Bestätigen schreibt nichts. Bei fehlenden Bildern oder ungültigen Herkunfts-/Maskendaten erscheint eine Meldung; betroffene Notizen werden nicht gespeichert. Karten aus Filterstapeln oder verschiedenen Zielstapeln müssen zuerst eindeutig zugeordnet werden.

Wenn eine entfernte Abdeckung eine Karte löscht, erscheint eine zusätzliche Vorschau mit Notiz-ID, Karten-IDs und Abdeckungs-IDs. Erst die ausdrückliche Zustimmung erlaubt die Löschung samt Lernfortschritt dieser Karten. Die übrigen Karten behalten ihre IDs und Lernplanung. Bei Bildfolge entfernt eine Maske nur einen Aufdeckschritt, nicht die einzelne Gesamtkarte. Die Speicherung lässt sich über Ankis Rückgängig-Funktion zurücknehmen.

## Direkt auf der Lernkarte

Im unterstützten Anki-Desktop-Reviewer erscheint unten auf verwalteten Bildkarten **„Masken bearbeiten“**. Er ersetzt „Toggle Masks“. Der Editor öffnet genau die angezeigte Notiz ohne Notion-Abruf. Bei Bildlücke/Bildlücken ist die gerade abgefragte Abdeckung vorausgewählt. Bei Bildfolge gibt es keine eindeutige einzelne Abdeckung; alle werden gemeinsam gezeigt. „Nächste Abdeckung aufdecken“ bleibt erhalten.

Speichern zeichnet dieselbe Karte auf derselben Frage-/Antwortseite neu. Es erfolgt keine Lernbewertung und kein Aufruf der nächsten Karte. Wird ausdrücklich die gerade angezeigte Karte selbst gelöscht, endet ihre Anzeige in der Stapelübersicht mit Hinweis; eine gelöschte Karte kann nicht weiter angezeigt werden. Abbrechen und unverändertes Bestätigen verändern die Karte nicht. Automatisches Weiterlernen pausiert während des Editors und wird anschließend wieder aktiviert, sofern es vorher aktiv war.

Die Bearbeitenschaltfläche wird nur über die Desktop-Reviewer-Anbindung ergänzt. In Vorschauen und mobilen Clients erscheint keine funktionslose Bearbeitenschaltfläche. Eine mobile Funktionsprüfung des übrigen Kartenverhaltens steht weiterhin aus.

## Notion und lokale Korrekturen

Lokale Änderungen schreiben nichts nach Notion. Bei unverändertem Quellbild und unveränderten Quellmasken bleiben sie beim nächsten Sync erhalten. Geänderte Aufgaben-/Header-Inhalte verlangen weiterhin eine Kontrolle und erhalten passende lokale Geometrie. Änderungen an Quellbild, Masken oder Typ verlangen eine neue Kontrolle mit dem vorhandenen Konflikthinweis.

Die getrennte Aktion **Extras → Notion Safe Sync: Bildmasken anhand Notion erneut prüfen** startet bewusst den bisherigen Abruf mit Seitenauswahl und erneuter Kontrolle. „Vorschau / Synchronisieren“ bleibt unverändert verfügbar.

## Darstellung

Der Editor berücksichtigt Auswahlrahmen und Griffe in seinem Zeichenbereich und zeichnet den sichtbaren Bereich vollständig neu. Das beseitigt zurückbleibende blaue Ziehspuren. „Mehr …“ bleibt auf der Rückseite geschlossen und erhält oberhalb einen relativen Abstand von etwa drei bis vier Textzeilen sowie eine dezente Trennlinie. Ohne Header entsteht kein leerer Informationsbereich. Die Änderung gilt für alle sieben eigenen Kartentypen und berücksichtigt helle/dunkle Darstellung.

## Tatsächlich geprüft / offen

60 Unit-/Integrationstests, die bestehende Qt-Bedienungsprüfung und der erweiterte tatsächliche AnkiQt-Reviewer wurden mit synthetischen temporären Sammlungen geprüft. Anki/aqt 26.09.3, Qt 6.11.2, Python 3.12.14; Qt/Chromium liefen unsichtbar mit Software-Fallback. Editor-Zeichenprüfungen bestanden zusätzlich bei simulierten 125 % und 200 %; Reviewer-Header bei 540/1200 Pixel Fensterbreite und heller/dunkler Darstellung.

Nicht direkt geprüft: dein Desktop-Build mit Python 3.13.15, manuelle Bedienung auf deinem Display, echte Windows-DPI-/Monitorwechsel, AnkiMobile/AnkiDroid sowie Mediensync und Offline-Nutzung auf einem zweiten Gerät. Details: `PRUEFBERICHT_1.4.0.md`. Keine produktive Sammlung oder produktive Synchronisation verwendet; Notion-Inhalte und Anki-Skill unverändert.
