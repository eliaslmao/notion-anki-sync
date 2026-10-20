# Notion Safe Sync · Notion → Anki

Ein Anki-Desktop-Add-on, das Lernkarten aus Notion übernimmt – mit Vorschau vor dem Schreiben, lokaler Bildmaskenbearbeitung und Erhalt bestehender Kartenidentitäten und Lernfortschritte.

**Aktuelle Version: 1.7.1** · [Installation](#installation) · [Bedienungsanleitung](Quellcode/ANLEITUNG_1.7.md) · [Notion-Format](Quellcode/NOTION_FORMAT.md) · [Änderungsverlauf](CHANGELOG.md)

## Funktionen

- Notion-Seiten auswählen, Änderungen prüfen und erst nach Bestätigung nach Anki übernehmen.
- Frage/Antwort, Eingabe, Cloze, kombinierte Lücken mit Eingabe und Bildkarten.
- **Bildmasken:** Bereiche einzeln abfragen, ohne sichtbare Nummern.
- **Bildreihenfolge:** nummerierte Bereiche Schritt für Schritt aufdecken. Die letzte Maske öffnet direkt die Rückseite; die Bewertung wählst du selbst.
- Masken lokal bearbeiten, verschieben und skalieren; Rückgängig/Wiederholen und bewusste Bestätigung von Löschungen.
- Proportionale Bilder und vergrößerbare Popup-Ansicht innerhalb des Anki-Fensters.
- Einheitliche helle und dunkle Gestaltung und optionale Quellen unter „Mehr …“.

## Installation

1. Lade **[Notion_Safe_Sync.ankiaddon](https://github.com/eliaslmao/notion-anki-sync/raw/refs/heads/main/downloads/v1.7.1/Notion_Safe_Sync.ankiaddon)** herunter. Weitere veröffentlichte Pakete stehen unter [Releases](https://github.com/eliaslmao/notion-anki-sync/releases).
2. Öffne Anki → **Extras/Tools → Erweiterungen/Add-ons → Aus Datei installieren** und wähle die Datei. Alternativ die Datei in Anki öffnen.
3. Starte Anki neu.
4. Öffne **Notion Safe Sync: Konfigurationen**. Trage deinen eigenen Notion-Integrationstoken und die gewünschten Seiten ein. Erteile der Integration in Notion Zugriff auf diese Seiten.
5. Öffne **Synchronisation Starten**, wähle Seiten und prüfe die Vorschau vor der Übernahme.

Beim Update werden die eigenen Kartenvorlagen beim Profilöffnen aktualisiert. Notion muss dafür nicht erneut abgerufen werden. Vor dem ersten Einsatz empfiehlt sich eine Sicherung und ein Anki-Testprofil.

Zugangsdaten gehören ausschließlich in die lokale Anki-Konfiguration. Das Repository und die Installationspakete enthalten eine leere Beispielkonfiguration. Das Add-on liest Notion und schreibt in deine lokale Anki-Sammlung; es erstellt keine Lerninhalte in Notion.

## Bedienung

Im Tools-Menü gibt es vier Einträge: **Konfigurationen**, **Synchronisation Starten**, **Bildmasken bearbeiten** und **Fehlerdiagnose**.

Ein Klick auf ein Bild öffnet das Popup. Ziehe das Anki-Fenster größer oder maximiere es, um das Bild weiter zu vergrößern. Escape oder „Schließen“ beendet die Ansicht. Masken und bereits aufgedeckte Schritte bleiben erhalten.

Bei Bildreihenfolgen decken Leertaste, Enter und „Weiter aufdecken“ jeweils einen Bereich auf. Mit dem letzten Bereich erscheint die Rückseite samt Bewertungsbuttons. Es erfolgt keine automatische Bewertung.

## Kompatibilität und Prüfstand

Desktop-Prüfstand: **Anki/aqt 26.09.3, Qt 6.11.2, Python 3.12.14**. Das Manifest verlangt mindestens Anki 26.09.3. 71 Unit-/Integrationstests sowie ergänzende Prüfungen im tatsächlichen Qt/Chromium-Reviewer wurden mit synthetischen Sammlungen ausgeführt.

Die erzwungene Aufdeckreihenfolge und das Bild-Popup sind für den Desktop-Reviewer geprüft. Ein gleichwertiges Verhalten auf AnkiMobile/AnkiDroid wird nicht zugesichert. Andere Python-Builds sowie echte Monitor-/DPI-Wechsel sind gesondert zu prüfen. Einzelheiten: [Prüfbericht 1.7.1](Quellcode/PRUEFBERICHT_1.7.1.md).

## Projektaufbau

| Pfad | Inhalt |
| --- | --- |
| `Quellcode/` | Add-on, Kartenvorlagen, Tests, Formatbeschreibung und Prüfberichte |
| `downloads/v1.7.1/` | Geprüftes Installationspaket und vollständiges Quellcodearchiv |
| `build.py` | Baut Installationspaket und Quellcodearchiv ohne Zugangsdaten |
| `CHANGELOG.md` | Versionsübersicht |
| `CONTRIBUTING.md` | Entwicklung, Tests und Veröffentlichung |
| `.github/workflows/release.yml` | Automatischer Build und Release bei neuer Versionsnummer |

## Selbst bauen

```sh
python build.py
```

Der Build verwendet nur die Python-Standardbibliothek. Er erzeugt `Notion_Safe_Sync.ankiaddon` und `Versionen/<Version>/`. Die Version stammt aus `Quellcode/manifest.json`. Für Funktionstests wird zusätzlich eine passende Anki/aqt-/Qt-Umgebung benötigt; siehe [Entwicklung](CONTRIBUTING.md).

## Fehler melden

Nutze [Issues](https://github.com/eliaslmao/notion-anki-sync/issues) und nenne Add-on-Version, Anki-Version, Betriebssystem und Schritte zum Nachstellen. Teile keine Tokens, produktiven Sammlungen oder privaten Notion-Inhalte.

## Lizenz

[MIT](LICENSE). Dieses Projekt ist ein unabhängiges Add-on und kein offizielles Produkt von Anki oder Notion.
