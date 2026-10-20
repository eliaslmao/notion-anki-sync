# Prüfbericht 1.7.0 – 20.10.2026

## Änderungen

Bilder werden nach verfügbarer Breite und Höhe proportional eingepasst. Die Höhenberechnung berücksichtigt Text, Kartenabstände, „Mehr …“ und den Bereich „Masken bearbeiten“. Fensteränderungen, geladene Bilder und geöffnete Zusatzinformationen lösen eine erneute Berechnung aus. Bild, native Masken-Canvas und Reihenfolgemasken bleiben zusammen; die vorhandene Vollbildansicht bleibt erhalten. Bei extrem kleinen Fenstern oder umfangreichem Text ist Scrollen weiterhin möglich.

Das letzte Aufdecken einer Bildreihenfolge öffnet sofort die normale Rückseite einschließlich Bewertungsbuttons. Das gilt für den nativen Antwortpfad und „Weiter aufdecken“. Die Karte wird dabei nicht bewertet. Tastenwiederholungen werden auch auf der Rückseite einer Bildreihenfolge abgefangen, damit Gedrückthalten der letzten Aufdecktaste keine Bewertung auslöst. Andere Kartentypen behalten den nativen Antwortpfad.

Geänderte UI-Dateien: `card_interactions.js` (proportionale Flächenberechnung), `card_style.py` (letzter Schritt), `reviewer_interactions.py` (Antwortübergang/Tastenwiederholung). Keine neuen Abhängigkeiten. Vorhandene Gestaltung nach dem Skill `apple-like-ui`, insbesondere `references/apple-hig-synthesis.md` und `references/source-index.md`, wurde beibehalten.

## Prüfung

- 71 Unit-/Integrationstests erfolgreich: Kernimport, Transport, Identitäten, lokale Korrekturen, Kartentypen, Vorlagenaktualisierung, Gestaltung und Antwortsteuerung.
- `test_ui.py` erfolgreich: vier Tools-Aktionen, Konfiguration, sichere Vorschau und Fehlerdiagnose.
- `test_reviewer.py` erfolgreich im tatsächlichen Anki/Chromium-Reviewer mit ausschließlich synthetischer Sammlung: alle sieben Kartentypen, lokale Maskenbearbeitung, Licht-/Dunkelmodus, kleine Fenster, größere Schrift, Hochformat 300×1200 und Querformat 1200×300, Masken-Canvas-Ausrichtung, Vollbild/Escape und Erhalt des Aufdeckstands. Bei 320×600 und 1000×900 wurden Bildende, Footerposition, sichtbarer Footer und Mitwachsen geprüft; bei kleineren Höhen zusätzlich das Seitenverhältnis. Space/Return, nativer Antwortknopf, direkter Antwortpfad und Kartenknopf führen beim letzten Schritt sofort zur Antwort. Keine automatische Bewertung; gehaltene Tasten überspringen bzw. bewerten nicht.
- `test_layout.py` ergänzend erfolgreich: starke Hochformate auf Vorder- und Rückseite, geschlossene/geöffnete Zusatzinformationen, Footerposition und Mitwachsen bei 520×700 und 1000×1000 für Bildmasken, mehrere Bildmasken, Bildreihenfolge und normale Bildkarten.
- Erzeugte Reviewer-Bilder für Hoch-/Querformat und Rückseite visuell geprüft. Keine manuelle Maus-/Monitorprüfung am produktiven Anki behauptet.
- Installationspaket und Quellcodearchiv: ZIP-Integrität, Version, enthaltene Interaktionsdateien und leere Paketkonfiguration geprüft. Neubau aus dem entpackten Quellcodearchiv erzeugt inhaltlich identische Paketeinträge.

Testumgebung: Anki/aqt 26.09.3, Qt 6.11.2, Python 3.12.14; Qt offscreen mit Software-Rendering. Der Python-3.13.15-Build des Nutzers, tatsächliche Monitor-/DPI-Wechsel und Mobilclients bleiben direkt offen. Die erzwungene schrittweise Antwortsteuerung und echtes Anki-Vollbild sind für den Desktop-Reviewer geprüft.

Keine produktive Sammlung und kein produktiver Sync wurden geöffnet. Notion, Kartendaten, interne Identitäten und der separate Anki-Skill wurden nicht verändert. Bestehende Versionen bleiben archiviert. Installation des neuen Pakets und Anki-Neustart aktualisieren die eigenen Vorlagen beim Profilöffnen.
