# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier dokumentiert.
Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

## [Unveröffentlicht]

## [1.1.0] - 2026-10-17

### Hinzugefügt
- Documentation Style (`DOCUMENTATION_STYLE.md`) mit Repo-Klassen, Pflichtdokumenten, Vorlagen für README, CHANGELOG, ARCHITECTURE, RUNBOOK und ADR sowie Regeln zur Versionierung.
- `ARCHITECTURE.md` beschreibt Aufbau und Ablauf der Prüfskripte.
- `CHANGELOG.md` mit den Änderungen je Version.
- Stylechecks melden, wenn der Abschnitt `Version definieren` in einem Projekt fehlt oder mehrfach vorkommt (in C außerdem, wenn er in einer `.c`-Datei steht), und eine noch vorhandene Zeile `Version` im Kopfblock.
- `tools/stylecheck_common.py` enthält den gemeinsamen Code beider Prüfer.
- C-Stylecheck meldet Includes im falschen Include-Abschnitt, Funktionen ohne Trennlinie danach, `break;` hinter einem case-Block und `#define`-Namen, die nicht in Großbuchstaben stehen. Pin-Defines aus CubeMX mit Endung `_Pin` bzw. `_Port` (`LED_Pin`, `LED_GPIO_Port`) sind davon ausgenommen.
- Beide Stylechecks melden mehr als eine Leerzeile zwischen zwei Abschnitten.
- C und Python Coding Style: Regeln für das Leerzeichen nach `//` und für leere Kommentarzeilen; C: Zuordnung der Includes zu den Abschnitten.
- C-Stylecheck prüft die Form aller Header-Abschnitte mit festem Namen (z. B. `Konstanten definieren`, `Version definieren`) und der Typedef-Abschnitte, wie Python bei Konstanten und Klassen.
- C-Stylecheck meldet in `.c`-Dateien Typedefs, und Variablen außerhalb von `Variablen definieren` / `Variablen einbinden`.
- C Coding Style: Unterabschnitte. Ein Abschnitt darf in benannte Blöcke geteilt werden, die nur durch eine Trennlinie getrennt sind. Der C-Stylecheck meldet dafür keine fehlende Leerzeile mehr und zählt Variablen darin zum übergeordneten Variablen-Abschnitt.
- Python-Stylecheck meldet `from`-Importe mit mehr als 5 Namen, die nicht einen Namen pro Zeile haben.
- `.stylecheck`: Der Abschnitt `[doc]` für das geplante `doc_check.py` erzeugt keine Warnung mehr.
- `tools/doc_check.py` prüft, ob ein Projekt alle notwendigen Dokumente hat: Pflichtdateien der Repo-Klasse, per `[doc] require` verlangte ARCHITECTURE, RUNBOOK oder ADRs, `## Lizenz` passend zur `LICENSE`, Fachdokumente in `docs/`, Ordner-READMEs und relative Links. Reports unter `reports/doc/`.
- `.stylecheck` in diesem Repository mit Klasse `referenz` und verlangter ARCHITECTURE.
- Das Repository `Diveturtle93` (GitHub-Profil) wird von allen Prüfskripten übersprungen.

### Geändert
- README nach der Gliederung für Referenz-Repos: Beschreibung, Inhalt, Verwendung und Abhängigkeiten.
- Eine Version pro Repository: Die Zeile `Version` entfällt im Dateikopf, der Abschnitt `Version definieren` steht nur noch einmal im Repository (C Coding Style, Python Coding Style).
- Der Abschnitt `Version definieren` ist pro Datei nicht mehr Pflicht. Wo er steht, müssen `_MAJOR`, `_MINOR`, `_PATCH` und `_DEV` vollständig sein.
- Die Prüfer verwenden eine gemeinsame Version (`STYLECHECK_COMMON_*` in `tools/stylecheck_common.py`) statt je einer eigenen.
- C-Dateien: `Sprache` im Kopfblock muss `C` enthalten, die Include-Abschnitte werden wie in Python auf ihre Form geprüft.
- C und Python Coding Style: Funktionsnamen dürfen Wörter mit `_` trennen (`ADC_Bremsdruck`, `ltc6811_write`). Geprüft werden nur noch die Namen von `#define` (C) und Klassen (Python).
- C-Stylecheck: Als Fall-through-Markierung zählt nur noch `// fall through - <Begruendung>`, andere Schreibweisen werden gemeldet.
- Die Styleguides liegen jetzt in `docs/` (`docs/C_CODING_STYLE.md`, `docs/PYTHON_CODING_STYLE.md`, `docs/DOCUMENTATION_STYLE.md`), wie es der Documentation Style für Fachdokumente verlangt.
- Leerzeichen vor `(` nach Schlüsselwörtern: Python prüft alle Schlüsselwörter (z. B. auch `return (`, `with (`), C zusätzlich `return (`.
- C-Header: Die Typedef-Abschnitte stehen jetzt nach `Version definieren` und vor `Konstanten definieren`. `Funktionen definieren` ist optional.
- C-Quelldateien: `Variablen definieren` ist optional.
- Documentation Style, Versionierung: Hilfsmodule einer Bibliothek (Ringpuffer, Transportschicht, angebundene ICs) haben keine eigene Version, sie gehören zur Version des Hauptheaders.
- Python Coding Style begründet, warum der Debug-Abschnitt anders als in C in jedem Modul Pflicht ist.
- Documentation Style, automatische Prüfung: Ob ARCHITECTURE, RUNBOOK oder ADRs nötig sind, wird in `[doc] require` festgelegt und von `doc_check.py` geprüft.

### Behoben
- C-Stylecheck: Das `default` eines verschachtelten `switch` zählt nicht mehr für den äußeren.
- C-Stylecheck: Eine Fall-through-Markierung mit mehrzeiliger Begründung wird erkannt.
- Beide Stylechecks erkennen gemischte Einrückung aus Tabs und Leerzeichen, nicht nur führende Leerzeichen.
- `tools/README.md` nennt alle automatischen Ausschlüsse so, wie die Prüfer sie anwenden.

## [1.0.0] - 2026-10-14

### Hinzugefügt
- Erste versionierte Veröffentlichung, übernommen aus dem Repository `Diveturtle93`.
- C Coding Style (`C_CODING_STYLE.md`) für `.c`- und `.h`-Dateien.
- Python Coding Style (`PYTHON_CODING_STYLE.md`) für `.py`-Dateien.
- `tools/c_stylecheck.py` prüft C-Dateien gegen den C Coding Style.
- `tools/py_stylecheck.py` prüft Python-Dateien gegen den Python Coding Style.
- Reports je Projekt und eine Übersicht über alle Projekte (`-r`, `-f`, `-c`).
- Projekteinstellungen über die Datei `.stylecheck` im geprüften Projekt.
- Automatische Ausschlüsse für HAL, CMSIS, Build-Ordner, Git-Submodule und virtuelle Python-Umgebungen; von STM32CubeMX erzeugte Dateien werden nur in den `USER CODE`-Bereichen geprüft.

[Unveröffentlicht]: https://github.com/Diveturtle93/Coding_Styleguide/compare/1.1.0...HEAD
[1.1.0]: https://github.com/Diveturtle93/Coding_Styleguide/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/Diveturtle93/Coding_Styleguide/releases/tag/1.0.0
