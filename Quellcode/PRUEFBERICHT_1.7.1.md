# Prüfbericht 1.7.1 – 20.10.2026

Die normale Bilddarstellung nutzt kleinere Außenabstände und weniger Leerraum vor „Mehr …“ und „Masken bearbeiten“. Die feste Begrenzung auf die ursprüngliche Pixelbreite entfällt; die Breitenobergrenze steigt. Die verfügbare Fensterhöhe und das ursprüngliche Seitenverhältnis bestimmen weiterhin die proportionale Größe. Bedienelemente bleiben unterhalb des Bildes.

Ein Klick öffnet ein abgerundetes Popup innerhalb des Anki-Fensters. Das Add-on schaltet Anki nicht mehr in Bildschirm-Vollbild und blendet keine Leisten aus. Das Popup wächst beim Vergrößern des Anki-Fensters mit. Eine manuell gewählte Maximierung bleibt nach dem Schließen erhalten. Escape und „Schließen“ schließen das Popup; Bild, Masken und Aufdeckstand bleiben zusammen. Die letzte Reihenfolgemaske führt weiterhin sofort zur Rückseite ohne automatische Bewertung.

Geänderte UI-Dateien: `card_style.py`, `card_interactions.js`, `reviewer_interactions.py`. Vorhandene Gestaltung nach `apple-like-ui` und den bereits verwendeten Referenzen `apple-hig-synthesis.md` und `source-index.md` fortgeführt. Keine neuen Abhängigkeiten.

Prüfungen: 71 Unit-/Integrationstests bestanden. `test_reviewer.py` prüft den tatsächlichen Reviewer mit synthetischer Sammlung: sieben Typen, Maskenbearbeitung, IDs und Lernzustand, Licht-/Dunkelmodus, kleine Fenster, größere Schrift, starke Hoch-/Querformate, native Maskenausrichtung und Popup/Escape ohne Wechsel des nativen Fensterzustands. `test_layout.py` prüft Vorder-/Rückseite und geöffnete Zusatzinformationen bei 520×700 und 1000×1000, proportional mitwachsendes Popup, sichtbare Werkzeugleiste und Erhalt einer während des Popups gewählten Maximierung. Reviewer-Screenshots visuell geprüft. Paketintegrität, leere Paketkonfiguration und identischer Neubau aus dem Quellcodearchiv geprüft.

Testumgebung: Anki/aqt 26.09.3, Qt 6.11.2, Python 3.12.14, Qt offscreen/Software-Rendering. Nutzer-Build Python 3.13.15, manuelle Monitor-/DPI-Prüfung und Mobilclients bleiben direkt offen. Kein produktiver Sync, keine produktive Sammlung und keine Änderungen an Notion oder dem separaten Anki-Skill. Bestehende Versionen bleiben archiviert.
