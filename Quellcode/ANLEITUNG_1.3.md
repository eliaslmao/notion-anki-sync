# Update auf Notion Safe Sync 1.3.0

1. Das neue `Notion_Safe_Sync.ankiaddon` installieren und Anki neu starten. Konfiguration und Sammlung bleiben erhalten. Zuerst ein Testprofil verwenden.
2. „Vorschau / Synchronisieren“ öffnen und Seiten auswählen. Beim ersten Sync nach 1.2 werden Bildmasken einmal pro Notiz neu geprüft.
3. Im Dialog **„Bildmasken prüfen und bearbeiten“** Abdeckungen ziehen, an den Griffen skalieren oder über Rechtsklick entfernen. IDs bleiben erhalten. „Rückgängig“/Strg+Z korrigiert Fehler; „Wiederholen“ stellt sie wieder her. Mindestens eine Maske muss bleiben.
4. „Bestätigen“ übernimmt nur den Entwurf. Erst die abschließende Gesamtvorschau schreibt nach Anki. Dort stehen ausdrücklich auch zu löschende gelernte Karten. Abbrechen übernimmt nichts.

Lokale Maskenkorrekturen bleiben bei unveränderter Notion-Quelle erhalten. Ändert sich Bild oder Maskendefinition, erscheint erneut die Kontrolle mit Konflikthinweis; alte Korrekturen werden nicht blind angewendet. Änderungen nur an Aufgabenstellung/Metadaten verlangen eine neue Kontrolle, behalten aber die passende lokale Geometrie. Für bewusstes erneutes Bearbeiten unveränderter Notizen: **Extras → Notion Safe Sync: Bildmasken bearbeiten**.

`[Lücke+Eingabe]` zeigt jetzt Felder direkt in den Lücken, auch mehrere gleichzeitig. Tab wechselt Felder; Enter deckt auf. Vergleich je Feld: Unicode-NFC, Leerraum vereinheitlicht und außen entfernt, sonst zeichen- und groß-/kleinschreibungsgenau. Die Rückseite zeigt Lösungen und Rückmeldungen. Die Anki-Lernbewertung wählst du weiterhin selbst.

Optional am Ende eines Blatt-Toggles:

```text
[Header] Quelle: Vorlesung 3, Seite 12
Link zum PDF oder weitere formatierte Hinweise
```

Alles ab diesem direkten Absatz ist Metadatum, keine Antwort und kein Masken-Steuertext. Auf jeder Rückseite öffnet „Mehr …“ den zunächst geschlossenen Abschnitt. Normale Notion-Links und Listen sind möglich. Ein Header ersetzt keine fehlende Antwort.

Vollständige Notation: `NOTION_FORMAT.md`. Prüfungen/Grenzen: `PRUEFBERICHT_1.3.0.md`. Im tatsächlichen Desktop-Reviewer mit Anki 26.09.3/Qt 6.11.2 geprüft, Test-Python 3.12.14. Python 3.13.15 und Mobilclients bleiben direkt zu prüfen. Notion-Inhalte und separater Anki-Skill wurden nicht verändert.
