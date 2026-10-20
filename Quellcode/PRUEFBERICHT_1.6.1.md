# Prüfbericht 1.6.1 – 20.10.2026

Die sichtbaren Tools-Aktionen wurden in `ui.py` auf vier reduziert und in die gewünschte Reihenfolge gebracht: Konfigurationen, Synchronisation Starten, Bildmasken bearbeiten, Fehlerdiagnose. Das bestehende Präfix „Notion Safe Sync:“ bleibt zur Zuordnung im Anki-Menü erhalten. Die Übernahme alter Konfiguration und die gesonderte erneute Notion-Bildprüfung sind keine sichtbaren Menüaktionen mehr.

„Synchronisation Starten“ ruft denselben sicheren Ablauf mit Seitenauswahl, Abruf und bestätigter Vorschau auf. Kartendarstellung, Speicherlogik, IDs, Lernfortschritte und Konfiguration werden durch diese Änderung nicht verändert.

Die vorhandene Qt-Bedienungsprüfung `test_ui.py` wurde an vier Aktionen und die neue Position der Synchronisation angepasst und erfolgreich mit synthetischen Objekten ausgeführt. Sie prüft weiterhin Konfiguration, Menü-Auslösung des Sync-Ablaufs, Auswahl/Abbruch, sichere Fehlerdiagnose und Fortschritt. Die 71 Funktions-/Integrationstests und echte Reviewer-Prüfung aus 1.6.0 werden als vorausgehende Prüfung dokumentiert, für diese reine Menüänderung nicht erneut behauptet.

Paket und Quellcodearchiv wurden gebaut und auf ZIP-Integrität, Version, leere Paketkonfiguration und vollständige Dateien geprüft. Ein Neubau aus dem separat entpackten Quellcodearchiv erzeugt inhaltlich identische Paketeinträge. Keine produktive Sammlung, kein produktiver Sync und keine Änderungen an Notion oder am Anki-Skill.

Testlaufzeit: Anki/aqt 26.09.3, Qt 6.11.2, Python 3.12.14. Nutzer-Build mit Python 3.13.15, manuelle Geräte-/DPI- und Mobilprüfungen bleiben direkt offen.
