# Entwicklung

## Quellcode und Build

Arbeite in `Quellcode/`. Das Verzeichnis ist das Add-on-Paket; relative Imports setzen Anki oder den Testaufbau voraus. `python build.py` prüft die Python-Syntax und baut die Pakete. Es werden keine Anki-Sammlung und kein Notion-Zugang für den Build benötigt. Zugangsdaten bleiben in der lokalen Anki-Konfiguration.

## Funktionstests

Die bisherigen Tests wurden mit Python 3.12.14 und Anki/aqt 26.09.3 ausgeführt. Für eine eigene Testumgebung passende `aqt`-/Qt-Abhängigkeiten installieren, z. B. `python -m pip install aqt==26.9.3`. Danach im Verzeichnis `Quellcode/`:

```sh
python -m unittest test_core test_transport test_integration test_types test_features test_local_masks test_design test_interactions
python test_ui.py
python test_reviewer.py
python test_layout.py
```

Die Reviewer-Programme starten eigenständige synthetische Profile und beenden ihren Prozess mit `os._exit`. Deshalb separat ausführen, nicht über eine pauschale Test-Discovery. Auf headless Systemen passende Qt-/Chromium-Systembibliotheken bereitstellen. Keine produktive Sammlung verwenden. Die GitHub-Automation baut und prüft die Pakete; sie behauptet keine vollständigen Reviewer-Tests.

Karten-/Notizidentitäten und Lernfortschritte müssen erhalten bleiben. Bestehende lokale Maskenkorrekturen nicht unbeabsichtigt überschreiben. Löschungen brauchen eine eindeutige Vorschau; Abbrechen darf keine Entwürfe übernehmen.

## Neue Version veröffentlichen

1. `human_version` in `Quellcode/manifest.json` erhöhen.
2. Anleitung, `CHANGELOG.md` und einen passenden Prüfbericht aktualisieren.
3. Tests mit synthetischen Daten ausführen und `python build.py` prüfen.
4. Änderungen nach `main` übernehmen.

Der Release-Workflow baut das Paket, prüft ZIP-Integrität und leere Konfiguration und erstellt für eine noch nicht vorhandene Version den Tag `v<VERSION>` und einen GitHub-Release mit Installationspaket und Quellcodearchiv. Vorhandene Releases werden nicht überschrieben. Der Workflow kann auch manuell über „Actions → Build and release → Run workflow“ gestartet werden.

Der Workflow benötigt `contents: write` für Releases. Er verwendet den temporären GitHub-Actions-Token; kein eigener Token muss im Quellcode hinterlegt werden. Falls Actions im Repository deaktiviert ist, bleibt der lokale Build nutzbar.
