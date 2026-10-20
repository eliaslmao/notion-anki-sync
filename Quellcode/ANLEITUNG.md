# Notion Safe Sync 1.7.1

Größere Bilder durch geringere Außenabstände und eine großzügigere Breitenbegrenzung. Ein Klick öffnet ein Popup innerhalb des vergrößerbaren Anki-Fensters. Menü und Bewertungsleiste bleiben sichtbar. Details: `ANLEITUNG_1.7.md` und `PRUEFBERICHT_1.7.1.md`. Die folgenden Abschnitte dokumentieren ältere Stände.

# Notion Safe Sync 1.7.0

## Aktueller Stand 1.7.0

Bilder passen sich proportional an die verfügbare Fensterfläche an und lassen Platz für die unteren Bedienelemente. Die letzte Maske einer Bildreihenfolge zeigt sofort die Rückseite mit Bewertungsbuttons, ohne automatische Bewertung. Bedienung: `ANLEITUNG_1.7.md`; Prüfung: `PRUEFBERICHT_1.7.0.md`. Die folgenden Abschnitte dokumentieren ältere Stände.

# Notion Safe Sync 1.6.1

## Aktueller Stand 1.6.1

Das Tools-Menü enthält nur noch Konfigurationen, Synchronisation Starten, Bildmasken bearbeiten und Fehlerdiagnose in dieser Reihenfolge, jeweils mit dem bisherigen Präfix „Notion Safe Sync:“. Die sichere Seitenauswahl und Vorschau bleiben erhalten. Details: `ANLEITUNG_1.6.md` und `PRUEFBERICHT_1.6.1.md`.

## Aktueller Stand 1.6.0

Einstieg: `ANLEITUNG_1.6.md`, Prüfungen: `PRUEFBERICHT_1.6.0.md`. Bilder bleiben auch in kleinen Fenstern proportional und öffnen per Klick die Vollbildansicht; Escape stellt die vorherige Ansicht wieder her. Normale Bildmasken tragen keine Zahlen. Bildreihenfolgen zeigen laufende Schrittnummern statt interner IDs. Im Desktop-Reviewer decken Leertaste, Enter und der native Antwortknopf zuerst jeweils nur eine Maske auf; erst nach allen Schritten ist die Rückseite erreichbar. Interne Identitäten, lokale Korrekturen und Lernfortschritte bleiben erhalten. Die folgenden Abschnitte dokumentieren ältere Versionen.

## Aktueller Stand 1.5.0

Einstieg: `ANLEITUNG_1.5.md`, Prüfungen und UI-Dateien: `PRUEFBERICHT_1.5.0.md`. Einheitliche Systemschrift, Abstände, Schaltflächen und helle/dunkle Farben für Dialoge und Karten. In der Bildbearbeitung heißen die beiden sichtbaren Varianten „Bildmasken“ und „Bildreihenfolge“. Die klare Überschrift, die Aufgabe und das Bild ersetzen technische Kartentyp-/Kartenanzahl-/ID-Texte. „Hilfe“ zeigt Bedienhinweise bei Bedarf; die Maskenauswahl ermöglicht auch Tastaturbearbeitung. Lokale Speicherung, Identität und Lernfortschritte bleiben erhalten. Die folgenden Abschnitte dokumentieren ältere Versionen.

## Aktueller Stand 1.4.0

Einstieg: `ANLEITUNG_1.4.md`, Prüfungen: `PRUEFBERICHT_1.4.0.md`. „Bildmasken bearbeiten“ arbeitet jetzt lokal mit vorhandenen Bildnotizen und Anki-Medien, ohne Notion-Abruf. Einzel-/Mehrfachauswahl und gemeinsame transaktionale Entwürfe sind möglich. Im Desktop-Reviewer ersetzt „Masken bearbeiten“ den bisherigen Toggle-Masks-Button; die aktuelle Abdeckung wird soweit eindeutig vorausgewählt. Kartenlöschungen verlangen eine eigene Bestätigung. Unverändertes Speichern schreibt nichts. Die getrennte Aktion „Bildmasken anhand Notion erneut prüfen“ erhält den bisherigen Quellabruf. Der Qt-Editor zeichnet Auswahlrahmen und Griffe vollständig neu; Header sind deutlicher durch Abstand und Linie abgesetzt. Die folgenden Abschnitte dokumentieren die früheren Versionen.

## Aktueller Stand 1.3.0

Neue Bedienung und Notion-Regeln: `NOTION_FORMAT.md`, Einstieg: `KARTENTYPEN.md`. Bildmasken werden pro betroffener Notiz in „Bildmasken prüfen und bearbeiten“ kontrolliert und bearbeitet, mit Rückgängig und dauerhaften lokalen Korrekturen. Bei unveränderter Notion-Quelle bleiben diese erhalten; bei Quelländerungen wird neu geprüft. `[Lücke+Eingabe]` besitzt jetzt eigene Inline-Felder direkt an den Lücken. `[Header]` erlaubt sichere Quellen/Metadaten für alle Kartentypen hinter einem zunächst geschlossenen „Mehr …“ auf der Rückseite. Nach Installation Anki neu starten und zuerst ein Testprofil verwenden. Für bewusstes erneutes Bearbeiten vorhandener Masken den entsprechenden neuen Extras-Menüpunkt wählen.

## Neu: zusätzliche Kartentypen

Die vollständige neue Formatanleitung, Beispiele, Migrationsregeln und geprüften Reviewer-Funktionen stehen in `KARTENTYPEN.md`. Neben den bisherigen normalen Frage–Antwort-Notizen gibt es nun Eingabe, native Cloze, Cloze mit Eingabe, native Bildlücke/Bildlücken und Bildfolge. Seitenauswahl, dosierter Abruf, Retry-After, lesbare Stapelnamen und sichere Anwendung bleiben erhalten. Bei Notiztypwechseln und einzelnen Kartenlöschungen ist eine ausdrückliche Vorschau erforderlich. Neue/geänderte Masken erhalten eine gemeinsame lokale Bildvorschau; bestätigte unveränderte Masken werden wiederverwendet.

## Neu in 1.1.1: lesbare Unterstapel ohne sichtbare Block-IDs

Themen erhalten nur ihren bereinigten Titel als Stapelnamen, etwa `Uni::Modellierung::BPMN`. Die stabilen Block-IDs und Themenpfade werden intern an den verwalteten Notizen gespeichert. Nur bei gleichen Namen im selben Elternstapel oder einer Kollision mit einem bereits vorhandenen fremden Stapel wird ein kurzer Zusatz verwendet, beispielsweise `BPMN (2)`. Dieser Zusatz enthält keine Notion-ID. Bereits zugeordnete Namen werden bei unveränderter Quelle wiederverwendet.

Beim nächsten bestätigten Sync werden Karten aus den bisherigen ID-Stapeln in die lesbaren Zielstapel verschoben. Notiz-ID, Karten-ID und Lernplanung bleiben erhalten. Die Vorschau weist solche Änderungen als `move` aus. Neue Zielstapel verwenden Ankis Vorgabeeinstellungen; bei individuell geänderten Stapeloptionen diese nach der Migration prüfen. Die alten ID-Stapel werden nur bereinigt, wenn ihre bisherige Verwendung durch ausgewählte verwaltete Notizen belegt ist, sie unterhalb eines konfigurierten Hauptstapels liegen und nach dem Verschieben weder Karten noch Unterstapel enthalten. Fremde Karten und fremde Unterstapel verhindern die Entfernung. Die Migration ist Teil des gemeinsamen Undo-Schritts. Es wurde keine persönliche Sammlung verändert.

Zusätzlich isoliert getestet: lesbare und kollisionsfreie Themennamen, stabile Namen bei wiederholtem Sync, Migration aus ID-Namen mit Erhalt der Karten-/Notiz-ID, Bereinigung leerer alter ID-Stapel sowie Erhalt fremder Karten und Unterstapel. Eigene neue und migrierte Notizen speichern Themenidentitäten ohne sichtbare IDs in Stapelnamen. Bei übernommenen Altnotizen werden Metadaten in einem kodierten Tag gespeichert, damit Leerzeichen in Themennamen keine Tag-Trennung verursachen.

## Neu in 1.1.0: Seitenauswahl, dosierter Abruf und Wiederholungen

Nach „Vorschau / Synchronisieren“ erscheint zuerst die Liste der aktiven konfigurierten Seiten mit Checkboxen und Zielstapeln. „Alle auswählen“ und „Auswahl aufheben“ ändern nur die Auswahl dieses Laufs, nicht die gespeicherte Konfiguration. Ohne Auswahl ist OK deaktiviert; Abbrechen sendet keine Anfrage. Erst nach Bestätigung werden die ausgewählten Seiten abgerufen und gemeinsam geplant. Nicht ausgewählte Quellen werden nicht abgerufen und ihre gespeicherten Karten nicht aktualisiert, verschoben oder gelöscht. Taucht die Block-ID einer bislang nicht ausgewählten Quelle in einer ausgewählten Seite auf, stoppt der Plan: beide beteiligten Quellen auswählen. Verschiebungen zwischen ausgewählten Quellen behalten Notiz-/Karten-ID und Lernplanung.

Notion-API-Anfragen laufen seriell mit mindestens 0,4 Sekunden Abstand. Ein zentraler Transport für API und Bilder behandelt HTTP 429/529 sowie vorübergehende GET-Fehler (500/502/503/504 und Verbindungs-/Übertragungsfehler). Maximal fünf Versuche insgesamt pro Anfrage. `Retry-After` wird als Mindestwartezeit eingehalten, auch über 60 Sekunden; zusätzlich exponentieller Rückstand (1/2/4/8 Sekunden) und kleiner Zufallsanteil. Ohne gültigen Header greift der Rückstand. HTTP 401/403/404, TLS-Zertifikatsfehler und explizit gesperrter Notion-API-Zugriff werden nicht blind wiederholt. Token-/Rechtemeldungen bleiben verständlich. Retry-After im Notion-Fehlerkörper wird ersatzweise gelesen, ohne diesen Körper zu protokollieren.

Der Anki-Fortschrittsdialog zeigt Seitenposition, Anfrage-/Versuchsnummer sowie einen Countdown während Wartezeiten. Die GUI läuft weiter; der Countdown wird nur im Qt-Hauptthread aktualisiert. Abbruch wird beim Warten spätestens nach etwa einer Sekunde verarbeitet. Eine laufende einzelne Netzwerkabfrage kann bis zum 40-Sekunden-Timeout benötigen. Ein unvollständiger Abruf oder abgebrochener Bilddownload erreicht weder Inhaltsanwendung noch Löschungen. Erst nach vollständigem Abruf, Validierung und Medienvorbereitung erscheint die Änderungsbestätigung.

Die frühere Meldung „Sync abgebrochen. Keine weiteren Änderungen …“ war eine Sammelmeldung, kein Beleg für ein Rate-Limit. Der bereits reproduzierte sofortige Fehler durch fehlendes `deck_name` bleibt gezielt abgefangen. Auch ungültige Token-Datentypen/Zeilenumbrüche werden vor dem Abruf gemeldet. Menü-Klick, Vorschau-Callbacks und Fehlerbehandlung sind separat von den Netzwerk-Retries getestet. Bei einem weiteren Fehler liefert „Fehlerdiagnose“ Add-on-/Anki-/Python-/Qt-Version, Phase und interne Aufrufstellen ohne vertrauliche Daten. Ein neuer, nicht reproduzierter Fehler auf dem Zielrechner wird nicht als behoben oder als Rate-Limit ausgegeben.

Offizielle Grundlage der Retry-Regeln: https://developers.notion.com/reference/request-limits (am 19.10.2026 geprüft).

Isolierte Abnahme dieser Version: 10 Parser-/Planungsprüfungen, 7 Transportprüfungen und 10 Integrationstests mit temporären Sammlungen sowie Qt-Tests für Auswahl, Abbruch, Menü-Klick, Fehlerdiagnose und thread-sicheren Fortschritt. Die Transporttests verwenden virtuelle Zeit und synthetische Antworten; keine reale Wartezeit oder privaten Notion-Inhalte. Die Tests greifen nicht auf die persönliche Sammlung zu und führen keinen produktiven Sync aus. Getestet mit Anki/aqt 26.9.3, Qt 6.11.2 und Python 3.12.14; der gemeldete Desktop-Build 29bb700b mit Python 3.13.15 wurde nicht direkt ausgeführt. Ein manueller End-to-End-Test in einem Testprofil bleibt erforderlich.

Update: Paket `Notion_Safe_Sync.ankiaddon` aus „Anki Deck“ installieren, Anki neu starten und unter „Vorschau / Synchronisieren“ zuerst eine kleine Testseite auswählen. Danach Vorschau und Kartenansicht prüfen. Konfiguration und vorige Versionsarchive bleiben erhalten.

## Korrektur 1.0.3: größere Importe und sichere Rücknahme

Ein Import von 72 synthetischen Karten reproduzierte in Version 1.0.2 die Meldung „Anwendung und Rücknahme fehlgeschlagen“. Ursache: Erst nach allen Einzeloperationen wurde der eigene Undo-Schritt zusammengeführt. Bei größeren Importen war dessen ursprünglicher Anker dann bereits aus Ankis begrenztem Undo-Verlauf gefallen. Version 1.0.3 führt nach jeder Sammlungsänderung zusammen und hält den Anker dadurch aktiv.

Zusätzlich geprüft: 72 neue Karten mit anschließendem Undo, 72 Inhalts-/Stapeländerungen mit erhaltener Identität und Undo, absichtlicher Fehler bei Karte 65 mit vollständiger Rücknahme einschließlich neu angelegter Stapel, sowie Wiederaufnahme eines vorherigen Teilimports mit 43 vorhandenen und 29 fehlenden Karten ohne Duplikate. Alle Prüfungen verwenden temporäre Sammlungen mit Anki 26.9.3.

Bei einem bereits aufgetretenen Fehler nicht allein aufgrund der alten Meldung die Sicherung zurückspielen. Die alte Version kann bereits alle oder einen Teil der Karten korrekt angelegt haben. Zuerst den aktuellen Zustand sichern, 1.0.3 installieren und Anki neu starten. In Ankis Browser findet `tag:notion_safe_sync_v1` die neu verwalteten Notizen. Danach nur die Vorschau starten. Bei unveränderter Quelle mit 72 zuvor vollständig angelegten Karten sollte sie `same: 72`, `new: 0` zeigen. Bei einem Teilimport sind entsprechend weniger neue Karten vorgesehen. Unerwartete Löschungen oder erneut 72 neue Karten trotz vorhandener importierter Karten: Vorschau abbrechen und Diagnose prüfen. Keine pauschale manuelle Löschung durchführen.

Die sichere Diagnose unterscheidet nun bei einer tatsächlich fehlgeschlagenen Rücknahme zusätzlich die Typen und internen Aufrufstellen des ursprünglichen Anwendungsfehlers und des Rücknahmefehlers, ohne deren Texte oder private Daten auszugeben. Die neue Meldung behauptet nicht mehr automatisch eine notwendige Wiederherstellung.

## Korrektur 1.0.2: sofortiger Vorschaufehler und Diagnose

Der gemeldete sofortige Abbruch wurde anhand der Struktur der lokalen Konfiguration reproduziert: Seiteneinträge hatten `page_id` und `name`, aber kein `deck_name`. Die alte Validierung löste dadurch einen verdeckten `KeyError` aus, bevor überhaupt ein Netzwerkabruf begann.

Fehlende oder ungültige Felder werden jetzt mit Eintragsnummer und Handlungsanweisung gemeldet. Im Konfigurationsdialog werden vorhandene Seitennamen als Vorschlag für fehlende Zielstapel angezeigt. Erst „Speichern“ übernimmt diese Vorschläge; zuvor bleiben Einstellungen unverändert. Den gewünschten Zielstapel für jede Seite ausdrücklich prüfen.

Die neue Menüfunktion „Fehlerdiagnose“ zeigt die letzte technische Diagnose der laufenden Sitzung: Add-on-/Anki-/Python-Version, Phase, Fehlertyp und interne Dateinamen mit Zeilennummern. Keine Ausnahmetexte, absoluten Pfade, Quelltextzeilen, lokalen Variablen, Tokens, Konfiguration oder URLs werden in diesen Diagnosebericht aufgenommen. Der Bericht bleibt nur im Arbeitsspeicher. Bekannte fachliche Fehlermeldungen (etwa fehlende Zielstapel oder HTTP-Status) erscheinen weiterhin verständlich im Dialog. Auch unerwartete Fehler in den Vorschau-Callbacks lösen die Sync-Sperre wieder.

Update: neues Paket installieren, Anki neu starten, Konfiguration öffnen, Zielstapel prüfen und speichern, dann Vorschau erneut ausführen. Die installierte Konfiguration wird durch das Paket nicht überschrieben. Das Update wurde mit Anki/aqt 26.9.3 und Python 3.12.14 isoliert geprüft. Gemeldete Nutzerumgebung: Anki 26.09.3, Python 3.13.15. Ein eigener Lauf unter Python 3.13.15 steht noch aus. Der konkrete Konfigurationsfehler und seine Behebung hängen nicht von einer Python-3.13-spezifischen API ab.

Eigenständige lokale Erweiterung für den bereitgestellten Auftrag. Das installierte Add-on 576859862, seine Konfiguration und die persönliche Sammlung wurden nicht verändert. Dieses Paket enthält keinen Code und keine Zugangsdaten des alten Add-ons. Für dessen eigene Dateien war keine Lizenz ausgewiesen; die mitgelieferten Bibliotheken haben separate Lizenzen. Deshalb wird kein modifiziertes Originalpaket weitergegeben.

## Installation und Update

1. Ankis normale Sammlungssicherung erstellen. Zum ersten Ausprobieren ein neues Anki-Testprofil und eine kleine Notion-Testseite verwenden.
2. `Notion_Safe_Sync.ankiaddon` unter Extras → Erweiterungen → Aus Datei installieren öffnen. Anki neu starten. Das Paket hat die eigene Kennung `notion_safe_sync`; offizielle Updates von 576859862 überschreiben es nicht.
3. Optional Extras → „Notion Safe Sync: alte Konfiguration übernehmen“. Dies kopiert Token und Seiten ausschließlich lokal, ohne vorhandene neue Einstellungen zu überschreiben. Ankis Add-on-Konfiguration kann profilübergreifend gelten: Im Testprofil unbedingt zuerst die Testseite konfigurieren!
4. Das bisherige Add-on 576859862 deaktivieren und Anki neu starten. Solange sein Code geladen ist, verweigert die neue Erweiterung den Sync. Nach der Migration den alten Import nicht wieder verwenden.
5. „Notion Safe Sync: Konfiguration“ öffnen. Token eintragen und die JSON-Seitenliste bearbeiten, beispielsweise:

```json
[
  {
    "page_id": "https://www.notion.so/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "deck_name": "Uni::Datenmanagement",
    "is_enabled": true
  }
]
```

Die Integration muss Leserechte für jede Seite haben. Mehrere Seiten sind möglich. Unterseiten separat eintragen; die frühere Einstellung `enable_recursive` wird bewusst nicht verwendet. Zum Update das neue lokale Paket erneut installieren. Konfiguration bleibt über Ankis Konfigurationsverwaltung erhalten; eigene Änderungen am Quellcode vorher sichern.

## Struktur und Bilder

Seite → konfigurierter Hauptstapel. Themen-Toggle → Unterstapel. Blatt-Toggle → eine normale Frage-Antwort-Karte. Beispiel: Modellierung → BPMN → Frage ergibt `Uni::Datenmanagement::Modellierung::BPMN`. Titel-Doppelpunkte werden durch Leerzeichen ersetzt. Nur bei Namenskonflikten gibt es einen kurzen Zusatz wie `(2)`. Es werden keine fremden Stapel umbenannt. Sicher erkannte leere alte ID-Stapel werden beim Wechsel auf lesbare Namen bereinigt; sonstige leere Unterstapel bleiben bestehen.

Toggle-Titel und anfängliche direkte Bilder bilden die Frage. Leere Absätze ohne Kinder werden übersprungen. Ab dem ersten anderen Block bleibt alles auf der Rückseite, auch spätere Bilder. Bildunterschriften bleiben beim Bild. Für ein reines Antwortbild einen Absatz „Antwort:“ davor setzen. Leere Frage ohne Fragebild oder leere Antwort bricht den gesamten Lauf ab. Listen, Tabellen, Überschriften, Layoutspalten, Code, Formeln und wichtige Textformatierungen werden unterstützt. Andere Blöcke innerhalb einer Karte brechen den Lauf mit Block-ID ab. Inhalte außerhalb von Blättern werden als Hinweise ausgewiesen.

## Vorschau und Migration

Extras → „Notion Safe Sync: Vorschau / Synchronisieren“. Netzwerkabruf und Bilder laufen im Hintergrund. Erst nach vollständigem Abruf aller aktiven Quellen erscheinen Änderungen, Übernahme-IDs und Lösch-IDs zur Bestätigung. Abbrechen verändert keine Karten.

Das ursprüngliche Add-on verwendet `Notion-Basic` mit `Front`, `Back`, `NotionID`, `LastSync`. Die NotionID enthält Seiten-URL und Block-ID als Fragment. Eindeutige IDs werden übernommen, ohne Notiztyp oder Karten zu ersetzen. Die neue Herkunft liegt bei übernommenen Notizen in eigenen Tags; neue Notizen haben zusätzlich `NotionSync`. Diese Kennzeichnungen nicht manuell verändern. Lokale Front-/Back-Änderungen werden beim nächsten Sync überschrieben.

Doppelte IDs, fehlende IDs und Notizen mit mehreren Kartentypen stoppen die Migration mit Notiz-IDs. Es gibt keine Textähnlichkeits-Zuordnung. Betroffene Altnotizen vorher manuell eindeutig zuordnen oder in einen separaten Notiztyp auslagern. Eindeutig identifizierte alte Notion-Notizen einer aktiven Quelle, deren Block inzwischen fehlt oder zum Thema wurde, erscheinen bereits bei der ersten Migration ausdrücklich in der Löschvorschau. Nicht verwaltete Notizen bleiben erhalten. Deaktivierte oder entfernte Seiten lösen keine Löschung aus.

## Fehler und Wiederherstellung

Abruf-, Validierungs- und Medienfehler passieren vor Sammlungsänderungen. Bilder werden anhand ihres Inhalts lokal gespeichert; signierte URLs stehen nicht auf den Karten. Es erfolgt keine globale Medienbereinigung. Bereits vorbereitete Medien können bei einem späteren Fehler unbenutzt zurückbleiben.

Sammlungsänderungen laufen über `CollectionOp` und werden zu einem Undo-Schritt zusammengeführt. Bei einem Anwendungsfehler wird dieser Schritt sofort zurückgenommen; Löschungen erfolgen erst nach erfolgreichen Updates. Dies ist keine einzelne absturzsichere Transaktion über Netzwerk, Dateien und Sammlung. Bei einem Programmabsturz oder einer gemeldeten fehlgeschlagenen Rücknahme Sammlung aus Ankis Sicherung wiederherstellen. Ein erfolgreich abgeschlossener Lauf kann über Bearbeiten → Rückgängig zurückgenommen werden. Medien werden durch Undo nicht entfernt.

Karten aus Filterstapeln zuerst zurück in ihre regulären Stapel schicken. Der Sync setzt keinen Lernzustand zurück. Alte fehlgeschlagene Importe ohne verwertbare IDs werden nicht automatisch repariert.

## Tatsächlich geprüfte Umgebung und offene Abnahme

Entwickelt und isoliert getestet mit Python 3.12.14 und den offiziellen Python-Paketen Anki/aqt 26.9.3 unter Windows. Das Installationspaket verlangt mindestens 26.9.3. Die tatsächlich installierte Desktop-Anki-Version konnte nicht festgestellt werden. Andere Versionen sind nicht nachgewiesen.

- `test_core.py`: Bildaufteilung (alle sechs Tabellenfälle), leere Eltern mit Kindern, ungültige/unsupported Blöcke, leere Titel mit Bild, Hierarchie mit Layout und Toggle-Überschrift, Unterseiten, globale Pläne, zweite Pagination mit Fehler, Überlappung, Medienfehler und wiederholbare Mediennamen.
- `test_integration.py`: echte temporäre Anki-Sammlung; identischer Sync, IDs/Lernplanung bei Inhalts-/Stapel-/Seitenwechsel, fremde Karte bei Löschung, Undo, deaktivierte Quelle, Blatt/Thema, sichere Migration, mehrdeutige/fehlende IDs, Rücknahme nach injiziertem Fehler, lokale Medien und Front-/Back-Rendering einschließlich Dateikollision.
- `test_ui.py`: Qt ohne sichtbares Fenster; Menüeinträge, Konfigurationsdialog, JSON und Speichern mit synthetischem Token.

Noch manuell nötig: Paket in einem echten Desktop-Testprofil installieren; konfigurierte Notion-Testseite mit drei Toggle-Ebenen, Bildern, Tabelle und Formel abrufen; Vorschau prüfen und bestätigen; Karten im Reviewer ansehen; Anki neu starten und offline prüfen; identisch wiederholen; in Notion korrigieren, verschieben und löschen; Lernhistorie kontrollieren; Zugriff entziehen und unveränderte Sammlung bestätigen. Ebenso regulären Anki-Mediensync zu einem zweiten Gerät prüfen. Ein echter Notion-End-to-End-Lauf, visuelle Desktop-Abnahme und geräteübergreifender Mediensync sind nicht erfolgt.

## Offizielle API-Grundlagen

- https://developers.notion.com/reference/get-block-children — vollständige Pagination und rekursive Kindabrufe. Verwendeter Notion-Version-Header: `2022-06-28` (Block-API, keine Datenbankabfragen).
- https://addon-docs.ankiweb.net/background-ops.html — QueryOp/CollectionOp.
- https://github.com/ankitects/anki/blob/main/pylib/anki/collection.py — Sammlungs- und Undo-APIs; die Tests verwenden konkret 26.9.3.

Tests erneut ausführen: `python test_core.py`, mit importierbarem Anki zusätzlich `python test_integration.py`, mit aqt/PyQt zusätzlich `python test_ui.py`. Unter Windows müssen gegebenenfalls `win32` und `win32/lib` auf dem Python-Suchpfad liegen. Alle Testinhalte sind synthetisch. Das Paket enthält keine Drittanbieter-Bibliotheken; es verwendet Ankis Laufzeit und die Python-Standardbibliothek.
