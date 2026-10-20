# Kartentypen – Notion Safe Sync 1.3.0

## Änderungen in 1.3.0

Die aktuelle vollständige Formatspezifikation steht in **`NOTION_FORMAT.md`**. Neu sind ein eigener Maskeneditor pro betroffener Notiz mit lokaler Quell-/Korrekturtrennung, Inline-Felder direkt in jeder aktuellen Textlücke und der optionale `[Header]`-Metadatenabschnitt mit geschlossenem „Mehr …“ auf der Rückseite. Alle bisherigen Kartentypen und Sync-Funktionen bleiben erhalten.

Beim ersten Sync nach 1.2 sind Bildmasken einmal pro Notiz neu zu bestätigen, weil der alte bildbezogene Hash keine notizbezogene Bestätigung belegt. Danach bleiben bestätigte unveränderte Notizen ohne erneuten Dialog. Bereits bestätigte Notizen lassen sich über „Extras → Notion Safe Sync: Bildmasken bearbeiten“ erneut öffnen. Lokale Korrekturen bleiben bei unverändertem Notion-Stand erhalten. Das Add-on schreibt weiterhin nichts nach Notion; der separate Anki-Skill wurde nicht verändert.

## Installation und erster Test

`Notion_Safe_Sync.ankiaddon` im Ordner „Anki Deck“ über Ankis Erweiterungsverwaltung installieren, Anki neu starten. Alte Erweiterung 576859862 deaktiviert lassen. Konfiguration, Seitenauswahl, dosierter Abruf und Retry-After bleiben erhalten. Zuerst ein separates Testprofil verwenden. Notion und der Anki-Skill wurden nicht verändert.

Die angegebene Notion-Testseite wurde zuerst unverändert über den Connector gelesen und anschließend ausschließlich lesend mit dem neuen Parser geprüft: **7 Notizen, 8 Karten**, Typen basic/input/cloze/cloze_input/image/images/sequence. Es wurde kein produktiver Anki-Sync ausgeführt. Bilder und Inhalte dieser Seite werden nicht in diesem Paket ausgeliefert.

## Formate

| Toggle-Titel | Inhalt vor Zusatzinfo | Ergebnis |
|---|---|---|
| Ohne Marker | bisherige Antwortblöcke | normale Frage–Antwort; bisherige anfängliche Bildaufteilung bleibt |
| `[Eingabe] Frage` | genau eine kurze einzeilige Textantwort | ein natives Anki-Eingabefeld und Vergleich |
| `[Lücke] Organisation` | `Die Stadt ist {{c1::Wien}}.` | native Cloze-Karte; Titel bleibt im Notizfeld zur Organisation |
| `[Lücke+Eingabe] Organisation` | `Der Planet ist {{c1::Jupiter}}.` | native Cloze-Karte mit eigenem Inline-Vergleich pro ausgeblendeter Stelle |
| `[Bildlücke] Aufgabe` | genau ein Bild und eine Abdeckung | eine native Bildverdeckungskarte |
| `[Bildlücken] Aufgabe` | genau ein Bild, mehrere Abdeckungen und Modus | eine native Karte pro Abdeckungs-ID |
| `[Bildfolge] Aufgabe` | genau ein Bild, mehrere Abdeckungen und Reihenfolge | eine Karte mit schrittweisem Aufdeckbutton |

Führende Leerzeichen vor Markern sind erlaubt. Marker werden nicht auf den Karten angezeigt. Themen-Toggles bleiben ausschließlich Themen/Unterstapel. Nur Blatt-Toggles werden importiert.

Bei Eingabe und Cloze beginnt ein eigener Absatz `Zusatzinfo:` den optionalen Erklärungsteil. Dieser erscheint ausschließlich hinten und gehört nicht zur Vergleichsantwort. Beispiel:

```text
[Eingabe] Hauptstadt von Österreich?
  Wien
  Zusatzinfo:
  Wien liegt an der Donau.
```

Die erwartete Eingabe bei `[Eingabe]` ist eine einzelne Textzeile, maximal 500 Zeichen. Cloze verwendet native Anki-Syntax inklusive `{{c1::Antwort::Hinweis}}` und balancierten verschachtelten Clozes. Unterstützte IDs: 1–499. Unterschiedliche Zahlen erzeugen unterschiedliche Karten. Wiederholtes `c1` gruppiert Stellen auf derselben Karte. Bei `[Lücke+Eingabe]` erscheint ab 1.3 an jeder aktuellen Lücke ein eigenes Inline-Feld. Vergleich: NFC-normalisiert, Leerraum vereinheitlicht und außen entfernt; Groß-/Kleinschreibung bleibt relevant. Die native Selbsteinstufung wird nicht automatisch ausgewählt. Details und Header-Regeln: `NOTION_FORMAT.md`.

## Bildmasken

Unter genau einem direkten Originalbild normale Absätze anlegen:

```text
Abdeckung 1: x=10%, y=10%, breite=30%, höhe=15%
Abdeckung 2:
x=55%, y=60%, breite=30%, höhe=15%
Modus: Alle verdecken, eine abfragen
```

Alternativer Modus für `[Bildlücken]`: `Modus: Eine verdecken, eine abfragen`. Im ersten Modus sind alle Stellen verdeckt; die aktuelle wird nativ hervorgehoben und auf der Rückseite aufgedeckt. Im zweiten Modus ist nur die aktuelle Stelle verdeckt. `[Bildlücke]` benötigt keinen Modus. `[Bildfolge]` benötigt stattdessen `Reihenfolge: 1, 2`, die jede Abdeckungs-ID genau einmal enthält. Ein Button deckt gemäß dieser Reihenfolge auf; Ankis Antworttaste zeigt anschließend alles offen. Die gesamte Bildfolge wird einmal bewertet, nicht jeder Klick separat.

Koordinaten beziehen sich auf das gesamte Originalbild, Ursprung links oben. Breite/Höhe müssen positiv sein, Rechtecke vollständig innerhalb 0–100 %. IDs müssen eindeutig sein. Nach Entfernen einer Abdeckung die übrigen IDs beibehalten, nicht neu nummerieren. Bei zwei auf eine verbleibende Abdeckung den Marker ausdrücklich auf `[Bildlücke]` ändern und den Modus entfernen. Die vorhandene Abdeckungs-ID beibehalten (z. B. 2); daraus wird keine neue ID 1.

Steuerdaten erscheinen nicht als Antworttext. Normale Textabsätze können zwischen ID und Koordinaten einen Zeilenumbruch enthalten. Unbekannte Marker, fehlende Bilder/Modi/Reihenfolgen, doppelte Abdeckungs-IDs, ungültige Clozes und ungültige Rechtecke brechen den betroffenen Gesamtlauf vor Sammlungsänderungen ab.

## Vorschau, Identität und Migration

Neue/geänderte Masken erhalten einen eigenen lokalen Kontroll-/Editordialog **pro Notion-Notiz**, mit allen stabil nummerierten Abdeckungen dieser Notiz. Verschieben, Größenänderung, Entfernen und Rückgängig sind möglich. Abbrechen verändert keine Notizen; auch „Bestätigen“ bleibt zunächst ein Entwurf bis zur Gesamtfreigabe. Lokale Korrekturen bleiben bei gleicher Quelle erhalten. Quelländerungen erfordern eine neue Prüfung und werden bei vorhandenen Korrekturen als Konflikt markiert. Es gibt keine gemeinsame Freigabe unterschiedlicher Toggles mit gleichen Bilddaten.

Die Notion-Block-ID identifiziert weiterhin genau eine Notiz. Zusätzliche Karten werden über die native Cloze-/Abdeckungsnummer identifiziert (`cN` → Kartenordinal `N-1`), niemals über Position, Text oder Koordinaten. Koordinaten-/Textkorrekturen erhalten vorhandene Karten-IDs, Lernstände und Planung. Neue Nummern erzeugen neue Karten; entfernte Nummern werden nur nach ausdrücklicher Löschvorschau entfernt. Entfernte und später erneut angelegte IDs erhalten eine neue Karte; gelöschte Lernhistorie wird nicht rekonstruiert.

Typwechsel und zu entfernende Einzelkarten werden in der abschließenden Vorschau mit Notiz-ID, altem/neuem Typ, Quell-IDs und Karten-IDs ausdrücklich aufgeführt. Erst die bestätigte Vorschau autorisiert Anwendung und Löschung. Ein normaler Einzelkartentyp ↔ Cloze/Bildverdeckung kann automatisch nur umgestellt werden, wenn die bisherige Karte ID 1 besitzt und der neue native Typ ebenfalls ID 1 enthält. Bei anderen nicht eindeutig zuordenbaren Wechseln wird sicher abgebrochen; eine manuelle Zuordnung ist erforderlich. Innerhalb nativer Cloze-/Bildtypen bleiben gemeinsame Nummern zugeordnet. Die tatsächliche Zuordnung wird in der isolierten Sammlung geprüft; es gibt keine heuristische Textähnlichkeit.

Die Modelle „Notion Safe Sync – …“ sind eigene, getrennte Notiztypen. Cloze-Kartenerzeugung und `[Eingabe]` nutzen native Anki-Filter. Der Vergleich von `[Lücke+Eingabe]` ist ab 1.3 eine eigene Inline-Lösung mit den dokumentierten Normalisierungsregeln. Bildlücke/Bildlücken klonen das von Anki zur Laufzeit bereitgestellte native Bildverdeckungsmodell samt Feld-Tags, Vorlagen und Laufzeit. Bildfolge verwendet eigene prozentual ausgerichtete HTML-Masken/Buttons. Notiztypwechsel erfolgen über Ankis native ChangeNotetype-API und können Ankis normale Anforderungen an einen vollständigen Sammlungssync auslösen.

## Tatsächlich geprüft / noch offen

- Anki/aqt **26.09.3**, Qt-Laufzeit **6.11.2**, Test-Python **3.12.14** unter Windows. Python **3.13.15** wurde nicht direkt ausgeführt.
- Anonyme Fixtures: sieben Formate, 7 Notizen/8 Karten, identischer Sync ohne Notizupdates, stabile IDs/Lernfortschritte bei Änderungen, Entfernen einzelner Clozes/Abdeckungen, Typwechsel mit expliziter Freigabe und Rücknahme unsicherer Migrationen.
- Bisherige Tests für normale Bildaufteilung, Hierarchie, Seitenauswahl, Retry-After, Quellenschutz, große Importe, Undo und Diagnose.
- **Tatsächlicher AnkiQt-Reviewer**, unsichtbar mit eigener Instanzkennung und temporärem Testprofil: native Eingabe sowie mehrere eigene Inline-Felder, Unicode-/Leerraumvergleich, Tab/Enter, richtige/falsche Antworten und Reset ohne automatische Bewertung; Header bei allen Typen mit geschlossenem „Mehr …“ und nativem Linkhandler; native Bildverdeckung, beide Modi, Skalierung und Bildfolge samt echter Bewertung. Drei getrennte native Maskeneditoren für drei Notizen mit identischem Bild geprüft. Das ersetzt keine manuelle visuelle Abnahme.
- Die konkrete Notion-Testseite wurde nur gelesen/geparst; ihre Notizen wurden nicht in einer produktiven Sammlung angelegt.
- Offen: manuelle sichtbare Desktop-Abnahme in deiner Python-3.13.15-Installation; AnkiMobile/AnkiDroid; regulärer Mediensync und Offline-Review auf einem zweiten Gerät. Die eigene Bildfolge benötigt JavaScript im jeweiligen Reviewer. Keine ungeprüfte Gerätekompatibilität zugesagt.

Quellcode enthält `test_types.py` und `test_reviewer.py`. Letzteres startet ausschließlich ein neu erzeugtes synthetisches Profil unter `Anki Deck/work`, verwendet eine eigene Anki-Instanzkennung und kein produktives Konto. Ausführung mit passender Anki/aqt-Python-Umgebung und `python -u test_reviewer.py`. Installationspakete schließen alle `test_*.py` aus. Zugangsdaten und Testseitenbilder sind nicht enthalten.

Offizielle Grundlagen: [Anki – Bearbeiten/Cloze/Bildverdeckung](https://docs.ankiweb.net/manual/editing), [native Eingabefilter](https://docs.ankiweb.net/manual/templates/fields). Die tatsächlichen APIs und Stockmodelle wurden zusätzlich am installierten Anki-26.09.3-Python-Paket geprüft.
