# Notion Safe Sync 1.7.1

## Tools-Menü

Die vier Einträge erscheinen mit dem Präfix „Notion Safe Sync:“ in dieser Reihenfolge:

1. **Konfigurationen**
2. **Synchronisation Starten**
3. **Bildmasken bearbeiten**
4. **Fehlerdiagnose**

Die Übernahme alter Einstellungen und die gesonderte erneute Bildprüfung aus Notion sind nicht mehr im Menü sichtbar. Die Synchronisation startet weiterhin mit Seitenauswahl und sicherer Vorschau; „Synchronisation Starten“ überspringt keine Bestätigung.

## Update

`Notion_Safe_Sync.ankiaddon` installieren und Anki neu starten. Eigene Kartenvorlagen werden beim Profilöffnen aktualisiert; dafür ist kein Notion-Abruf nötig. Notizinhalte, lokale Korrekturen, Karten-IDs und Lernfortschritte bleiben erhalten.

## Größere Bilder und Popup-Ansicht

Kleinere Außenabstände und eine großzügigere Breitenbegrenzung geben den Bildern mehr Platz. Bilder behalten ihr ursprüngliches Seitenverhältnis auch in schmalen oder niedrigen Fenstern. Die verfügbare Breite und Höhe bestimmen die Bildgröße gemeinsam. Untere Trennlinien und Bedienelemente erhalten Platz; beim Vergrößern des Fensters wächst das Bild proportional mit. Bei sehr kleinen Fenstern oder umfangreichem Text bleibt Scrollen möglich.

**Auf das Bild klicken** öffnet ein Popup innerhalb des Anki-Fensters. Menü- und Bewertungsleisten bleiben sichtbar. Ziehe das Anki-Fenster größer oder maximiere es, um das Bild weiter zu vergrößern. Es wird proportional eingepasst. „Schließen“ oder **Escape** schließt das Popup.

Masken werden gemeinsam mit dem Bild vergrößert. Bereits aufgedeckte Schritte bleiben aufgedeckt; verdeckte Bereiche bleiben verdeckt. Es wird kein unmaskiertes Ersatzbild gezeigt. Öffnen und Schließen lösen keine Bewertung aus. Eine zwischenzeitliche Größenänderung oder Maximierung des Anki-Fensters bleibt beim Schließen erhalten.

## Nummern bedeuten Reihenfolge

- **Bildmasken:** Keine Zahlen auf den Rechtecken – weder beim Bearbeiten noch beim Lernen. Die Bereiche werden einzeln abgefragt.
- **Bildreihenfolge:** Die Rechtecke zeigen ihre Aufdeckreihenfolge **1, 2, 3 …**. Das sind sichtbare Schrittnummern, keine internen Identitäten.

Die internen IDs bleiben erhalten, auch wenn die sichtbaren Schrittnummern nach dem Entfernen einer Maske wieder zusammenhängend sind. Für die Auswahl im Editor stehen „Maske …“ bzw. „Schritt …“ zur Verfügung.

## Reihenfolgen vollständig durchgehen

Auf der Vorderseite einer Bildreihenfolge gilt im Desktop-Reviewer:

1. **Leertaste, Enter oder „Antwort zeigen“** deckt genau die nächste Maske auf.
2. Mit der letzten Maske erscheinen sofort die Rückseite und die normalen Bewertungsbuttons. Ein zusätzlicher Tastendruck entfällt.
3. Erst danach bewertest du wie gewohnt. Es erfolgt keine automatische Bewertung.

„Weiter aufdecken“ funktioniert zusätzlich weiterhin per Mausklick. „Zurücksetzen“ verdeckt alle Schritte erneut; dann müssen sie wieder einzeln durchgegangen werden. Gedrückthalten einer Taste überspringt keine weiteren Schritte. Automatisches Aufdecken der Frage ist bei Bildreihenfolgen pausiert. Für andere Kartentypen bleibt Ankis normales Verhalten erhalten.

Diese Sperre hängt am tatsächlichen Anki-Desktop-Antwortpfad. Sie gilt damit auch für den unteren Antwortknopf, nicht nur für einen Knopf auf der Karte. Andere Clients erhalten die Bild-/Reihenfolgevorlagen, sind aber nicht als gleichwertig geprüft; insbesondere wird eine gleich starke Antwortsperre auf AnkiMobile/AnkiDroid nicht behauptet.

## Unverändert

Lokale Bearbeitung ohne Notion, gemeinsame Entwürfe, Abbrechen, Undo/Redo, sichere Löschbestätigung, Seitenauswahl und Erhalt lokaler Korrekturen bei unveränderter Quelle bleiben verfügbar. Notion-Inhalte und der separate Anki-Skill wurden nicht verändert.

## Prüfung

71 Unit-/Integrationstests sowie Qt- und tatsächliche Reviewer-Prüfungen mit anonymen temporären Sammlungen bestanden. Hoch-/Querformat 300×1200 / 1200×300 bei kleinen Viewports, Popup/Escape, sichtbare Masken, Schrittstand, native Tastaturereignisse, Antwortknopf, Zurücksetzen und Tastenwiederholungen wurden geprüft. Testumgebung: Anki/aqt 26.09.3, Qt 6.11.2, Python 3.12.14.

Dein Python-3.13.15-Build, manuelle Fenster-/DPI-/Monitorprüfung und Mobilclients bleiben direkt zu prüfen. Einzelheiten: `PRUEFBERICHT_1.7.1.md`.
