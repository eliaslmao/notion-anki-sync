# Notion-Format – verbindliche Regeln ab 1.7.1

## Darstellung ab 1.7

In Bildauswahl und Bearbeitungsfenster gibt es zwei sichtbare Varianten: **Bildmasken** (einzeln abfragen, ohne Zahlen auf den Rechtecken) und **Bildreihenfolge** (schrittweise aufdecken, mit laufenden Schrittnummern). Die bestehenden Importmarker und internen Notiztypen unten bleiben aus Kompatibilitätsgründen unverändert. Sichtbare Schrittnummern sind von stabilen Quell-IDs getrennt. Eine Umbenennung in Notion ist nicht erforderlich. Alle sieben eigenen Kartentypen erhalten dieselbe adaptive Grundgestaltung. Bilder bleiben proportional und öffnen per Klick ein Popup innerhalb des Anki-Fensters. Im Desktop-Reviewer müssen alle Reihenfolge-Schritte durchlaufen werden, bevor die Rückseite erreichbar ist; Leertaste/Enter und der native Antwortknopf decken jeweils nur einen Schritt auf. Das Bild wird proportional in die verfügbare Fensterfläche eingepasst. Die letzte aufgedeckte Maske zeigt sofort die Rückseite mit Bewertungsbuttons. Bedienung und Grenzen: `ANLEITUNG_1.7.md`.

## Struktur und Kartentyp

Konfigurierte Seite → Hauptstapel. Toggles mit enthaltenen Toggles → Themen-Unterstapel. Nur Blatt-Toggles erzeugen Notizen. Normale Toggles und Toggle-Überschriften werden unterstützt; echte Unterseiten separat konfigurieren. Block-ID = Notizidentität. Cloze-/Abdeckungs-ID = zusätzliche Kartenidentität. IDs nicht nachträglich neu nummerieren.

Führende Leerzeichen vor Titelmarkern sind erlaubt. Marker erscheinen nicht auf Karten:

| Titel | Bedeutung |
|---|---|
| Ohne Marker | normale Frage–Antwort; Titel und anfängliche direkte Bilder vorne, ab erstem sonstigen nicht leeren Block alles hinten |
| `[Eingabe] Frage` | eine kurze einzeilige erwartete Textantwort; natives Anki-Eingabefeld |
| `[Lücke] Organisation` | native `{{c1::Antwort}}`-Clozes aus dem Inhalt; Titel organisatorisch |
| `[Lücke+Eingabe] Organisation` | native Cloze-Karten, zusätzlich ein eigenes Inline-Eingabefeld je aktuell ausgeblendeter Stelle |
| `[Bildlücke] Aufgabe` | genau ein Originalbild und eine Abdeckung |
| `[Bildlücken] Aufgabe` | genau ein Originalbild, mehrere Quell-Abdeckungen und ein unterstützter Modus |
| `[Bildfolge] Aufgabe` | genau ein Originalbild, mehrere Quell-Abdeckungen und explizite Reihenfolge; eine Karte |

Unterschiedliche Cloze-Zahlen erzeugen unterschiedliche Karten. Wiederholtes `c1` gruppiert mehrere gleichzeitig ausgeblendete Stellen derselben Karte. IDs 1–499. Bei `[Lücke+Eingabe]` erhält jede gleichzeitig ausgeblendete Stelle ihr eigenes Feld, auch bei wiederholtem `c1`. Der Vergleich ist **Unicode-NFC, führende/abschließende Leerzeichen ignoriert, zusammenhängende Leerraumzeichen zu einem Leerzeichen vereinheitlicht; Groß-/Kleinschreibung und sonstige Zeichen bleiben relevant**. Keine automatische Lernbewertung. Tab wechselt Felder, Enter zeigt die Antwort. Nach dem Aufdecken erscheinen Lösung und individuelle Richtig-/Falsch-Rückmeldung. Beim nächsten Fragenaufruf sind die Eingaben leer.

## Zusatzinfo und optionaler Header

Bei Eingabe und Cloze beginnt ein eigener Absatz `Zusatzinfo:` den optionalen Erklärungsteil. Er bleibt ausschließlich hinten und gehört nicht zur Vergleichsantwort.

Für **alle Kartentypen** kann am Ende ein direkter Absatz mit `[Header]` beginnen:

```text
[Lücke+Eingabe] Österreich
  Die Hauptstadt ist {{c1::Wien}}.
  Zusatzinfo:
  Wien liegt an der Donau.
  [Header] Quelle: Vorlesung 3, Seite 12
  Link zum ursprünglichen PDF
  - Weiterer Quellenhinweis
```

Der restliche Inhalt des Header-Absatzes und **alle folgenden direkten Blöcke** sind Metadaten. Genau ein Header pro Blatt; nicht mitten im Text und nicht innerhalb eines verschachtelten Absatzes. Formatierter Text, sichere anklickbare Links und Listen werden unterstützt. Keine freien HTML-/JavaScript-Inhalte werden ausgeführt. Sichere Linkschemata: HTTPS, HTTP und mailto; Anki öffnet Links über seinen vorgesehenen URL-Handler.

Header hat ab seinem Beginn Vorrang vor späteren `Zusatzinfo:`-Wörtern: diese sind dann ebenfalls nur Metadaten. Metadaten sind weder Frage, erwartete Antwort, Cloze-Inhalt noch Bild-Steuerdaten. Cloze-ähnlicher Text im Header/Erklärungsteil wird wörtlich dargestellt und erzeugt keine zusätzlichen Karten. Ein Header ersetzt keine fehlende Antwort oder fehlende Masken. Die bisherige anfängliche Bildaufteilung wird auf den Inhalt **vor** dem Header angewendet.

Auf der Rückseite erscheint unten im Karteninhalt „Mehr …“, standardmäßig geschlossen. Der eigene Informationsbereich ist mit etwa drei bis vier relativen Textzeilen Abstand und dezenter Trennlinie von der Antwort getrennt. Er klappt Metadaten auf und zu, ohne Ankis Bewertungsleiste zu verändern. Ohne Metadaten erscheint kein Button und kein zusätzlicher Abstand. Beim nächsten Kartenaufruf beginnt der Bereich wieder geschlossen.

## Bild-Steuerdaten

Als direkte normale Textabsätze vor dem Header/Erklärungsteil:

```text
Abdeckung 1: x=10%, y=10%, breite=30%, höhe=15%
Abdeckung 2:
x=55%, y=60%, breite=30%, höhe=15%
Modus: Alle verdecken, eine abfragen
```

Alternativer Modus für `[Bildlücken]`: `Modus: Eine verdecken, eine abfragen`. Für `[Bildfolge]` stattdessen `Reihenfolge: 1, 2`, mit jeder Abdeckungs-ID genau einmal. `[Bildlücke]` hat keinen Modus und keine Reihenfolge. Ein Zeilenumbruch zwischen Abdeckungs-ID und Koordinaten ist erlaubt. Ursprung links oben im vollständigen Originalbild, Prozentwerte 0–100; positive Breite/Höhe, vollständig innerhalb des Bildes.

Bei `[Bildlücken]` eine Karte pro ID, bei `[Bildfolge]` eine Karte mit Schritten nach Reihenfolge. Steuerdaten erscheinen nicht als Antworttext. Unbekannte Marker, doppelte Abdeckungs-IDs, fehlerhafte Clozes und ungültige Rechtecke stoppen den Lauf vor Inhaltsänderungen/Löschungen.

## Lokale Maskenkorrekturen

Jede neue/geänderte Bildmasken-Notiz erhält ihren **eigenen** Dialog „Bildmasken bearbeiten“ bzw. „Bildreihenfolge bearbeiten“. Alle Abdeckungen einer Notiz werden gemeinsam geprüft; zwei Toggles mit identischem Bild/identischen Masken erhalten trotzdem zwei Dialoge. Bestätigungen berücksichtigen Block-ID, Kartentyp, Bildinhalt, Masken, Modus/Reihenfolge und Quellaufgabe/-Metadaten. Wechselnde Download-URLs allein ändern diese Identität nicht.

Linksklick+Ziehen verschiebt; Ecken-/Randgriffe ändern die Größe; Rechtsklick entfernt eine Abdeckung. IDs bleiben unverändert. Rückgängig/Wiederholen bzw. Strg+Z/Strg+Y korrigieren versehentliche Änderungen. Ausgewählte Masken sind blau hervorgehoben. Bearbeitung erfolgt in Originalbildkoordinaten und wird als Prozentwerte gespeichert, unabhängig von der Ansichtsgröße.

„Bestätigen“ übernimmt zunächst nur den Dialogentwurf. Erst die anschließende ausdrücklich bestätigte Gesamtvorschau schreibt nach Anki. Abbrechen eines Dialogs oder der Gesamtvorschau übernimmt nichts, auch keine zuvor in diesem Lauf bearbeiteten Entwürfe. Mindestens eine Maske muss bleiben; eine lokale Bearbeitung erzeugt keine leere Notiz. Bei lokaler Reduzierung mehrerer Masken auf eine bleibt die verbleibende ID erhalten; es erfolgt kein automatischer Marker-/ID-Wechsel.

Korrekturen werden lokal an der verwalteten Anki-Notiz mit Herkunft, getrennten Quell-/Korrekturmasken und Quell-Fingerabdruck gespeichert, nicht in Notion. Beim unveränderten Quellstand werden sie wiederverwendet, ohne erneute automatische Kontrolle. Bei geändertem Quellbild, Maskenstand oder Typ ist erneut zu prüfen. Falls dabei lokale Korrekturen vorhanden waren, erscheint ein Konflikthinweis; angezeigt wird die neue Quellgeometrie, nicht blind eine alte Korrektur. Änderungen nur an Aufgabe/Metadaten verlangen ebenfalls eine neue Kontrolle, behalten aber die weiterhin passende lokale Geometrie.

Ab 1.4 öffnet „Extras → Notion Safe Sync: Bildmasken bearbeiten“ eine lokale Auswahl vorhandener verwalteter Bildnotizen mit Titel, Zielstapel und Typ. Einzel-/Mehrfachauswahl sowie Alle/Keine sind möglich. Verwendet werden gespeicherte Masken und Ankis lokales Originalbild; kein Token und kein Notion-Abruf. Jede Notiz öffnet einmal mit allen Masken. Alle Entwürfe werden gemeinsam gespeichert; Abbrechen verwirft den ganzen Aufruf. Fehlende Bilder und unlesbare/mehrdeutige Herkunftsdaten führen zu einer Meldung ohne Speicherung der betroffenen Notiz. Unverändertes Bestätigen schreibt nichts. Die getrennte Aktion „Bildmasken anhand Notion erneut prüfen“ bietet den bisherigen erneuten Quellabruf mit Seitenauswahl.

Im unterstützten Desktop-Reviewer ergänzt die gezielte Anki-Brücke unten „Masken bearbeiten“ statt „Toggle Masks“. Der Editor erhält genau die angezeigte Notiz, bei Bildlücke/Bildlücken mit vorausgewählter aktueller Abdeckungs-ID. Speichern aktualisiert dieselbe Karte und Seite ohne Bewertung oder nächste Karte. Wird gerade diese Karte ausdrücklich gelöscht, endet ihre Anzeige in der Stapelübersicht mit Hinweis. Bildfolge behält ihre Aufdeckschaltfläche. In anderen Clients und Vorschauen wird kein funktionsloser Bearbeiten-Button erzeugt. Beide lokalen Einstiege verwenden dieselbe Speicher-/Validierungslogik und ausdrückliche Löschbestätigung. Details: `ANLEITUNG_1.4.md`.

Entfernte Masken können gelernte Karten betreffen. Die Gesamtvorschau nennt ausdrücklich die gelöschten Karten- und Quell-IDs. Die übrigen Karten behalten ID und Lernfortschritt. Beim Entfernen von Bildfolge-Schritten bleibt deren einzelne Gesamtkarte bestehen; die Aufdeckreihenfolge wird um die entfernten IDs bereinigt.

## Clients

Funktional geprüft: Windows Anki/aqt 26.09.3 mit echter Reviewer-/Scheduler-/Chromium-Laufzeit, Qt 6.11.2, Test-Python 3.12.14. Python 3.13.15, AnkiMobile und AnkiDroid nicht direkt geprüft. Inline-Vergleich und Bildfolge benötigen JavaScript. Browser-Vorschau und fremde Clients sind kein Nachweis für Ankis Desktop-Reviewer. Die native Variante von `[Eingabe]` bleibt erhalten. Nicht ausgewählte ältere 1.2-Cloze-Eingaben behalten ihren bisherigen nativen Einzelfeld-Fallback bis zum eigenen Sync.
